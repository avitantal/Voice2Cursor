"""
bot_store.py — persistent list of bots the user has used.

Stored as JSON next to the EXE (or next to main.py in dev). Each entry holds
token + chat_id + an optional display name (the bot's @username, fetched lazily
from Telegram) + a last_used timestamp used for ordering in the tray menu.
"""
import sys
import json
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
BOTS_FILE = BASE_DIR / "bots.json"


def _read() -> list[dict]:
    if not BOTS_FILE.exists():
        return []
    try:
        data = json.loads(BOTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write(bots: list[dict]) -> None:
    try:
        BOTS_FILE.write_text(json.dumps(bots, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_bots() -> list[dict]:
    """All known bots, most recently used first."""
    bots = _read()
    bots.sort(key=lambda b: b.get("last_used", 0), reverse=True)
    return bots


def touch(token: str, chat_id: str, name: Optional[str] = None) -> None:
    """Upsert a bot and refresh its last_used timestamp. If name is None, keeps any existing name."""
    token = (token or "").strip()
    chat_id = (chat_id or "").strip()
    if not token or not chat_id:
        return
    bots = _read()
    for b in bots:
        if b.get("token") == token:
            b["chat_id"] = chat_id
            if name:
                b["name"] = name
            b["last_used"] = time.time()
            _write(bots)
            return
    bots.append({
        "token": token,
        "chat_id": chat_id,
        "name": (name or "").strip(),
        "last_used": time.time(),
    })
    _write(bots)


def update_name(token: str, name: str) -> None:
    """Update only the display name (called once Telegram tells us the @username)."""
    name = (name or "").strip()
    if not name:
        return
    bots = _read()
    changed = False
    for b in bots:
        if b.get("token") == token and b.get("name") != name:
            b["name"] = name
            changed = True
    if changed:
        _write(bots)


def remove(token: str) -> None:
    bots = [b for b in _read() if b.get("token") != token]
    _write(bots)


def display_label(bot: dict) -> str:
    """Human-friendly menu label."""
    name = (bot.get("name") or "").strip()
    if name:
        return name
    token = bot.get("token", "")
    return f"bot {token[:6]}…{token[-4:]}" if len(token) > 12 else "bot"
