# from tkinter import Tk
# from editor.ui import TextEditorUI

# if __name__ == "__main__":
#      root = Tk()
#      app = TextEditorUI(root)
# root.mainloop()


import tkinter as tk
from editor.welcome import WelcomeScreen


def main():
    root = tk.Tk()
    root.geometry("520x300")
    root.resizable(False, False)

    # Start with Welcome screen in the same root window
    WelcomeScreen(root)

    root.mainloop()


if __name__ == "__main__":
    main()
