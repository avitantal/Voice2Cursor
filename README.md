# Voice2Cursor

Dictate into any Windows app via Telegram — send a voice message or text, and it appears at your cursor instantly.

[![Version](https://img.shields.io/badge/version-v1.0.6-brightgreen.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## How It Works

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
- **EXE build** — ships as a standalone executable, no Python required to run
- **Auto-start** — registers to launch at Windows login, no admin rights required
- **Rotating logs** — up to 3 × 1 MB log files under `logs/`

---

## Setup

### 1. Configure

```bash
copy .env.example .env
```

Edit `.env`:

```ini
BOT_TOKEN=your_bot_token
ALLOWED_CHAT_ID=your_chat_id
```

**How to find your values:**
- **BOT_TOKEN** — chat with [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
- **ALLOWED_CHAT_ID** — send a message to your bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `result[0].message.chat.id`

### 2. Build & install

```bat
build.bat
```

That's it. The script installs all dependencies, builds the EXE, copies `.env` automatically, and tells you how to register auto-start.

### 3. Register auto-start

```bash
python setup_task_scheduler.py
```

Tries Task Scheduler first (30-second delay after login). Falls back to the user Startup folder if elevation is needed — no admin rights required either way.

```bash
python setup_task_scheduler.py --remove   # unregister
```

---

## Security

| Mechanism | Detail |
|-----------|--------|
| Sender whitelist | Only `ALLOWED_CHAT_ID` can trigger a paste |
| Blocked windows | Terminals, KeePass, Bitwarden, 1Password, LastPass, Registry Editor, Task Manager |
| Stale guard | Messages older than 30 s are discarded |

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
└── .env.example
```

---

## Troubleshooting

**Nothing is pasted** — check `logs/voice2cursor.log` for `BLOCKED` or `Paste failed` entries. Make sure the target window is in focus when you send the message.

**Tray icon is gray** — no network. The bot reconnects automatically with exponential backoff.

**Bot doesn't start** — confirm `BOT_TOKEN` in `.env` is correct. Run `python main.py` manually to see errors.

---

## Changelog

### v1.0.6 — 2026-05-15
- Settings window: fixed "שמור והפעל מחדש" button not responding on frozen EXE — replaced `os.execv` with `subprocess.Popen` + `sys.exit`
- Settings window: fixed UI updates from validation thread (thread-safe via `root.after`)

### v1.0.5 — 2026-05-15
- Tray menu: added "⚙ הגדרות" — opens settings window with current values pre-filled, restarts bot after save

### v1.0.4 — 2026-05-15
- First-run setup wizard: GUI window on first launch to enter Bot Token and Chat ID, validates against Telegram, saves .env automatically

### v1.0.3 — 2026-05-15
- Tray menu: added "שלח Enter אוטומטי" toggle (auto-send Enter after paste)
- build.bat: now creates a ZIP file for easy distribution after each build

### v1.0.2 — 2026-05-15
- Tray icon tooltip now shows version number (e.g. "Voice2Cursor v1.0.2 — פעיל")

### v1.0.1 — 2026-05-15
- Reduced `MAX_RETRY_DELAY` from 60 s to 15 s — faster recovery after network errors

### v1.0.0 — 2026-05-15
- Initial release
- Telegram long-polling with single-user whitelist
- Clipboard injection via Ctrl+V into the active window
- Blocked-window safety list
- System tray status icon
- PyInstaller EXE build (`build.bat`)
- Auto-start via Task Scheduler / Startup folder

---

## License

MIT — see [LICENSE](LICENSE)

---
---

# Voice2Cursor — עברית

כלי Windows שמאזין להודעות טלגרם ומדביק את הטקסט אוטומטית לחלון הפעיל. שלח הודעת קול או טקסט מהטלפון — הוא מופיע ישירות בסמן.

---

## איך זה עובד

```
[מיקרופון] → הודעת קול בטלגרם → תמלול → Telegram Bot API
                                                    ↓
                                     Voice2Cursor (שירות רקע של Windows)
                                                    ↓
                                     לוח גזירים → Ctrl+V → החלון הפעיל
```

---

## יכולות

- **כל אפליקציה** — מדביק ל-VS Code, Word, Notepad, דפדפנים, צ'אט, כל דבר שמקבל Ctrl+V
- **תמלול קול** — עובד עם תמלול הקול המובנה של טלגרם
- **משתמש מורשה בלבד** — רק ה-chat ID שהגדרת יכול להפעיל הדבקה
- **הדבקה בטוחה** — חסום אוטומטית בטרמינלים, מנהלי סיסמאות ועוד
- **הגנת הודעות ישנות** — מתעלם מהודעות ישנות מ-30 שניות
- **אייקון במגש המערכת** — ירוק = פעיל, אפור = שגיאת רשת; לחיצה ימנית ליציאה
- **קובץ EXE** — ניתן להפצה ללא Python
- **הפעלה אוטומטית** — עולה עם Windows, ללא הרשאות מנהל

---

## הגדרה

### שלב 1 — הגדרת .env

```bash
copy .env.example .env
```

ערוך את `.env`:

```ini
BOT_TOKEN=הטוקן_שלך
ALLOWED_CHAT_ID=ה_chat_id_שלך
```

**איך להשיג את הערכים:**
- **BOT_TOKEN** — פתח טלגרם → חפש [@BotFather](https://t.me/BotFather) → `/newbot`
- **ALLOWED_CHAT_ID** — שלח הודעה לבוט שלך, פתח בדפדפן `https://api.telegram.org/bot<TOKEN>/getUpdates` והעתק את `result[0].message.chat.id`

### שלב 2 — בנייה

```bat
build.bat
```

הסקריפט מתקין תלויות, בונה EXE, מעתיק `.env` אוטומטית — הכל בלחיצה אחת.

### שלב 3 — הפעלה אוטומטית עם Windows

```bash
python setup_task_scheduler.py
```

מנסה Task Scheduler (עם עיכוב של 30 שניות אחרי כניסה). אם נדרשות הרשאות מנהל — עובר אוטומטית לתיקיית Startup. **לא נדרשות הרשאות מנהל**.

```bash
python setup_task_scheduler.py --remove   # הסרה
```

---

## אבטחה

| מנגנון | פירוט |
|--------|-------|
| רשימת מורשים | רק `ALLOWED_CHAT_ID` שהגדרת יכול להפעיל הדבקה |
| חלונות חסומים | טרמינלים, KeePass, Bitwarden, 1Password, LastPass, עורך רישום, מנהל משימות |
| הגנת הודעות ישנות | הודעות ישנות מ-30 שניות נזרקות |

---

## פתרון בעיות

**לא מדביק** — בדוק `logs\voice2cursor.log` ל-`BLOCKED` או `Paste failed`. ודא שהחלון היעד בפוקוס בזמן שליחת ההודעה.

**האייקון אפור** — אין רשת. הבוט מתחבר מחדש אוטומטית.

**הבוט לא עולה** — ודא ש-`BOT_TOKEN` ב-`.env` נכון.
