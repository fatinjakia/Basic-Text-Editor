from tkinter import *
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import os
import json
import threading
import time
import textwrap
import tkinter.font as tkfont
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.pdfencrypt import StandardEncryption

from editor.file_manager import FileManager
from editor.commands import word_count, get_cursor_line_col, open_find_replace_dialog

AUTOSAVE_DIR = "autosave"


class TextEditorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Text Editor")
        self.root.geometry("1050x740")

        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        self.fm = FileManager()
        self.file_lock = threading.Lock()
        self.dark_mode = False

        # ---------- Font State ----------
        self.available_fonts = sorted(set(tkfont.families()))
        self.font_var = StringVar(value=self.pick_default_font())
        self.size_var = IntVar(value=12)

        # ---------- Toolbar ----------
        self.toolbar = Frame(root)
        self.toolbar.pack(fill=X, padx=6, pady=4)

        Label(self.toolbar, text="Font:").pack(side=LEFT, padx=(2, 4))
        self.font_combo = ttk.Combobox(
            self.toolbar, values=self.available_fonts,
            textvariable=self.font_var, width=28, state="readonly"
        )
        self.font_combo.pack(side=LEFT, padx=(0, 8))
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_font_current_tab())

        Label(self.toolbar, text="Size:").pack(side=LEFT, padx=(2, 4))
        self.size_combo = ttk.Combobox(
            self.toolbar,
            values=[8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 28, 32],
            textvariable=self.size_var, width=6, state="readonly"
        )
        self.size_combo.pack(side=LEFT, padx=(0, 8))
        self.size_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_font_current_tab())

        Button(self.toolbar, text="Apply (This Tab)", command=self.apply_font_current_tab).pack(side=LEFT, padx=4)
        Button(self.toolbar, text="Apply (All Tabs)", command=self.apply_font_all_tabs).pack(side=LEFT, padx=4)

        self.font_hint = Label(self.toolbar, text="", fg="gray")
        self.font_hint.pack(side=LEFT, padx=10)

        # ---------- Notebook ----------
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=1, fill=BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_status())

        # Status bar
        self.status = Label(root, text="Ready", anchor=W)
        self.status.pack(fill=X)

        self.create_menu()
        self.bind_shortcuts()

        # Always start with one empty tab
        self.new_tab()

        self.start_autosave()

        self.fm.log_event("APP_START", "Editor started")
        self.refresh_recent_menu()
        self.refresh_status()

        # Exit on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.exit_editor()

    # ================= Fonts =================
    def pick_default_font(self) -> str:
        preferred = ["Consolas", "Cascadia Mono", "Courier New", "Segoe UI", "Arial", "Times New Roman"]
        for f in preferred:
            if f in tkfont.families():
                return f
        return tkfont.families()[0] if tkfont.families() else "Arial"

    def current_font_tuple(self):
        return (self.font_var.get(), int(self.size_var.get()))

    def apply_font_to_textwidget(self, text_widget: Text):
        text_widget.configure(font=self.current_font_tuple())

    def apply_font_current_tab(self):
        frame = self.current_frame()
        if not frame:
            return
        self.apply_font_to_textwidget(frame._text)
        self.redraw_lines(frame._gutter, frame._text)
        self.refresh_status()
        self.fm.log_event("FONT_CHANGE_TAB", f"{self.font_var.get()} {self.size_var.get()}")

    def apply_font_all_tabs(self):
        for tab in self.notebook.tabs():
            f = self.root.nametowidget(tab)
            self.apply_font_to_textwidget(f._text)
            self.redraw_lines(f._gutter, f._text)
        self.refresh_status()
        self.fm.log_event("FONT_CHANGE_ALL", f"{self.font_var.get()} {self.size_var.get()}")

    # ================= Tab & Editor widgets =================
    def make_editor_widgets(self, parent):
        container = Frame(parent)
        container.pack(expand=1, fill=BOTH)

        gutter = Canvas(container, width=45, highlightthickness=0)
        gutter.pack(side=LEFT, fill=Y)

        text = Text(container, undo=True, wrap="word")
        text.pack(side=LEFT, expand=1, fill=BOTH)

        self.apply_font_to_textwidget(text)

        scroll = Scrollbar(container, command=text.yview)
        scroll.pack(side=RIGHT, fill=Y)
        text.configure(yscrollcommand=lambda f, l: self.on_scroll(f, l, gutter, text, scroll))

        text.bind("<KeyRelease>", lambda e: self.redraw_lines(gutter, text))
        text.bind("<MouseWheel>", lambda e: self.redraw_lines(gutter, text))
        text.bind("<ButtonRelease>", lambda e: self.redraw_lines(gutter, text))
        text.bind("<Configure>", lambda e: self.redraw_lines(gutter, text))
        text.bind("<<Modified>>", lambda e, t=text: self.on_modified(t))

        return gutter, text

    def on_scroll(self, first, last, gutter, text, scroll):
        scroll.set(first, last)
        self.redraw_lines(gutter, text)

    def redraw_lines(self, gutter, text):
        gutter.delete("all")
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#9aa0a6" if self.dark_mode else "#444"
        gutter.config(bg=bg)

        i = text.index("@0,0")
        while True:
            d = text.dlineinfo(i)
            if not d:
                break
            y = d[1]
            line = i.split(".")[0]
            gutter.create_text(40, y, anchor="ne", text=line, fill=fg)
            i = text.index(f"{i}+1line")

    def new_tab(self, content="", file_path=None, title="Untitled"):
        frame = Frame(self.notebook)
        gutter, text = self.make_editor_widgets(frame)

        text.insert("1.0", content)
        frame._text = text
        frame._gutter = gutter
        frame._file_path = file_path
        frame._modified = False
        frame._tab_id = f"tab_{int(time.time() * 1000)}"

        self.notebook.add(frame, text=title)
        self.notebook.select(frame)

        self.apply_theme(text, gutter)
        self.redraw_lines(gutter, text)
        self.try_recover(frame)

    def current_frame(self):
        tab_id = self.notebook.select()
        return self.root.nametowidget(tab_id) if tab_id else None

    # ================= Menu =================
    def create_menu(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="New Tab", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="Save All Tabs", command=self.save_all_tabs, accelerator="Ctrl+Alt+S")

        file_menu.add_separator()
        file_menu.add_command(label="File Properties", command=self.file_properties)

        self.recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_tab, accelerator="Ctrl+W")
        file_menu.add_command(label="Exit", command=self.on_close)

        edit_menu = Menu(menu, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace", command=self.find_replace, accelerator="Ctrl+F")

        view_menu = Menu(menu, tearoff=0)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode, accelerator="Ctrl+H")

        tools_menu = Menu(menu, tearoff=0)
        tools_menu.add_command(label="Open Activity Log", command=self.open_log)
        tools_menu.add_command(label="Export Project Report (TXT)", command=self.export_project_report_txt)
        tools_menu.add_command(label="Export Current Tab as PDF (Password)", command=self.export_pdf)

        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        menu.add_cascade(label="View", menu=view_menu)
        menu.add_cascade(label="Tools", menu=tools_menu)

    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.root.bind("<Control-Alt-s>", lambda e: self.save_all_tabs())
        self.root.bind("<Control-w>", lambda e: self.close_tab())
        self.root.bind("<Control-f>", lambda e: self.find_replace())
        self.root.bind("<Control-h>", lambda e: self.toggle_dark_mode())
        self.root.bind("<Control-p>", lambda e: self.export_pdf())

    # ================= Status / Modified =================
    def refresh_status(self):
        frame = self.current_frame()
        if not frame:
            return
        text = frame._text

        wc = word_count(text)
        ln, col = get_cursor_line_col(text)
        name = os.path.basename(frame._file_path) if frame._file_path else "Untitled"
        mod = "*" if frame._modified else ""

        self.status.config(
            text=f"{name}{mod} | Words: {wc} | Ln {ln}, Col {col} | Font: {self.font_var.get()} {self.size_var.get()}"
        )
        self.notebook.tab(self.notebook.index(frame), text=name + mod)
        self.redraw_lines(frame._gutter, frame._text)

    def on_modified(self, text):
        frame = self.current_frame()
        if not frame:
            return
        frame._modified = True
        text.edit_modified(False)
        self.refresh_status()

    # ================= Basic actions =================
    def current_text(self):
        frame = self.current_frame()
        return frame._text if frame else None

    def undo(self):
        t = self.current_text()
        if t:
            t.edit_undo()

    def redo(self):
        t = self.current_text()
        if t:
            t.edit_redo()

    def new_file(self):
        self.new_tab()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not path:
            return
        self.open_specific_file(path)

    # ✅ REQUIRED FUNCTION (Welcome + Recent uses this)
    def open_specific_file(self, path: str):
        try:
            content = self.fm.open_file(path)
            self.new_tab(content, os.path.abspath(path), os.path.basename(path))
            self.fm.add_recent(path)
            self.refresh_recent_menu()
            self.fm.log_event("OPEN_FILE", os.path.abspath(path))
        except Exception as e:
            messagebox.showerror("Open Error", str(e))

    def save_file(self):
        frame = self.current_frame()
        if not frame:
            return
        if not frame._file_path:
            return self.save_as()

        with self.file_lock:
            try:
                self.fm.save_file(frame._file_path, frame._text.get("1.0", END))
                frame._modified = False
                self.fm.add_recent(frame._file_path)
                self.refresh_recent_menu()
                self.fm.log_event("SAVE_FILE", frame._file_path)
                self.refresh_status()
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def save_as(self):
        frame = self.current_frame()
        if not frame:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        frame._file_path = os.path.abspath(path)
        self.save_file()

    def save_all_tabs(self):
        saved = 0
        skipped = 0
        with self.file_lock:
            for tab in self.notebook.tabs():
                f = self.root.nametowidget(tab)
                if not f._file_path:
                    skipped += 1
                    continue
                try:
                    self.fm.save_file(f._file_path, f._text.get("1.0", END))
                    f._modified = False
                    saved += 1
                except Exception:
                    skipped += 1

        self.fm.log_event("SAVE_ALL", f"saved={saved} skipped={skipped}")
        self.refresh_status()
        messagebox.showinfo("Save All", f"Saved: {saved}\nSkipped (unsaved tabs): {skipped}")

    def close_tab(self):
        frame = self.current_frame()
        if not frame:
            return
        self.notebook.forget(frame)
        if not self.notebook.tabs():
            self.new_tab()

    def exit_editor(self):
        self.fm.log_event("APP_EXIT", "")
        self.root.destroy()

    def file_properties(self):
        frame = self.current_frame()
        if not frame or not frame._file_path:
            messagebox.showinfo("File Properties", "This tab has no saved file yet.")
            return
        info = self.fm.file_info(frame._file_path)
        messagebox.showinfo(
            "File Properties",
            f"Path: {info['path']}\nSize: {info['size']} bytes\nModified: {info['modified']}",
        )

    # ================= Recent files =================
    def refresh_recent_menu(self):
        self.recent_menu.delete(0, END)
        recents = self.fm.load_recent_files()
        if not recents:
            self.recent_menu.add_command(label="(empty)", state="disabled")
            return
        for p in recents[:10]:
            self.recent_menu.add_command(label=p, command=lambda x=p: self.open_recent(x))

    def open_recent(self, path: str):
        if not os.path.exists(path):
            messagebox.showerror("Recent File", "File not found.")
            return
        self.open_specific_file(path)

    # ================= Find / Replace =================
    def find_replace(self):
        t = self.current_text()
        if t:
            open_find_replace_dialog(self.root, t)

    # ================= Theme =================
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        for tab in self.notebook.tabs():
            f = self.root.nametowidget(tab)
            self.apply_theme(f._text, f._gutter)
            self.redraw_lines(f._gutter, f._text)
        self.fm.log_event("TOGGLE_THEME", "dark" if self.dark_mode else "light")
        self.refresh_status()

    def apply_theme(self, text, gutter):
        if self.dark_mode:
            text.config(bg="#1e1e1e", fg="#e6e6e6", insertbackground="#e6e6e6")
            gutter.config(bg="#1e1e1e")
            self.status.config(bg="#1e1e1e", fg="#e6e6e6")
            self.toolbar.config(bg="#1e1e1e")
        else:
            text.config(bg="white", fg="black", insertbackground="black")
            gutter.config(bg="#f0f0f0")
            self.status.config(bg=self.root.cget("bg"), fg="black")
            self.toolbar.config(bg=self.root.cget("bg"))

    # ================= Autosave + Recovery =================
    def autosave_path(self, frame):
        return os.path.join(AUTOSAVE_DIR, f"{frame._tab_id}.autosave.txt")

    def start_autosave(self):
        def worker():
            while True:
                time.sleep(10)
                with self.file_lock:
                    for tab in self.notebook.tabs():
                        f = self.root.nametowidget(tab)
                        if f._modified:
                            try:
                                with open(self.autosave_path(f), "w", encoding="utf-8") as a:
                                    a.write(f._text.get("1.0", END))
                            except Exception:
                                pass

        threading.Thread(target=worker, daemon=True).start()

    def try_recover(self, frame):
        p = self.autosave_path(frame)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()
                if data.strip():
                    if messagebox.askyesno("Recovery", "Autosave found for this tab. Restore it?"):
                        frame._text.delete("1.0", END)
                        frame._text.insert("1.0", data)
                        frame._modified = True
                        self.fm.log_event("RECOVERY_RESTORE", p)
            except Exception:
                pass

    # ================= Log =================
    def open_log(self):
        log_path = os.path.abspath("logs/editor.log")
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
        try:
            os.startfile(log_path)
        except Exception:
            messagebox.showinfo("Log", log_path)

    # ================= Export Project Report =================
    def export_project_report_txt(self):
        frame = self.current_frame()
        if not frame:
            return

        report_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="project_report.txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if not report_path:
            return

        try:
            name = os.path.basename(frame._file_path) if frame._file_path else "Untitled"
            wc = word_count(frame._text)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log_path = os.path.abspath("logs/editor.log")
            tail = []
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    tail = f.readlines()[-50:]

            report = []
            report.append("BASIC TEXT EDITOR - PROJECT REPORT\n")
            report.append(f"Generated: {now}\n")
            report.append(f"Current Tab: {name}\n")
            report.append(f"Word Count: {wc}\n")

            if frame._file_path and os.path.exists(frame._file_path):
                info = self.fm.file_info(frame._file_path)
                report.append(f"File Path: {info['path']}\n")
                report.append(f"File Size: {info['size']} bytes\n")
                report.append(f"Last Modified: {info['modified']}\n")

            report.append("\n--- Recent Activity (last 50 log lines) ---\n")
            report.extend(tail if tail else ["(No logs found)\n"])

            with open(report_path, "w", encoding="utf-8") as out:
                out.writelines(report)

            self.fm.log_event("EXPORT_REPORT", os.path.abspath(report_path))
            messagebox.showinfo("Project Report", "Project report exported ✅")

        except Exception as e:
            messagebox.showerror("Report Error", str(e))

    # ================= PDF Export (Password Protected) =================
    def export_pdf(self):
        frame = self.current_frame()
        if not frame:
            return
        text = frame._text

        default_name = "Untitled.pdf"
        if frame._file_path:
            default_name = os.path.splitext(os.path.basename(frame._file_path))[0] + ".pdf"

        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not pdf_path:
            return

        pwd = simpledialog.askstring(
            "PDF Password",
            "Set a password to open this PDF (leave empty = no password):",
            show="*"
        )

        try:
            content = text.get("1.0", "end-1c")

            encrypt_obj = None
            if pwd and pwd.strip():
                user_pwd = pwd.strip()
                encrypt_obj = StandardEncryption(
                    userPassword=user_pwd,
                    ownerPassword=user_pwd,
                    canPrint=1,
                    canModify=0,
                    canCopy=0,
                    canAnnotate=0
                )

            c = canvas.Canvas(pdf_path, pagesize=A4, encrypt=encrypt_obj)
            page_w, page_h = A4

            lm, rm, tm, bm = 2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm
            body_font, body_size, line_h = "Courier", 11, 14

            usable_w = page_w - lm - rm
            max_chars = max(40, int(usable_w / (0.55 * body_size)))

            file_title = os.path.basename(pdf_path)
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            page = 1

            def header_footer():
                c.setFont("Helvetica-Bold", 10)
                c.drawString(lm, page_h - 1.5 * cm, file_title)
                c.setFont("Helvetica", 9)
                c.drawRightString(page_w - rm, page_h - 1.5 * cm, now)

                c.setFont("Helvetica", 9)
                c.drawCentredString(page_w / 2, 1.5 * cm, f"Page {page}")
                c.setFont(body_font, body_size)

            y = page_h - tm
            c.setFont(body_font, body_size)
            header_footer()

            for raw in content.splitlines():
                lines = textwrap.wrap(raw, width=max_chars) or [""]
                for line in lines:
                    if y <= bm:
                        c.showPage()
                        page += 1
                        y = page_h - tm
                        header_footer()
                    c.drawString(lm, y, line)
                    y -= line_h

            c.save()
            self.fm.log_event("EXPORT_PDF", os.path.abspath(pdf_path))

            if pwd and pwd.strip():
                messagebox.showinfo("Export PDF", "PDF exported with password protection ✅")
            else:
                messagebox.showinfo("Export PDF", "PDF exported (no password) ✅")

        except Exception as e:
            messagebox.showerror("Export PDF Error", str(e))
