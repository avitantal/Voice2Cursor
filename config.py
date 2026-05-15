import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise RuntimeError(f"Missing required config: {key} — check your .env file")
    return val

BOT_TOKEN = _require("BOT_TOKEN")
ALLOWED_CHAT_ID = int(_require("ALLOWED_CHAT_ID"))

POLL_TIMEOUT = 30          # seconds — long-polling hold time
RETRY_DELAY = 5            # seconds — wait after network error
MAX_RETRY_DELAY = 60       # seconds — cap for exponential backoff
MESSAGE_MAX_AGE = 30       # seconds — discard older messages (stale replay protection)
PASTE_DELAY = 0            # seconds — countdown before paste
OFFSET_FILE = Path(__file__).parent / "offset.txt"
LOG_DIR = Path(__file__).parent / "logs"
