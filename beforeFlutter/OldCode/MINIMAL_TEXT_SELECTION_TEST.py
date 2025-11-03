#!/usr/bin/env python3
"""
MINIMAL TEXT SELECTION TEST
This is the absolute simplest Tkinter text widget that supports selection.
If this doesn't work, it's a system issue, not the code.
"""
import tkinter as tk
from tkinter import scrolledtext

# Create window
root = tk.Tk()
root.title("MINIMAL TEXT SELECTION TEST")
root.geometry("600x400")

# Create the SIMPLEST possible text widget that allows selection
text = scrolledtext.ScrolledText(root, state=tk.NORMAL)
text.pack(fill=tk.BOTH, expand=True)

# Add some test text
text.insert("1.0", "Line 1: Try to select this text with your mouse\n")
text.insert(tk.END, "Line 2: Click and drag to highlight\n")
text.insert(tk.END, "Line 3: Right-click for context menu\n")
text.insert(tk.END, "Line 4: Press Ctrl+C to copy\n")
text.insert(tk.END, "\n")
text.insert(tk.END, "If you CANNOT select this text, there is a problem with:\n")
text.insert(tk.END, "  - Your Python installation\n")
text.insert(tk.END, "  - Your Tkinter installation\n")
text.insert(tk.END, "  - Your Windows configuration\n")
text.insert(tk.END, "\n")
text.insert(tk.END, "If you CAN select this text, then the Sparky client code has a bug.\n")

print("=" * 60)
print("MINIMAL TEXT SELECTION TEST")
print("=" * 60)
print("Window opened. Try the following:")
print("1. Click and drag to select text")
print("2. Right-click for menu")
print("3. Press Ctrl+C to copy")
print("")
print("RESULT:")
print("  - If selection WORKS: The problem is in Sparky's code")
print("  - If selection FAILS: The problem is your system/Python/Tkinter")
print("=" * 60)

root.mainloop()
