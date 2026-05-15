import sys
import threading
from pathlib import Path
import pystray
from PIL import Image, ImageDraw

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

def is_auto_enter() -> bool:
    return _auto_enter

def _toggle_auto_enter(icon, item):
    global _auto_enter
    _auto_enter = not _auto_enter

def _bot_label() -> str:
    return _bot_name.strip()

def _title(status: str = "פעיל") -> str:
    base = f"Voice2Cursor v{VERSION}"
    bot = _bot_label()
    return f"{base} | {bot} — {status}" if bot else f"{base} — {status}"

def _build_tray(on_exit, on_settings):
    global _tray
    _tray = pystray.Icon(
        "Voice2Cursor",
        ICON_GREEN,
        _title(),
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: _title(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("שלח Enter אוטומטי", _toggle_auto_enter, checked=lambda item: _auto_enter),
            pystray.MenuItem("⚙ הגדרות", lambda: on_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("יציאה", lambda: on_exit()),
        ),
    )
    _tray.run()

def start(on_exit, on_settings, bot_name: str = ""):
    global _bot_name
    _bot_name = bot_name
    t = threading.Thread(target=_build_tray, args=(on_exit, on_settings), daemon=True)
    t.start()

def set_error():
    if _tray:
        _tray.icon = ICON_GRAY
        _tray.title = _title("שגיאה")

def set_ok():
    if _tray:
        _tray.icon = ICON_GREEN
        _tray.title = _title()

def stop():
    if _tray:
        _tray.stop()
