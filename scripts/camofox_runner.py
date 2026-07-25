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

    return {"ok": True, "raw": out}


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
    cmd = ["camofox-browser", "type", ref, text]
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


# ---------------------------------------------------------------------------
# Lightweight selector helpers built on top of snapshot text
# ---------------------------------------------------------------------------

def find_ref_by_role(snapshot_text: str, role: str, name_hint: Optional[str] = None) -> Optional[str]:
    """
    Light parser for camofox/Hermes accessibility snapshot lines.
    Handles both:
      - textbox "How can I help you today?" [e8]:
      - textbox "How can I help you today?" [e8]
    """
    import re
    pattern = rf'-\s+{re.escape(role)}\s+"([^"]+)"\s+\[([^\]]+)\]'
    for line in snapshot_text.splitlines():
        m = re.search(pattern, line)
        if not m:
            continue
        label, ref = m.group(1), m.group(2)
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
