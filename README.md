# Basic Text Editor (OS Course Project - Upgraded)

## Features
- New / Open / Save / Save As
- Recent Files (stored in JSON)
- File Properties (size, last modified, absolute path)
- Status bar: filename, modified state, word count, cursor position
- Find & Replace dialog
- Auto-save (background thread) + Recovery on startup
- Dark mode toggle
- Keyboard shortcuts

## OS Concepts Demonstrated
- File I/O: open, read, write, close
- File management: metadata, recent files list
- Threading: background autosave worker
- Synchronization: file_lock prevents concurrent writes (critical section)

## How to Run
1. Install Python 3.10+
2. Open the folder in VS Code
3. Run:
   python main.py
