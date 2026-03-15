import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import site_chat_core as generic_web_chat  # noqa: E402


class RecordingKeyboard:
    def __init__(self) -> None:
        self.calls = []

    def press(self, key: str) -> None:
        self.calls.append(("press", key))

    def type(self, text: str, delay: int = 0) -> None:
        self.calls.append(("type", text, delay))


class RecordingPage:
    def __init__(self) -> None:
        self.keyboard = RecordingKeyboard()


class RecordingLocator:
    def __init__(
        self,
        tag_name: str = "div",
        click_error: Exception = None,
        fill_error: Exception = None,
        dom_error: Exception = None,
    ) -> None:
        self.tag_name = tag_name
        self.click_error = click_error
        self.fill_error = fill_error
        self.dom_error = dom_error
        self.click_count = 0
        self.fill_calls = []
        self.dom_fill_calls = []

    def click(self) -> None:
        if self.click_error is not None:
            raise self.click_error
        self.click_count += 1

    def fill(self, text: str) -> None:
        if self.fill_error is not None:
            raise self.fill_error
        self.fill_calls.append(text)

    def evaluate(self, script: str, value=None):
        if value is None:
            return self.tag_name
        if self.dom_error is not None:
            raise self.dom_error
        self.dom_fill_calls.append(value)
        return None


class RecordingContext:
    def __init__(self, pages=None) -> None:
        self.pages = list(pages or [])
        self.new_page_calls = 0
        self.page = object()

    def new_page(self):
        self.new_page_calls += 1
        return self.page


class RecordingStartupPage:
    def __init__(self, url: str) -> None:
        self.url = url


class GenericWebChatPlaywrightTests(unittest.TestCase):
    def test_normalize_text_strips_noise_and_blank_lines(self) -> None:
        normalized = generic_web_chat.normalize_text(
            "\n内容由 AI 生成\n\nFirst line\n  Second line  \n"
        )

        self.assertEqual(normalized, "First line\nSecond line")

    def test_latest_new_text_prefers_new_items_over_existing_baseline(self) -> None:
        latest = generic_web_chat.latest_new_text(
            ["existing", "new answer"],
            ["existing"],
        )

        self.assertEqual(latest, "new answer")

    def test_interpret_missing_reply_requests_login_when_login_phrase_present(self) -> None:
        result = generic_web_chat.interpret_missing_reply(
            visible_text="Please sign in to continue chatting.",
            login_phrases=["sign in", "log in"],
            blocked_phrases=["not supported"],
        )

        self.assertEqual(result, "login_required")

    def test_interpret_missing_reply_reports_blocked_state(self) -> None:
        result = generic_web_chat.interpret_missing_reply(
            visible_text="Current system is not supported.",
            login_phrases=["sign in", "log in"],
            blocked_phrases=["not supported"],
        )

        self.assertEqual(result, "blocked")

    def test_interpret_missing_reply_reports_error_state(self) -> None:
        result = generic_web_chat.interpret_missing_reply(
            visible_text="Something went wrong. Try again later.",
            login_phrases=["sign in", "log in"],
            blocked_phrases=["not supported"],
            error_phrases=["something went wrong"],
        )

        self.assertEqual(result, "error")

    def test_supported_sites_include_qwen_gemini_and_grok(self) -> None:
        self.assertTrue({"qwen", "gemini", "grok"}.issubset(generic_web_chat.SITE_CONFIG))

    def test_resolve_site_name_uses_default_site_for_wrappers(self) -> None:
        self.assertEqual(generic_web_chat.resolve_site_name(None, "qwen"), "qwen")

    def test_resolve_site_name_rejects_mismatched_wrapper_site(self) -> None:
        with self.assertRaises(ValueError):
            generic_web_chat.resolve_site_name("grok", "qwen")

    def test_gemini_skips_pre_send_login_gate(self) -> None:
        self.assertFalse(generic_web_chat.should_wait_until_ready("gemini"))
        self.assertTrue(generic_web_chat.should_wait_until_ready("qwen"))

    def test_derive_status_prefers_ready_when_input_is_visible(self) -> None:
        status = generic_web_chat.derive_status(
            input_visible=True,
            login_selector_visible=True,
            interpretation="login_required",
        )

        self.assertEqual(status, "ready")

    def test_derive_status_requires_login_without_input(self) -> None:
        status = generic_web_chat.derive_status(
            input_visible=False,
            login_selector_visible=True,
            interpretation="unknown",
        )

        self.assertEqual(status, "login_required")

    def test_fill_question_prefers_locator_fill_without_keyboard(self) -> None:
        page = RecordingPage()
        locator = RecordingLocator(tag_name="div")

        generic_web_chat.fill_question(page, locator, "hello")

        self.assertEqual(locator.fill_calls, ["hello"])
        self.assertEqual(locator.dom_fill_calls, [])
        self.assertEqual(page.keyboard.calls, [])

    def test_fill_question_for_qwen_does_not_require_click_before_fill(self) -> None:
        page = RecordingPage()
        locator = RecordingLocator(click_error=RuntimeError("click failed"))

        generic_web_chat.fill_question_for_site("qwen", page, locator, "hello")

        self.assertEqual(locator.fill_calls, ["hello"])
        self.assertEqual(locator.click_count, 0)
        self.assertEqual(page.keyboard.calls, [])

    def test_fill_question_uses_dom_fallback_before_keyboard(self) -> None:
        page = RecordingPage()
        locator = RecordingLocator(tag_name="div", fill_error=RuntimeError("fill failed"))

        generic_web_chat.fill_question(page, locator, "hello")

        self.assertEqual(locator.fill_calls, [])
        self.assertEqual(locator.dom_fill_calls, ["hello"])
        self.assertEqual(page.keyboard.calls, [])

    def test_open_dedicated_page_creates_new_page(self) -> None:
        context = RecordingContext()

        page = generic_web_chat.open_dedicated_page(context)

        self.assertIs(page, context.page)
        self.assertEqual(context.new_page_calls, 1)

    def test_open_dedicated_page_reuses_single_startup_page(self) -> None:
        startup_page = RecordingStartupPage("about:blank")
        context = RecordingContext(pages=[startup_page])

        page = generic_web_chat.open_dedicated_page(context)

        self.assertIs(page, startup_page)
        self.assertEqual(context.new_page_calls, 0)

    def test_open_dedicated_page_reuses_existing_target_page(self) -> None:
        target_page = RecordingStartupPage("https://chat.qwen.ai/")
        context = RecordingContext(pages=[target_page])

        page = generic_web_chat.open_dedicated_page(context, "https://chat.qwen.ai/")

        self.assertIs(page, target_page)
        self.assertEqual(context.new_page_calls, 0)


if __name__ == "__main__":
    unittest.main()
