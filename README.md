# Voice2Cursor

Dictate into any Windows app via Telegram — send a voice message or text, and it appears at your cursor instantly.

[![Version](https://img.shields.io/badge/version-v1.0.0-brightgreen.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## How It Works

1. You send a text message (or a voice message transcribed by Telegram) to your private bot
2. Voice2Cursor receives it via long-polling
3. The text is pasted into whatever window is currently in focus — as if you typed it

```
[Phone mic] → Telegram voice message → transcription → Telegram Bot API
                                                              ↓
                                          Voice2Cursor (Windows background service)
                                                              ↓
                                              Clipboard → Ctrl+V → active window
```

---

## Features

- **Any app** — pastes into VS Code, Word, Notepad, browsers, chat apps, anything that accepts Ctrl+V
- **Voice-first** — works with Telegram's built-in voice-to-text transcription
- **Authorized only** — single whitelist chat ID; all other senders are silently ignored
- **Safe injection** — blocks paste into terminals, password managers, registry editors, and task manager
- **Stale message protection** — discards messages older than 30 seconds (replay prevention)
- **System tray** — green/gray dot shows live connection status; right-click to exit
- **EXE build** — ships as a standalone executable via PyInstaller, no Python required
- **Auto-start** — registers to launch at Windows login, no admin rights required
- **Rotating logs** — up to 3 × 1 MB log files under `logs/`

---

## Requirements

- Windows 10 / 11
- Python 3.10+ *(only needed to build the EXE — not needed to run it)*
- A Telegram bot token ([create one via @BotFather](https://t.me/BotFather))
- Your personal Telegram chat ID ([get it via @userinfobot](https://t.me/userinfobot))

---

## Quick Start

### 1. Configure

```bash
copy .env.example .env
```

Edit `.env`:

```ini
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
ALLOWED_CHAT_ID=987654321
```

**How to find your chat ID:**
1. Send any message to your new bot
2. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
3. Copy the value of `result[0].message.chat.id`

### 2. Build EXE

```bat
build.bat
```

Installs dependencies, builds `dist\Voice2Cursor\Voice2Cursor.exe`, and copies `.env` automatically.

### 3. Register auto-start

```bash
python setup_task_scheduler.py
```

Tries Task Scheduler first (30-second delay after login). Falls back to the user Startup folder — no admin rights needed either way.

```bash
# To unregister
python setup_task_scheduler.py --remove
```

### Run without building (development)

```bash
pip install -r requirements.txt
python main.py
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | Telegram Bot API long-polling |
| `pywin32` | Clipboard access + keyboard simulation |
| `pystray` | Windows system tray icon |
| `Pillow` | Tray icon rendering |
| `python-dotenv` | `.env` config loading |

---

## Security

### Authorization
Only messages from `ALLOWED_CHAT_ID` are processed. All other senders receive no response and are logged as unauthorized.

### Blocked windows
Paste is refused if the foreground window title matches any of the following (case-insensitive):

| Blocked |
|---------|
| cmd.exe / PowerShell / Terminal |
| KeePass / Bitwarden / 1Password / LastPass |
| Registry Editor (regedit) |
| Task Manager |

### Stale message guard
Messages older than 30 seconds are discarded, preventing replayed or queued messages from injecting text after a restart.

---

## Project Structure

```
Voice2Cursor/
├── main.py                  # Bot loop — polls Telegram, dispatches messages
├── config.py                # Loads and validates .env settings
├── security.py              # Chat ID whitelist + blocked-window check
├── injector.py              # Clipboard write + Ctrl+V keystroke
├── tray.py                  # System tray icon and menu
├── setup_task_scheduler.py  # Registers / removes auto-start
├── Voice2Cursor.spec        # PyInstaller build spec
├── build.bat                # One-click build script
├── VERSION                  # Current version number
├── requirements.txt
├── .env.example
└── logs/
    └── voice2cursor.log     # Rotating log (3 × 1 MB)
```

---

## Troubleshooting

**Nothing is pasted**
- Check `logs/voice2cursor.log` — look for `BLOCKED` or `Paste failed` entries
- Make sure the target window is in focus when you send the message
- Verify `ALLOWED_CHAT_ID` matches your actual chat ID

**Tray icon is gray**
- No network connectivity to Telegram API
- The bot reconnects automatically with exponential backoff

**Bot doesn't start**
- Confirm `BOT_TOKEN` is correct in `.env`
- Run `python main.py` manually to see startup errors in the console

**Auto-start registration fails**
- Make sure you're running as your normal user (not elevated/admin)
- Check that `pythonw.exe` exists in your Python installation directory

---

## Changelog

### v1.0.0 — 2026-05-15
- Initial release
- Telegram long-polling bot with single-user whitelist
- Clipboard injection via Ctrl+V into the active window
- Blocked-window safety list (terminals, password managers, etc.)
- System tray icon with green/gray status indicator
- PyInstaller EXE build (`build.bat`)
- Auto-start via Task Scheduler / Startup folder (`setup_task_scheduler.py`)
- Rotating log files

---

## License

MIT — see [LICENSE](LICENSE)
