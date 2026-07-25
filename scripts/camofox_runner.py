import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def run(cmd: list[str], cwd: Optional[Path] = None) -> dict:
    """Run a camofox-browser CLI command and parse JSON/text output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "camofox-browser CLI not found. Install it first."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"camofox-browser command timed out: {' '.join(cmd)}")

    out = result.stdout.strip()
    err = result.stderr.strip()
    if result.returncode != 0:
        raise RuntimeError(
            f"camofox-browser failed (rc={result.returncode}): {err or out}"
        )

    # Try JSON first, fall back to plain text.
    if out.startswith("{"):
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    if out.startswith("["):
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass

    # camofox-browser eval/console output uses key: value lines.
    parsed: dict = {"ok": True, "raw": out}
    for line in out.splitlines():
        if line.startswith("result:"):
            parsed["result"] = line[len("result:"):].strip()
        elif line.startswith("resultType:"):
            parsed["resultType"] = line[len("resultType:"):].strip()
        elif line.startswith("truncated:"):
            parsed["truncated"] = line[len("truncated:"):].strip().lower() == "true"
        elif line.startswith("ok:"):
            parsed["ok"] = line[len("ok:"):].strip().lower() == "true"
    return parsed


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------

def open_url(url: str, cwd: Optional[Path] = None) -> str:
    """Open a URL and return the tabId."""
    result = run(["camofox-browser", "open", url], cwd=cwd)
    raw = result.get("raw", "")
    import re
    m = re.search(r"tabId:\s*([^\s]+)", raw)
    if not m:
        raise RuntimeError(f"camofox-browser open did not return tabId: {result}")
    return m.group(1)


def snapshot(tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> str:
    """Get the current accessibility snapshot text."""
    cmd = ["camofox-browser", "snapshot"]
    if tab_id:
        cmd.append(tab_id)
    result = run(cmd, cwd=cwd)
    return result.get("raw", "")


def click(ref: str, tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    cmd = ["camofox-browser", "click", ref]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def type_text(ref: str, text: str, tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    # camofox-browser `type` appends rather than replacing in some versions;
    # focus the field and clear it via JS before typing.
    try:
        click(ref, tab_id=tab_id, cwd=cwd)
    except Exception:
        pass
    try:
        _clear_focused_via_js(tab_id=tab_id, cwd=cwd)
    except Exception:
        pass
    cmd = ["camofox-browser", "type", ref, text]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def _clear_focused_via_js(tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    """Best-effort clear of the currently focused input/textarea."""
    expression = (
        "(() => {"
        "const el = document.activeElement;"
        "if (!el || !['INPUT','TEXTAREA'].includes(el.tagName)) return 'not-focused';"
        "el.value = '';"
        "el.dispatchEvent(new Event('input', {bubbles: true}));"
        "el.dispatchEvent(new Event('change', {bubbles: true}));"
        "return 'cleared';"
        "})()"
    )
    cmd = ["camofox-browser", "eval", expression]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def press(key: str, tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    cmd = ["camofox-browser", "press", key]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def get_text(tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> str:
    cmd = ["camofox-browser", "get-text"]
    if tab_id:
        cmd.append(tab_id)
    result = run(cmd, cwd=cwd)
    return result.get("raw", "")


def get_url(tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> str:
    cmd = ["camofox-browser", "get-url"]
    if tab_id:
        cmd.append(tab_id)
    result = run(cmd, cwd=cwd)
    return result.get("raw", "")


def wait_seconds(seconds: float) -> None:
    time.sleep(seconds)


def list_sessions(cwd: Optional[Path] = None) -> list[str]:
    """List saved camofox session names."""
    result = run(["camofox-browser", "session", "list", "--format", "json"], cwd=cwd)
    if isinstance(result, list):
        data = result
    else:
        raw = result.get("raw", "") if isinstance(result, dict) else ""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(data, list):
        return []
    names: list[str] = []
    for item in data:
        if isinstance(item, str) and item:
            names.append(item)
        elif isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


def save_session(name: str, tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    """Save the current tab state as a named camofox session."""
    cmd = ["camofox-browser", "session", "save", name]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def load_session(name: str, tab_id: Optional[str] = None, cwd: Optional[Path] = None) -> None:
    """Load a saved camofox session into the current or specified tab."""
    cmd = ["camofox-browser", "session", "load", name]
    if tab_id:
        cmd.append(tab_id)
    run(cmd, cwd=cwd)


def fill_credentials(
    tab_id: str,
    email_ref: str,
    password_ref: str,
    email: str,
    password: str,
    cwd: Optional[Path] = None,
) -> None:
    """Fill login form using camofox CLI type commands.

    The `fill` command is flaky in some camofox versions, so we use
    `type` as a more reliable fallback.
    """
    type_text(email_ref, email, tab_id=tab_id, cwd=cwd)
    type_text(password_ref, password, tab_id=tab_id, cwd=cwd)


# ---------------------------------------------------------------------------
# Lightweight selector helpers built on top of snapshot text
# ---------------------------------------------------------------------------

def find_ref_by_role(snapshot_text: str, role: str, name_hint: Optional[str] = None) -> Optional[str]:
    """
    Light parser for camofox/Hermes accessibility snapshot lines.
    Handles:
      - textbox "How can I help you today?" [e8]:
      - textbox "How can I help you today?" [e8]
      - textbox [e20]:
      - textbox [e20]
    """
    import re
    patterns = [
        rf'-\s+{re.escape(role)}\s+"([^"]+)"\s+\[([^\]]+)\]',
        rf'-\s+{re.escape(role)}\s+\[([^\]]+)\]',
    ]
    for line in snapshot_text.splitlines():
        for pattern in patterns:
            m = re.search(pattern, line)
            if not m:
                continue
            if len(m.groups()) == 2:
                label, ref = m.group(1), m.group(2)
            else:
                label, ref = "", m.group(1)
            if name_hint and name_hint.lower() not in label.lower():
                continue
            return ref
    return None


def find_ref_by_text(snapshot_text: str, text_hint: str) -> Optional[str]:
    """Find a generic element ref whose visible text matches."""
    import re
    for line in snapshot_text.splitlines():
        if text_hint.lower() in line.lower() and "[" in line and "]" in line:
            m = re.search(r'\[([^\]]+)\]', line)
            if m:
                return m.group(1)
    return None
