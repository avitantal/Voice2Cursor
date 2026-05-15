"""
Run once to register Voice2Cursor to auto-start at Windows login.
Usage:
  python setup_task_scheduler.py          # register
  python setup_task_scheduler.py --remove # unregister

Strategy (no admin rights required):
  1. Try Windows Task Scheduler (schtasks) — preferred, supports 30-sec delay.
  2. Fall back to a .bat shortcut in the user's Startup folder.
"""
import os
import sys
import subprocess
from pathlib import Path

TASK_NAME    = "Voice2Cursor"
WORKDIR      = Path(__file__).parent
EXE_PATH     = WORKDIR / "dist" / "Voice2Cursor" / "Voice2Cursor.exe"
STARTUP_DIR  = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
STARTUP_BAT  = STARTUP_DIR / "Voice2Cursor.bat"

if EXE_PATH.exists():
    COMMAND   = str(EXE_PATH)
    ARGUMENTS = []
else:
    COMMAND   = str(Path(sys.executable).parent / "pythonw.exe")
    ARGUMENTS = [str(WORKDIR / "main.py")]


# ── Task Scheduler (preferred) ──────────────────────────────────────────────

def _register_schtasks() -> bool:
    """Returns True if registration succeeded."""
    tr = COMMAND + (f' "{ARGUMENTS[0]}"' if ARGUMENTS else "")
    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", TASK_NAME,
            "/TR", tr,
            "/SC", "ONLOGON",
            "/DELAY", "0000:30",
            "/RL", "LIMITED",
            "/F",
        ],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _remove_schtasks():
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True, text=True,
    )


# ── Startup folder fallback ──────────────────────────────────────────────────

def _register_startup_bat():
    args_str = f' "{ARGUMENTS[0]}"' if ARGUMENTS else ""
    bat = f'@echo off\nstart "" "{COMMAND}"{args_str}\n'
    STARTUP_BAT.write_text(bat)


def _remove_startup_bat():
    STARTUP_BAT.unlink(missing_ok=True)


# ── Public interface ─────────────────────────────────────────────────────────

def register():
    mode = "EXE" if EXE_PATH.exists() else "Python script"
    print(f"Registering '{TASK_NAME}' ({mode}): {COMMAND}")

    if _register_schtasks():
        print("Registered via Task Scheduler. Voice2Cursor will start automatically 30 s after login.")
    else:
        print("Task Scheduler unavailable — using Startup folder instead.")
        _register_startup_bat()
        print(f"Shortcut created: {STARTUP_BAT}")
        print("Voice2Cursor will start automatically at next login.")


def remove():
    _remove_schtasks()
    _remove_startup_bat()
    print(f"'{TASK_NAME}' removed from both Task Scheduler and Startup folder.")


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        register()
