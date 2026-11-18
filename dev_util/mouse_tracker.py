#!/usr/bin/env python3
"""
Mouse Coordinate Tracker
Shows real-time mouse coordinates in a small popup that follows the cursor.
Press 'q' or Escape to quit, 'c' to copy current coordinates to clipboard.
"""

import pyautogui
import tkinter as tk
import pyperclip

class MouseTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mouse Tracker")

        # Remove window decorations and make it float on top
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.85)

        # Create label for coordinates
        self.label = tk.Label(
            self.root,
            text="X: 0, Y: 0",
            font=('Monaco', 14, 'bold'),
            bg='#2d2d2d',
            fg='#00ff00',
            padx=10,
            pady=5
        )
        self.label.pack()

        # Instructions label
        self.info_label = tk.Label(
            self.root,
            text="[C] Copy  [Q/Esc] Quit",
            font=('Monaco', 9),
            bg='#2d2d2d',
            fg='#888888',
            padx=10,
            pady=2
        )
        self.info_label.pack()

        # Bind keyboard events
        self.root.bind('<Key-q>', self.quit)
        self.root.bind('<Escape>', self.quit)
        self.root.bind('<Key-c>', self.copy_coords)
        self.root.bind('<Key-C>', self.copy_coords)

        # Store current coordinates
        self.current_x = 0
        self.current_y = 0

        # Start updating
        self.update_position()

    def update_position(self):
        try:
            # Get mouse position
            self.current_x, self.current_y = pyautogui.position()

            # Update label
            self.label.config(text=f"X: {self.current_x}, Y: {self.current_y}")

            # Position window near mouse (offset to avoid cursor overlap)
            offset_x = 20
            offset_y = 20

            # Get screen size to prevent window going off-screen
            screen_w, screen_h = pyautogui.size()
            window_w = self.root.winfo_width()
            window_h = self.root.winfo_height()

            new_x = self.current_x + offset_x
            new_y = self.current_y + offset_y

            # Adjust if would go off right edge
            if new_x + window_w > screen_w:
                new_x = self.current_x - window_w - offset_x

            # Adjust if would go off bottom edge
            if new_y + window_h > screen_h:
                new_y = self.current_y - window_h - offset_y

            self.root.geometry(f"+{new_x}+{new_y}")

            # Schedule next update (every 50ms for smooth tracking)
            self.root.after(50, self.update_position)

        except Exception as e:
            print(f"Error: {e}")
            self.root.after(50, self.update_position)

    def copy_coords(self, event=None):
        """Copy current coordinates to clipboard"""
        coords = f"({self.current_x}, {self.current_y})"
        try:
            pyperclip.copy(coords)
            # Flash the label to indicate copy
            original_bg = self.label.cget('bg')
            self.label.config(bg='#004400')
            self.root.after(150, lambda: self.label.config(bg=original_bg))
            print(f"Copied: {coords}")
        except Exception as e:
            print(f"Could not copy to clipboard: {e}")

    def quit(self, event=None):
        self.root.destroy()

    def run(self):
        # Focus window to receive keyboard input
        self.root.focus_force()
        print("Mouse Tracker running...")
        print("Press 'C' to copy coordinates, 'Q' or 'Escape' to quit")
        self.root.mainloop()

if __name__ == "__main__":
    tracker = MouseTracker()
    tracker.run()
