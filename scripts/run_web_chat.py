import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from typing import Optional

from playwright.sync_api import Page
from playwright.sync_api import sync_playwright

STARTED_DEBUG_BROWSER = None
STARTED_DEBUG_BROWSER_LOG_HANDLE = None
CHROME_STARTUP_LOG_NAME = "chrome_startup.log"


SITE_CONFIG = {
    "yuanbao": {
        "mode": "legacy",
        "script": "scripts/yuanbao_playwright.py",
        "url": "https://yuanbao.tencent.com/chat",
        "ready_selectors": ["textarea", 'div[role="textbox"]', '[contenteditable="true"]'],
        "login_selectors": ['text="登录"', 'text="微信扫码登录"', 'text="上次登录"', ".t-dialog__position"],
        "ignore_login_when_ready": True,
        "default_output": "out/yuanbao_answer.txt",
    },
    "longcat": {
        "mode": "legacy",
        "script": "scripts/longcat_playwright.py",
        "url": "https://longcat.chat/",
        "ready_selectors": ['div[role="textbox"]', '[contenteditable="true"]', "textarea"],
        "login_selectors": ['text="登录"', 'text="扫码登录"', 'text="Sign in"'],
        "default_output": "out/longcat_answer.txt",
    },
    "doubao": {
        "mode": "legacy",
        "script": "scripts/doubao_playwright.py",
        "url": "https://www.doubao.com/chat/?channel=sysceo&from_login=1",
        "ready_selectors": ["textarea", 'div[role="textbox"]', '[contenteditable="true"]'],
        "login_selectors": ['button[data-testid="to_login_button"]', 'text="登录"'],
        "ignore_login_when_ready": True,
        "default_output": "out/doubao_answer.txt",
    },
    "qwen": {
        "mode": "generic",
        "script": "scripts/qwen_playwright.py",
        "url": "https://chat.qwen.ai/",
        "default_output": "out/qwen_answer.txt",
    },
    "gemini": {
        "mode": "generic",
        "script": "scripts/gemini_playwright.py",
        "url": "https://gemini.google.com/app",
        "default_output": "out/gemini_answer.txt",
    },
    "grok": {
        "mode": "generic",
        "script": "scripts/grok_playwright.py",
        "url": "https://grok.com/",
        "default_output": "out/grok_answer.txt",
    },
}

IGNORE_DIRS = {
    "Cache",
    "Code Cache",
    "GPUCache",
    "GrShaderCache",
    "ShaderCache",
    "DawnCache",
    "DawnGraphiteCache",
    "DawnWebGPUCache",
    "GraphiteDawnCache",
    "Crashpad",
    "Temp",
}

LOCK_MARKERS = (
    "SingletonLock",
    "SingletonCookie",
    "SingletonSocket",
    "LOCK",
)

SHARED_USER_DATA_ITEMS = (
    "Local State",
    "First Run",
    "Last Version",
    "Variations",
)

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


@dataclass(frozen=True)
class BrowserInstallation:
    name: str
    browser_path: Path
    user_data_dir: Path
    profile_directory: str = "Default"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standardized runner for Yuanbao, LongCat, Doubao, Qwen, Gemini, and Grok chat automation."
    )
    parser.add_argument("--site", choices=sorted(SITE_CONFIG), required=True, help="Target chat site.")
    parser.add_argument("--prompt", required=True, help="Prompt to send to the site.")
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to the current directory or nearest parent containing the site scripts.",
    )
    parser.add_argument("--output", help="Optional output path. Defaults to out/<site>_answer.txt.")
    parser.add_argument("--cdp-http", default="http://127.0.0.1:9222", help="Chrome DevTools HTTP endpoint.")
    parser.add_argument("--cdp-url", help="Chrome DevTools WebSocket URL. If supplied, it is used directly.")
    parser.add_argument("--browser-path", help="Optional Chromium-family executable path.")
    parser.add_argument(
        "--debug-profile-dir",
        help="Isolated debug browser user-data-dir. Defaults to <repo-root>/chrome_debug_profile_skill.",
    )
    parser.add_argument(
        "--user-data-source",
        help="Optional source browser user-data-dir to seed into the isolated debug profile.",
    )
    parser.add_argument("--port", type=int, default=9222, help="DevTools port used when auto-starting the browser.")
    parser.add_argument("--timeout", type=int, default=240, help="Site-script timeout in seconds.")
    parser.add_argument("--stable-rounds", type=int, default=5, help="Stable polling rounds passed to the site script.")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval passed to the site script.")
    parser.add_argument("--login-timeout", type=int, default=600, help="Maximum seconds to wait for user login.")
    parser.add_argument("--headless", action="store_true", help="Launch auto-started browser in headless mode.")
    parser.add_argument("--no-new-chat", action="store_true", help="Pass through to sites that support skipping the new-chat click.")
    return parser.parse_args()


def proxy_free_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def fetch_json(url: str) -> dict:
    opener = proxy_free_opener()
    with opener.open(url, timeout=10) as response:
        return json.load(response)


def endpoint_ready(cdp_http: str) -> bool:
    try:
        fetch_json(cdp_http.rstrip("/") + "/json/version")
        return True
    except Exception:
        return False


def fetch_ws_url(cdp_http: str) -> str:
    payload = fetch_json(cdp_http.rstrip("/") + "/json/version")
    ws_url = payload.get("webSocketDebuggerUrl")
    if not ws_url:
        raise RuntimeError(f"DevTools endpoint did not return webSocketDebuggerUrl: {cdp_http}")
    return ws_url


def required_script_paths() -> list[str]:
    return sorted({config["script"] for config in SITE_CONFIG.values()})


def repo_contains_site_scripts(candidate: Path) -> bool:
    return all((candidate / script_path).exists() for script_path in required_script_paths())


def find_repo_root(start: Optional[str]) -> Path:
    if start:
        candidate = Path(start).expanduser().resolve()
        if repo_contains_site_scripts(candidate):
            return candidate
        raise RuntimeError(f"repo-root does not contain the site scripts: {candidate}")

    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        if repo_contains_site_scripts(candidate):
            return candidate
    raise RuntimeError("Could not find the repository root containing the site scripts.")


def known_browser_installations() -> list[BrowserInstallation]:
    home = Path.home()
    if sys.platform == "darwin":
        return [
            BrowserInstallation(
                "chrome",
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                home / "Library" / "Application Support" / "Google" / "Chrome",
            ),
            BrowserInstallation(
                "arc",
                Path("/Applications/Arc.app/Contents/MacOS/Arc"),
                home / "Library" / "Application Support" / "Arc" / "User Data",
            ),
            BrowserInstallation(
                "brave",
                Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
                home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser",
            ),
            BrowserInstallation(
                "edge",
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                home / "Library" / "Application Support" / "Microsoft Edge",
            ),
            BrowserInstallation(
                "chromium",
                Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
                home / "Library" / "Application Support" / "Chromium",
            ),
        ]

    if sys.platform.startswith("linux"):
        return [
            BrowserInstallation("chrome", Path("/usr/bin/google-chrome"), home / ".config" / "google-chrome"),
            BrowserInstallation("chrome", Path("/usr/bin/google-chrome-stable"), home / ".config" / "google-chrome"),
            BrowserInstallation("chromium", Path("/usr/bin/chromium"), home / ".config" / "chromium"),
            BrowserInstallation("chromium", Path("/usr/bin/chromium-browser"), home / ".config" / "chromium"),
            BrowserInstallation(
                "brave",
                Path("/usr/bin/brave-browser"),
                home / ".config" / "BraveSoftware" / "Brave-Browser",
            ),
            BrowserInstallation("edge", Path("/usr/bin/microsoft-edge"), home / ".config" / "microsoft-edge"),
        ]

    if sys.platform.startswith("win"):
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        return [
            BrowserInstallation(
                "chrome",
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                local / "Google" / "Chrome" / "User Data",
            ),
            BrowserInstallation(
                "chrome",
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                local / "Google" / "Chrome" / "User Data",
            ),
            BrowserInstallation(
                "edge",
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                local / "Microsoft" / "Edge" / "User Data",
            ),
            BrowserInstallation(
                "brave",
                Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
                local / "BraveSoftware" / "Brave-Browser" / "User Data",
            ),
        ]

    return []


def guessed_user_data_dir(browser_path: Path) -> Optional[Path]:
    path_text = str(browser_path).lower()
    home = Path.home()
    if "arc" in path_text:
        return home / "Library" / "Application Support" / "Arc" / "User Data"
    if "brave" in path_text:
        if sys.platform == "darwin":
            return home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser"
        if sys.platform.startswith("linux"):
            return home / ".config" / "BraveSoftware" / "Brave-Browser"
        if sys.platform.startswith("win"):
            local = Path(os.environ.get("LOCALAPPDATA", ""))
            return local / "BraveSoftware" / "Brave-Browser" / "User Data"
    if "edge" in path_text or "msedge" in path_text:
        if sys.platform == "darwin":
            return home / "Library" / "Application Support" / "Microsoft Edge"
        if sys.platform.startswith("linux"):
            return home / ".config" / "microsoft-edge"
        if sys.platform.startswith("win"):
            local = Path(os.environ.get("LOCALAPPDATA", ""))
            return local / "Microsoft" / "Edge" / "User Data"
    if "chromium" in path_text:
        if sys.platform == "darwin":
            return home / "Library" / "Application Support" / "Chromium"
        return home / ".config" / "chromium"
    return default_user_data_source()


def default_user_data_source() -> Optional[Path]:
    for candidate in known_browser_installations():
        if candidate.user_data_dir:
            return candidate.user_data_dir
    return None


def choose_profile_directory(user_data_dir: Path) -> str:
    local_state = user_data_dir / "Local State"
    if not local_state.exists():
        return "Default"

    try:
        payload = json.loads(local_state.read_text(encoding="utf-8"))
    except Exception:
        return "Default"

    info_cache = payload.get("profile", {}).get("info_cache", {})
    if not isinstance(info_cache, dict) or not info_cache:
        return "Default"

    signed_in_candidates: list[tuple[float, str]] = []
    fallback_candidates: list[tuple[float, str]] = []
    for directory, info in info_cache.items():
        if not isinstance(info, dict):
            continue
        active_time = float(info.get("active_time") or 0)
        fallback_candidates.append((active_time, directory))
        if info.get("user_name") or info.get("gaia_name"):
            signed_in_candidates.append((active_time, directory))

    candidates = signed_in_candidates or fallback_candidates
    if not candidates:
        return "Default"
    candidates.sort()
    return candidates[-1][1]


def detect_browser_installation(explicit_path: Optional[str], explicit_user_data_source: Optional[str]) -> BrowserInstallation:
    if explicit_path:
        browser_path = Path(explicit_path).expanduser().resolve()
        if not browser_path.exists():
            raise RuntimeError(f"Browser path does not exist: {explicit_path}")
        user_data_dir = (
            Path(explicit_user_data_source).expanduser().resolve()
            if explicit_user_data_source
            else guessed_user_data_dir(browser_path)
        )
        if user_data_dir is None:
            raise RuntimeError("Could not determine the browser user-data-dir. Pass --user-data-source explicitly.")
        return BrowserInstallation(
            browser_path.stem.lower(),
            browser_path,
            user_data_dir,
            choose_profile_directory(user_data_dir),
        )

    for candidate in known_browser_installations():
        if candidate.browser_path.exists():
            return BrowserInstallation(
                candidate.name,
                candidate.browser_path,
                candidate.user_data_dir,
                choose_profile_directory(candidate.user_data_dir),
            )

    if sys.platform.startswith("linux"):
        fallback_bins = [
            ("google-chrome", Path.home() / ".config" / "google-chrome"),
            ("google-chrome-stable", Path.home() / ".config" / "google-chrome"),
            ("chromium", Path.home() / ".config" / "chromium"),
            ("chromium-browser", Path.home() / ".config" / "chromium"),
            ("brave-browser", Path.home() / ".config" / "BraveSoftware" / "Brave-Browser"),
            ("microsoft-edge", Path.home() / ".config" / "microsoft-edge"),
        ]
        for binary_name, user_data_dir in fallback_bins:
            found = shutil.which(binary_name)
            if found:
                return BrowserInstallation(
                    binary_name,
                    Path(found),
                    user_data_dir,
                    choose_profile_directory(user_data_dir),
                )

    raise RuntimeError(
        "Could not locate a supported Chromium-family browser. Pass --browser-path explicitly."
    )


def profile_appears_locked(user_data_dir: Path) -> bool:
    return any(os.path.lexists(user_data_dir / marker) for marker in LOCK_MARKERS)


def clear_lock_markers(user_data_dir: Path) -> None:
    for marker in LOCK_MARKERS:
        marker_path = user_data_dir / marker
        if not os.path.lexists(marker_path):
            continue
        try:
            if marker_path.is_dir() and not marker_path.is_symlink():
                shutil.rmtree(marker_path)
            else:
                marker_path.unlink()
        except OSError:
            continue


def browser_proxy_arg() -> Optional[str]:
    for key in ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "all_proxy", "ALL_PROXY"):
        value = os.environ.get(key)
        if value:
            return f"--proxy-server={value}"
    return None


def reset_directory(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return

    for child in path.iterdir():
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        except OSError:
            continue


def startup_log_path(user_data_dir: Path) -> Path:
    return user_data_dir / CHROME_STARTUP_LOG_NAME


def read_startup_log_excerpt(user_data_dir: Path, max_lines: int = 20) -> str:
    log_path = startup_log_path(user_data_dir)
    if not log_path.exists():
        return ""

    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

    lines = [line.rstrip() for line in content.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:])


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        return

    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def seed_debug_profile(source: Optional[Path], target: Path, profile_directory: str = "Default") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    if source and source.exists():
        try:
            if source.resolve() == target.resolve():
                clear_lock_markers(target)
                return
        except OSError:
            pass

    reset_directory(target)

    if not source or not source.exists():
        return

    for item_name in SHARED_USER_DATA_ITEMS:
        copy_path(source / item_name, target / item_name)

    profile_source = source / profile_directory
    if profile_source.exists():
        copy_path(profile_source, target / profile_directory)

    clear_lock_markers(target)


def start_debug_browser(installation: BrowserInstallation, port: int, headless: bool, initial_url: str = "about:blank") -> None:
    global STARTED_DEBUG_BROWSER
    global STARTED_DEBUG_BROWSER_LOG_HANDLE
    installation.user_data_dir.mkdir(parents=True, exist_ok=True)
    clear_lock_markers(installation.user_data_dir)
    log_path = startup_log_path(installation.user_data_dir)
    try:
        if STARTED_DEBUG_BROWSER_LOG_HANDLE is not None:
            STARTED_DEBUG_BROWSER_LOG_HANDLE.close()
    except Exception:
        pass
    STARTED_DEBUG_BROWSER_LOG_HANDLE = open(log_path, "wb")
    args = [
        str(installation.browser_path),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={installation.user_data_dir}",
        f"--profile-directory={installation.profile_directory}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-breakpad",
        initial_url,
    ]
    proxy_arg = browser_proxy_arg()
    if proxy_arg:
        args.append(proxy_arg)
    if headless:
        args.append("--headless=new")
    if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
        args.append("--no-sandbox")

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    STARTED_DEBUG_BROWSER = subprocess.Popen(
        args,
        stdout=STARTED_DEBUG_BROWSER_LOG_HANDLE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )


def stop_debug_browser(process) -> None:
    global STARTED_DEBUG_BROWSER_LOG_HANDLE
    if process is None:
        try:
            if STARTED_DEBUG_BROWSER_LOG_HANDLE is not None:
                STARTED_DEBUG_BROWSER_LOG_HANDLE.close()
                STARTED_DEBUG_BROWSER_LOG_HANDLE = None
        except Exception:
            return
        return

    try:
        process.terminate()
    except Exception:
        pass
    try:
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
        try:
            process.wait(timeout=5)
        except Exception:
            pass
    finally:
        try:
            if STARTED_DEBUG_BROWSER_LOG_HANDLE is not None:
                STARTED_DEBUG_BROWSER_LOG_HANDLE.close()
                STARTED_DEBUG_BROWSER_LOG_HANDLE = None
        except Exception:
            pass


def wait_for_endpoint(cdp_http: str, timeout: int = 45) -> None:
    started = time.time()
    while time.time() - started < timeout:
        if endpoint_ready(cdp_http):
            return
        time.sleep(1)
    raise RuntimeError(f"Chrome DevTools endpoint did not become ready: {cdp_http}")


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


def legacy_site_ready(ready_visible: bool, login_visible: bool, ignore_login_when_ready: bool = False) -> bool:
    return ready_visible and (ignore_login_when_ready or not login_visible)


def open_automation_page(context, target_url: Optional[str] = None) -> Page:
    existing_pages = list(getattr(context, "pages", []))
    for existing_page in existing_pages:
        try:
            if target_url and target_url in existing_page.url:
                return existing_page
        except Exception:
            continue
    for existing_page in reversed(existing_pages):
        try:
            if existing_page.url not in STARTUP_PAGE_PREFIXES:
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


def ensure_logged_in(site: str, ws_url: str, login_timeout: int) -> None:
    config = SITE_CONFIG[site]
    if config.get("mode") != "legacy":
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context(viewport={"width": 1440, "height": 960})
        page = open_automation_page(context, config["url"])
        if page.url in STARTUP_PAGE_PREFIXES:
            page.goto(config["url"], wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        if legacy_site_ready(
            ready_visible=any_visible(page, config["ready_selectors"]),
            login_visible=any_visible(page, config["login_selectors"]),
            ignore_login_when_ready=config.get("ignore_login_when_ready", False),
        ):
            return

        print(
            f"[{site}] login required. Complete login in the opened browser window; execution will continue automatically.",
            flush=True,
        )
        started = time.time()
        while time.time() - started < login_timeout:
            try:
                page = open_automation_page(context, config["url"])
                if page.url in STARTUP_PAGE_PREFIXES:
                    page.goto(config["url"], wait_until="domcontentloaded", timeout=60000)
                if legacy_site_ready(
                    ready_visible=any_visible(page, config["ready_selectors"]),
                    login_visible=any_visible(page, config["login_selectors"]),
                    ignore_login_when_ready=config.get("ignore_login_when_ready", False),
                ):
                    return
                page.wait_for_timeout(2000)
            except Exception:
                time.sleep(2)

        raise RuntimeError(f"[{site}] login was not completed within {login_timeout} seconds.")


def build_site_command(args: argparse.Namespace, repo_root: Path, ws_url: str) -> list[str]:
    config = SITE_CONFIG[args.site]
    script_path = repo_root / config["script"]
    output = args.output or str(repo_root / config["default_output"])

    if config["mode"] == "generic":
        return [
            sys.executable,
            str(script_path),
            "--question",
            args.prompt,
            "--cdp-url",
            ws_url,
            "--timeout",
            str(args.timeout),
            "--stable-rounds",
            str(args.stable_rounds),
            "--interval",
            str(args.interval),
            "--login-timeout",
            str(args.login_timeout),
            "--output",
            output,
        ]

    cmd = [
        sys.executable,
        str(script_path),
        args.prompt,
        "--cdp-url",
        ws_url,
        "--skip-login-wait",
        "--timeout",
        str(args.timeout),
        "--stable-rounds",
        str(args.stable_rounds),
        "--interval",
        str(args.interval),
        "--output",
        output,
    ]
    if args.no_new_chat and args.site in {"longcat", "doubao"}:
        cmd.append("--no-new-chat")
    return cmd


def resolve_ws_url(args: argparse.Namespace, repo_root: Path) -> str:
    if args.cdp_url:
        return args.cdp_url

    if endpoint_ready(args.cdp_http):
        return fetch_ws_url(args.cdp_http)

    installation = detect_browser_installation(args.browser_path, args.user_data_source)
    debug_profile_dir = (
        Path(args.debug_profile_dir).expanduser().resolve()
        if args.debug_profile_dir
        else (repo_root / "chrome_debug_profile_skill")
    )
    seed_debug_profile(installation.user_data_dir, debug_profile_dir, installation.profile_directory)
    debug_installation = BrowserInstallation(
        name=installation.name,
        browser_path=installation.browser_path,
        user_data_dir=debug_profile_dir,
        profile_directory=installation.profile_directory,
    )

    print(
        f"Starting {installation.name} with isolated debug profile {debug_profile_dir} for {args.site} on {args.cdp_http} ...",
        flush=True,
    )
    start_debug_browser(
        debug_installation,
        args.port,
        args.headless,
        SITE_CONFIG.get(args.site, {}).get("url", "about:blank"),
    )
    try:
        wait_for_endpoint(args.cdp_http)
    except RuntimeError as exc:
        log_path = startup_log_path(debug_profile_dir)
        log_excerpt = read_startup_log_excerpt(debug_profile_dir)
        message = f"{exc}. If the copied debug profile is stale, remove {debug_profile_dir} and retry."
        if log_excerpt:
            message += f" Startup log ({log_path}):\n{log_excerpt}"
        else:
            message += f" Startup log path: {log_path}"
        raise RuntimeError(
            message
        ) from exc
    return fetch_ws_url(args.cdp_http)


def main() -> int:
    global STARTED_DEBUG_BROWSER
    args = parse_args()
    try:
        repo_root = find_repo_root(args.repo_root)
        ws_url = resolve_ws_url(args, repo_root)

        if SITE_CONFIG[args.site]["mode"] == "legacy":
            ensure_logged_in(args.site, ws_url, args.login_timeout)

        cmd = build_site_command(args, repo_root, ws_url)
        print("Running:", " ".join(f'"{part}"' if " " in part else part for part in cmd), flush=True)
        completed = subprocess.run(cmd, cwd=repo_root)
        return completed.returncode
    finally:
        stop_debug_browser(STARTED_DEBUG_BROWSER)
        STARTED_DEBUG_BROWSER = None


if __name__ == "__main__":
    raise SystemExit(main())
