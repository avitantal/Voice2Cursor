@echo off
REM Fast publish build — no dependency install, no --clean (uses PyInstaller cache).
REM Use build.bat for a clean, full-dependency build.

for /f "tokens=*" %%v in (VERSION) do set VER=%%v
echo [Voice2Cursor] Fast build — v%VER%

REM Preserve runtime data — pyinstaller may recreate dist\Voice2Cursor and wipe it.
if exist "dist\Voice2Cursor\bots.json"     copy /Y "dist\Voice2Cursor\bots.json"     "_preserved_bots.json"     > nul
if exist "dist\Voice2Cursor\bots.json.bak" copy /Y "dist\Voice2Cursor\bots.json.bak" "_preserved_bots.json.bak" > nul
if exist "dist\Voice2Cursor\offset.txt"    copy /Y "dist\Voice2Cursor\offset.txt"    "_preserved_offset.txt"    > nul

pyinstaller Voice2Cursor.spec --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    if exist "_preserved_bots.json"     del "_preserved_bots.json"
    if exist "_preserved_bots.json.bak" del "_preserved_bots.json.bak"
    if exist "_preserved_offset.txt"    del "_preserved_offset.txt"
    exit /b 1
)

copy /Y VERSION dist\Voice2Cursor\VERSION > nul
if exist .env (
    copy /Y .env dist\Voice2Cursor\.env > nul
) else (
    echo WARNING: .env not found in dist\Voice2Cursor — copy manually before running.
)
if exist "_preserved_bots.json"     move /Y "_preserved_bots.json"     "dist\Voice2Cursor\bots.json"     > nul
if exist "_preserved_bots.json.bak" move /Y "_preserved_bots.json.bak" "dist\Voice2Cursor\bots.json.bak" > nul
if exist "_preserved_offset.txt"    move /Y "_preserved_offset.txt"    "dist\Voice2Cursor\offset.txt"    > nul

if exist "Voice2Cursor_v%VER%.zip" del "Voice2Cursor_v%VER%.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Voice2Cursor' -DestinationPath 'Voice2Cursor_v%VER%.zip' -Force"

echo.
echo Done — v%VER%
echo   EXE:  dist\Voice2Cursor\Voice2Cursor.exe
echo   ZIP:  Voice2Cursor_v%VER%.zip
