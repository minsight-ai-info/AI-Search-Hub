import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_camofox_chat as chat  # noqa: E402


class LoginStateTests(unittest.TestCase):
    def test_visible_login_action_does_not_block_a_ready_chat(self):
        snapshot = '''
- button "Log in" [e1]
- textbox "Ask Grok anything" [e2]
'''
        self.assertTrue(chat.is_chat_ready(snapshot, "grok"))
        self.assertFalse(chat.has_login_blocker(snapshot, "grok"))
        self.assertFalse(chat.is_login_page(snapshot, "grok"))

    def test_doubao_login_dialog_blocks_even_when_chat_input_exists(self):
        snapshot = '''
- textbox "发消息或按住空格说话..." [e2]
- dialog "登录以解锁"
- textbox "请输入手机号" [e3]
'''
        self.assertTrue(chat.is_chat_ready(snapshot, "doubao"))
        self.assertTrue(chat.has_login_blocker(snapshot, "doubao"))
        self.assertTrue(chat.is_login_page(snapshot, "doubao"))

    def test_credential_form_is_a_login_blocker(self):
        snapshot = '''
- heading: Welcome back
- textbox "Email" [e1]
- textbox "Password" [e2]
- button "Sign in" [e3]
'''
        self.assertTrue(chat.has_login_blocker(snapshot, "grok"))
        self.assertTrue(chat.is_login_page(snapshot, "grok"))


class AnswerExtractionTests(unittest.TestCase):
    def test_extraction_keeps_answer_and_discards_login_page_noise(self):
        snapshot = '''
- paragraph: Sign up to continue seamlessly with Grok's full power
- paragraph: AI Search Hub test successful
- text: Log in
'''
        self.assertEqual(
            chat.extract_answer_from_snapshot(snapshot, "grok", "hello"),
            "AI Search Hub test successful",
        )

    def test_extraction_returns_empty_for_login_page_only(self):
        snapshot = '''
- paragraph: Sign up to continue seamlessly with Grok's full power
- text: Log in
- textbox "Email" [e1]
'''
        self.assertEqual(chat.extract_answer_from_snapshot(snapshot, "grok", "hello"), "")

    def test_extraction_discards_known_chat_shell_noise(self):
        snapshot = '''
- text: Chats
- text: Instant High
- text: Explore inspiration
- text: Need help? Feedback
'''
        self.assertEqual(chat.extract_answer_from_snapshot(snapshot, "kimi", "hello"), "")


class LoginWaitTests(unittest.TestCase):
    def test_wait_for_chat_ready_requires_consecutive_composer_snapshots(self):
        loading = '- heading: Loading'
        ready = '- textbox "Ask Grok anything" [e2]'
        snapshots = iter([loading, ready, ready])
        with (
            patch.object(chat, "snapshot", side_effect=lambda **_: next(snapshots)) as take_snapshot,
            patch.object(chat, "wait_seconds"),
            patch.object(chat.time, "time", side_effect=[0, 0, 1, 2, 3]),
        ):
            self.assertTrue(chat.wait_for_chat_ready("grok", 10, tab_id="tab"))
        self.assertEqual(take_snapshot.call_count, 3)

    def test_wait_for_login_saves_only_after_ready_state_settles(self):
        login = '- dialog "登录以解锁"\n- textbox "请输入手机号" [e1]'
        ready = '- textbox "发消息或按住空格说话..." [e2]'
        snapshots = iter([login, ready, ready])
        with (
            patch.object(chat, "snapshot", side_effect=lambda **_: next(snapshots)) as take_snapshot,
            patch.object(chat, "wait_seconds"),
            patch.object(chat, "save_debug_state"),
            patch.object(chat, "save_session") as save_session,
            patch.object(chat.time, "time", side_effect=[0, 0, 1, 2, 3]),
        ):
            self.assertTrue(chat.wait_for_login("doubao", 10, tab_id="tab"))
        self.assertEqual(take_snapshot.call_count, 3)
        save_session.assert_called_once_with("doubao", tab_id="tab", cwd=None)


if __name__ == "__main__":
    unittest.main()
