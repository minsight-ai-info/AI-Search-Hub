import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from camofox_runner import (
    find_ref_by_role,
    find_ref_by_text,
    get_text,
    get_url,
    list_sessions,
    load_session,
    open_url,
    press,
    save_session,
    snapshot,
    type_text,
    wait_seconds,
)

COMMON_NOISE_SUBSTRINGS = [
    "内容由 AI 生成",
    "AI-generated",
    "AI 生成",
]

SITE_CONFIG = {
    "qwen": {
        "url": "https://chat.qwen.ai/",
        "input_role": "textbox",
        "input_hint": "How can I help you today?",
        "submit_key": "Enter",
        "login_text": "Log in",
        "login_signup_text": "Sign up",
        "answer_roles": ("paragraph", "heading"),
        "answer_contains": ("Thinking completed",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + [
            "AI-generated content may not be accurate",
            "By using Qwen Studio, you agree to our Terms of Service and Privacy Policy",
        ],
    },
    "gemini": {
        "url": "https://gemini.google.com/app",
        "input_role": "textbox",
        "input_hint": "Enter a prompt",
        "submit_key": "Enter",
        "login_text": "Sign in",
        "answer_roles": ("paragraph", "heading"),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "grok": {
        "url": "https://grok.com/",
        "input_role": "textbox",
        "input_hint": "Ask Grok anything",
        "submit_key": "Enter",
        "login_text": "Sign in",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "minimaxi": {
        "url": "https://agent.minimaxi.com/",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "Sign in",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + [
            "内容由 MiniMax 生成",
            "内容由AI生成，重要信息请务必核",
        ],
    },
    "kimi": {
        "url": "https://kimi.moonshot.cn/",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + [
            "内容由 Kimi 生成",
            "由 Kimi 生成",
        ],
    },
    "doubao": {
        "url": "https://www.doubao.com/chat/?channel=sysceo&from_login=1",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "yuanbao": {
        "url": "https://yuanbao.tencent.com/chat",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "longcat": {
        "url": "https://longcat.chat/",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run AI Search Hub via camofox browser automation."
    )
    parser.add_argument(
        "--site",
        choices=sorted(SITE_CONFIG),
        required=True,
        help="Target chat site.",
    )
    parser.add_argument("--prompt", required=True, help="Question to send.")
    parser.add_argument("--output", help="Optional file path to store the final answer.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Maximum seconds to wait for the final answer.",
    )
    parser.add_argument(
        "--stable-rounds",
        type=int,
        default=4,
        help="How many unchanged polls indicate the answer is complete.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds while waiting for the answer.",
    )
    parser.add_argument(
        "--login-timeout",
        type=int,
        default=600,
        help="Maximum seconds to wait for manual login.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to the current directory or nearest parent containing scripts.",
    )
    return parser.parse_args()


def find_repo_root(start: Optional[str]) -> Path:
    if start:
        candidate = Path(start).expanduser().resolve()
        if (candidate / "scripts" / "camofox_runner.py").exists():
            return candidate
        raise RuntimeError(f"repo-root does not contain camofox scripts: {candidate}")

    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "scripts" / "camofox_runner.py").exists():
            return candidate
    raise RuntimeError("Could not find the repository root containing camofox scripts.")


def wait_for_login(site: str, login_timeout: int) -> None:
    print(
        f"[{site}] login may be required. If a login page appears, complete login in the camofox browser; "
        f"execution will continue automatically for up to {login_timeout} seconds.",
        flush=True,
    )
    deadline = time.time() + login_timeout
    last_snapshot = ""
    stable = 0
    config = SITE_CONFIG[site]

    while time.time() < deadline:
        text = snapshot()
        if text == last_snapshot:
            stable += 1
        else:
            last_snapshot = text
            stable = 0

        # Detect still-on-login-page after login timeout window.
        if stable >= 3:
            lowered = text.lower()
            login_markers = [
                config["login_text"].lower(),
                config.get("login_signup_text", "").lower(),
                "sign in",
                "log in",
                "登录",
                "注册",
                "sign up",
            ]
            if any(marker and marker in lowered for marker in login_markers if marker):
                continue
            return

        wait_seconds(1.0)

    print(f"[{site}] login wait timed out after {login_timeout} seconds.", flush=True)


def normalize_text(text: str, noise_substrings: Optional[list[str]] = None) -> str:
    """Strip noise and collapse whitespace."""
    noise = set(noise_substrings or [])
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(n in line for n in noise):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def extract_answer_from_snapshot(
    snapshot_text: str,
    site: str,
    question: str,
) -> str:
    """Extract the assistant answer from an accessibility snapshot."""
    config = SITE_CONFIG[site]
    noise = config.get("noise_substrings", [])
    answer_roles = config.get("answer_roles", ("paragraph",))
    answer_contains = config.get("answer_contains", ())

    # The assistant answer on Qwen and similar chat UIs typically appears as
    # either a `paragraph:` line or a `text:` line in the accessibility tree.
    candidate_lines: list[str] = []
    for line in snapshot_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(n in stripped for n in noise):
            continue
        for role in answer_roles:
            if stripped.startswith(f"- {role} ") or stripped.startswith(f"- {role}:"):
                content = stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped
                if content:
                    candidate_lines.append(content)
                break
        # Also capture generic text lines that are not UI noise.
        if stripped.startswith("- text:"):
            content = stripped.split(":", 1)[-1].strip()
            if content and not any(n in content for n in noise):
                candidate_lines.append(content)

    # Fallback: if no role-based candidates, try any non-noise, non-ui line.
    if not candidate_lines:
        for line in snapshot_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(n in stripped for n in noise):
                continue
            if stripped.startswith("-"):
                continue
            if stripped.startswith("?") or stripped.startswith("By "):
                continue
            candidate_lines.append(stripped)

    if not candidate_lines:
        return ""

    # Remove the user's question from the candidate lines.
    normalized_question = normalize_text(question, noise)
    if normalized_question:
        candidate_lines = [
            line for line in candidate_lines
            if normalized_question not in line
        ]

    # Prefer lines that contain answer indicators.
    if answer_contains:
        containing = [
            line for line in candidate_lines
            if any(c in line for c in answer_contains)
        ]
        if containing:
            candidate_lines = containing

    # Join and clean up.
    answer = "\n".join(candidate_lines).strip()
    for fragment in ["AI-generated content may not be accurate", "Terms of Service and Privacy Policy"]:
        answer = answer.replace(fragment, "")
    return answer.strip()


def collect_answer_from_snapshot(
    site: str,
    question: str,
    timeout: int,
    stable_rounds: int,
    interval: float,
) -> str:
    """Poll snapshots and extract the answer text."""
    deadline = time.time() + timeout
    last_answer = ""
    stable_count = 0
    last_snapshot = ""

    while time.time() < deadline:
        snap = snapshot()
        if snap == last_snapshot:
            stable_count += 1
        else:
            last_snapshot = snap
            # New snapshot content means the page changed; reset stability.
            if stable_count >= stable_rounds:
                stable_count = stable_rounds - 1
            else:
                stable_count = 0

        answer = extract_answer_from_snapshot(snap, site, question)
        if answer:
            if answer == last_answer:
                stable_count += 1
            else:
                last_answer = answer
                stable_count = 0

        if stable_count >= stable_rounds and last_answer:
            return last_answer

        wait_seconds(interval)

    return last_answer.strip()


def main(default_site: Optional[str] = None) -> int:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = parse_args()
    site = args.site
    repo_root = find_repo_root(args.repo_root)

    config = SITE_CONFIG[site]

    # ------------------------------------------------------------------ session
    existing_sessions = list_sessions(cwd=repo_root)
    if site in existing_sessions:
        print(f"[{site}] reusing saved camofox session: {site}", flush=True)
        tab_id = open_url(config["url"], cwd=repo_root)
        print(f"[{site}] opened {config['url']} tab={tab_id}", flush=True)
        load_session(site, tab_id=tab_id, cwd=repo_root)
        print(f"[{site}] session loaded", flush=True)
    else:
        print(f"[{site}] no saved session found; opening fresh", flush=True)
        tab_id = open_url(config["url"], cwd=repo_root)
        print(f"[{site}] opened {config['url']} tab={tab_id}", flush=True)

        wait_for_login(site, args.login_timeout)

        # Detect whether we are still on the login page after waiting.
        snap = snapshot(tab_id=tab_id, cwd=repo_root)
        login_markers = [
            config.get("login_text", "").lower(),
            config.get("login_signup_text", "").lower(),
            "sign in",
            "log in",
            "登录",
            "注册",
            "sign up",
        ]
        lowered = snap.lower()
        still_login = any(m and m in lowered for m in login_markers if m)
        if still_login:
            print(
                f"[{site}] still appears to be on the login page; the run may fail "
                f"until you complete login and rerun.",
                flush=True,
            )
        else:
            print(f"[{site}] saving session '{site}' for reuse", flush=True)
            save_session(site, tab_id=tab_id, cwd=repo_root)

    try:
        snap = snapshot(tab_id=tab_id, cwd=repo_root)
        input_ref = find_ref_by_role(snap, config["input_role"], config.get("input_hint"))
        if not input_ref:
            input_ref = find_ref_by_role(snap, "textbox")
        if not input_ref:
            raise RuntimeError(
                f"[{site}] could not find input box in snapshot:\n{snap}"
            )

        type_text(input_ref, args.prompt, tab_id=tab_id, cwd=repo_root)
        press(config["submit_key"], tab_id=tab_id, cwd=repo_root)

        answer = collect_answer_from_snapshot(
            site, args.prompt, args.timeout, args.stable_rounds, args.interval
        )
        if not answer:
            print(f"[{site}] no answer collected within timeout.", flush=True)
            return 1

        print("\n===== 最终回答 =====\n")
        print(answer)

        if args.output:
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(answer, encoding="utf-8")
            print(f"\n[{site}] answer saved to {path}", flush=True)

        return 0

    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
