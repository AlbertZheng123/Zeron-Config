#!/usr/bin/env python3
"""
Interactive tool to capture reference images with crosshair selection
"""

import pyautogui
import time
import sys

def capture_reference_image():
    """Capture a reference image from screen."""

    print("=" * 80)
    print("REFERENCE IMAGE CAPTURE TOOL")
    print("=" * 80)
    print()
    print("Instructions:")
    print("1. Position your cursor at the TOP-LEFT corner of what you want to capture")
    print("2. Note the coordinates (we'll display them)")
    print("3. Then position cursor at BOTTOM-RIGHT corner")
    print("4. We'll capture that exact region")
    print()

    # Get top-left corner
    print("STEP 1: Move your mouse to the TOP-LEFT corner of the target")
    print("         (e.g., top-left of the button/icon you want to detect)")
    print("         You have 5 seconds to position your mouse...")

    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print()

    x1, y1 = pyautogui.position()
    print(f"✓ Top-left captured: ({x1}, {y1})")
    print()

    # Get bottom-right corner
    print("STEP 2: Move your mouse to the BOTTOM-RIGHT corner of the target")
    print("         (e.g., bottom-right of the same button/icon)")
    print("         You have 5 seconds to position your mouse...")

    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print()

    x2, y2 = pyautogui.position()
    print(f"✓ Bottom-right captured: ({x2}, {y2})")
    print()

    # Check for Retina/HiDPI scaling
    test_screenshot = pyautogui.screenshot()
    screen_w, screen_h = pyautogui.size()
    scale_factor = test_screenshot.size[0] / screen_w
    print(f"Display scale factor: {scale_factor}x")

    # Calculate dimensions (in PyAutoGUI coordinates)
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    # Scale coordinates for actual screenshot
    scaled_left = int(left * scale_factor)
    scaled_top = int(top * scale_factor)
    scaled_width = int(width * scale_factor)
    scaled_height = int(height * scale_factor)

    print(f"Capture region (PyAutoGUI coords):")
    print(f"  Position: ({left}, {top})")
    print(f"  Size: {width} x {height} pixels")
    print(f"Scaled region (actual screenshot):")
    print(f"  Position: ({scaled_left}, {scaled_top})")
    print(f"  Size: {scaled_width} x {scaled_height} pixels")
    print()

    if width < 10 or height < 10:
        print("ERROR: Region too small! Make sure you select a larger area.")
        return

    # Take FULL screenshot and crop the scaled region
    # This ensures we get the actual Retina resolution pixels
    print("Capturing screenshot at native resolution...")
    full_screenshot = pyautogui.screenshot()

    # Crop the region at the scaled coordinates
    cropped = full_screenshot.crop((
        scaled_left,
        scaled_top,
        scaled_left + scaled_width,
        scaled_top + scaled_height
    ))

    # Save with timestamp
    filename = f"references/reference_{int(time.time())}.png"
    cropped.save(filename)

    print(f"✓ Reference image saved to: {filename}")
    print(f"  Actual saved size: {cropped.size}")
    print()
    print("=" * 80)
    print("TIPS FOR BEST RESULTS:")
    print("=" * 80)
    print("1. Capture ONLY the essential part (not extra background)")
    print("2. Make sure the element is clearly visible and not partially hidden")
    print("3. Avoid capturing changing elements (timers, animations)")
    print("4. The smaller and more specific the capture, the better")
    print("5. Test with confidence 0.7-0.8 first")
    print()
    print(f"Update your script to use: image_name = \"{filename.split('/')[-1]}\"")
    print("=" * 80)


if __name__ == "__main__":
    try:
        capture_reference_image()
    except KeyboardInterrupt:
        print("\n\nCapture cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
