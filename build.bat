@echo off
echo [Voice2Cursor] Installing dependencies...
pip install -r requirements.txt pyinstaller

echo.
echo [Voice2Cursor] Building EXE...
pyinstaller Voice2Cursor.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete! EXE is in: dist\Voice2Cursor\Voice2Cursor.exe
echo.
echo To register as Windows startup task, run:
echo   python setup_task_scheduler.py
echo.
pause
