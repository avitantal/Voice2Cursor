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
echo [Voice2Cursor] Copying config files to dist folder...
if exist .env (
    copy /Y .env dist\Voice2Cursor\.env > nul
) else (
    echo WARNING: .env not found. Copy it manually to dist\Voice2Cursor\.env before running.
)
copy /Y VERSION dist\Voice2Cursor\VERSION > nul
echo Done.

echo.
echo Build complete! EXE is in: dist\Voice2Cursor\Voice2Cursor.exe
echo.
echo To register as Windows startup task, run:
echo   python setup_task_scheduler.py
echo.
pause
