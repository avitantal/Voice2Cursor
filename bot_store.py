"""
bot_store.py — persistent list of bots the user has used.

Stored as JSON next to the EXE (or next to main.py in dev). Each entry holds
token + chat_id + an optional display name (the bot's @username, fetched lazily
from Telegram) + a last_used timestamp used for ordering in the tray menu.

Writes are atomic (tempfile + os.replace) and keep a `.bak` of the previous
version. Reads refuse to silently treat a corrupt file as empty — they fall
back to the backup, and if both fail they raise so callers can't blindly
overwrite the bots list with a truncated singleton.
"""
import os
import sys
import json
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
BOTS_FILE = BASE_DIR / "bots.json"
BACKUP_FILE = BASE_DIR / "bots.json.bak"


class BotStoreReadError(Exception):
    """Raised when bots.json exists with content but cannot be parsed AND the
    backup is also unusable. Callers must not overwrite on this — losing the
    history that's hidden behind a parse error is exactly what we want to avoid.
    """


def _parse(path: Path) -> Optional[list[dict]]:
    """Return a parsed list, or None if the file is missing/empty/invalid."""
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("bot_store: failed to read %s: %s", path.name, e)
        return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception as e:
        logger.warning("bot_store: failed to parse %s: %s", path.name, e)
        return None
    return data if isinstance(data, list) else None


def _read() -> list[dict]:
    """Return saved bots, or raise BotStoreReadError if the file looks corrupt
    and no backup can save us."""
    if not BOTS_FILE.exists():
        return []
    primary = _parse(BOTS_FILE)
    if primary is not None:
        return primary

    # Primary unreadable but exists with content — try backup before giving up.
    backup = _parse(BACKUP_FILE)
    if backup is not None:
        logger.warning("bot_store: primary corrupt — recovered %d bot(s) from backup", len(backup))
        return backup

    raise BotStoreReadError(f"{BOTS_FILE.name} exists but cannot be parsed and no usable backup")


def _write(bots: list[dict]) -> None:
    """Atomic write: temp file in same dir + os.replace + backup of previous state."""
    try:
        if BOTS_FILE.exists():
            try:
                BACKUP_FILE.write_bytes(BOTS_FILE.read_bytes())
            except Exception as e:
                logger.warning("bot_store: failed to refresh backup: %s", e)

        fd, tmp_path = tempfile.mkstemp(prefix="bots.", suffix=".tmp", dir=str(BASE_DIR))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(bots, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, BOTS_FILE)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise
    except Exception as e:
        logger.error("bot_store: write failed (%d bot(s) NOT persisted): %s", len(bots), e)


def load_bots() -> list[dict]:
    """All known bots, most recently used first. Returns [] on unrecoverable error."""
    try:
        bots = _read()
    except BotStoreReadError as e:
        logger.error("bot_store: %s — returning empty list for read-only callers", e)
        return []
    bots.sort(key=lambda b: b.get("last_used", 0), reverse=True)
    return bots


def touch(token: str, chat_id: str, name: Optional[str] = None) -> None:
    """Upsert a bot and refresh its last_used timestamp. If name is None, keeps
    any existing name. Refuses to write if the store is corrupt — better to skip
    one touch than to wipe the history."""
    token = (token or "").strip()
    chat_id = (chat_id or "").strip()
    if not token or not chat_id:
        return
    try:
        bots = _read()
    except BotStoreReadError as e:
        logger.error("bot_store.touch aborted — %s. Existing bots preserved.", e)
        return
    for b in bots:
        if b.get("token") == token:
            b["chat_id"] = chat_id
            if name:
                b["name"] = name
            b["last_used"] = time.time()
            _write(bots)
            logger.info("bot_store: touched existing bot (%s, total=%d)", _short(token), len(bots))
            return
    bots.append({
        "token": token,
        "chat_id": chat_id,
        "name": (name or "").strip(),
        "last_used": time.time(),
    })
    _write(bots)
    logger.info("bot_store: added new bot (%s, total=%d)", _short(token), len(bots))


def update_name(token: str, name: str) -> None:
    """Update only the display name (called once Telegram tells us the @username)."""
    name = (name or "").strip()
    if not name:
        return
    try:
        bots = _read()
    except BotStoreReadError as e:
        logger.error("bot_store.update_name aborted — %s", e)
        return
    changed = False
    for b in bots:
        if b.get("token") == token and b.get("name") != name:
            b["name"] = name
            changed = True
    if changed:
        _write(bots)
        logger.info("bot_store: renamed bot (%s -> %s)", _short(token), name)


def remove(token: str) -> None:
    try:
        bots = _read()
    except BotStoreReadError as e:
        logger.error("bot_store.remove aborted — %s", e)
        return
    before = len(bots)
    bots = [b for b in bots if b.get("token") != token]
    if len(bots) == before:
        logger.info("bot_store.remove: no match for %s", _short(token))
        return
    _write(bots)
    logger.info("bot_store: removed bot (%s, remaining=%d)", _short(token), len(bots))


def display_label(bot: dict) -> str:
    """Human-friendly menu label."""
    name = (bot.get("name") or "").strip()
    if name:
        return name
    token = bot.get("token", "")
    return f"bot {token[:6]}…{token[-4:]}" if len(token) > 12 else "bot"


def _short(token: str) -> str:
    return f"{token[:6]}…{token[-4:]}" if len(token) > 12 else token
