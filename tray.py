import sys
import logging
import threading
import traceback
from pathlib import Path
import pystray
from PIL import Image, ImageColor, ImageDraw

import bot_store

logger = logging.getLogger(__name__)

_base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
try:
    VERSION = (_base / "VERSION").read_text().strip()
except Exception:
    VERSION = "?"

def _mix(left: tuple[int, int, int], right: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(left, right))


def _make_icon(color: str) -> Image.Image:
    size = 256
    base = ImageColor.getrgb(color)
    deep = _mix(base, (17, 18, 24), 0.42)
    highlight = _mix(base, (255, 255, 255), 0.28)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([22, 28, 238, 244], fill=(0, 0, 0, 74))
    draw.ellipse([14, 14, 242, 242], fill=deep + (255,))
    draw.ellipse([24, 20, 232, 228], fill=base + (255,))
    draw.ellipse([42, 36, 214, 204], outline=highlight + (150,), width=8)
    draw.arc([46, 48, 210, 214], 214, 326, fill=(255, 255, 255, 90), width=10)

    # Microphone mark, kept chunky so it survives the tiny tray rendering.
    draw.rounded_rectangle([92, 56, 136, 148], radius=22, fill=(255, 255, 255, 244))
    draw.rounded_rectangle([106, 70, 122, 132], radius=8, fill=deep + (210,))
    draw.arc([74, 96, 154, 180], 26, 154, fill=(255, 255, 255, 236), width=11)
    draw.line([114, 150, 114, 180], fill=(255, 255, 255, 236), width=12)
    draw.line([90, 180, 138, 180], fill=(255, 255, 255, 236), width=12)

    cursor = [(148, 132), (218, 188), (184, 196), (202, 226), (180, 238), (162, 204), (134, 226)]
    draw.line(cursor + [cursor[0]], fill=(255, 255, 255, 240), width=12, joint="curve")
    draw.polygon(cursor, fill=(18, 24, 38, 238))

    return img.resize((64, 64), Image.Resampling.LANCZOS)

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
_on_reconnect = None   # callable() — only used while in error state

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
        pystray.MenuItem(
            "🔄 התחבר מחדש",
            lambda: _on_reconnect() if _on_reconnect else None,
            visible=lambda item: _status == "שגיאה",
        ),
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

def set_on_reconnect(callback):
    global _on_reconnect
    _on_reconnect = callback

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
