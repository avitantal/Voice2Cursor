import time
import logging
import win32clipboard
import win32con
import win32api
from security import is_safe_target

logger = logging.getLogger(__name__)

def paste_text(text: str) -> bool:
    safe, window_title = is_safe_target()
    if not safe:
        logger.warning("BLOCKED — window: %s", window_title)
        return False

    try:
        _do_paste(text)
        logger.info("Pasted OK | window: %s | len: %d", window_title, len(text))
        return True
    except Exception as e:
        logger.error("Paste failed: %s", e)
        return False

def _do_paste(text: str):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    win32clipboard.CloseClipboard()

    time.sleep(0.05)

    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('V'), 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
