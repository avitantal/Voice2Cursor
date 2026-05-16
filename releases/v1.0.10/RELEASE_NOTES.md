# Voice2Cursor v1.0.10 - Release

**Built:** 2026-05-16 19:07:41
**First fully-working release.** All prior versions had a tray icon or settings-window regression.

## Artifacts

| File | Size | SHA-256 |
|------|------|---------|
| Voice2Cursor.exe | 11.45 MB | `AA7A7EC6B0D7E92F932D11EEED180E09E3A39A1E97140FA1F867300555279A80` |
| Voice2Cursor_v1.0.10.zip | 32.66 MB | `46A5D00190EDB0A9BDBD2DE245491D4B689B9A6125FAAFC72566B7F097CB577A` |

The ZIP contains the full `dist\Voice2Cursor\` folder (EXE + PyInstaller `_internal`).
On a fresh machine, unzip somewhere stable, drop a `.env` with `BOT_TOKEN` +
`ALLOWED_CHAT_ID` next to the EXE, then run `Voice2Cursor.exe`. On first launch
without a `.env` the GUI wizard runs automatically.

## What works (verified)

- Tray icon registers (log: `Tray icon created - entering pystray run loop`)
- Telegram bot name resolved and shown in tray title
- `bots.json` written on startup and updated with `@username` from Telegram
- Tray submenu **bots** lists every saved bot, `checked=radio` on the current one
- Tray menu **settings** spawns a child process (`--settings` flag); after the
  child saves the wizard, the parent detects the `.env` mtime change and restarts
- Switching bots from the tray writes `.env`, resets `offset.txt`, restarts cleanly

## Notes for future builds

Always use `build.bat` (or `pyinstaller Voice2Cursor.spec --clean --noconfirm`
followed by copying `VERSION` + `.env` into `dist\Voice2Cursor\`).
The ZIP packager script is at `.qa\make-zip.ps1`.
Stop any running `Voice2Cursor.exe` before rebuilding - PyInstaller cannot
overwrite the locked binary, and `Compress-Archive` cannot read the locked log.
