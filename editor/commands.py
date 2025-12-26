from tkinter import *
from tkinter import messagebox


def word_count(text_widget: Text) -> int:
    content = text_widget.get("1.0", "end-1c").strip()
    return len(content.split()) if content else 0


def get_cursor_line_col(text_widget: Text):
    index = text_widget.index(INSERT)  # e.g. "3.5"
    line, col = index.split(".")
    return int(line), int(col)


def open_find_replace_dialog(root, text_widget: Text):
    """
    Find/Replace dialog (Unicode + uses editor font so Bangla typing works here too).
    """
    win = Toplevel(root)
    win.title("Find & Replace")
    win.geometry("430x230")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()

    # Use same font as editor so Bangla shows correctly
    try:
        editor_font = text_widget.cget("font")
    except Exception:
        editor_font = ("Arial", 12)

    frm = Frame(win)
    frm.pack(fill=BOTH, expand=True, padx=12, pady=12)

    Label(frm, text="Find:").grid(row=0, column=0, sticky="w", pady=6)
    find_var = StringVar()
    find_entry = Entry(frm, textvariable=find_var, width=30, font=editor_font)
    find_entry.grid(row=0, column=1, pady=6, sticky="w")

    Label(frm, text="Replace:").grid(row=1, column=0, sticky="w", pady=6)
    rep_var = StringVar()
    rep_entry = Entry(frm, textvariable=rep_var, width=30, font=editor_font)
    rep_entry.grid(row=1, column=1, pady=6, sticky="w")

    def do_find():
        text_widget.tag_remove("match", "1.0", END)
        needle = find_var.get()
        if not needle:
            return

        start = "1.0"
        found_any = False
        while True:
            pos = text_widget.search(needle, start, stopindex=END)
            if not pos:
                break
            endpos = f"{pos}+{len(needle)}c"
            text_widget.tag_add("match", pos, endpos)
            start = endpos
            found_any = True

        text_widget.tag_config("match", background="yellow")
        if not found_any:
            messagebox.showinfo("Find", "No match found.")

    def do_replace_one():
        needle = find_var.get()
        repl = rep_var.get()
        if not needle:
            return

        pos = text_widget.search(needle, INSERT, stopindex=END)
        if not pos:
            messagebox.showinfo("Replace", "No next match found.")
            return
        endpos = f"{pos}+{len(needle)}c"
        text_widget.delete(pos, endpos)
        text_widget.insert(pos, repl)

    def do_replace_all():
        needle = find_var.get()
        repl = rep_var.get()
        if not needle:
            return
        content = text_widget.get("1.0", END)
        text_widget.delete("1.0", END)
        text_widget.insert("1.0", content.replace(needle, repl))

    btns = Frame(frm)
    btns.grid(row=2, column=0, columnspan=2, pady=14, sticky="w")

    Button(btns, text="Find", width=10, command=do_find).pack(side=LEFT, padx=4)
    Button(btns, text="Replace Next", width=12, command=do_replace_one).pack(side=LEFT, padx=4)
    Button(btns, text="Replace All", width=10, command=do_replace_all).pack(side=LEFT, padx=4)

    Label(frm, text="Bangla typing: switch keyboard using Win + Space", fg="gray").grid(
        row=3, column=0, columnspan=2, sticky="w"
    )

    find_entry.focus_set()
