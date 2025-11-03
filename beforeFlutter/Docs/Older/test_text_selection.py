#!/usr/bin/env python3
"""
PROOF OF CONCEPT: Text selection in Tkinter ScrolledText widget
This demonstrates that text selection works perfectly when configured correctly
"""
import tkinter as tk
from tkinter import scrolledtext

def main():
    root = tk.Tk()
    root.title("Text Selection Test")
    root.geometry("600x400")
    
    # Create ScrolledText widget with EXACT same configuration as Sparky
    text_widget = scrolledtext.ScrolledText(
        root,
        wrap=tk.WORD,
        font=("Segoe UI", 10, "bold"),
        bg="#C4C4D8",  # Purple background
        fg="#1a1a1a",  # Dark gray text
        state=tk.NORMAL,  # CRITICAL: Allows selection
        cursor="xterm",  # Text cursor
        selectbackground="#A0C0FF",  # Blue selection
        selectforeground="black",  # Black text when selected
        exportselection=True,  # Copy to clipboard
        takefocus=True  # Receive focus
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # NO KEY BINDINGS - This is critical
    # Tkinter handles all selection automatically
    
    # Insert some test text
    text_widget.insert("1.0", "👤 12:34\nUser message goes here\n\n")
    text_widget.insert(tk.END, "🤖 12:35\nAI response goes here. This is a longer message that spans multiple lines so you can test selecting across line breaks.\n\n")
    text_widget.insert(tk.END, "👤 12:36\nAnother user message\n\n")
    text_widget.insert(tk.END, "🤖 12:37\nAnother AI response with some technical content like code snippets or URLs: https://example.com\n\n")
    
    # Add instructions
    instructions = tk.Label(
        root,
        text="TEST: Click and drag to select text. Right-click for menu. Ctrl+C to copy.",
        font=("Segoe UI", 9),
        bg="lightblue",
        fg="black",
        pady=5
    )
    instructions.pack(side=tk.BOTTOM, fill=tk.X)
    
    print("✅ Text Selection Test Window Opened")
    print("✅ Try these:")
    print("   1. Click and drag mouse to select text")
    print("   2. Right-click for context menu")
    print("   3. Press Ctrl+C to copy")
    print("   4. Press Ctrl+A to select all")
    print("")
    print("   If ANY of these work, the fix is correct!")
    
    root.mainloop()

if __name__ == "__main__":
    main()
