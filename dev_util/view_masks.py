#!/usr/bin/env python3
"""
View Masks - Displays all wave templates and their generated masks.
Separate from the detection test for easier debugging.
"""

import cv2
import numpy as np
import pyautogui
import os

# Reference images folder
REFERENCES_FOLDER = "references"

# Scale factor for Retina displays
scale_factor = 1.0


def get_scale_factor():
    """Detect display scale factor (for Retina displays)."""
    global scale_factor
    test_shot = pyautogui.screenshot()
    screen_w, _ = pyautogui.size()
    scale_factor = test_shot.size[0] / screen_w
    print(f"Display scale factor: {scale_factor}")
    return scale_factor


def create_mask_from_template(template):
    """
    Create a mask that isolates ONLY the white pixels of the digit.
    White (255) = white parts of the number, Black (0) = everything else.
    """
    # Convert to HSV
    hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)

    # Extract channels
    h, s, v = cv2.split(hsv)

    # Find WHITE pixels only:
    # - Low saturation (white has no color)
    # - High value/brightness (white is bright)
    white_mask = cv2.bitwise_and(
        cv2.inRange(s, 0, 50),      # Low saturation
        cv2.inRange(v, 200, 255)    # High brightness
    )

    return white_mask


def load_wave_templates():
    """Load all wave reference images and create masks for them."""
    templates = {}

    for i in range(16):  # Waves 0-15
        filename = f"wave_{i}_ref.png"
        filepath = os.path.join(REFERENCES_FOLDER, filename)

        if os.path.exists(filepath):
            template = cv2.imread(filepath)
            if template is not None:
                # Scale for Retina if needed
                if scale_factor > 1:
                    new_w = int(template.shape[1] / scale_factor)
                    new_h = int(template.shape[0] / scale_factor)
                    template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

                # Create mask for this template
                mask = create_mask_from_template(template)

                templates[i] = {
                    'image': template,
                    'mask': mask,
                    'shape': template.shape
                }
                print(f"Loaded wave_{i}_ref.png ({template.shape[1]}x{template.shape[0]})")

    return templates


def display_all_masks(templates):
    """Display all templates and their masks in a combined image."""
    if not templates:
        print("No templates to display")
        return

    # Sort by wave number
    sorted_waves = sorted(templates.keys())

    # Calculate grid size
    num_templates = len(sorted_waves)
    cols = min(4, num_templates)  # Max 4 columns
    rows = (num_templates + cols - 1) // cols

    # Scale factor for display
    display_scale = 4

    # Find max dimensions
    max_h = max(templates[w]['shape'][0] for w in sorted_waves)
    max_w = max(templates[w]['shape'][1] for w in sorted_waves)

    # Create combined image (template on top, mask on bottom for each)
    cell_h = (max_h * 2 + 30) * display_scale  # template + mask + label
    cell_w = (max_w + 10) * display_scale

    combined = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, wave_num in enumerate(sorted_waves):
        row = idx // cols
        col = idx % cols

        template = templates[wave_num]['image']
        mask = templates[wave_num]['mask']

        # Scale up for visibility
        template_scaled = cv2.resize(template, None, fx=display_scale, fy=display_scale, interpolation=cv2.INTER_NEAREST)
        mask_scaled = cv2.resize(mask, None, fx=display_scale, fy=display_scale, interpolation=cv2.INTER_NEAREST)

        # Convert mask to BGR for display
        mask_bgr = cv2.cvtColor(mask_scaled, cv2.COLOR_GRAY2BGR)

        # Position in grid
        y_start = row * cell_h
        x_start = col * cell_w

        # Draw label
        label = f"Wave {wave_num}"
        cv2.putText(combined, label, (x_start + 5, y_start + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw template
        t_y = y_start + 25
        t_h, t_w = template_scaled.shape[:2]
        combined[t_y:t_y + t_h, x_start:x_start + t_w] = template_scaled

        # Draw "Mask:" label
        cv2.putText(combined, "Mask:", (x_start + 5, t_y + t_h + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Draw mask below template
        m_y = t_y + t_h + 20
        m_h, m_w = mask_bgr.shape[:2]
        combined[m_y:m_y + m_h, x_start:x_start + m_w] = mask_bgr

    cv2.imshow("All Templates & Masks", combined)
    print("\nShowing all templates and masks.")
    print("Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    print("=" * 50)
    print("Wave Template Mask Viewer")
    print("=" * 50)

    # Get scale factor
    get_scale_factor()

    # Load templates
    print("\nLoading wave templates...")
    templates = load_wave_templates()

    if not templates:
        print("\nNo templates loaded!")
        print("Please ensure you have wave_X_ref.png files in the references/ folder.")
        return

    print(f"\nLoaded {len(templates)} wave templates")

    # Display all templates and masks
    display_all_masks(templates)


if __name__ == "__main__":
    main()
