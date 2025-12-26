# import tkinter as tk
# from tkinter import filedialog, messagebox, simpledialog

# from editor.ui import TextEditorUI


# class WelcomeScreen:
#     def __init__(self, root: tk.Tk):
#         self.root = root
#         self.root.title("Welcome - Basic Text Editor")

#         self.frame = tk.Frame(root, padx=22, pady=22)
#         self.frame.pack(fill="both", expand=True)

#         # Title
#         tk.Label(
#             self.frame,
#             text="WELCOME",
#             font=("Segoe UI", 24, "bold"),
#             fg="#1E88E5"
#         ).pack(anchor="w")

#         tk.Label(
#             self.frame,
#             text="Basic Text Editor\nChoose an option to start",
#             font=("Segoe UI", 12),
#             fg="#444"
#         ).pack(anchor="w", pady=(6, 20))

#         # Buttons
#         btn_row = tk.Frame(self.frame)
#         btn_row.pack(fill="x")

#         tk.Button(
#             btn_row, text="➕  New File", width=16, height=2,
#             command=self.new_file
#         ).pack(side="left", padx=6)

#         tk.Button(
#             btn_row, text="📂  Open File", width=16, height=2,
#             command=self.open_file
#         ).pack(side="left", padx=6)

#         tk.Button(
#             btn_row, text="➡  Continue", width=16, height=2,
#             command=self.continue_editor
#         ).pack(side="left", padx=6)

#         tk.Label(
#             self.frame,
#             text="Tip: Ctrl+S to save · Ctrl+P to export PDF",
#             font=("Segoe UI", 10),
#             fg="gray"
#         ).pack(anchor="w", pady=(22, 0))

#         # Center window
#         self.center_window(520, 300)

#         # Close app
#         self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

#     def center_window(self, w, h):
#         self.root.update_idletasks()
#         x = (self.root.winfo_screenwidth() // 2) - (w // 2)
#         y = (self.root.winfo_screenheight() // 2) - (h // 2)
#         self.root.geometry(f"{w}x{h}+{x}+{y}")

#     # ---------- Security ----------
#     def require_pin(self, app: TextEditorUI) -> bool:
#         cfg = app.fm.load_config()
#         if not cfg.get("pin_enabled"):
#             return True

#         pin = simpledialog.askstring("Security", "Enter PIN:", show="*")
#         if pin is None:
#             return False

#         if app.fm.verify_pin(pin):
#             return True

#         messagebox.showerror("Security", "Wrong PIN!")
#         return False

#     # ---------- Switch to editor ----------
#     def start_editor(self, open_path=None, fresh=False):
#         # Clear welcome UI
#         for w in self.root.winfo_children():
#             w.destroy()

#         # Make editor window size
#         self.root.title("Basic Text Editor - OS Project (Final Pro)")
#         self.root.geometry("1050x740")
#         self.root.resizable(True, True)

#         # Create editor
#         app = TextEditorUI(self.root)

#         # Security check (using app config + verify)
#         if not self.require_pin(app):
#             self.root.destroy()
#             return

#         # If fresh new file requested: close all tabs and create one empty
#         if fresh:
#             try:
#                 for tab in app.notebook.tabs():
#                     app.notebook.forget(tab)
#             except Exception:
#                 pass
#             app.new_tab()

#         # Open file if requested
#         if open_path:
#             app.open_specific_file(open_path)

#     def new_file(self):
#         self.start_editor(fresh=True)

#     def open_file(self):
#         path = filedialog.askopenfilename(
#             title="Open File",
#             filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
#         )
#         if not path:
#             return
#         self.start_editor(open_path=path)

#     def continue_editor(self):
#         self.start_editor()















import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from editor.ui import TextEditorUI


class WelcomeScreen:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Welcome - Basic Text Editor")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        self.frame = tk.Frame(root, padx=22, pady=22)
        self.frame.pack(fill="both", expand=True)

        # ---------------- Title ----------------
        tk.Label(
            self.frame,
            text="WELCOME",
            font=("Segoe UI", 24, "bold"),
            fg="#1E88E5"
        ).pack(anchor="w")

        tk.Label(
            self.frame,
            text="Basic Text Editor\nChoose an option to start",
            font=("Segoe UI", 12),
            fg="#444"
        ).pack(anchor="w", pady=(6, 20))

        # ---------------- Buttons ----------------
        btn_row = tk.Frame(self.frame)
        btn_row.pack(fill="x")

        tk.Button(
            btn_row, text="➕  New File", width=16, height=2,
            command=self.new_file
        ).pack(side="left", padx=6)

        tk.Button(
            btn_row, text="📂  Open File", width=16, height=2,
            command=self.open_file
        ).pack(side="left", padx=6)

        tk.Button(
            btn_row, text="➡  Continue", width=16, height=2,
            command=self.continue_editor
        ).pack(side="left", padx=6)

        # ---------------- Footer ----------------
        tk.Label(
            self.frame,
            text="Tip: Ctrl+S to save · Ctrl+P to export PDF",
            font=("Segoe UI", 10),
            fg="gray"
        ).pack(anchor="w", pady=(22, 0))

        self.center_fixed(520, 300)

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # ---------------- Center helpers ----------------
    def center_fixed(self, w, h):
        """Center using a fixed width/height."""
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.lift()
        self.root.focus_force()

    def center_current(self):
        """
        Center using the CURRENT actual window size.
        This is the key fix for Windows 11.
        """
        self.root.update_idletasks()

        # Actual size after widgets are drawn
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        # Fallback if Windows returns 1/1 early
        if w < 200:
            w = self.root.winfo_reqwidth()
        if h < 200:
            h = self.root.winfo_reqheight()

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        # Only move position; keep current size
        self.root.geometry(f"+{x}+{y}")
        self.root.lift()
        self.root.focus_force()

    # ---------------- Security ----------------
    def require_pin(self, app: TextEditorUI) -> bool:
        cfg = app.fm.load_config()
        if not cfg.get("pin_enabled"):
            return True

        pin = simpledialog.askstring("Security", "Enter PIN:", show="*")
        if pin is None:
            return False

        if app.fm.verify_pin(pin):
            return True

        messagebox.showerror("Security", "Wrong PIN!")
        return False

    # ---------------- Switch to editor ----------------
    def start_editor(self, open_path=None, fresh=False):
        # Remove welcome UI
        for w in self.root.winfo_children():
            w.destroy()

        # Prepare editor window
        self.root.title("Basic Text Editor - OS Project (Final Pro)")
        self.root.resizable(True, True)

        # Set size first (position will be fixed AFTER UI loads)
        self.root.geometry("1050x740")

        # Create editor UI
        app = TextEditorUI(self.root)

        # Security check
        if not self.require_pin(app):
            self.root.destroy()
            return

        # New file option
        if fresh:
            try:
                for tab in app.notebook.tabs():
                    app.notebook.forget(tab)
            except Exception:
                pass
            app.new_tab()

        # Open file option
        if open_path:
            app.open_specific_file(open_path)

        # ✅ THE REAL FIX: center AFTER everything is drawn
        self.root.after(120, self.center_current)

    # ---------------- Button actions ----------------
    def new_file(self):
        self.start_editor(fresh=True)

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        self.start_editor(open_path=path)

    def continue_editor(self):
        self.start_editor()
