import sys
import traceback
from pathlib import Path

# Catch any crash before logging is set up and write to a fixed path
def _early_except(exc_type, exc_value, exc_tb):
    crash = Path(sys.executable).parent / "crash.txt" if getattr(sys, "frozen", False) else Path(__file__).parent / "crash.txt"
    crash.write_text("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
sys.excepthook = _early_except

# --settings mode: open the settings window only, then exit. Used by the tray
# to dodge tkinter/pystray cross-thread problems by running the GUI in its own
# process with a clean main thread.
if "--settings" in sys.argv:
    from setup_wizard import run_settings
    run_settings()
    sys.exit(0)

# First-run setup: open GUI wizard if .env is missing or incomplete
from setup_wizard import needs_setup, run_wizard
if needs_setup():
    if not run_wizard():
        sys.exit(0)

import os
import time
import logging
import logging.handlers
import subprocess
import threading
import requests
from config import (
    BOT_TOKEN, ALLOWED_CHAT_ID, POLL_TIMEOUT, RETRY_DELAY, MAX_RETRY_DELAY,
    MESSAGE_MAX_AGE, OFFSET_FILE, LOG_DIR,
)
from security import is_authorized
from injector import paste_text
import tray
import bot_store

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

LOG_DIR.mkdir(exist_ok=True)
handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "voice2cursor.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[handler],
)
logger = logging.getLogger(__name__)
_current_bot_name = ""


def get_updates(offset: int):
    """Return list of updates, or None on network error."""
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": POLL_TIMEOUT},
            timeout=POLL_TIMEOUT + 10,
        )
        r.raise_for_status()
        refresh_bot_name()
        tray.set_ok()
        return r.json().get("result", [])
    except requests.exceptions.RequestException as e:
        logger.warning("Network error: %s", e)
        tray.set_error()
        return None

def send_reply(chat_id: int, text: str):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception:
        pass

def load_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0

def save_offset(offset: int):
    OFFSET_FILE.write_text(str(offset))

def on_exit():
    logger.info("Exiting via tray")
    tray.stop()
    os._exit(0)

def _restart_self():
    """Stop tray, scrub stale env, relaunch the EXE / python script."""
    tray.stop()
    env = os.environ.copy()
    env.pop("BOT_TOKEN", None)
    env.pop("ALLOWED_CHAT_ID", None)
    if getattr(sys, "frozen", False):
        subprocess.Popen([sys.executable], env=env)
    else:
        subprocess.Popen([sys.executable, *sys.argv], env=env)
    os._exit(0)

def on_settings():
    """Launch the settings UI in a child process — avoids tkinter/pystray threading issues.
    If the child writes a new .env (mtime advances), we restart self to pick it up."""
    def _run():
        env_file = OFFSET_FILE.parent / ".env"
        before_mtime = env_file.stat().st_mtime if env_file.exists() else 0
        cmd = [sys.executable, "--settings"] if getattr(sys, "frozen", False) else [sys.executable, sys.argv[0], "--settings"]
        try:
            subprocess.run(cmd, check=False)
        except Exception as e:
            logger.warning("Settings subprocess failed: %s", e)
            return
        after_mtime = env_file.stat().st_mtime if env_file.exists() else 0
        if after_mtime > before_mtime:
            logger.info("Settings saved — restarting")
            _restart_self()
    threading.Thread(target=_run, daemon=True).start()

def on_reconnect():
    """Manual reconnect from tray menu — restart the process to drop any stuck state."""
    logger.info("Manual reconnect requested from tray")
    threading.Thread(target=_restart_self, daemon=True).start()

def on_switch_bot(token: str, chat_id: str):
    """Switch active bot from the tray submenu: write .env, restart self."""
    def _run():
        env_file = OFFSET_FILE.parent / ".env"
        env_file.write_text(f"BOT_TOKEN={token.strip()}\nALLOWED_CHAT_ID={chat_id.strip()}\n", encoding="utf-8")
        # Reset offset so the newly-active bot does not skip queued messages
        OFFSET_FILE.write_text("0", encoding="utf-8")
        bot_store.touch(token, chat_id)
        logger.info("Switching to bot %s — restarting", token[:6] + "…")
        _restart_self()
    threading.Thread(target=_run, daemon=True).start()

def _fetch_bot_name() -> str:
    try:
        r = requests.get(f"{API}/getMe", timeout=8)
        data = r.json()
        if not r.ok or not data.get("ok"):
            return ""
        bot = data.get("result", {})
        username = bot.get("username", "").strip()
        return f"@{username}" if username else bot.get("first_name", "").strip()
    except Exception:
        return ""

def refresh_bot_name(force: bool = False) -> str:
    global _current_bot_name
    if _current_bot_name and not force:
        return _current_bot_name

    bot_name = _fetch_bot_name()
    if bot_name:
        _current_bot_name = bot_name
        tray.set_bot_name(bot_name)
        bot_store.update_name(BOT_TOKEN, bot_name)
        logger.info("Telegram bot detected: %s", bot_name)
    elif force:
        logger.warning("Could not fetch Telegram bot name for tray tooltip")
    return _current_bot_name

def main():
    global _current_bot_name
    logger.info("Voice2Cursor starting up")

    # Register the active bot in the local store (so tray submenu lists it)
    bot_store.touch(BOT_TOKEN, str(ALLOWED_CHAT_ID))

    _current_bot_name = _fetch_bot_name()
    if _current_bot_name:
        bot_store.update_name(BOT_TOKEN, _current_bot_name)
        logger.info("Telegram bot detected: %s", _current_bot_name)
    else:
        logger.warning("Telegram bot name unavailable at startup; will retry after connection")

    tray.set_on_switch_bot(on_switch_bot)
    tray.set_on_reconnect(on_reconnect)
    tray.start(on_exit, on_settings, bot_name=_current_bot_name, current_token=BOT_TOKEN)

    offset = load_offset()
    retry_delay = RETRY_DELAY

    while True:
        updates = get_updates(offset)

        if updates is None:
            # Network error — backoff and retry
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
            continue

        retry_delay = RETRY_DELAY

        for update in updates:
            offset = update["update_id"] + 1
            save_offset(offset)

            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            msg_time = msg.get("date", 0)
            text = msg.get("text", "").strip()

            if not is_authorized(chat_id):
                logger.warning("Unauthorized sender: %d", chat_id)
                continue

            if time.time() - msg_time > MESSAGE_MAX_AGE:
                logger.info("Stale message discarded")
                continue

            if not text:
                send_reply(chat_id, "שלח טקסט.")
                continue

            threading.Thread(target=paste_text, args=(text,), daemon=True).start()

if __name__ == "__main__":
    main()
