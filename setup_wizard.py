"""
Setup wizard — first-run and settings.
Asks for BOT_TOKEN, detects ALLOWED_CHAT_ID automatically via getUpdates, saves .env.
"""
import sys
import os
from pathlib import Path
import requests
import threading
import subprocess

def _base_dir() -> Path:
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

ENV_PATH = _base_dir() / ".env"


def needs_setup() -> bool:
    if not ENV_PATH.exists():
        return True
    text = ENV_PATH.read_text()
    has_token = any(line.startswith("BOT_TOKEN=") and len(line.split("=", 1)[1].strip()) > 10 for line in text.splitlines())
    has_chat  = any(line.startswith("ALLOWED_CHAT_ID=") and line.split("=", 1)[1].strip().lstrip("-").isdigit() for line in text.splitlines())
    return not (has_token and has_chat)


def _load_current() -> tuple[str, str]:
    """Return (token, chat_id) from existing .env, or empty strings."""
    if not ENV_PATH.exists():
        return "", ""
    token, chat_id = "", ""
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("BOT_TOKEN="):
            token = line.split("=", 1)[1].strip()
        elif line.startswith("ALLOWED_CHAT_ID="):
            chat_id = line.split("=", 1)[1].strip()
    return token, chat_id


def _validate(token: str, chat_id: str) -> tuple[bool, str]:
    _log_path = _base_dir() / "logs" / "voice2cursor.log"
    try:
        _log_path.parent.mkdir(exist_ok=True)
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(f"[WIZARD] validate token={repr(token[:20])}... chat_id={repr(chat_id)}\n")
    except Exception:
        pass
    token = token.strip()
    chat_id = chat_id.strip()
    if not token:
        return False, "נא להזין Bot Token."
    if not chat_id.lstrip("-").isdigit():
        return False, "Chat ID חייב להיות מספר — השתמש בכפתור 'זהה אוטומטית'."
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=8)
        data = r.json()
        if not r.ok or not data.get("ok"):
            desc = data.get("description", "")
            return False, f"הטוקן לא תקין — {desc}" if desc else "הטוקן לא תקין — בדוק שוב ב-@BotFather."
    except requests.exceptions.ConnectionError:
        return False, "אין חיבור לאינטרנט."
    except Exception as e:
        return False, f"שגיאת רשת: {e}"
    return True, ""


def _save(token: str, chat_id: str):
    ENV_PATH.write_text(f"BOT_TOKEN={token.strip()}\nALLOWED_CHAT_ID={chat_id.strip()}\n", encoding="utf-8")
    offset_file = _base_dir() / "offset.txt"
    offset_file.write_text("0", encoding="utf-8")
    try:
        import bot_store
        bot_store.touch(token, chat_id)
    except Exception:
        pass


def _fetch_chat_id(token: str, on_found, on_error, on_timeout, cancel_flag: list):
    """Poll getUpdates, skip old messages, wait for a new one, call on_found(chat_id)."""
    try:
        # Get current offset to skip old messages
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        data = r.json()
        if not data.get("ok"):
            on_error("טוקן לא תקין")
            return
        updates = data.get("result", [])
        offset = updates[-1]["update_id"] + 1 if updates else 0

        if cancel_flag[0]:
            return

        # Long-poll for a new message (up to 60 s)
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": offset, "timeout": 60},
            timeout=65,
        )
        if cancel_flag[0]:
            return

        data = r.json()
        if not data.get("ok"):
            on_error("שגיאה בקבלת עדכונים")
            return

        for update in data.get("result", []):
            msg = (update.get("message")
                   or update.get("channel_post")
                   or update.get("edited_message"))
            if msg:
                on_found(str(msg["chat"]["id"]))
                return

        on_timeout()

    except requests.exceptions.Timeout:
        on_timeout()
    except Exception:
        on_error("שגיאת רשת")


def _open_window(title: str, subtitle: str, current_token: str, current_chat: str,
                 btn_label: str, on_close_without_save) -> bool:
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return False

    root = tk.Tk()
    root.title(title)
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    root.update_idletasks()
    w, h = 480, 460
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.lift()
    root.focus_force()

    BG     = "#1e1e2e"
    CARD   = "#2a2a3e"
    ACCENT = "#7c3aed"
    FG     = "#e2e8f0"
    MUTED  = "#94a3b8"
    RED    = "#f87171"
    GREEN  = "#34d399"
    YELLOW = "#f59e0b"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TEntry", fieldbackground=CARD, foreground=FG,
                    bordercolor="#3f3f5a", relief="flat", padding=8)
    style.map("TEntry", fieldbackground=[("focus", "#32324a")])

    def label(parent, text, size=11, color=FG, anchor="w", **kw):
        return tk.Label(parent, text=text, bg=BG, fg=color,
                        font=("Segoe UI", size), anchor=anchor, **kw)

    # Header
    header = tk.Frame(root, bg=ACCENT, height=56)
    header.pack(fill="x")
    tk.Label(header, text="⚙  Voice2Cursor", bg=ACCENT, fg="white",
             font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=16, pady=12)

    # Body
    body = tk.Frame(root, bg=BG, padx=28, pady=20)
    body.pack(fill="both", expand=True)

    label(body, subtitle, size=12).pack(anchor="w", pady=(0, 16))

    # Bot Token
    label(body, "🔑  Bot Token", size=10, color=MUTED).pack(anchor="w")
    token_var = tk.StringVar(value=current_token)
    token_row = tk.Frame(body, bg=BG)
    token_row.pack(fill="x", pady=(2, 2))
    token_entry = ttk.Entry(token_row, textvariable=token_var, width=44, show="•", font=("Consolas", 10))
    token_entry.pack(side="left", fill="x", expand=True, ipady=4)
    _show_state = [False]
    def _toggle_token():
        _show_state[0] = not _show_state[0]
        token_entry.config(show="" if _show_state[0] else "•")
        toggle_btn.config(text="הסתר" if _show_state[0] else "הצג")
    toggle_btn = tk.Button(token_row, text="הצג", bg=CARD, fg=MUTED,
                           font=("Segoe UI", 9), relief="flat", cursor="hand2",
                           padx=8, command=_toggle_token)
    toggle_btn.pack(side="right", padx=(6, 0), ipady=4)

    def _get_clipboard() -> str:
        """Read clipboard via PowerShell — bypasses Tkinter clipboard bugs on Windows."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return result.stdout.strip()
        except Exception:
            try:
                return root.clipboard_get().strip()
            except tk.TclError:
                return ""

    def _make_context_menu(entry, var, masked=False):
        menu = tk.Menu(root, tearoff=0, bg=CARD, fg=FG,
                       activebackground=ACCENT, activeforeground="white",
                       font=("Segoe UI", 9), relief="flat", bd=0)

        def _paste():
            text = _get_clipboard()
            if text:
                var.set(text)

        def _copy():
            try:
                root.clipboard_clear()
                root.clipboard_append(var.get())
            except tk.TclError:
                pass

        def _clear():
            var.set("")

        menu.add_command(label="הדבק  (Paste)", command=_paste)
        if not masked:
            menu.add_command(label="העתק  (Copy)", command=_copy)
        menu.add_separator()
        menu.add_command(label="נקה", command=_clear)

        def _show(event):
            entry.focus_set()
            menu.post(event.x_root, event.y_root)

        entry.bind("<Button-3>", _show)

        def _paste_key(event=None):
            _paste()
            return "break"
        for _seq in ("<Control-v>", "<Control-V>", "<<Paste>>"):
            entry.bind(_seq, _paste_key)

    _make_context_menu(token_entry, token_var, masked=True)

    label(body, "  קבל מ-@BotFather  →  /newbot", size=9, color=MUTED).pack(anchor="w", pady=(0, 14))

    # Chat ID
    label(body, "🆔  Chat ID שלך", size=10, color=MUTED).pack(anchor="w")
    chat_var = tk.StringVar(value=current_chat)
    chat_row = tk.Frame(body, bg=BG)
    chat_row.pack(fill="x", pady=(2, 2))
    chat_entry = ttk.Entry(chat_row, textvariable=chat_var, width=36, font=("Consolas", 10))
    chat_entry.pack(side="left", fill="x", expand=True, ipady=4)

    _cancel_flag = [False]

    detect_status_var = tk.StringVar()
    detect_lbl = tk.Label(body, textvariable=detect_status_var, bg=BG, fg=MUTED,
                          font=("Segoe UI", 9), anchor="w", wraplength=420)

    def do_detect():
        token = token_var.get().strip()
        if not token:
            detect_status_var.set("✗  הזן תחילה את הטוקן.")
            detect_lbl.config(fg=RED)
            detect_lbl.pack(anchor="w", pady=(4, 8))
            return

        _cancel_flag[0] = False
        detect_btn.config(state="disabled", text="מאזין...")
        detect_status_var.set("📱  שלח כל הודעה לבוט שלך בטלגרם...")
        detect_lbl.config(fg=MUTED)
        detect_lbl.pack(anchor="w", pady=(4, 8))

        def on_found(chat_id):
            def _upd():
                chat_var.set(chat_id)
                detect_status_var.set(f"✓  נמצא: {chat_id}")
                detect_lbl.config(fg=GREEN)
                detect_btn.config(state="normal", text="זהה אוטומטית")
            root.after(0, _upd)

        def on_error(msg):
            def _upd():
                detect_status_var.set(f"✗  {msg}")
                detect_lbl.config(fg=RED)
                detect_btn.config(state="normal", text="זהה אוטומטית")
            root.after(0, _upd)

        def on_timeout():
            def _upd():
                detect_status_var.set("⏱  פג הזמן — נסה שוב.")
                detect_lbl.config(fg=YELLOW)
                detect_btn.config(state="normal", text="זהה אוטומטית")
            root.after(0, _upd)

        threading.Thread(
            target=_fetch_chat_id,
            args=(token, on_found, on_error, on_timeout, _cancel_flag),
            daemon=True,
        ).start()

    _make_context_menu(chat_entry, chat_var, masked=False)

    detect_btn = tk.Button(chat_row, text="זהה אוטומטית", bg=ACCENT, fg="white",
                           activebackground="#6d28d9", activeforeground="white",
                           font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                           padx=10, command=do_detect)
    detect_btn.pack(side="right", padx=(6, 0), ipady=4)

    # Show detect_lbl placeholder (hidden until first detect)
    detect_lbl.pack(anchor="w", pady=(4, 8))

    # Status
    status_var = tk.StringVar()
    status_lbl = tk.Label(body, textvariable=status_var, bg=BG, fg=RED,
                          font=("Segoe UI", 9), anchor="w", wraplength=420)
    status_lbl.pack(anchor="w", pady=(0, 12))

    # Buttons
    btn_frame = tk.Frame(body, bg=BG)
    btn_frame.pack(fill="x")

    result = {"ok": False}

    def on_save():
        token   = token_var.get().strip()
        chat_id = chat_var.get().strip()
        btn.config(state="disabled", text="מאמת...")
        status_var.set("")
        root.update()

        def do_validate():
            ok, msg = _validate(token, chat_id)
            if ok:
                _save(token, chat_id)
                result["ok"] = True
                _cancel_flag[0] = True
                root.after(0, root.destroy)
            else:
                def _show_error():
                    status_var.set("✗  " + msg)
                    status_lbl.config(fg=RED)
                    btn.config(state="normal", text=btn_label)
                root.after(0, _show_error)

        threading.Thread(target=do_validate, daemon=True).start()

    btn = tk.Button(
        btn_frame, text=btn_label,
        bg=ACCENT, fg="white", activebackground="#6d28d9", activeforeground="white",
        font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
        padx=20, pady=8, command=on_save,
    )
    btn.pack(side="right")

    def _on_close():
        _cancel_flag[0] = True
        on_close_without_save()
        try:
            root.destroy()
        except Exception:
            pass

    token_entry.focus_set()
    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()

    return result["ok"]


def run_wizard() -> bool:
    """First-run wizard — exit app if closed without saving."""
    return _open_window(
        title="Voice2Cursor — הגדרה ראשונה",
        subtitle="ברוך הבא! בואו נגדיר את הבוט שלך.",
        current_token="",
        current_chat="",
        btn_label="שמור והתחל ▶",
        on_close_without_save=lambda: sys.exit(0),
    )


def run_settings() -> bool:
    """Settings window — pre-filled with current values, restart app if saved."""
    token, chat_id = _load_current()
    return _open_window(
        title="Voice2Cursor — הגדרות",
        subtitle="עדכן את פרטי הבוט שלך.",
        current_token=token,
        current_chat=chat_id,
        btn_label="שמור והפעל מחדש ▶",
        on_close_without_save=lambda: None,
    )
