import logging
import threading
import traceback
import pystray
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

from app_assets import app_base_dir, app_icon_png
import bot_store

logger = logging.getLogger(__name__)

_base = app_base_dir()
try:
    VERSION = (_base / "VERSION").read_text().strip()
except Exception:
    VERSION = "?"


def _load_icon() -> Image.Image:
    try:
        return Image.open(app_icon_png()).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    except Exception:
        logger.warning("Could not load app icon asset; using a simple fallback icon", exc_info=True)
        return Image.new("RGBA", (64, 64), (14, 165, 233, 255))


def _disabled_icon(icon: Image.Image) -> Image.Image:
    alpha = icon.getchannel("A")
    gray = ImageOps.grayscale(icon).convert("RGBA")
    gray.putalpha(alpha)
    return ImageEnhance.Brightness(gray).enhance(0.62)


def _with_status_dot(icon: Image.Image, color: str) -> Image.Image:
    img = icon.copy()
    draw = ImageDraw.Draw(img)
    draw.ellipse([44, 44, 63, 63], fill=(10, 12, 18, 230))
    draw.ellipse([48, 48, 60, 60], fill=color)
    return img


_BASE_ICON = _load_icon()
ICON_OK = _with_status_dot(_BASE_ICON, "#22c55e")
ICON_ERROR = _with_status_dot(_disabled_icon(_BASE_ICON), "#6b7280")

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
        _tray = pystray.Icon("Voice2Cursor", ICON_OK, _title(), menu=_build_menu())
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
        _tray.icon = ICON_ERROR
        _tray.title = _title()

def set_ok():
    global _status
    _status = "פעיל"
    if _tray:
        _tray.icon = ICON_OK
        _tray.title = _title()

def stop():
    if _tray:
        _tray.stop()
