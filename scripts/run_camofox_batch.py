import argparse
import concurrent.futures
import json
import sys
import time
from pathlib import Path

from camofox_runner import (
    click,
    find_ref_by_role,
    find_ref_by_text,
    list_sessions,
    load_session,
    open_url,
    run,
    snapshot,
    type_text,
    wait_seconds,
)
from run_camofox_chat import (
    SITE_CONFIG,
    clean_custom_answer,
    decode_doubao_payload,
    extract_answer_from_snapshot,
    has_login_blocker,
    is_answer_ready,
    submit_prompt,
    wait_for_chat_ready,
)


def build_command(
    repo_root: Path,
    site: str,
    prompt: str,
    output_dir: Path,
    timeout: int,
    min_answer_chars: int,
) -> list[str]:
    """Compatibility helper; documents the equivalent one-site invocation."""
    return [
        sys.executable,
        str(repo_root / "scripts" / "run_camofox_chat.py"),
        "--site", site,
        "--prompt", prompt,
        "--timeout", str(timeout),
        "--min-answer-chars", str(min_answer_chars),
        "--output", str(output_dir / f"{site}.txt"),
    ]


def is_retriable_open_error(message: str) -> bool:
    return any(marker in message for marker in (
        "NS_BINDING_ABORTED", "NS_ERROR_UNKNOWN_HOST", "Request timed out", "page.goto",
    ))


def is_retriable_poll_error(message: str) -> bool:
    """Browser RPC timeouts are transient; keep the model tab alive until its deadline."""
    lower = message.lower()
    return any(marker in lower for marker in (
        "request timed out",
        "ns_binding_aborted",
        "ns_error_unknown_host",
    ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare chat tabs serially, then poll all platform answers in one coordinated loop."
    )
    parser.add_argument("--sites", nargs="+", required=True, choices=sorted(SITE_CONFIG))
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--min-answer-chars", type=int, default=200)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--stable-rounds", type=int, default=3)
    parser.add_argument("--open-retries", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def open_with_retry(url: str, repo_root: Path, attempts: int) -> str:
    error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return open_url(url, cwd=repo_root)
        except RuntimeError as exc:
            error = exc
            if not is_retriable_open_error(str(exc)) or attempt == attempts:
                raise
            wait_seconds(2.0 * attempt)
    raise RuntimeError(str(error))


def prepare_site(site: str, prompt: str, repo_root: Path, sessions: set[str], open_retries: int) -> dict:
    """Serial browser navigation avoids camofox's single-navigation race."""
    config = SITE_CONFIG[site]
    tab_id = open_with_retry(config["url"], repo_root, open_retries)
    if site in sessions:
        load_session(site, tab_id=tab_id, cwd=repo_root)
    wait_seconds(2.0)
    snap = snapshot(tab_id=tab_id, cwd=repo_root)
    if has_login_blocker(snap, site):
        raise RuntimeError("blocking login UI detected; login is required before batch execution")
    if not wait_for_chat_ready(site, 12, tab_id=tab_id, cwd=repo_root):
        raise RuntimeError("chat composer did not become ready")
    snap = snapshot(tab_id=tab_id, cwd=repo_root)
    input_ref = find_ref_by_role(snap, config["input_role"], config.get("input_hint"))
    if not input_ref:
        input_ref = find_ref_by_role(snap, "textbox")
    if not input_ref:
        raise RuntimeError("chat input was not found")
    type_text(input_ref, prompt, tab_id=tab_id, cwd=repo_root)
    submit_prompt(site, snapshot(tab_id=tab_id, cwd=repo_root), tab_id, cwd=repo_root)
    return {"site": site, "tab_id": tab_id, "last_answer": "", "stable_count": 0, "started": time.monotonic()}


def extract_candidate(task: dict, prompt: str, repo_root: Path) -> tuple[str, str]:
    site = task["site"]
    snap = snapshot(tab_id=task["tab_id"], cwd=repo_root)
    custom_js = SITE_CONFIG[site].get("custom_answer_js")
    if custom_js:
        result = run(["camofox-browser", "eval", custom_js, task["tab_id"]], cwd=repo_root)
        raw = result.get("result", "") or result.get("raw", "")
        if site == "doubao" and isinstance(raw, str):
            raw, _ = decode_doubao_payload(raw)
        answer = clean_custom_answer(raw, prompt, site) if isinstance(raw, str) else ""
    else:
        answer = extract_answer_from_snapshot(snap, site, prompt)
    return answer, snap


def close_tab(tab_id: str, repo_root: Path) -> None:
    try:
        run(["camofox-browser", "close", tab_id], cwd=repo_root)
    except Exception:
        pass


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    sites = list(dict.fromkeys(args.sites))
    sessions = set(list_sessions(cwd=repo_root))
    tasks: list[dict] = []
    records: list[dict] = []

    print(f"Preparing {len(sites)} browser tabs serially; responses will then be polled together.", flush=True)
    for site in sites:
        started = time.monotonic()
        try:
            task = prepare_site(site, args.prompt, repo_root, sessions, args.open_retries)
            tasks.append(task)
            print(f"[{site}] prompt submitted", flush=True)
        except Exception as exc:
            records.append({
                "site": site,
                "ok": False,
                "reason": str(exc),
                "duration_seconds": round(time.monotonic() - started, 1),
            })
            print(f"[{site}] preparation failed: {exc}", flush=True)

    while tasks:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {executor.submit(extract_candidate, task, args.prompt, repo_root): task for task in tasks}
            poll_results = []
            for future, task in futures.items():
                try:
                    poll_results.append((task, *future.result()))
                except Exception as exc:
                    poll_results.append((task, exc, None))

        for task, answer_or_error, snap in poll_results:
            site = task["site"]
            elapsed = time.monotonic() - task["started"]
            if elapsed > args.timeout:
                records.append({"site": site, "ok": False, "reason": "answer timeout", "duration_seconds": round(elapsed, 1)})
                close_tab(task["tab_id"], repo_root)
                tasks.remove(task)
                continue
            if isinstance(answer_or_error, Exception):
                error_message = str(answer_or_error)
                if is_retriable_poll_error(error_message):
                    task["poll_retries"] = task.get("poll_retries", 0) + 1
                    print(f"[{site}] transient browser poll timeout; keeping tab alive (retry {task['poll_retries']})", flush=True)
                    continue
                records.append({"site": site, "ok": False, "reason": f"poll failed: {error_message}", "duration_seconds": round(elapsed, 1)})
                close_tab(task["tab_id"], repo_root)
                tasks.remove(task)
                continue
            answer = answer_or_error
            lower_snap = snap.lower()
            if "system is currently busy" in lower_snap or "capacity is busy" in lower_snap:
                records.append({"site": site, "ok": False, "reason": "platform capacity busy", "duration_seconds": round(elapsed, 1)})
                close_tab(task["tab_id"], repo_root)
                tasks.remove(task)
                continue
            if not is_answer_ready(site, answer, snap, args.min_answer_chars):
                continue
            if answer == task["last_answer"]:
                task["stable_count"] += 1
            else:
                task["last_answer"] = answer
                task["stable_count"] = 0
            if task["stable_count"] >= args.stable_rounds:
                output_path = output_dir / f"{site}.txt"
                output_path.write_text(answer, encoding="utf-8")
                records.append({
                    "site": site,
                    "ok": True,
                    "duration_seconds": round(elapsed, 1),
                    "output": str(output_path),
                    "chars": len(answer),
                })
                print(f"[{site}] complete: {len(answer)} chars in {elapsed:.1f}s", flush=True)
                close_tab(task["tab_id"], repo_root)
                tasks.remove(task)
        if tasks:
            wait_seconds(args.interval)

    records.sort(key=lambda record: sites.index(record["site"]))
    summary = {
        "prompt": args.prompt,
        "timeout_seconds": args.timeout,
        "min_answer_chars": args.min_answer_chars,
        "records": records,
    }
    summary_path = output_dir / "batch-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path}", flush=True)
    return 0 if all(record["ok"] for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
