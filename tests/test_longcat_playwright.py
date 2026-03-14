import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import longcat_playwright  # noqa: E402


class LongcatPlaywrightTests(unittest.TestCase):
    def test_latest_new_text_ignores_user_prompt_echo_when_reply_is_present(self) -> None:
        latest = longcat_playwright.latest_new_text(
            current=["这是模型回答", "AI最新的新闻是什么"],
            baseline=[],
            question="AI最新的新闻是什么",
        )

        self.assertEqual(latest, "这是模型回答")

    def test_latest_new_text_returns_empty_when_only_prompt_echo_exists(self) -> None:
        latest = longcat_playwright.latest_new_text(
            current=["AI最新的新闻是什么"],
            baseline=[],
            question="AI最新的新闻是什么",
        )

        self.assertEqual(latest, "")

    def test_latest_new_text_strips_prompt_prefix_from_combined_block(self) -> None:
        latest = longcat_playwright.latest_new_text(
            current=["AI最新的新闻是什么\n操作太快啦，请稍后再试～"],
            baseline=[],
            question="AI最新的新闻是什么",
        )

        self.assertEqual(latest, "操作太快啦，请稍后再试～")


if __name__ == "__main__":
    unittest.main()
