"""
Run this once (as the current user) to register Voice2Cursor as a Windows startup task.
Usage: python setup_task_scheduler.py [--remove]
"""
import sys
import subprocess
from pathlib import Path

TASK_NAME = "Voice2Cursor"
SCRIPT = Path(__file__).parent / "main.py"
PYTHONW = Path(sys.executable).parent / "pythonw.exe"
WORKDIR = Path(__file__).parent

XML = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal logonType="InteractiveToken">
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions>
    <Exec>
      <Command>{PYTHONW}</Command>
      <Arguments>"{SCRIPT}"</Arguments>
      <WorkingDirectory>{WORKDIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

def register():
    xml_path = WORKDIR / "_task.xml"
    xml_path.write_text(XML, encoding="utf-16")
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", str(xml_path), "/F"],
        capture_output=True, text=True,
    )
    xml_path.unlink(missing_ok=True)
    if result.returncode == 0:
        print(f"Task '{TASK_NAME}' registered. Voice2Cursor will start automatically on login.")
    else:
        print("Failed to register task:")
        print(result.stderr)

def remove():
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Task '{TASK_NAME}' removed.")
    else:
        print("Could not remove task (maybe it doesn't exist).")
        print(result.stderr)

if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        register()
