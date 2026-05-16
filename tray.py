import sys
import logging
import threading
import traceback
from pathlib import Path
import pystray
from PIL import Image, ImageDraw

import bot_store

logger = logging.getLogger(__name__)

_base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
try:
    VERSION = (_base / "VERSION").read_text().strip()
except Exception:
    VERSION = "?"

def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img

ICON_GREEN = _make_icon("#22c55e")
ICON_GRAY  = _make_icon("#6b7280")

_tray: pystray.Icon | None = None
_auto_enter: bool = False
_bot_name: str = ""
_status: str = "פעיל"
_current_token: str = ""
_on_exit = None
_on_settings = None
_on_switch_bot = None  # callable(token: str, chat_id: str)

def is_auto_enter() -> bool:
    return _auto_enter

def _toggle_auto_enter(icon, item):
    global _auto_enter
    _auto_enter = not _auto_enter

def _bot_label() -> str:
    return _bot_name.strip()

def _title() -> str:
    base = f"Voice2Cursor v{VERSION}"
    bot = _bot_label()
    sep = " - "
    return f"{base} | {bot}{sep}{_status}" if bot else f"{base}{sep}{_status}"

def _make_bot_click(token: str, chat_id: str):
    def _click(icon, item):
        if _on_switch_bot and token != _current_token:
            _on_switch_bot(token, chat_id)
    return _click

def _make_bot_checked(token: str):
    def _check(item):
        return token == _current_token
    return _check

def _build_menu():
    """Build the entire tray menu fresh. Called once at icon creation and again
    whenever the bots list changes (via _rebuild_tray)."""
    items = [
        pystray.MenuItem(lambda item: _title(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("שלח Enter אוטומטי", _toggle_auto_enter, checked=lambda item: _auto_enter),
    ]
    bots = bot_store.load_bots()
    if bots:
        bot_items = []
        for bot in bots:
            token = bot.get("token", "")
            chat_id = bot.get("chat_id", "")
            label = bot_store.display_label(bot)
            bot_items.append(pystray.MenuItem(
                label,
                _make_bot_click(token, chat_id),
                checked=_make_bot_checked(token),
                radio=True,
            ))
        items.append(pystray.MenuItem("🤖 בוטים", pystray.Menu(*bot_items)))
    items.extend([
        pystray.MenuItem("⚙ הגדרות", lambda: _on_settings() if _on_settings else None),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("יציאה", lambda: _on_exit() if _on_exit else None),
    ])
    return pystray.Menu(*items)

def _build_tray():
    global _tray
    try:
        _tray = pystray.Icon("Voice2Cursor", ICON_GREEN, _title(), menu=_build_menu())
        logger.info("Tray icon created — entering pystray run loop")
        _tray.run()
        logger.info("pystray run loop exited normally")
    except Exception:
        logger.error("Tray failed:\n%s", traceback.format_exc())

def start(on_exit, on_settings, bot_name: str = "", current_token: str = ""):
    global _bot_name, _current_token, _on_exit, _on_settings
    _bot_name = bot_name
    _current_token = current_token
    _on_exit = on_exit
    _on_settings = on_settings
    t = threading.Thread(target=_build_tray, daemon=True, name="tray")
    t.start()

def set_bot_name(bot_name: str):
    global _bot_name
    _bot_name = bot_name.strip()
    if _tray:
        _tray.title = _title()

def set_current_token(token: str):
    global _current_token
    _current_token = (token or "").strip()

def set_on_switch_bot(callback):
    global _on_switch_bot
    _on_switch_bot = callback

def set_error():
    global _status
    _status = "שגיאה"
    if _tray:
        _tray.icon = ICON_GRAY
        _tray.title = _title()

def set_ok():
    global _status
    _status = "פעיל"
    if _tray:
        _tray.icon = ICON_GREEN
        _tray.title = _title()

def stop():
    if _tray:
        _tray.stop()
