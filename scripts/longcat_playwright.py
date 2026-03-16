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


URL = "https://longcat.chat/"
DEFAULT_PROFILE_DIR = Path("./longcat_profile")

INPUT_SELECTORS = [
    'div[role="textbox"]',
    '[contenteditable="true"]',
    "textarea",
]

NEW_CHAT_SELECTORS = [
    'text="开启新对话"',
    'text="新对话"',
    'text="New Chat"',
]

SEND_SELECTORS = [
    'button:has-text("发送")',
    'button[aria-label*="发送"]',
    'button[title*="发送"]',
    '[role="button"][aria-label*="发送"]',
]

ASSISTANT_SELECTORS = [
    '[class*="assistant"]',
    '[class*="markdown"]',
    '[class*="message"]',
    '[data-message-author-role="assistant"]',
    '[data-testid*="assistant"]',
]

GENERATION_RUNNING_SELECTORS = [
    'button:has-text("停止")',
    'button:has-text("停止生成")',
    'button[aria-label*="停止"]',
]

GENERATION_DONE_SELECTORS = [
    'button:has-text("重新生成")',
    'button:has-text("复制")',
    'text="已搜到"',
]

NOISE_SUBSTRINGS = [
    "内容由AI生成",
    "内容由 AI 生成",
    "登录后为您保存历史对话",
    "请先登录",
]

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use Playwright to open LongCat chat, send one question, and wait for the final answer."
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="搜索杭州美食相关",
        help="Question to send to LongCat.",
    )
    parser.add_argument(
        "--url",
        default=URL,
        help="Chat URL. Defaults to the LongCat chat entry.",
    )
    parser.add_argument(
        "--profile-dir",
        default=str(DEFAULT_PROFILE_DIR.resolve()),
        help="Persistent browser profile directory.",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to store the final answer.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode.",
    )
    parser.add_argument(
        "--skip-login-wait",
        action="store_true",
        help="Skip waiting for manual Enter confirmation after opening the page.",
    )
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
        help="How many unchanged polling rounds indicate the answer is complete.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds while waiting for the answer.",
    )
    parser.add_argument(
        "--executable-path",
        help="Optional Chromium executable path if you want to use a local browser binary.",
    )
    parser.add_argument(
        "--cdp-url",
        help="Connect to an existing Chrome/Chromium instance via CDP.",
    )
    parser.add_argument(
        "--cdp-http",
        help="Fetch webSocketDebuggerUrl from an existing Chrome DevTools HTTP endpoint, for example http://127.0.0.1:9222.",
    )
    parser.add_argument(
        "--no-new-chat",
        action="store_true",
        help="Do not click the new-chat entry before sending the question.",
    )
    return parser.parse_args()


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


def normalize_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(noise in line for noise in NOISE_SUBSTRINGS):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def strip_prompt_prefix(text: str, question: str) -> str:
    normalized_question = normalize_text(question)
    normalized_text = normalize_text(text)
    if not normalized_question or not normalized_text:
        return normalized_text
    if normalized_text == normalized_question:
        return ""
    prefix = normalized_question + "\n"
    if normalized_text.startswith(prefix):
        return normalized_text[len(prefix):].strip()
    return normalized_text


def candidate_texts(page: Page) -> list[str]:
    texts: list[str] = []

    for selector in ASSISTANT_SELECTORS:
        try:
            locator = page.locator(selector)
            count = min(locator.count(), 50)
            for index in range(count):
                item = locator.nth(index)
                try:
                    if not item.is_visible():
                        continue
                    text = normalize_text(item.inner_text(timeout=1000))
                    if len(text) >= 2:
                        texts.append(text)
                except Exception:
                    continue
        except Exception:
            continue

    deduped: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if text not in seen:
            deduped.append(text)
            seen.add(text)
    return deduped


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


def latest_new_text(current: list[str], baseline: list[str], question: str = "") -> str:
    baseline_set = set(baseline)
    
    def sanitize(text: str) -> str:
        return strip_prompt_prefix(text, question)

    new_items = [
        sanitize(text) for text in current if text not in baseline_set and sanitize(text)
    ]
    if new_items:
        return new_items[-1]

    if current and baseline and current[-1] != baseline[-1]:
        return sanitize(current[-1])

    if current and not baseline:
        return sanitize(current[-1])

    return ""


def wait_answer_finished(
    page: Page,
    baseline_texts: list[str],
    question: str,
    stable_rounds: int,
    interval: float,
    timeout: int,
) -> str:
    started = time.time()
    last_text = ""
    stable_count = 0

    while time.time() - started < timeout:
        current_texts = candidate_texts(page)
        current_text = latest_new_text(current_texts, baseline_texts, question=question)
        running = any_visible(page, GENERATION_RUNNING_SELECTORS)
        done_hint = any_visible(page, GENERATION_DONE_SELECTORS)

        if current_text:
            if current_text == last_text:
                stable_count += 1
            else:
                last_text = current_text
                stable_count = 0

        if current_text and stable_count >= stable_rounds and (done_hint or not running):
            return current_text

        time.sleep(interval)

    return last_text


def fill_question(page: Page, input_box: Locator, question: str) -> None:
    input_box.click()
    try:
        input_box.fill(question)
        return
    except Exception:
        pass

    try:
        input_box.evaluate(
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
        return
    except Exception:
        pass

    page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(question, delay=20)


def open_automation_page(context, target_url: Optional[str] = None) -> Page:
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


def try_new_chat(page: Page) -> None:
    for selector in NEW_CHAT_SELECTORS:
        try:
            locator = page.locator(selector)
            if locator.count() and locator.first.is_visible():
                locator.first.click(timeout=3000)
                page.wait_for_timeout(1200)
                return
        except Exception:
            continue


def try_send(page: Page, input_box: Locator) -> None:
    for selector in SEND_SELECTORS:
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


def ask_longcat(
    question: str,
    url: str,
    profile_dir: str,
    headless: bool,
    skip_login_wait: bool,
    timeout: int,
    stable_rounds: int,
    interval: float,
    executable_path: Optional[str],
    cdp_url: Optional[str],
    cdp_http: Optional[str],
    no_new_chat: bool,
) -> str:
    with sync_playwright() as playwright:
        browser = None
        resolved_cdp_url = resolve_cdp_url(cdp_url, cdp_http)
        if resolved_cdp_url:
            browser = playwright.chromium.connect_over_cdp(resolved_cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context(
                viewport={"width": 1440, "height": 960}
            )
            page = open_automation_page(context, url)
        else:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=headless,
                viewport={"width": 1440, "height": 960},
                executable_path=executable_path,
            )
            page = open_automation_page(context, url)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightError:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

        print(f"当前标题: {page.title()}", flush=True)
        print(f"当前地址: {page.url}", flush=True)

        if not skip_login_wait:
            print("如果页面要求登录，请先手动完成登录并进入聊天页。", flush=True)
            input("准备好后按回车继续...")

        if not no_new_chat:
            try_new_chat(page)

        input_box = first_visible(page, INPUT_SELECTORS, timeout_ms=15000)
        baseline_texts = candidate_texts(page)
        fill_question(page, input_box, question)
        try_send(page, input_box)

        answer = wait_answer_finished(
            page=page,
            baseline_texts=baseline_texts,
            question=question,
            stable_rounds=stable_rounds,
            interval=interval,
            timeout=timeout,
        )

        if browser is None:
            context.close()

        return answer


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()

    try:
        answer = ask_longcat(
            question=args.question,
            url=args.url,
            profile_dir=args.profile_dir,
            headless=args.headless,
            skip_login_wait=args.skip_login_wait,
            timeout=args.timeout,
            stable_rounds=args.stable_rounds,
            interval=args.interval,
            executable_path=args.executable_path,
            cdp_url=args.cdp_url,
            cdp_http=args.cdp_http,
            no_new_chat=args.no_new_chat,
        )
    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1

    write_output(args.output, answer)
    print("\n===== 最终回答 =====\n")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
