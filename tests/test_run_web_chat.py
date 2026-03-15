import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_web_chat  # noqa: E402


class RecordingPage:
    def __init__(self, url: str) -> None:
        self.url = url


class RecordingContext:
    def __init__(self, pages=None) -> None:
        self.pages = list(pages or [])
        self.new_page_calls = 0
        self.page = object()

    def new_page(self):
        self.new_page_calls += 1
        return self.page


class RunWebChatTests(unittest.TestCase):
    def test_find_repo_root_uses_scripts_directory_layout(self) -> None:
        resolved = run_web_chat.find_repo_root(str(PROJECT_ROOT))
        self.assertEqual(resolved, PROJECT_ROOT)

    def test_build_site_command_routes_qwen_to_dedicated_driver(self) -> None:
        args = SimpleNamespace(
            site="qwen",
            prompt="hello",
            output=None,
            timeout=240,
            stable_rounds=5,
            interval=2.0,
            login_timeout=600,
            no_new_chat=False,
        )

        command = run_web_chat.build_site_command(args, PROJECT_ROOT, "ws://example.test/devtools/browser/abc")

        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[1], str(PROJECT_ROOT / "scripts" / "qwen_playwright.py"))
        self.assertEqual(command[2:4], ["--question", "hello"])
        self.assertIn("--cdp-url", command)
        self.assertIn("ws://example.test/devtools/browser/abc", command)
        self.assertIn(str(PROJECT_ROOT / "out" / "qwen_answer.txt"), command)

    def test_profile_appears_locked_when_singleton_lock_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir)
            (profile_dir / "SingletonLock").write_text("", encoding="utf-8")

            self.assertTrue(run_web_chat.profile_appears_locked(profile_dir))

    def test_profile_appears_locked_when_broken_singleton_symlink_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir)
            (profile_dir / "SingletonSocket").symlink_to(profile_dir / "missing-socket")

            self.assertTrue(run_web_chat.profile_appears_locked(profile_dir))

    def test_profile_not_locked_without_singleton_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir)
            self.assertFalse(run_web_chat.profile_appears_locked(profile_dir))

    def test_clear_lock_markers_removes_broken_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir)
            marker = profile_dir / "SingletonSocket"
            marker.symlink_to(profile_dir / "missing-socket")

            run_web_chat.clear_lock_markers(profile_dir)

            self.assertFalse(marker.exists())
            self.assertFalse(marker.is_symlink())

    def test_seed_debug_profile_copies_regular_files_but_skips_lock_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            (source_dir / "Default").mkdir(parents=True)
            (source_dir / "Default" / "Preferences").write_text("prefs", encoding="utf-8")
            (source_dir / "Local State").write_text("{}", encoding="utf-8")
            (source_dir / "SingletonLock").write_text("locked", encoding="utf-8")

            run_web_chat.seed_debug_profile(source_dir, target_dir, "Default")

            self.assertTrue((target_dir / "Default" / "Preferences").exists())
            self.assertTrue((target_dir / "Local State").exists())
            self.assertFalse((target_dir / "SingletonLock").exists())

    def test_seed_debug_profile_refreshes_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            (source_dir / "Profile 4").mkdir(parents=True)
            (target_dir / "Profile 4").mkdir(parents=True)
            (source_dir / "Profile 4" / "Preferences").write_text("new", encoding="utf-8")
            (source_dir / "Local State").write_text("{}", encoding="utf-8")
            (target_dir / "Profile 4" / "Preferences").write_text("old", encoding="utf-8")

            run_web_chat.seed_debug_profile(source_dir, target_dir, "Profile 4")

            self.assertEqual((target_dir / "Profile 4" / "Preferences").read_text(encoding="utf-8"), "new")

    def test_seed_debug_profile_removes_stale_target_files_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            (source_dir / "Profile 4").mkdir(parents=True)
            (source_dir / "Profile 4" / "Preferences").write_text("new", encoding="utf-8")
            (source_dir / "Local State").write_text("{}", encoding="utf-8")
            (target_dir / "stale.txt").parent.mkdir(parents=True, exist_ok=True)
            (target_dir / "stale.txt").write_text("stale", encoding="utf-8")

            run_web_chat.seed_debug_profile(source_dir, target_dir, "Profile 4")

            self.assertFalse((target_dir / "stale.txt").exists())
            self.assertEqual((target_dir / "Profile 4" / "Preferences").read_text(encoding="utf-8"), "new")

    def test_seed_debug_profile_copies_only_selected_profile_and_shared_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            (source_dir / "Profile 4").mkdir(parents=True)
            (source_dir / "Profile 4" / "Preferences").write_text("p4", encoding="utf-8")
            (source_dir / "Profile 2").mkdir(parents=True)
            (source_dir / "Profile 2" / "Preferences").write_text("p2", encoding="utf-8")
            (source_dir / "Local State").write_text("{}", encoding="utf-8")

            run_web_chat.seed_debug_profile(source_dir, target_dir, "Profile 4")

            self.assertTrue((target_dir / "Profile 4" / "Preferences").exists())
            self.assertFalse((target_dir / "Profile 2").exists())
            self.assertTrue((target_dir / "Local State").exists())

    def test_choose_profile_directory_prefers_most_recent_signed_in_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            user_data_dir = Path(temp_dir)
            local_state = user_data_dir / "Local State"
            local_state.write_text(
                """
                {
                  "profile": {
                    "info_cache": {
                      "Default": {"name": "Chrome", "user_name": "", "gaia_name": "", "active_time": 100},
                      "Profile 2": {"name": "Work", "user_name": "work@example.com", "gaia_name": "Work", "active_time": 200},
                      "Profile 4": {"name": "Main", "user_name": "main@example.com", "gaia_name": "Main", "active_time": 300}
                    }
                  }
                }
                """,
                encoding="utf-8",
            )

            self.assertEqual(run_web_chat.choose_profile_directory(user_data_dir), "Profile 4")

    def test_browser_proxy_arg_prefers_https_proxy(self) -> None:
        with mock.patch.dict(
            run_web_chat.os.environ,
            {
                "https_proxy": "http://127.0.0.1:7890",
                "http_proxy": "http://127.0.0.1:8888",
                "all_proxy": "socks5://127.0.0.1:9999",
            },
            clear=False,
        ):
            self.assertEqual(
                run_web_chat.browser_proxy_arg(),
                "--proxy-server=http://127.0.0.1:7890",
            )

    def test_resolve_ws_url_seeds_isolated_profile_and_launches_browser(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            debug_dir = Path(temp_dir) / "debug"
            source_dir.mkdir(parents=True)
            (source_dir / "Default").mkdir(parents=True)
            (source_dir / "Default" / "Preferences").write_text("prefs", encoding="utf-8")
            installation = run_web_chat.BrowserInstallation(
                name="chrome",
                browser_path=Path("/tmp/fake-browser"),
                user_data_dir=source_dir,
            )
            args = SimpleNamespace(
                cdp_url=None,
                cdp_http="http://127.0.0.1:9222",
                browser_path=None,
                user_data_source=None,
                debug_profile_dir=str(debug_dir),
                site="qwen",
                port=9222,
                headless=False,
            )

            with mock.patch.object(run_web_chat, "endpoint_ready", side_effect=[False, True]):
                with mock.patch.object(run_web_chat, "detect_browser_installation", return_value=installation):
                    with mock.patch.object(run_web_chat, "start_debug_browser") as start_browser:
                        with mock.patch.object(run_web_chat, "fetch_ws_url", return_value="ws://example.test/devtools/browser/copied"):
                            ws_url = run_web_chat.resolve_ws_url(args, PROJECT_ROOT)

            self.assertEqual(ws_url, "ws://example.test/devtools/browser/copied")
            resolved_debug_dir = debug_dir.resolve()
            self.assertTrue((resolved_debug_dir / "Default" / "Preferences").exists())
            start_browser.assert_called_once()
            launched_installation = start_browser.call_args.args[0]
            self.assertEqual(launched_installation.user_data_dir, resolved_debug_dir)

    def test_resolve_ws_url_reports_startup_log_on_endpoint_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            debug_dir = Path(temp_dir) / "debug"
            source_dir.mkdir(parents=True)
            installation = run_web_chat.BrowserInstallation(
                name="chrome",
                browser_path=Path("/tmp/fake-browser"),
                user_data_dir=source_dir,
            )
            args = SimpleNamespace(
                cdp_url=None,
                cdp_http="http://127.0.0.1:9222",
                browser_path=None,
                user_data_source=None,
                debug_profile_dir=str(debug_dir),
                site="gemini",
                port=9222,
                headless=False,
            )

            def fake_start_browser(*_args, **_kwargs):
                (debug_dir / run_web_chat.CHROME_STARTUP_LOG_NAME).write_text(
                    "chrome failed to start\nprofile error\n",
                    encoding="utf-8",
                )

            with mock.patch.object(run_web_chat, "endpoint_ready", return_value=False):
                with mock.patch.object(run_web_chat, "detect_browser_installation", return_value=installation):
                    with mock.patch.object(run_web_chat, "start_debug_browser", side_effect=fake_start_browser):
                        with mock.patch.object(
                            run_web_chat,
                            "wait_for_endpoint",
                            side_effect=RuntimeError("Chrome DevTools endpoint did not become ready: http://127.0.0.1:9222"),
                        ):
                            with self.assertRaises(RuntimeError) as raised:
                                run_web_chat.resolve_ws_url(args, PROJECT_ROOT)

            message = str(raised.exception)
            self.assertIn(run_web_chat.CHROME_STARTUP_LOG_NAME, message)
            self.assertIn("profile error", message)

    def test_legacy_site_ready_ignores_login_button_when_configured(self) -> None:
        self.assertTrue(
            run_web_chat.legacy_site_ready(
                ready_visible=True,
                login_visible=True,
                ignore_login_when_ready=True,
            )
        )

    def test_legacy_site_ready_requires_login_by_default(self) -> None:
        self.assertFalse(
            run_web_chat.legacy_site_ready(
                ready_visible=True,
                login_visible=True,
                ignore_login_when_ready=False,
            )
        )

    def test_start_debug_browser_uses_requested_start_url(self) -> None:
        installation = run_web_chat.BrowserInstallation(
            name="chrome",
            browser_path=Path("/Applications/Fake Chrome"),
            user_data_dir=Path("/tmp/fake-profile"),
        )

        with mock.patch.object(subprocess, "Popen") as popen:
            run_web_chat.start_debug_browser(
                installation,
                port=9222,
                headless=False,
                initial_url="https://gemini.google.com/app",
            )

        args = popen.call_args.args[0]
        self.assertIn("--remote-debugging-port=9222", args)
        self.assertIn("--disable-breakpad", args)
        self.assertIn("https://gemini.google.com/app", args)
        self.assertNotIn("--restore-last-session", args)

    def test_stop_debug_browser_terminates_process(self) -> None:
        process = mock.Mock()
        process.wait.side_effect = [subprocess.TimeoutExpired(cmd="chrome", timeout=5), None]

        run_web_chat.stop_debug_browser(process)

        process.terminate.assert_called_once()
        process.kill.assert_called_once()

    def test_open_automation_page_prefers_existing_non_startup_page(self) -> None:
        startup_page = RecordingPage("about:blank")
        login_page = RecordingPage("https://xui.ptlogin2.qq.com/cgi-bin/xlogin")
        context = RecordingContext(pages=[startup_page, login_page])

        page = run_web_chat.open_automation_page(context, "https://yuanbao.tencent.com/chat")

        self.assertIs(page, login_page)
        self.assertEqual(context.new_page_calls, 0)

    def test_yuanbao_ignores_login_marker_once_input_is_ready(self) -> None:
        self.assertTrue(run_web_chat.SITE_CONFIG["yuanbao"].get("ignore_login_when_ready", False))


if __name__ == "__main__":
    unittest.main()
