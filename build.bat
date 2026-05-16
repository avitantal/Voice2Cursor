@echo off
echo [Voice2Cursor] Installing dependencies...
pip install -r requirements.txt pyinstaller

echo.
echo [Voice2Cursor] Preserving runtime data across rebuild...
if exist "dist\Voice2Cursor\bots.json" copy /Y "dist\Voice2Cursor\bots.json" "_preserved_bots.json" > nul
if exist "dist\Voice2Cursor\bots.json.bak" copy /Y "dist\Voice2Cursor\bots.json.bak" "_preserved_bots.json.bak" > nul
if exist "dist\Voice2Cursor\offset.txt" copy /Y "dist\Voice2Cursor\offset.txt" "_preserved_offset.txt" > nul

echo.
echo [Voice2Cursor] Building EXE...
pyinstaller Voice2Cursor.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed.
    if exist "_preserved_bots.json" del "_preserved_bots.json"
    if exist "_preserved_bots.json.bak" del "_preserved_bots.json.bak"
    if exist "_preserved_offset.txt" del "_preserved_offset.txt"
    pause
    exit /b 1
)

echo.
echo [Voice2Cursor] Copying config files...
copy /Y VERSION dist\Voice2Cursor\VERSION > nul
if exist .env (
    copy /Y .env dist\Voice2Cursor\.env > nul
) else (
    echo WARNING: .env not found. Copy it manually to dist\Voice2Cursor\.env before running.
)
if exist "_preserved_bots.json"     move /Y "_preserved_bots.json"     "dist\Voice2Cursor\bots.json"     > nul
if exist "_preserved_bots.json.bak" move /Y "_preserved_bots.json.bak" "dist\Voice2Cursor\bots.json.bak" > nul
if exist "_preserved_offset.txt"    move /Y "_preserved_offset.txt"    "dist\Voice2Cursor\offset.txt"    > nul
echo Done.

echo.
echo [Voice2Cursor] Creating ZIP for distribution...
for /f "tokens=*" %%v in (VERSION) do set VER=%%v
if exist "Voice2Cursor_v%VER%.zip" del "Voice2Cursor_v%VER%.zip"
powershell -Command "Compress-Archive -Path 'dist\Voice2Cursor' -DestinationPath 'Voice2Cursor_v%VER%.zip' -Force"
echo ZIP created: Voice2Cursor_v%VER%.zip

echo.
echo Build complete!
echo   EXE:  dist\Voice2Cursor\Voice2Cursor.exe
echo   ZIP:  Voice2Cursor_v%VER%.zip
echo.
echo To register as Windows startup task, run:
echo   python setup_task_scheduler.py
echo.
pause
