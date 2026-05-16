@echo off
REM Fast publish build — no dependency install, no --clean (uses PyInstaller cache).
REM Use build.bat for a clean, full-dependency build.

for /f "tokens=*" %%v in (VERSION) do set VER=%%v
echo [Voice2Cursor] Fast build — v%VER%

pyinstaller Voice2Cursor.spec --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    exit /b 1
)

copy /Y VERSION dist\Voice2Cursor\VERSION > nul
if exist .env (
    copy /Y .env dist\Voice2Cursor\.env > nul
) else (
    echo WARNING: .env not found in dist\Voice2Cursor — copy manually before running.
)

if exist "Voice2Cursor_v%VER%.zip" del "Voice2Cursor_v%VER%.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Voice2Cursor' -DestinationPath 'Voice2Cursor_v%VER%.zip' -Force"

echo.
echo Done — v%VER%
echo   EXE:  dist\Voice2Cursor\Voice2Cursor.exe
echo   ZIP:  Voice2Cursor_v%VER%.zip
