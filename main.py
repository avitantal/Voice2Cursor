import sys
import traceback
from pathlib import Path

# Catch any crash before logging is set up and write to a fixed path
def _early_except(exc_type, exc_value, exc_tb):
    crash = Path(sys.executable).parent / "crash.txt" if getattr(sys, "frozen", False) else Path(__file__).parent / "crash.txt"
    crash.write_text("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
sys.excepthook = _early_except

# First-run setup: open GUI wizard if .env is missing or incomplete
from setup_wizard import needs_setup, run_wizard, run_settings
if needs_setup():
    if not run_wizard():
        sys.exit(0)

import os
import queue
import time
import logging
import logging.handlers
import subprocess
import threading
import requests
from config import (
    BOT_TOKEN, POLL_TIMEOUT, RETRY_DELAY, MAX_RETRY_DELAY,
    MESSAGE_MAX_AGE, OFFSET_FILE, LOG_DIR,
)
from security import is_authorized
from injector import paste_text
import tray

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

# Persistent GUI thread — all tkinter windows must run on the same thread
# to keep Win32 keyboard routing intact.
_gui_queue: queue.Queue = queue.Queue()

def _gui_worker():
    while True:
        task = _gui_queue.get()
        if task is None:
            return
        try:
            task()
        except Exception:
            pass

threading.Thread(target=_gui_worker, daemon=True, name="gui-worker").start()


def get_updates(offset: int):
    """Return list of updates, or None on network error."""
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": POLL_TIMEOUT},
            timeout=POLL_TIMEOUT + 10,
        )
        r.raise_for_status()
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

def on_settings():
    def _run():
        saved = run_settings()
        if saved:
            logger.info("Settings saved — restarting")
            tray.stop()
            env = os.environ.copy()
            env.pop("BOT_TOKEN", None)
            env.pop("ALLOWED_CHAT_ID", None)
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable], env=env)
            else:
                subprocess.Popen([sys.executable, *sys.argv], env=env)
            os._exit(0)
    _gui_queue.put(_run)

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

def main():
    logger.info("Voice2Cursor starting up")
    bot_name = _fetch_bot_name()
    tray.start(on_exit, on_settings, bot_name=bot_name)

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
