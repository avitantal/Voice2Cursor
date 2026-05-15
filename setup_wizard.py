"""
First-run setup wizard — opens when .env is missing or incomplete.
Asks for BOT_TOKEN and ALLOWED_CHAT_ID, validates against Telegram, saves .env.
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import requests
import threading

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


def _validate(token: str, chat_id: str) -> tuple[bool, str]:
    token = token.strip()
    chat_id = chat_id.strip()
    if not token:
        return False, "נא להזין Bot Token."
    if not chat_id.lstrip("-").isdigit():
        return False, "Chat ID חייב להיות מספר."
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=8)
        if not r.ok or not r.json().get("ok"):
            return False, "הטוקן לא תקין — בדוק שוב ב-@BotFather."
    except requests.exceptions.ConnectionError:
        return False, "אין חיבור לאינטרנט."
    except Exception:
        return False, "שגיאת רשת — נסה שוב."
    return True, ""


def _save(token: str, chat_id: str):
    ENV_PATH.write_text(f"BOT_TOKEN={token.strip()}\nALLOWED_CHAT_ID={chat_id.strip()}\n", encoding="utf-8")


def run_wizard():
    root = tk.Tk()
    root.title("Voice2Cursor — הגדרה ראשונה")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    # ── center window ──────────────────────────────────────────────────────
    root.update_idletasks()
    w, h = 480, 420
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    BG     = "#1e1e2e"
    CARD   = "#2a2a3e"
    ACCENT = "#7c3aed"
    FG     = "#e2e8f0"
    MUTED  = "#94a3b8"
    RED    = "#f87171"
    GREEN  = "#4ade80"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TEntry", fieldbackground=CARD, foreground=FG,
                    bordercolor="#3f3f5a", relief="flat", padding=8)
    style.map("TEntry", fieldbackground=[("focus", "#32324a")])

    def label(parent, text, size=11, color=FG, anchor="w", **kw):
        return tk.Label(parent, text=text, bg=BG, fg=color,
                        font=("Segoe UI", size), anchor=anchor, **kw)

    # ── header ─────────────────────────────────────────────────────────────
    header = tk.Frame(root, bg=ACCENT, height=56)
    header.pack(fill="x")
    tk.Label(header, text="⚙  Voice2Cursor", bg=ACCENT, fg="white",
             font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=16, pady=12)

    # ── body ───────────────────────────────────────────────────────────────
    body = tk.Frame(root, bg=BG, padx=28, pady=20)
    body.pack(fill="both", expand=True)

    label(body, "ברוך הבא! בואו נגדיר את הבוט שלך.", size=12).pack(anchor="w", pady=(0, 16))

    # Bot Token
    label(body, "🔑  Bot Token", size=10, color=MUTED).pack(anchor="w")
    token_var = tk.StringVar()
    token_entry = ttk.Entry(body, textvariable=token_var, width=52, show="•", font=("Consolas", 10))
    token_entry.pack(fill="x", ipady=4, pady=(2, 2))
    label(body, "  קבל מ-@BotFather  →  /newbot", size=9, color=MUTED).pack(anchor="w", pady=(0, 14))

    # Chat ID
    label(body, "🆔  Chat ID שלך", size=10, color=MUTED).pack(anchor="w")
    chat_var = tk.StringVar()
    chat_entry = ttk.Entry(body, textvariable=chat_var, width=52, font=("Consolas", 10))
    chat_entry.pack(fill="x", ipady=4, pady=(2, 2))
    label(body, "  שלח הודעה לבוט, פתח:  api.telegram.org/bot<TOKEN>/getUpdates", size=9, color=MUTED).pack(anchor="w", pady=(0, 16))

    # Status
    status_var = tk.StringVar()
    status_lbl = tk.Label(body, textvariable=status_var, bg=BG, fg=RED,
                          font=("Segoe UI", 9), anchor="w", wraplength=420)
    status_lbl.pack(anchor="w", pady=(0, 12))

    # Button
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
                root.after(0, root.destroy)
            else:
                status_var.set("✗  " + msg)
                status_lbl.config(fg=RED)
                btn.config(state="normal", text="שמור והתחל ▶")

        threading.Thread(target=do_validate, daemon=True).start()

    btn = tk.Button(
        btn_frame, text="שמור והתחל ▶",
        bg=ACCENT, fg="white", activebackground="#6d28d9", activeforeground="white",
        font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
        padx=20, pady=8, command=on_save,
    )
    btn.pack(side="right")

    # Show token in plain text on hover
    def show_token(e):  token_entry.config(show="")
    def hide_token(e):  token_entry.config(show="•")
    token_entry.bind("<Enter>", show_token)
    token_entry.bind("<Leave>", hide_token)

    token_entry.focus_set()
    root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    root.mainloop()

    return result["ok"]
