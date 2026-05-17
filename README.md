# Voice2Cursor

Dictate into any Windows app via Telegram — send a voice message or text, and it appears at your cursor instantly.

[![Version](https://img.shields.io/badge/version-v1.0.16-brightgreen.svg)](VERSION)
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
- **System tray** — green/gray dot shows live connection status, header line shows the bot username and version
- **Polished app icon** — bundled Windows `.ico` and source PNG under `assets/`, used by the EXE, system tray, and settings window
- **Multi-bot switching** — every bot you've used is remembered in `bots.json`; switch from the **🤖 בוטים** tray submenu in one click (writes `.env`, resets offset, restarts)
- **Saved-bots management** — settings window lists all saved bots with **Load** / **🗑** controls and highlights the active one; delete is confirmed and disabled for the active bot
- **Manual reconnect** — when the tray icon turns gray (network error), a **🔄 התחבר מחדש** item appears in the menu to restart the connection immediately
- **Settings GUI** — first-run wizard + tray "⚙ הגדרות" (runs in its own subprocess to dodge tkinter/pystray threading issues)
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

For repeat builds between version bumps, use the fast variant — skips `pip install` and the PyInstaller `--clean` step, using the cached build artifacts:

```bat
build-fast.bat
```

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
├── assets/                  # App icon source PNG + Windows ICO
├── app_assets.py            # Runtime asset lookup for source and PyInstaller builds
├── main.py                  # Bot loop — polls Telegram, dispatches messages
├── config.py                # Loads and validates .env settings
├── security.py              # Chat ID whitelist + blocked-window check
├── injector.py              # Clipboard write + Ctrl+V keystroke
├── tray.py                  # System tray icon + menu (incl. bots submenu)
├── bot_store.py             # bots.json read/write — list of known bots
├── setup_wizard.py          # First-run + settings GUI (tkinter)
├── setup_task_scheduler.py  # Registers / removes auto-start
├── Voice2Cursor.spec        # PyInstaller build spec
├── build.bat                # Full build (installs deps + clean PyInstaller run)
├── build-fast.bat           # Fast incremental rebuild (skips pip + --clean)
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

### v1.0.16 — 2026-05-17
- App icon is now loaded at runtime too: the system tray uses the generated icon with a small status dot, and the settings window title bar uses the bundled `.ico` / PNG.
- PyInstaller bundles `assets/voice2cursor-icon.png` and `.ico` into the app, so frozen builds can find the icon files instead of relying only on the source tree.

### v1.0.15 — 2026-05-17
- `build.bat` / `build-fast.bat` now preserve `bots.json`, `bots.json.bak`, and `offset.txt` across PyInstaller rebuilds — PyInstaller removes `dist\Voice2Cursor\` during COLLECT (verified in log: `INFO: Removing dir ...\dist\Voice2Cursor`), so every rebuild used to wipe the EXE-side bot list. Build failure cleans up the temp copies.
- Added the generated Voice2Cursor app icon (`assets/voice2cursor-icon.png` + `.ico`) and wired it into both PyInstaller specs so the rebuilt EXE carries the branded icon.

### v1.0.14 — 2026-05-17
- Settings window: all section headers centered (top brand, subtitle, active-bot indicator, "Bot Token", "Chat ID שלך", "בוטים שמורים", BotFather hint). RTL/LTR mixing made left-anchored headers feel uneven; centering removes the directional choice.

### v1.0.13 — 2026-05-17
- `bot_store`: atomic writes (tempfile + `os.replace`) and a `bots.json.bak` snapshot on every successful write — prevents partial-write corruption from wiping the bot list
- `bot_store`: on parse failure, fall back to `bots.json.bak`; if both are unreadable, refuse to `touch` / `remove` rather than silently overwriting an existing-but-unparseable file with a singleton (this was the path that could lose saved bots after a settings change)
- `bot_store`: log every add / update / remove with the short token prefix and remaining count, so future "where did my bot go" questions have a clear audit trail in `voice2cursor.log`

### v1.0.12 — 2026-05-16
- Settings window: shows the active bot's name (🟢 פעיל: …) at the top, so the saved-bots list has obvious context
- Saved-bots delete: confirmation dialog before removing — the RTL row layout made the 🗑 button easy to hit by accident
- Saved-bots delete: 🗑 is disabled for the currently-active bot (deleting it is meaningless — `main.py` re-adds it on next startup via `bot_store.touch`)
- Added `build-fast.bat` — skips `pip install` and `--clean` for quick rebuilds between version bumps

### v1.0.11 — 2026-05-16
- Settings window: new **🤖 בוטים שמורים** section listing every saved bot with **טען** (load into fields) and **🗑** (delete) controls — covers the gaps the tray submenu left
- Tray menu: new **🔄 התחבר מחדש** item, shown only while status is "שגיאה" — restarts the process to drop any stuck network state

### v1.0.10 — 2026-05-16  *(first fully-working build)*
- Tray menu: new **🤖 בוטים** submenu listing every bot the app has been used with (radio-selected current bot, click to switch — writes `.env`, resets offset, restarts)
- Bot list persisted to `bots.json` next to the EXE (token + chat_id + Telegram `@username` + last_used timestamp; menu is sorted most-recent-first)
- Settings window: launches in a clean child process via `--settings` flag, fixing intermittent failures to open caused by tkinter running on the pystray callback thread
- `setup_wizard._save` now registers the saved bot in `bots.json` automatically
- Tray init: wrapped `pystray.run()` in try/except + logging so silent thread death is visible in the log; switched bots submenu to static construction (the earlier callable form prevented the tray icon from registering on Win32)
- Startup log now includes "Telegram bot detected: …" on success, "Tray icon created — entering pystray run loop" once the icon is live

### v1.0.9 — 2026-05-15
- Setup wizard: auto-detect Chat ID via Telegram `getUpdates` long-polling — user sends any message to the bot and the field fills automatically
- Setup wizard: right-click paste/copy menu on token & chat fields, with PowerShell `Get-Clipboard` fallback for tkinter clipboard bugs
- Tray tooltip & menu header now show the bot username (`@bot_name`) alongside the version
- Settings restart: clear stale `BOT_TOKEN` / `ALLOWED_CHAT_ID` env vars and pass `override=True` to `load_dotenv` so switching bots picks up new credentials
- `get_updates`: distinguish network errors (`None`) from empty results; backoff only on real failures
- Wizard saves: reset `offset.txt` to `0` so a newly configured bot does not skip messages

### v1.0.7 — 2026-05-15
- Settings window: fixed Ctrl+V paste into token field — tkinter now runs on a persistent dedicated thread (Win32 keyboard routing broken when creating a new thread per open)
- Settings window: replaced hover-reveal on token field with an explicit "הצג / הסתר" toggle button
- Settings restart: fixed `subprocess.Popen` receiving EXE path twice — now uses `[sys.executable]` only

### v1.0.6 — 2026-05-15
- Tray "יציאה": fixed exit not closing the process — `sys.exit` in pystray callback only kills that thread; replaced with `os._exit`
- Settings window: fixed window freezing — settings now open in a dedicated thread so the Win32 message pump is not blocked
- Settings window: fixed "שמור והפעל מחדש" not restarting on frozen EXE — replaced `os.execv` with `subprocess.Popen` + `os._exit`
- Settings window: fixed UI updates from validation thread (thread-safe via `root.after`)
- Settings window: added note that Chat ID cannot be auto-verified — user must confirm it manually

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
- **אייקון במגש המערכת** — ירוק = פעיל, אפור = שגיאת רשת; כותרת התפריט מראה גרסה ושם בוט
- **החלפת בוטים** — כל בוט שהשתמשת בו נשמר ב-`bots.json`; תת-תפריט **🤖 בוטים** בטריי מאפשר מעבר ביניהם בלחיצה אחת
- **ניהול בוטים שמורים** — במסך ההגדרות מופיעה רשימת הבוטים השמורים עם **טען** / **🗑** והבוט הפעיל מודגש; מחיקה כוללת אישור ומנוטרלת לבוט הפעיל
- **רענון ידני** — כשהאייקון אפור (שגיאת רשת), פריט **🔄 התחבר מחדש** מופיע בתפריט הטריי ומפעיל מחדש את החיבור
- **GUI הגדרות** — אשף ראשון + "⚙ הגדרות" בטריי (רץ בתת-תהליך נפרד למניעת קונפליקטים tkinter/pystray)
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

לבילד מהיר בין גרסאות (ללא `pip install` וללא `--clean`, שימוש ב-cache של PyInstaller):

```bat
build-fast.bat
```

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
