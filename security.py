import win32gui
from config import ALLOWED_CHAT_ID

BLOCKED_TITLES = [
    "cmd.exe", "powershell", "windows powershell", "terminal",
    "keepass", "bitwarden", "1password", "lastpass",
    "registry editor", "task manager", "regedit",
]

def is_authorized(chat_id: int) -> bool:
    return chat_id == ALLOWED_CHAT_ID

def is_safe_target() -> tuple[bool, str]:
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd).lower()
    for blocked in BLOCKED_TITLES:
        if blocked in title:
            return False, title
    return True, title
