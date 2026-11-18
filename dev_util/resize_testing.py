#!/usr/bin/env python3
"""
Test script for resizing application windows on macOS.
"""

import subprocess


def resize_window(app_name, x, y, width, height):
    """Resize an application window using System Events."""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set frontmost to true
            tell window 1
                set position to {{{x}, {y}}}
                set size to {{{width}, {height}}}
            end tell
        end tell
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Resized '{app_name}' to {width}x{height} at ({x}, {y})")
    else:
        print(f"Error: {result.stderr}")


if __name__ == "__main__":
    # Resize Chrome to 1000x700 at top-left corner
    resize_window("Google Chrome", 0, 25, 1000, 700)
