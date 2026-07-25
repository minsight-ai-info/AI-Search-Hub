import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from camofox_runner import (
    click,
    fill_credentials,
    find_ref_by_role,
    find_ref_by_text,
    get_text,
    get_url,
    list_sessions,
    load_session,
    open_url,
    press,
    run,
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

# Navigation and onboarding text that appears in AX snapshots but is never an
# assistant reply. Keep entries specific enough to avoid filtering real content.
CHAT_SHELL_NOISE = [
    "Chats",
    "Instant High",
    "Explore inspiration",
    "Need help? Feedback",
    "Imagine",
    "Make stunning AI images & videos",
    "Use Skills & Connectors",
    "Generate files",
    "Chat history",
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
        "custom_answer_js": None,
    },
    "gemini": {
        "url": "https://gemini.google.com/app",
        "input_role": "textbox",
        "input_hint": "Enter a prompt",
        "submit_key": "Enter",
        "login_text": "Sign in",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
        "custom_answer_js": None,
    },
    "grok": {
        "url": "https://grok.com/",
        "input_role": "textbox",
        "input_hint": "Ask Grok anything",
        "submit_key": "Enter",
        "login_text": "Sign in",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
        "custom_answer_js": None,
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
        "custom_answer_js": None,
    },
    "kimi": {
        "url": "https://kimi.moonshot.cn/",
        "input_role": "textbox",
        "input_hint": "Ask anything, or task an agent...",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + [
            "内容由 Kimi 生成",
            "由 Kimi 生成",
        ],
        "custom_answer_js": None,
    },
    "doubao": {
        "url": "https://www.doubao.com/chat/?channel=sysceo&from_login=1",
        "input_role": "textbox",
        "input_hint": "发消息或按住空格说话...",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
        "custom_answer_js": (
            "(() => {"
            "const wrappers = Array.from(document.querySelectorAll('div.flex.flex-col.flex-grow.max-w-full.min-w-0'));"
            "if (!wrappers.length) return '';"
            "const lastWrapper = wrappers[wrappers.length - 1];"
            "const firstBlock = lastWrapper.children[0];"
            "if (!firstBlock) return '';"
            "return (firstBlock.innerText || firstBlock.textContent || '').trim();"
            "})()"
        ),
    },
    "yuanbao": {
        "url": "https://yuanbao.tencent.com/chat",
        "input_role": "textbox",
        "input_hint": "",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
        "custom_answer_js": None,
    },
    "longcat": {
        "url": "https://longcat.chat/",
        "input_role": "textbox",
        "input_hint": "Tell me what you need.",
        "submit_key": "Enter",
        "login_text": "登录",
        "answer_roles": ("paragraph",),
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
        "custom_answer_js": None,
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
    parser.add_argument("--email", help="Email for auto-login. Required when no saved session exists.")
    parser.add_argument("--password", help="Password for auto-login. Required when no saved session exists.")
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


def is_chat_ready(snapshot_text: str, site: str) -> bool:
    """Return whether the site's chat composer is present in an AX snapshot."""
    config = SITE_CONFIG[site]
    hint = config.get("input_hint", "").lower()
    lowered = snapshot_text.lower()
    if hint:
        return hint in lowered
    # A few sites expose an unlabeled composer.  Do not treat credential forms
    # as a ready chat UI; those are handled as a login blocker below.
    return "textbox" in lowered and not any(
        marker in lowered for marker in ("password", "邮箱", "email", "请输入手机号")
    )


def has_login_blocker(snapshot_text: str, site: str) -> bool:
    """Detect a login form/modal that actually blocks chat, not a header action."""
    lowered = snapshot_text.lower()
    if site == "doubao" and any(
        marker in lowered for marker in ("dialog", "登录以解锁", "请输入手机号")
    ):
        return True

    # Credential fields are unambiguous evidence of a login flow.
    credential_markers = ("password", "邮箱", "email", "请输入手机号")
    if any(marker in lowered for marker in credential_markers):
        return True

    # A standalone sign-in/sign-up page has a login action but no composer.
    login_markers = ("sign in", "log in", "sign up", "signin", "signup", "登录", "注册")
    return not is_chat_ready(snapshot_text, site) and any(
        marker in lowered for marker in login_markers
    )


def is_login_page(snapshot_text: str, site: str) -> bool:
    """Backward-compatible alias for the blocking-login classifier."""
    return has_login_blocker(snapshot_text, site)


def save_debug_state(
    site: str,
    stage: str,
    snapshot_text: str,
    tab_id: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Path:
    """Persist AX state and, when possible, a PNG screenshot for diagnosis."""
    debug_dir = Path.home() / "artifacts" / "ai-search-hub" / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    base = debug_dir / f"{site}-{stage}-{stamp}"
    text_path = base.with_suffix(".txt")
    text_path.write_text(snapshot_text, encoding="utf-8")
    try:
        cmd = ["camofox-browser", "screenshot", "--path", str(base.with_suffix(".png"))]
        if tab_id:
            cmd.append(tab_id)
        run(cmd, cwd=cwd)
    except Exception:
        pass
    return text_path


def wait_for_chat_ready(
    site: str,
    timeout: int,
    tab_id: Optional[str] = None,
    cwd: Optional[Path] = None,
    ready_polls: int = 2,
) -> bool:
    """Wait for a loaded chat UI, without saving or assuming authentication."""
    deadline = time.time() + timeout
    ready_count = 0
    while time.time() < deadline:
        text = snapshot(tab_id=tab_id, cwd=cwd)
        if has_login_blocker(text, site):
            return False
        if is_chat_ready(text, site):
            ready_count += 1
            if ready_count >= ready_polls:
                return True
        else:
            ready_count = 0
        wait_seconds(1.0)
    return False


def wait_for_login(
    site: str,
    login_timeout: int,
    tab_id: Optional[str] = None,
    cwd: Optional[Path] = None,
    ready_polls: int = 2,
) -> bool:
    """Wait until the login blocker is gone and the composer is stable.

    A saved session is created only after consecutive ready snapshots.  This
    avoids treating a clicked login button (or EOF on a non-interactive shell)
    as proof that login succeeded.
    """
    print(
        f"[{site}] 检测到需要登录。请在 camofox 浏览器完成登录；"
        f"脚本会自动继续，最长等待 {login_timeout} 秒。",
        flush=True,
    )
    deadline = time.time() + login_timeout
    ready_count = 0
    reported_blocker = False
    last_snapshot = ""

    while time.time() < deadline:
        text = snapshot(tab_id=tab_id, cwd=cwd)
        last_snapshot = text
        if has_login_blocker(text, site):
            ready_count = 0
            if not reported_blocker:
                save_debug_state(site, "login-blocked", text, tab_id=tab_id, cwd=cwd)
                print(f"[{site}] 登录窗口仍在，等待完成登录。", flush=True)
                reported_blocker = True
        elif is_chat_ready(text, site):
            ready_count += 1
            if ready_count >= ready_polls:
                save_session(site, tab_id=tab_id, cwd=cwd)
                print(f"[{site}] 登录成功，session 已保存。", flush=True)
                return True
        else:
            ready_count = 0
        wait_seconds(1.0)

    if last_snapshot:
        save_debug_state(site, "login-timeout", last_snapshot, tab_id=tab_id, cwd=cwd)
    print(f"[{site}] 等待登录超时，未检测到稳定的聊天输入框。", flush=True)
    return False


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
    """Extract the assistant answer from an accessibility snapshot.
    More robust version with stronger login page filtering."""
    config = SITE_CONFIG[site]
    noise = [*config.get("noise_substrings", []), *CHAT_SHELL_NOISE]
    answer_roles = config.get("answer_roles", ("paragraph",))
    answer_contains = config.get("answer_contains", ())

    candidate_lines: list[str] = []

    for line in snapshot_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(n in stripped for n in noise):
            continue

        # Skip obvious login/signup noise (new robust rule)
        if any(m in stripped.lower() for m in ["sign up", "sign in", "log in", "登录", "注册", "signup", "signin", "password", "email", "account", "phone", "手机号"]):
            continue

        for role in answer_roles:
            if stripped.startswith(f"- {role} ") or stripped.startswith(f"- {role}:"):
                content = stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped
                if content:
                    candidate_lines.append(content)
                break

        # Also capture generic text lines that are not UI noise
        if stripped.startswith("- text:"):
            content = stripped.split(":", 1)[-1].strip()
            if content and not any(n in content for n in noise):
                candidate_lines.append(content)

    # Fallback: if no role-based candidates, try any non-noise, non-ui line
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

    # Remove the user's question (keep trailing answer text)
    normalized_question = normalize_text(question, noise)
    if normalized_question:
        cleaned = []
        for line in candidate_lines:
            if normalized_question in line:
                rest = line.replace(normalized_question, "").strip()
                if rest:
                    cleaned.append(rest)
            else:
                cleaned.append(line)
        candidate_lines = cleaned

    # Prefer lines that contain answer indicators
    if answer_contains:
        containing = [
            line for line in candidate_lines
            if any(c in line for c in answer_contains)
        ]
        if containing:
            candidate_lines = containing

    # Final cleanup
    answer = "\n".join(candidate_lines).strip()
    for fragment in ["AI-generated content may not be accurate", "Terms of Service and Privacy Policy", "Sign up to continue seamlessly"]:
        answer = answer.replace(fragment, "")
    return answer.strip()


def collect_answer_from_snapshot(
    site: str,
    question: str,
    timeout: int,
    stable_rounds: int,
    interval: float,
    tab_id: str,
    cwd: Optional[Path] = None,
) -> str:
    """Poll snapshots and extract the answer text."""
    deadline = time.time() + timeout
    last_answer = ""
    stable_count = 0
    last_snapshot = ""
    config = SITE_CONFIG[site]
    custom_js = config.get("custom_answer_js")

    while time.time() < deadline:
        snap = snapshot(tab_id=tab_id, cwd=cwd)
        if snap == last_snapshot:
            stable_count += 1
        else:
            last_snapshot = snap
            if stable_count >= stable_rounds:
                stable_count = stable_rounds - 1
            else:
                stable_count = 0

        if custom_js:
            try:
                js_result = run(
                    ["camofox-browser", "eval", custom_js, tab_id],
                    cwd=cwd,
                )
                answer = js_result.get("result", "") or js_result.get("raw", "")
                if isinstance(answer, str):
                    answer = answer.strip()
            except Exception:
                answer = ""
        else:
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
    reusing_session = site in existing_sessions
    if reusing_session:
        print(f"[{site}] reusing saved camofox session: {site}", flush=True)
    else:
        print(f"[{site}] no saved session found; opening fresh", flush=True)

    tab_id = open_url(config["url"], cwd=repo_root)
    print(f"[{site}] opened {config['url']} tab={tab_id}", flush=True)
    if reusing_session:
        load_session(site, tab_id=tab_id, cwd=repo_root)
        print(f"[{site}] session loaded; validating chat state", flush=True)

    # A freshly opened page and a restored session can both land on a login
    # screen.  Always validate before sending the prompt.
    wait_seconds(2.0)
    snap = snapshot(tab_id=tab_id, cwd=repo_root)
    session_saved = False
    if has_login_blocker(snap, site):
        print(f"[{site}] detected blocking login UI.", flush=True)
        auto_logged_in = False
        if args.email and args.password:
            email_ref = find_ref_by_role(snap, "textbox", "Email") or find_ref_by_role(snap, "textbox", "邮箱")
            password_ref = find_ref_by_role(snap, "textbox", "Password") or find_ref_by_role(snap, "textbox", "密码")
            if email_ref and password_ref:
                print(f"[{site}] attempting auto-login with provided credentials...", flush=True)
                try:
                    fill_credentials(tab_id, email_ref, password_ref, args.email, args.password, cwd=repo_root)
                    refreshed = snapshot(tab_id=tab_id, cwd=repo_root)
                    signin_ref = find_ref_by_text(refreshed, "Sign in") or find_ref_by_text(refreshed, "登录")
                    if signin_ref:
                        click(signin_ref, tab_id=tab_id, cwd=repo_root)
                    auto_logged_in = wait_for_chat_ready(site, 8, tab_id=tab_id, cwd=repo_root)
                    if auto_logged_in:
                        save_session(site, tab_id=tab_id, cwd=repo_root)
                        session_saved = True
                        print(f"[{site}] auto-login succeeded; session saved.", flush=True)
                except Exception as exc:
                    print(f"[{site}] auto-login failed: {exc}", flush=True)

        if not auto_logged_in:
            if not wait_for_login(site, args.login_timeout, tab_id=tab_id, cwd=repo_root):
                return 1
            session_saved = True
    elif not wait_for_chat_ready(site, 12, tab_id=tab_id, cwd=repo_root):
        save_debug_state(site, "chat-not-ready", snap, tab_id=tab_id, cwd=repo_root)
        print(f"[{site}] 页面未进入可用聊天状态，已保存调试快照。", flush=True)
        return 1
    elif not reusing_session:
        # A no-login site still gets a reusable browser state, but only after
        # the composer has appeared in consecutive snapshots.
        save_session(site, tab_id=tab_id, cwd=repo_root)
        session_saved = True
        print(f"[{site}] chat state confirmed; session saved.", flush=True)

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
            site, args.prompt, args.timeout, args.stable_rounds, args.interval, tab_id, cwd=repo_root
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
