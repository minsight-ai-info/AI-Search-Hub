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
    def test_kimi_logged_in_composer_hint_is_ready(self):
        snapshot = '- textbox [e20]:\n- text: Type "/" to invoke plugins and skills'
        self.assertTrue(chat.is_chat_ready(snapshot, "kimi"))


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

    def test_gemini_extraction_uses_answer_boundary(self):
        snapshot = '''
- heading "You said question" [level=2]:
  - paragraph: question
- heading "Gemini said" [level=2]
- paragraph: First answer paragraph
- heading "1. Details" [level=2]
- paragraph: Second answer paragraph
- group:
  - textbox "Enter a prompt for Gemini" [e1]
- paragraph: Gemini is AI and can make mistakes.
'''
        self.assertEqual(
            chat.extract_answer_from_snapshot(snapshot, "gemini", "question"),
            "First answer paragraph\n1. Details\nSecond answer paragraph",
        )

    def test_kimi_extraction_starts_at_final_answer_heading(self):
        snapshot = '''
- text: Internal planning text
- heading "Final title" [level=1]
- heading "Section" [level=2]
- listitem: First point
- strong: Important label
- text: Follow-up detail High demand. Switched to K2.6 Instant for speed.
- textbox [e1]:
'''
        self.assertEqual(
            chat.extract_answer_from_snapshot(snapshot, "kimi", "question"),
            "Final title\nSection\nFirst point\nImportant label\nFollow-up detail",
        )
    def test_qwen_extraction_ignores_sidebar_and_user_message(self):
        snapshot = '''
- text: Community Coder Projects All chats
- main:
  - paragraph: question
  - text: Thinking completed
  - text: Final answer opening.
  - heading "Key finding" [level=3]
  - listitem: Supporting detail
  - button "Regenerate" [e1]
  - textbox "How can I help you today?" [e2]
'''
        self.assertEqual(
            chat.extract_answer_from_snapshot(snapshot, "qwen", "question"),
            "Final answer opening.\nKey finding\nSupporting detail",
        )


class CompletionGateTests(unittest.TestCase):
    def test_qwen_answer_is_not_ready_until_regenerate_is_visible(self):
        answer = "A sufficiently detailed answer that is long enough to be credible."
        self.assertFalse(chat.is_answer_ready("qwen", answer, "- text: Thinking completed", 20))
        self.assertTrue(chat.is_answer_ready("qwen", answer, "- button \"Regenerate\" [e1]", 20))

    def test_search_status_fails_research_answer_length_gate(self):
        self.assertFalse(chat.is_answer_ready("doubao", "搜索 4 个关键词，参考 24 篇资料", "", 200))
class DoubaoResponseTests(unittest.TestCase):
    def test_doubao_payload_requires_non_streaming_final_message(self):
        payload = '{"text":"最终回答正文","streaming":false}'
        self.assertEqual(chat.decode_doubao_payload(payload), ("最终回答正文", True))
        self.assertEqual(chat.decode_doubao_payload('{"text":"生成中","streaming":true}'), ("生成中", False))

    def test_doubao_sse_rate_limit_is_extracted(self):
        body = 'id: 0\nevent: STREAM_ERROR\ndata: {"error_code":710022004,"error_msg":"rate limited"}\n\n'
        self.assertEqual(chat.parse_doubao_sse_error(body), "rate limited")


class KimiResponseTests(unittest.TestCase):
    def test_contenteditable_clear_script_supports_kimi_composer(self):
        import camofox_runner
        with patch.object(camofox_runner, "run") as run_command:
            camofox_runner._clear_focused_via_js(tab_id="tab")
        expression = run_command.call_args.args[0][2]
        self.assertIn("el.isContentEditable", expression)
        self.assertIn("el.innerHTML = ''", expression)

    def test_contenteditable_input_is_set_via_js_not_cli_type(self):
        import camofox_runner
        with (
            patch.object(camofox_runner, "click"),
            patch.object(camofox_runner, "run", return_value={"result": "contenteditable"}) as run_command,
        ):
            camofox_runner.type_text("e1", "KIMI_PROBE", tab_id="tab")
        commands = [call.args[0] for call in run_command.call_args_list]
        self.assertTrue(any("InputEvent" in command[2] for command in commands if command[1] == "eval"))
        self.assertFalse(any(command[1] == "type" for command in commands))

    def test_kimi_custom_extractor_targets_final_markdown_block(self):
        script = chat.SITE_CONFIG["kimi"]["custom_answer_js"]
        self.assertIn("chat-content-item-assistant", script)
        self.assertIn("markdown-container", script)

    def test_runner_preserves_multiline_eval_result(self):
        import camofox_runner
        completed = type("Completed", (), {"returncode": 0, "stdout": "ok: true\nresult: first line\nsecond line\nresultType: string\ntruncated: false\n", "stderr": ""})()
        with patch.object(camofox_runner.subprocess, "run", return_value=completed):
            result = camofox_runner.run(["camofox-browser", "eval", "1+1"])
        self.assertEqual(result["result"], "first line\nsecond line")


class BatchRunnerTests(unittest.TestCase):
    def test_batch_command_sets_per_platform_output_and_quality_gate(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import run_camofox_batch as batch

        command = batch.build_command(
            repo_root=Path("/repo"),
            site="qwen",
            prompt="research question",
            output_dir=Path("/output"),
            timeout=90,
            min_answer_chars=200,
        )
        self.assertIn("--min-answer-chars", command)
        self.assertIn("200", command)
        self.assertIn("/output/qwen.txt", command)

    def test_navigation_errors_are_retriable(self):
        import run_camofox_batch as batch

        self.assertTrue(batch.is_retriable_open_error("NS_BINDING_ABORTED"))
        self.assertTrue(batch.is_retriable_open_error("NS_ERROR_UNKNOWN_HOST"))
        self.assertFalse(batch.is_retriable_open_error("invalid site configuration"))


class PromptSubmissionTests(unittest.TestCase):
    def test_gemini_uses_send_button_when_available(self):
        with (
            patch.dict(chat.SITE_CONFIG["gemini"], {"submit_button_text": "Send message"}),
            patch.object(chat, "find_ref_by_text", return_value="e14"),
            patch.object(chat, "click") as click_submit,
            patch.object(chat, "press") as press_enter,
        ):
            chat.submit_prompt("gemini", "- button \"Send message\" [e14]", "tab")
        click_submit.assert_called_once_with("e14", tab_id="tab", cwd=None)
        press_enter.assert_not_called()


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
