import sys
import time
import logging
import logging.handlers
import threading
import requests
from pathlib import Path
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

def get_updates(offset: int) -> list:
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
        return []

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
    sys.exit(0)

def main():
    logger.info("Voice2Cursor starting up")
    tray.start(on_exit)

    offset = load_offset()
    retry_delay = RETRY_DELAY

    while True:
        updates = get_updates(offset)

        if not updates:
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
            time.sleep(retry_delay)
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
