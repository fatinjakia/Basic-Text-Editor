import os
import json
from datetime import datetime

RECENT_FILE = os.path.join("data", "recent_files.json")
LOG_FILE = os.path.join("logs", "editor.log")


class FileManager:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        if not os.path.exists(RECENT_FILE):
            with open(RECENT_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")

    # ===================== FILE I/O (UTF-8 SAFE) =====================
    def open_file(self, path: str) -> str:
        """
        Reads file as UTF-8 to preserve Bangla.
        If an old ANSI file is opened, fallback safely.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # fallback for old Windows ANSI files
            with open(path, "r", encoding="cp1252", errors="replace") as f:
                return f.read()

    def save_file(self, path: str, content: str):
        """
        Always saves as UTF-8 so Bangla stays correct.
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def file_info(self, path: str) -> dict:
        st = os.stat(path)
        return {
            "path": os.path.abspath(path),
            "size": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ===================== RECENT FILES =====================
    def load_recent_files(self):
        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def add_recent(self, path: str):
        path = os.path.abspath(path)
        items = self.load_recent_files()
        if path in items:
            items.remove(path)
        items.insert(0, path)
        items = items[:10]
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    # ===================== LOGGING =====================
    def log_event(self, event: str, details: str):
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {event}: {details}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
