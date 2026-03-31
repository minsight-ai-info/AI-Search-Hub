import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Iterable
from typing import Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import sync_playwright


COMMON_INPUT_SELECTORS = [
    "textarea",
    'div[role="textbox"]',
    '[contenteditable="true"]',
]

COMMON_SEND_SELECTORS = [
    'button:has-text("发送")',
    'button:has-text("Send")',
    'button:has-text("提交")',
    'button[aria-label*="发送"]',
    'button[aria-label*="Send"]',
    'button[title*="发送"]',
    'button[title*="Send"]',
    'button[data-testid*="send"]',
]

COMMON_ASSISTANT_SELECTORS = [
    '[data-testid*="assistant"]',
    '[data-message-author-role="assistant"]',
    '[data-role="assistant"]',
    '[class*="assistant"]',
    '[class*="response"]',
    '[class*="markdown"]',
    '[class*="message"]',
    "article",
    "main",
]

COMMON_GENERATION_RUNNING_SELECTORS = [
    'button:has-text("停止")',
    'button:has-text("Stop")',
    'button:has-text("停止生成")',
    'button[aria-label*="停止"]',
    'button[aria-label*="Stop"]',
]

COMMON_GENERATION_DONE_SELECTORS = [
    'button:has-text("重新生成")',
    'button:has-text("Regenerate")',
    'button:has-text("复制")',
    'button:has-text("Copy")',
    'button:has-text("Share")',
]

COMMON_LOGIN_PHRASES = [
    "登录",
    "注册",
    "sign in",
    "log in",
    "continue with google",
    "continue with x",
    "sign in to continue",
    "log in to continue",
    "扫码登录",
]

COMMON_BLOCKED_PHRASES = [
    "not supported",
    "unsupported",
    "当前系统暂不支持",
    "current system does not support",
    "not available in your region",
]

COMMON_ERROR_PHRASES = [
    "出了点问题",
    "something went wrong",
    "try again later",
]

COMMON_NOISE_SUBSTRINGS = [
    "内容由 AI 生成",
    "AI-generated",
    "AI 生成",
]

SITE_LINE_EXCLUSIONS = {
    "qwen": {
        "??????",
        "??",
        "???????",
        "??????...",
        "??????",
        "??",
        "???????????????",
    },
    "minimaxi": {
        "已思考",
        "已完成 Web搜索",
        "查看此任务中的所有文件",
        "当前你拥有AI视窗的控制权",
        "结束",
        "全能",
        "当前进程",
        "文件",
    },
    "kimi": {
        "Agent",
        "K2.5 Instant",
        "K2 Instant",
        "K1.5",
        "Kimi Claw Is Ready!",
        "One-click OpenClaw, Kimi works 24/7",
        "Credit System Upgrade Coming",
        "Later",
        "Learn More",
        "New Chat",
    },
}

SITE_LINE_PREFIX_EXCLUSIONS = {
    "minimaxi": (
        "好的，我已收到您的请求",
        "我来为你搜索",
    ),
}

SITE_TEXT_TRUNCATION_MARKERS = {
    "minimaxi": (
        "查看此任务中的所有文件",
        "当前你拥有AI视窗的控制权",
    ),
}

STARTUP_PAGE_PREFIXES = (
    "",
    "about:blank",
    "chrome://newtab",
    "chrome://newtab/",
    "edge://newtab",
    "edge://newtab/",
    "brave://newtab",
    "brave://newtab/",
    "arc://newtab",
    "arc://newtab/",
)

SITE_CONFIG = {
    "qwen": {
        "url": "https://chat.qwen.ai/",
        "input_selectors": COMMON_INPUT_SELECTORS + ['div[data-slate-editor="true"]'],
        "send_selectors": COMMON_SEND_SELECTORS,
        "assistant_selectors": COMMON_ASSISTANT_SELECTORS,
        "generation_running_selectors": COMMON_GENERATION_RUNNING_SELECTORS,
        "generation_done_selectors": COMMON_GENERATION_DONE_SELECTORS,
        "login_selectors": ['text="Sign in"', 'text="Continue with Google"'],
        "login_phrases": COMMON_LOGIN_PHRASES,
        "blocked_phrases": COMMON_BLOCKED_PHRASES,
        "attempt_send_before_login": True,
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + ["\u5185\u5bb9\u7531\u901a\u4e49\u751f\u6210"],
    },
    "gemini": {
        "url": "https://gemini.google.com/app",
        "input_selectors": COMMON_INPUT_SELECTORS + ['rich-textarea textarea', '[aria-label*="Enter a prompt"]'],
        "send_selectors": COMMON_SEND_SELECTORS + ['button[aria-label*="Send message"]'],
        "assistant_selectors": [
            "message-content",
            "[data-response-id]",
            '[class*="response"]',
            '[class*="markdown"]',
            "article",
        ],
        "generation_running_selectors": COMMON_GENERATION_RUNNING_SELECTORS,
        "generation_done_selectors": COMMON_GENERATION_DONE_SELECTORS,
        "login_selectors": ['text="Sign in"', 'text="Continue with Google"', 'text="Log in"'],
        "login_phrases": COMMON_LOGIN_PHRASES,
        "blocked_phrases": COMMON_BLOCKED_PHRASES,
        "error_phrases": COMMON_ERROR_PHRASES,
        "login_overrides_ready": True,
        "attempt_send_before_login": True,
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "grok": {
        "url": "https://grok.com/",
        "input_selectors": COMMON_INPUT_SELECTORS,
        "send_selectors": COMMON_SEND_SELECTORS + ['button[aria-label*="Ask Grok"]'],
        "assistant_selectors": COMMON_ASSISTANT_SELECTORS,
        "generation_running_selectors": COMMON_GENERATION_RUNNING_SELECTORS,
        "generation_done_selectors": COMMON_GENERATION_DONE_SELECTORS,
        "login_selectors": ['text="Sign in"', 'text="Log in"', 'text="Continue with X"', 'text="Continue with Google"'],
        "login_phrases": COMMON_LOGIN_PHRASES,
        "blocked_phrases": COMMON_BLOCKED_PHRASES,
        "error_phrases": COMMON_ERROR_PHRASES,
        "noise_substrings": COMMON_NOISE_SUBSTRINGS,
    },
    "minimaxi": {
        "url": "https://agent.minimaxi.com/",
        "input_selectors": COMMON_INPUT_SELECTORS + ['div[data-slate-editor="true"]'],
        "send_selectors": COMMON_SEND_SELECTORS + ['button[aria-label*="Send"]', 'button[type="submit"]'],
        "assistant_selectors": ['[class*=\"stream-message-content\"]', '[class*=\"stream-message-text\"]', '[class*=\"received\"]', '[class*=\"markdown\"]', '[class*=\"prose\"]', 'article'],
        "generation_running_selectors": COMMON_GENERATION_RUNNING_SELECTORS,
        "generation_done_selectors": COMMON_GENERATION_DONE_SELECTORS + ['button:has-text("Retry")'],
        "login_selectors": ['text="Sign in"', 'text="Log in"', 'text="Continue with Google"'],
        "login_phrases": COMMON_LOGIN_PHRASES,
        "blocked_phrases": COMMON_BLOCKED_PHRASES,
        "error_phrases": COMMON_ERROR_PHRASES,
        "attempt_send_before_login": True,
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + ["\u5185\u5bb9\u7531 MiniMax \u751f\u6210", "\u5185\u5bb9\u7531AI\u751f\u6210\uff0c\u91cd\u8981\u4fe1\u606f\u8bf7\u52a1\u5fc5\u6838\u67e5"],
    },
    "kimi": {
        "url": "https://kimi.moonshot.cn/",
        # Intentionally excludes generic "textarea" and div[role="textbox"] to avoid
        # matching the phone-number <input> on Kimi's login page, which would
        # incorrectly signal that the chat interface is ready.
        "input_selectors": [
            'div[contenteditable="true"][data-lexical-editor="true"]',
            '.input-area div[contenteditable="true"]',
            'div[contenteditable="true"]',
        ],
        "send_selectors": COMMON_SEND_SELECTORS + [
            'button[aria-label*="发送"]',
            'button[data-testid*="send"]',
            'button[type="submit"]',
        ],
        "assistant_selectors": COMMON_ASSISTANT_SELECTORS + [
            '[class*="segment_"]',
            '[class*="chat-item--assistant"]',
            '.markdown-body',
            '[class*="chat-item"]',
        ],
        "generation_running_selectors": COMMON_GENERATION_RUNNING_SELECTORS + [
            'button:has-text("停止响应")',
            'button[aria-label*="停止"]',
            'button[aria-label*="stop"]',
            'button[aria-label*="Stop"]',
            '[class*="stop"]',
            '[class*="abort"]',
        ],
        "generation_done_selectors": COMMON_GENERATION_DONE_SELECTORS + [
            'button:has-text("重新回答")',
            'button:has-text("重试")',
            'button:has-text("Retry")',
        ],
        "login_selectors": [
            'text="登录"',
            'text="立即登录"',
            'text="手机号登录"',
            'text="Log in"',
        ],
        "login_phrases": COMMON_LOGIN_PHRASES + ["立即登录", "手机号登录"],
        "blocked_phrases": COMMON_BLOCKED_PHRASES,
        "error_phrases": COMMON_ERROR_PHRASES,
        "noise_substrings": COMMON_NOISE_SUBSTRINGS + [
            "内容由 Kimi 生成",
            "由 Kimi 生成",
            "Kimi Claw Is Ready!",
            "One-click OpenClaw",
            "Credit System Upgrade",
            "credit balance",
            "K2.5 Instant",
            "K2 Instant",
        ],
    },
}


def parse_args(default_site: Optional[str] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            f"Open the {default_site} chat site, send one question, and wait for the final answer."
            if default_site
            else "Open a supported web chat site, send one question, and wait for the final answer."
        )
    )
    parser.add_argument(
        "--site",
        choices=sorted(SITE_CONFIG),
        help=argparse.SUPPRESS if default_site else "Target site.",
    )
    parser.add_argument("--question", required=True, help="Question to send.")
    parser.add_argument("--output", help="Optional file path to store the final answer.")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum seconds to wait for the final answer.")
    parser.add_argument(
        "--stable-rounds",
        type=int,
        default=4,
        help="How many unchanged polling rounds indicate the answer is complete.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds while waiting for the answer.",
    )
    parser.add_argument("--login-timeout", type=int, default=600, help="Maximum seconds to wait for manual login.")
    parser.add_argument("--executable-path", help="Optional Chromium executable path.")
    parser.add_argument("--profile-dir", help="Persistent browser profile directory for standalone launches.")
    parser.add_argument("--cdp-url", help="Connect to an existing Chrome/Chromium instance via CDP.")
    parser.add_argument(
        "--cdp-http",
        help="Fetch webSocketDebuggerUrl from an existing Chrome DevTools HTTP endpoint, for example http://127.0.0.1:9222.",
    )
    return parser.parse_args()


def resolve_site_name(requested_site: Optional[str], default_site: Optional[str] = None) -> str:
    if default_site:
        if default_site not in SITE_CONFIG:
            raise ValueError(f"Unsupported default site: {default_site}")
        if requested_site and requested_site != default_site:
            raise ValueError(
                f"Wrapper is locked to {default_site}, but received mismatched --site {requested_site}."
            )
        return default_site

    if not requested_site:
        raise ValueError("--site is required when no wrapper default site is provided.")
    return requested_site


def normalize_text(text: str, noise_substrings: Optional[Iterable[str]] = None) -> str:
    active_noise = list(noise_substrings or COMMON_NOISE_SUBSTRINGS)
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(noise in line for noise in active_noise):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def latest_new_text(current: list[str], baseline: list[str]) -> str:
    baseline_set = set(baseline)
    new_items = [text for text in current if text not in baseline_set]
    if new_items:
        return new_items[-1]

    if current and baseline and current[-1] != baseline[-1]:
        return current[-1]

    if current and not baseline:
        return current[-1]

    return ""


def interpret_missing_reply(
    visible_text: str,
    login_phrases: Iterable[str],
    blocked_phrases: Iterable[str],
    error_phrases: Iterable[str] = (),
) -> str:
    lowered_text = visible_text.lower()
    if any(phrase.lower() in lowered_text for phrase in blocked_phrases):
        return "blocked"
    if any(phrase.lower() in lowered_text for phrase in error_phrases):
        return "error"
    if any(phrase.lower() in lowered_text for phrase in login_phrases):
        return "login_required"
    return "unknown"


def derive_status(input_visible: bool, login_selector_visible: bool, interpretation: str) -> str:
    if interpretation == "blocked":
        return "blocked"
    if input_visible:
        return "ready"
    if login_selector_visible or interpretation == "login_required":
        return "login_required"
    return "waiting"


def first_visible(page: Page, selectors: Iterable[str], timeout_ms: int = 3000) -> Locator:
    deadline = time.time() + timeout_ms / 1000
    last_error: Optional[Exception] = None

    while time.time() < deadline:
        for selector in selectors:
            try:
                locator = page.locator(selector)
                count = locator.count()
                for index in range(count):
                    candidate = locator.nth(index)
                    if candidate.is_visible():
                        return candidate
            except Exception as exc:
                last_error = exc
        time.sleep(0.2)

    raise RuntimeError(
        f"Could not find a visible element. selectors={list(selectors)} last_error={last_error}"
    )


def any_visible(page: Page, selectors: Iterable[str]) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = locator.count()
            for index in range(count):
                if locator.nth(index).is_visible():
                    return True
        except Exception:
            continue
    return False


def candidate_texts(page: Page, selectors: Iterable[str], noise_substrings: Iterable[str]) -> list[str]:
    texts: list[str] = []

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = min(locator.count(), 50)
            for index in range(count):
                item = locator.nth(index)
                try:
                    if not item.is_visible():
                        continue
                    text = normalize_text(item.inner_text(timeout=1000), noise_substrings)
                    if len(text) >= 10:
                        texts.append(text)
                except Exception:
                    continue
        except Exception:
            continue

    if not texts:
        try:
            body_text = normalize_text(page.locator("body").inner_text(timeout=2000), noise_substrings)
            if body_text:
                texts.append(body_text)
        except Exception:
            pass

    deduped: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if text not in seen:
            deduped.append(text)
            seen.add(text)
    return deduped


def visible_page_text(page: Page, noise_substrings: Iterable[str]) -> str:
    try:
        return normalize_text(page.locator("body").inner_text(timeout=2000), noise_substrings)
    except Exception:
        return ""


def clean_answer_text(site_name: str, text: str, question: str) -> str:
    config = SITE_CONFIG[site_name]
    normalized = normalize_text(text, config["noise_substrings"])
    if not normalized:
        return ""

    for marker in SITE_TEXT_TRUNCATION_MARKERS.get(site_name, ()): 
        marker_index = normalized.find(marker)
        if marker_index != -1:
            normalized = normalized[:marker_index].rstrip()
            break

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    normalized_question = normalize_text(question, config["noise_substrings"])
    if normalized_question and normalized_question in lines:
        last_prompt_index = max(index for index, line in enumerate(lines) if line == normalized_question)
        lines = lines[last_prompt_index + 1 :]

    exclusions = SITE_LINE_EXCLUSIONS.get(site_name, set())
    prefix_exclusions = SITE_LINE_PREFIX_EXCLUSIONS.get(site_name, ())
    filtered_lines: list[str] = []
    for line in lines:
        if line in exclusions:
            continue
        if any(line.startswith(prefix) for prefix in prefix_exclusions):
            continue
        if site_name == "minimaxi" and line.endswith("s") and line[:-1].replace(".", "", 1).isdigit():
            continue
        filtered_lines.append(line)

    if site_name == "minimaxi":
        filtered_lines = [line for line in filtered_lines if line != "Thinking Process"]
        while filtered_lines and not any("一" <= ch <= "鿿" for ch in filtered_lines[0]):
            filtered_lines.pop(0)

    return "\n".join(filtered_lines).strip()


def select_all_shortcut() -> str:
    return "Meta+A" if sys.platform == "darwin" else "Control+A"


def dom_fill(locator: Locator, question: str) -> None:
    locator.evaluate(
        """
        (el, value) => {
            if ('value' in el) {
                el.value = value;
            } else {
                el.textContent = value;
            }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        question,
    )


def fill_question(page: Page, input_box: Locator, question: str) -> None:
    input_box.click()
    try:
        input_box.fill(question)
        return
    except Exception:
        pass

    try:
        dom_fill(input_box, question)
        return
    except Exception:
        pass

    page.keyboard.press(select_all_shortcut())
    page.keyboard.press("Backspace")
    page.keyboard.type(question, delay=20)


def fill_question_for_site(site_name: str, page: Page, input_box: Locator, question: str) -> None:
    if site_name == "qwen":
        try:
            input_box.fill(question)
            return
        except Exception:
            pass

        try:
            dom_fill(input_box, question)
            return
        except Exception:
            pass

    if site_name == "kimi":
        # Kimi uses a Lexical rich-text editor whose internal React state is only
        # updated by real keyboard events.  input_box.fill() writes text visually
        # but leaves the editor state stale, keeping the send button disabled.
        input_box.click()
        page.wait_for_timeout(300)
        page.keyboard.press(select_all_shortcut())
        page.keyboard.press("Backspace")
        page.keyboard.type(question, delay=15)
        page.wait_for_timeout(500)

        # Try Enter first (works when input has focus and no modal intercepts).
        input_box.press("Enter")
        page.wait_for_timeout(400)

        # If Enter did not submit (e.g. Lexical config treats Enter as newline),
        # fall back to locating the send button via JavaScript: traverse up from the
        # contenteditable and click the first enabled button containing an SVG icon.
        sent = page.evaluate("""() => {
            const input = document.querySelector('div[contenteditable="true"]');
            if (!input) return false;
            let el = input;
            for (let i = 0; i < 8; i++) {
                el = el.parentElement;
                if (!el) break;
                const btns = Array.from(el.querySelectorAll('button'))
                    .filter(b => !b.disabled && b.offsetParent !== null && b.querySelector('svg'));
                if (btns.length > 0) {
                    btns[btns.length - 1].click();
                    return true;
                }
            }
            return false;
        }""")
        if sent:
            return
        # Last resort: Enter via page keyboard
        input_box.click()
        page.keyboard.press("Enter")
        return

    fill_question(page, input_box, question)


def open_dedicated_page(context, target_url: Optional[str] = None) -> Page:
    existing_pages = list(getattr(context, "pages", []))
    for existing_page in existing_pages:
        try:
            if target_url and target_url in existing_page.url:
                return existing_page
        except Exception:
            continue
    if len(existing_pages) == 1:
        try:
            if existing_pages[0].url in STARTUP_PAGE_PREFIXES:
                return existing_pages[0]
        except Exception:
            pass
    return context.new_page()


def try_send(page: Page, input_box: Locator, send_selectors: Iterable[str]) -> None:
    for selector in send_selectors:
        try:
            locator = page.locator(selector)
            count = locator.count()
            for index in range(count):
                button = locator.nth(index)
                if button.is_visible() and button.is_enabled():
                    button.click()
                    return
        except Exception:
            continue

    input_box.click()
    page.keyboard.press("Enter")


def write_output(output_path: Optional[str], answer: str) -> None:
    if not output_path:
        return

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(answer, encoding="utf-8")


def resolve_cdp_url(cdp_url: Optional[str], cdp_http: Optional[str]) -> Optional[str]:
    if cdp_url:
        return cdp_url

    if not cdp_http:
        return None

    version_url = cdp_http.rstrip("/") + "/json/version"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(version_url, timeout=10) as response:
        payload = json.load(response)

    ws_url = payload.get("webSocketDebuggerUrl")
    if not ws_url:
        raise RuntimeError(f"DevTools endpoint did not return webSocketDebuggerUrl: {version_url}")
    return ws_url


def connect_browser(playwright, profile_dir: Optional[str], headless: bool, executable_path: Optional[str], cdp_url: Optional[str], cdp_http: Optional[str]):
    resolved_cdp_url = resolve_cdp_url(cdp_url, cdp_http)
    if resolved_cdp_url:
        browser = playwright.chromium.connect_over_cdp(resolved_cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context(
            viewport={"width": 1440, "height": 960}
        )
        return browser, context

    if not profile_dir:
        raise RuntimeError("Standalone launch requires --profile-dir when --cdp-url/--cdp-http is not supplied.")

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=headless,
        viewport={"width": 1440, "height": 960},
        executable_path=executable_path,
    )
    return None, context


def detect_page_status(page: Page, site_name: str) -> str:
    config = SITE_CONFIG[site_name]
    body_text = visible_page_text(page, config["noise_substrings"])
    interpretation = interpret_missing_reply(
        body_text,
        config["login_phrases"],
        config["blocked_phrases"],
        config.get("error_phrases", ()),
    )
    input_visible = any_visible(page, config["input_selectors"])
    login_selector_visible = any_visible(page, config["login_selectors"])
    if interpretation == "error":
        return "error"
    if config.get("login_overrides_ready") and (login_selector_visible or interpretation == "login_required"):
        return "login_required"
    return derive_status(input_visible, login_selector_visible, interpretation)


def suppress_login_required_during_response(status: str, current_text: str, running: bool, done_hint: bool, last_text: str) -> str:
    if status != "login_required":
        return status
    if current_text or running or (done_hint and last_text):
        return "ready"
    return status


def open_site_page(page: Page, site_name: str) -> Page:
    url = SITE_CONFIG[site_name]["url"]
    if url not in page.url:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    return page


def should_wait_until_ready(site_name: str) -> bool:
    return not SITE_CONFIG[site_name].get("attempt_send_before_login", False)


def wait_until_ready(page: Page, site_name: str, login_timeout: int) -> Page:
    started = time.time()
    login_notified = False
    login_detected = False

    while time.time() - started < login_timeout:
        # Once login is detected, stop navigating so the user's login flow is
        # not interrupted by repeated page.goto() calls.
        if not login_detected:
            page = open_site_page(page, site_name)
        status = detect_page_status(page, site_name)

        if status == "ready":
            return page

        if status == "blocked":
            body_text = visible_page_text(page, SITE_CONFIG[site_name]["noise_substrings"])
            raise RuntimeError(f"[{site_name}] page is blocked or unsupported: {body_text[:200]}")

        if status == "login_required":
            login_detected = True
            if not login_notified:
                print(
                    f"[{site_name}] login required. Complete login in the opened browser window; execution will continue automatically.",
                    flush=True,
                )
                login_notified = True

        try:
            page.wait_for_timeout(2000)
        except Exception:
            time.sleep(2)

    raise RuntimeError(f"[{site_name}] login or page readiness was not completed within {login_timeout} seconds.")


def ensure_input_box(page: Page, site_name: str, login_timeout: int) -> tuple[Page, Locator]:
    try:
        return page, first_visible(page, SITE_CONFIG[site_name]["input_selectors"], timeout_ms=15000)
    except Exception as exc:
        status = detect_page_status(page, site_name)
        if status != "login_required":
            raise

        print(
            f"[{site_name}] login required. Complete login in the opened browser window; execution will continue automatically.",
            flush=True,
        )
        page = wait_until_ready(page, site_name, login_timeout)
        try:
            return page, first_visible(page, SITE_CONFIG[site_name]["input_selectors"], timeout_ms=15000)
        except Exception:
            raise exc


def wait_for_answer(
    page: Page,
    site_name: str,
    baseline_texts: list[str],
    question: str,
    stable_rounds: int,
    interval: float,
    timeout: int,
) -> dict:
    config = SITE_CONFIG[site_name]
    started = time.time()
    last_text = ""
    stable_count = 0

    while time.time() - started < timeout:
        current_texts = candidate_texts(page, config["assistant_selectors"], config["noise_substrings"])
        current_text = clean_answer_text(site_name, latest_new_text(current_texts, baseline_texts), question)
        running = any_visible(page, config["generation_running_selectors"])
        done_hint = any_visible(page, config["generation_done_selectors"])
        status = suppress_login_required_during_response(
            detect_page_status(page, site_name),
            current_text,
            running,
            done_hint,
            last_text,
        )

        if status == "login_required":
            return {"status": "login_required", "answer": ""}
        if status == "blocked":
            body_text = visible_page_text(page, config["noise_substrings"])
            return {"status": "blocked", "answer": body_text}
        if status == "error":
            body_text = visible_page_text(page, config["noise_substrings"])
            return {"status": "error", "answer": body_text}

        if current_text:
            if current_text == last_text:
                stable_count += 1
            else:
                last_text = current_text
                stable_count = 0

        if current_text and stable_count >= stable_rounds and (done_hint or not running):
            return {"status": "answer", "answer": current_text}

        time.sleep(interval)

    if last_text:
        return {"status": "answer", "answer": clean_answer_text(site_name, last_text, question)}

    status = detect_page_status(page, site_name)
    if status == "login_required":
        return {"status": "login_required", "answer": ""}
    if status == "blocked":
        body_text = visible_page_text(page, config["noise_substrings"])
        return {"status": "blocked", "answer": body_text}
    if status == "error":
        body_text = visible_page_text(page, config["noise_substrings"])
        return {"status": "error", "answer": body_text}
    return {"status": "no_reply", "answer": ""}


def ask_site(
    site_name: str,
    question: str,
    profile_dir: Optional[str],
    headless: bool,
    timeout: int,
    stable_rounds: int,
    interval: float,
    login_timeout: int,
    executable_path: Optional[str],
    cdp_url: Optional[str],
    cdp_http: Optional[str],
) -> str:
    config = SITE_CONFIG[site_name]
    with sync_playwright() as playwright:
        browser, context = connect_browser(
            playwright=playwright,
            profile_dir=profile_dir,
            headless=headless,
            executable_path=executable_path,
            cdp_url=cdp_url,
            cdp_http=cdp_http,
        )
        page = open_dedicated_page(context, config["url"])

        try:
            if should_wait_until_ready(site_name):
                page = wait_until_ready(page, site_name, login_timeout)
            else:
                page = open_site_page(page, site_name)
            baseline_texts = candidate_texts(page, config["assistant_selectors"], config["noise_substrings"])
            page, input_box = ensure_input_box(page, site_name, login_timeout)
            fill_question_for_site(site_name, page, input_box, question)
            try_send(page, input_box, config["send_selectors"])

            result = wait_for_answer(page, site_name, baseline_texts, question, stable_rounds, interval, timeout)
            if result["status"] == "answer":
                return result["answer"]

            if result["status"] == "login_required":
                print(
                    f"[{site_name}] no usable reply yet and the site now requires login. Waiting for login, then retrying the question.",
                    flush=True,
                )
                page = wait_until_ready(page, site_name, login_timeout)
                baseline_texts = candidate_texts(page, config["assistant_selectors"], config["noise_substrings"])
                page, input_box = ensure_input_box(page, site_name, login_timeout)
                fill_question_for_site(site_name, page, input_box, question)
                try_send(page, input_box, config["send_selectors"])

                retry_result = wait_for_answer(page, site_name, baseline_texts, question, stable_rounds, interval, timeout)
                if retry_result["status"] == "answer":
                    return retry_result["answer"]
                if retry_result["status"] == "blocked":
                    raise RuntimeError(f"[{site_name}] page is blocked or unsupported: {retry_result['answer'][:200]}")
                if retry_result["status"] == "login_required":
                    raise RuntimeError(f"[{site_name}] login completed, but the site still returned to a login-required state.")
                raise RuntimeError(
                    f"[{site_name}] no reply was produced after login. The site may require updated selectors or a different page state."
                )

            if result["status"] == "blocked":
                raise RuntimeError(f"[{site_name}] page is blocked or unsupported: {result['answer'][:200]}")
            if result["status"] == "error":
                raise RuntimeError(f"[{site_name}] page returned an error after sending the question: {result['answer'][:200]}")

            raise RuntimeError(
                f"[{site_name}] no reply was detected. The site may need login, may have changed its page structure, or did not produce an answer."
            )
        finally:
            if browser is None:
                context.close()


def main(default_site: Optional[str] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(default_site)
    site_name = resolve_site_name(args.site, default_site)

    try:
        answer = ask_site(
            site_name=site_name,
            question=args.question,
            profile_dir=args.profile_dir,
            headless=args.headless,
            timeout=args.timeout,
            stable_rounds=args.stable_rounds,
            interval=args.interval,
            login_timeout=args.login_timeout,
            executable_path=args.executable_path,
            cdp_url=args.cdp_url,
            cdp_http=args.cdp_http,
        )
    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        return 130
    except PlaywrightError as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1

    write_output(args.output, answer)
    print("\n===== 最终回答 =====\n")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
