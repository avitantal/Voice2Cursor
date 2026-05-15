# Voice2Cursor

Dictate into any Windows app via Telegram — send a voice message or text, and it appears at your cursor instantly.

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
- **Auto-start** — optional Windows Task Scheduler registration, no admin rights required
- **Rotating logs** — up to 3 × 1 MB log files under `logs/`

---

## Requirements

- Windows 10 / 11
- Python 3.10+
- A Telegram bot token ([create one via @BotFather](https://t.me/BotFather))
- Your personal Telegram chat ID ([get it via @userinfobot](https://t.me/userinfobot))

---

## Installation

```bash
git clone https://github.com/your-username/Voice2Cursor.git
cd Voice2Cursor
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | Telegram Bot API long-polling |
| `pywin32` | Clipboard access + keyboard simulation |
| `pystray` | Windows system tray icon |
| `Pillow` | Tray icon rendering |
| `python-dotenv` | `.env` config loading |

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

```ini
# .env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
ALLOWED_CHAT_ID=987654321
```

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Token from @BotFather |
| `ALLOWED_CHAT_ID` | Your personal chat ID — only this sender can trigger pastes |

**How to find your chat ID:**
1. Send any message to your new bot
2. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
3. Copy the value of `result[0].message.chat.id`

---

## Build EXE (recommended)

Build a standalone Windows executable — no Python required on the target machine:

```bat
build.bat
```

The output is placed in `dist\Voice2Cursor\Voice2Cursor.exe`. Copy your `.env` file into that folder before running.

### Run without building

```bash
python main.py
```

A tray icon appears in the system notification area (bottom-right). Green = connected, Gray = network error.

## Auto-start at Login

After building, register Voice2Cursor to launch automatically on Windows login:

```bash
python setup_task_scheduler.py
```

This tries Task Scheduler first (supports a 30-second delay). If that requires elevation, it falls back to placing a shortcut in your user Startup folder — no admin rights needed either way.

```bash
# To unregister
python setup_task_scheduler.py --remove
```

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

If a paste is blocked, the event is logged and no clipboard modification occurs.

### Stale message guard
Messages older than 30 seconds are discarded. This prevents replayed or queued messages from injecting text after the bot restarts.

---

## Project Structure

```
Voice2Cursor/
├── main.py                  # Bot loop — polls Telegram, dispatches messages
├── config.py                # Loads and validates .env settings
├── security.py              # Chat ID whitelist + blocked-window check
├── injector.py              # Clipboard write + Ctrl+V keystroke
├── tray.py                  # System tray icon and menu
├── setup_task_scheduler.py  # Registers / removes Windows startup task
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
- Check your internet connection; the bot will reconnect automatically with exponential backoff

**Bot doesn't start**
- Confirm `BOT_TOKEN` is correct in `.env`
- Run `python main.py` manually to see startup errors in the console

**Task Scheduler registration fails**
- Make sure you're running the script as your normal user (not elevated/admin)
- Check that `pythonw.exe` exists in your Python installation directory

---

## License

MIT — see [LICENSE](LICENSE)
