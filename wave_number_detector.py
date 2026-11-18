#!/usr/bin/env python3
"""
Wave Number Detector Module
Detects wave numbers on screen using individual digit template matching.
Used by macro_app_main.py for "Wait, Round Completed (Wave X)" steps.

Approach: Instead of matching whole wave number images (which requires a
template for every possible number), this extracts individual digit masks
(0-9) from single-digit reference images and slides them across the screen
capture. This works for ANY wave number, not just ones with pre-captured refs.
"""

import cv2
import numpy as np
import pyautogui
from mss import mss
import os
import threading
import time
from time import perf_counter

from macro_app.services.detection_profile import DetectionProfiler

# Wave counter region (left, top, right, bottom)
WAVE_REGION = (405, 85, 445, 118)  # 40x33 pixels

# Yen display region (left, top, right, bottom)
YEN_REGION = (527, 535, 663, 558)  # 136x23 pixels

# Reference images folder
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCES_FOLDER = os.path.join(_MODULE_DIR, "references")

# Confidence threshold for individual digit matching
CONFIDENCE_THRESHOLD = 0.60

# Non-maximum suppression: if horizontal overlap between two detections
# exceeds this fraction of the smaller width, suppress the weaker one
NMS_OVERLAP_RATIO = 0.3

# Module state
scale_factor = 1.0
digit_templates = {}
yen_digit_templates = {}
_screen_capture = None
_runtime_screen_capture = None
_region_translator = None
_detection_profiler = None
_templates_initialized = False
_templates_init_lock = threading.Lock()
_capture_lock = threading.RLock()


def _get_screen_capture():
    """Lazily create a shared mss capture session."""
    global _screen_capture
    if _screen_capture is None:
        _screen_capture = mss()
    return _screen_capture


def _capture_region_bgr(region):
    """Capture a screen region as BGR using mss."""
    with _capture_lock:
        if _runtime_screen_capture is not None:
            return _runtime_screen_capture.capture_base_region_bgr(region)
        if _region_translator is not None:
            region = _region_translator(region)
        left, top, right, bottom = region
        width = right - left
        height = bottom - top
        shot = _get_screen_capture().grab(
            {"left": left, "top": top, "width": width, "height": height}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)


def set_screen_capture(screen_capture):
    """Set the shared runtime capture backend."""
    global _runtime_screen_capture
    with _capture_lock:
        _runtime_screen_capture = screen_capture


def clear_screen_capture():
    """Restore the default mss capture path."""
    global _runtime_screen_capture
    with _capture_lock:
        _runtime_screen_capture = None


def set_region_translator(region_translator):
    """Set an optional region translator for relative positioning."""
    global _region_translator
    with _capture_lock:
        _region_translator = region_translator


def clear_region_translator():
    """Clear the active region translator."""
    global _region_translator
    with _capture_lock:
        _region_translator = None


def set_detection_profiler(detection_profiler: DetectionProfiler | None):
    """Set an optional runtime detection profiler."""
    global _detection_profiler
    _detection_profiler = detection_profiler


def clear_detection_profiler():
    """Clear the active detection profiler."""
    global _detection_profiler
    _detection_profiler = None


def get_scale_factor():
    """Detect display scale factor (for Retina displays)."""
    global scale_factor
    test_shot = pyautogui.screenshot()
    screen_w, _ = pyautogui.size()
    scale_factor = test_shot.size[0] / screen_w
    print(f"[wave_number_detector] Display scale factor: {scale_factor}")
    return scale_factor


def ensure_templates_initialized():
    """Initialize digit templates on first use."""
    if not _templates_initialized:
        init_wave_templates()


def create_white_mask(img):
    """Create binary mask of white pixels using HSV filtering.

    White pixels = low saturation + high brightness.
    Isolates white digit text from colored backgrounds.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, v = cv2.split(hsv)

    white_mask = cv2.bitwise_and(
        cv2.inRange(s, 0, 50),
        cv2.inRange(v, 200, 255)
    )
    return white_mask


def create_yellow_mask(img):
    """Create binary mask of yellow/gold pixels (yen text color).

    Yellow/gold text in the game has:
    - Hue in the yellow range (~15-45 in OpenCV's 0-180 scale)
    - High saturation (vivid color)
    - High value/brightness (bright text)
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (15, 80, 150), (45, 255, 255))
    return mask


def extract_digit_template(img):
    """Extract the digit region from a single-digit reference image.

    Creates white mask, finds contours, merges vertically-overlapping
    contours into one bounding box, and crops just that region.
    """
    mask = create_white_mask(img)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Start with the largest contour
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    bx1, by1, bx2, by2 = x, y, x + w, y + h

    # Merge any contour that overlaps horizontally (handles multi-part digits)
    for cnt in contours:
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        if cx < bx2 and cx + cw > bx1:
            bx1 = min(bx1, cx)
            by1 = min(by1, cy)
            bx2 = max(bx2, cx + cw)
            by2 = max(by2, cy + ch)

    # Crop with small padding
    pad = 2
    crop_x1 = max(0, bx1 - pad)
    crop_y1 = max(0, by1 - pad)
    crop_x2 = min(mask.shape[1], bx2 + pad)
    crop_y2 = min(mask.shape[0], by2 + pad)

    return mask[crop_y1:crop_y2, crop_x1:crop_x2]


def _extract_yellow_digit_template(img):
    """Extract digit region from a yen reference image using yellow mask."""
    mask = create_yellow_mask(img)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    bx1, by1, bx2, by2 = x, y, x + w, y + h

    for cnt in contours:
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        if cx < bx2 and cx + cw > bx1:
            bx1 = min(bx1, cx)
            by1 = min(by1, cy)
            bx2 = max(bx2, cx + cw)
            by2 = max(by2, cy + ch)

    pad = 2
    crop_x1 = max(0, bx1 - pad)
    crop_y1 = max(0, by1 - pad)
    crop_x2 = min(mask.shape[1], bx2 + pad)
    crop_y2 = min(mask.shape[0], by2 + pad)

    return mask[crop_y1:crop_y2, crop_x1:crop_x2]


def init_wave_templates():
    """Load wave_0_ref through wave_9_ref and extract individual digit masks.
    Also loads yen_0_ref through yen_9_ref for yen detection.

    On Retina displays, templates are scaled down to match live capture resolution.
    """
    global digit_templates, yen_digit_templates, scale_factor, _templates_initialized

    if _templates_initialized:
        return digit_templates

    with _templates_init_lock:
        if _templates_initialized:
            return digit_templates

        get_scale_factor()

        digit_templates = {}

        print(f"[wave_number_detector] Loading wave digit templates (scale_factor: {scale_factor})")

        for digit in range(10):
            filename = f"wave_{digit}_ref.png"
            filepath = os.path.join(REFERENCES_FOLDER, filename)

            if not os.path.exists(filepath):
                print(f"[wave_number_detector] WARNING: Missing {filename} — digit {digit} unavailable")
                continue

            img = cv2.imread(filepath)
            if img is None:
                print(f"[wave_number_detector] WARNING: Could not read {filename}")
                continue

            original_size = f"{img.shape[1]}x{img.shape[0]}"

            # Scale down for Retina before extracting mask
            if scale_factor > 1:
                new_w = int(img.shape[1] / scale_factor)
                new_h = int(img.shape[0] / scale_factor)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            cropped = extract_digit_template(img)
            if cropped is None:
                print(f"[wave_number_detector] WARNING: No white pixels in {filename}")
                continue

            digit_templates[digit] = cropped
            white_px = cv2.countNonZero(cropped)
            print(f"[wave_number_detector] Wave digit {digit}: {original_size} -> {cropped.shape[1]}x{cropped.shape[0]} mask, {white_px} white pixels")

        if not digit_templates:
            print("[wave_number_detector] WARNING: No wave digit templates loaded!")

        print(f"[wave_number_detector] Loaded {len(digit_templates)}/10 wave digit templates")

        # Load yen digit templates (yellow text)
        yen_digit_templates = {}
        print(f"[wave_number_detector] Loading yen digit templates...")

        for digit in range(10):
            filename = f"yen_{digit}_ref.png"
            filepath = os.path.join(REFERENCES_FOLDER, filename)

            if not os.path.exists(filepath):
                print(f"[wave_number_detector] WARNING: Missing {filename} — yen digit {digit} unavailable")
                continue

            img = cv2.imread(filepath)
            if img is None:
                print(f"[wave_number_detector] WARNING: Could not read {filename}")
                continue

            original_size = f"{img.shape[1]}x{img.shape[0]}"

            if scale_factor > 1:
                new_w = int(img.shape[1] / scale_factor)
                new_h = int(img.shape[0] / scale_factor)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            cropped = _extract_yellow_digit_template(img)
            if cropped is None:
                print(f"[wave_number_detector] WARNING: No yellow pixels in {filename}")
                continue

            yen_digit_templates[digit] = cropped
            yellow_px = cv2.countNonZero(cropped)
            print(f"[wave_number_detector] Yen digit {digit}: {original_size} -> {cropped.shape[1]}x{cropped.shape[0]} mask, {yellow_px} yellow pixels")

        if not yen_digit_templates:
            print("[wave_number_detector] WARNING: No yen digit templates loaded!")

        print(f"[wave_number_detector] Loaded {len(yen_digit_templates)}/10 yen digit templates")
        _templates_initialized = True
        return digit_templates


def _non_maximum_suppression(detections):
    """Remove overlapping detections, keeping highest confidence."""
    if not detections:
        return []

    detections = sorted(detections, key=lambda d: d[5], reverse=True)

    kept = []
    for det in detections:
        x1, _, w1, _, _, _ = det

        overlaps = False
        for k in kept:
            x2, _, w2, _, _, _ = k

            overlap_left = max(x1, x2)
            overlap_right = min(x1 + w1, x2 + w2)

            if overlap_right > overlap_left:
                overlap_w = overlap_right - overlap_left
                min_w = min(w1, w2)
                if overlap_w / min_w > NMS_OVERLAP_RATIO:
                    overlaps = True
                    break

        if not overlaps:
            kept.append(det)

    kept.sort(key=lambda d: d[0])
    return kept


def _detect_number(test_mask):
    """Find all digits in a binary mask using per-digit template matching.

    Returns (detected_number_or_None, min_confidence_across_digits).
    """
    all_detections = []

    for digit, template in digit_templates.items():
        t_h, t_w = template.shape[:2]

        if t_h > test_mask.shape[0] or t_w > test_mask.shape[1]:
            continue

        result = cv2.matchTemplate(test_mask, template, cv2.TM_CCOEFF_NORMED)

        locations = np.where(result >= CONFIDENCE_THRESHOLD)
        for y, x in zip(*locations):
            conf = result[y, x]
            all_detections.append((x, y, t_w, t_h, digit, conf))

    filtered = _non_maximum_suppression(all_detections)

    if filtered:
        number_str = "".join(str(d[4]) for d in filtered)
        min_conf = min(d[5] for d in filtered)
        try:
            return int(number_str), min_conf
        except ValueError:
            return None, 0

    return None, 0


def _format_digit_detections(filtered: list[tuple[int, int, int, int, int, float]]) -> list[dict[str, float | int]]:
    return [
        {
            "digit": int(det[4]),
            "confidence": float(det[5]),
            "x": int(det[0]),
            "y": int(det[1]),
            "width": int(det[2]),
            "height": int(det[3]),
        }
        for det in filtered
    ]


def capture_wave_region():
    """Capture the wave counter region from screen."""
    return _capture_region_bgr(WAVE_REGION)


def detect_specific_wave(target_wave, debug=False):
    """
    Detect if a specific wave number is shown on screen.
    Captures the wave region, creates white mask, matches individual digits,
    and checks if the assembled number matches the target.

    Args:
        target_wave: The wave number to look for
        debug: If True, print debug information

    Returns:
        (found, confidence) tuple where found is True if target wave detected
    """
    started_at = perf_counter()
    try:
        ensure_templates_initialized()
        screenshot = capture_wave_region()

        screenshot_mask = create_white_mask(screenshot)
        white_count = cv2.countNonZero(screenshot_mask)

        if debug:
            print(f"[wave_number_detector] DEBUG: Screenshot white pixels: {white_count}")

        if white_count < 10:
            if debug:
                print(f"[wave_number_detector] DEBUG: Skipping - not enough white pixels ({white_count} < 10)")
            return False, 0

        detected, confidence = _detect_number(screenshot_mask)

        if debug:
            print(f"[wave_number_detector] DEBUG: Detected={detected}, confidence={confidence:.3f}, target={target_wave}")

        if detected is not None and detected == target_wave:
            return True, confidence

        return False, confidence
    finally:
        if _detection_profiler is not None:
            _detection_profiler.record("wave_number", perf_counter() - started_at)


def detect_current_wave(debug=False):
    """Detect the currently visible wave number, if any."""
    started_at = perf_counter()
    try:
        ensure_templates_initialized()
        screenshot = capture_wave_region()
        screenshot_mask = create_white_mask(screenshot)
        white_count = cv2.countNonZero(screenshot_mask)

        if debug:
            print(f"[wave_number_detector] DEBUG CURRENT: white pixels={white_count}")

        if white_count < 10:
            return None, 0.0

        detected, confidence = _detect_number(screenshot_mask)
        if debug:
            print(f"[wave_number_detector] DEBUG CURRENT: detected={detected}, confidence={confidence:.3f}")
        return detected, confidence
    finally:
        if _detection_profiler is not None:
            _detection_profiler.record("wave_current", perf_counter() - started_at)


def wait_for_wave(target_wave, check_stop_callback=None, status_callback=None):
    """
    Continuously check for a specific wave number until detected.

    Args:
        target_wave: The wave number to wait for
        check_stop_callback: Optional function that returns True if we should stop waiting
        status_callback: Optional function to call with status updates

    Returns:
        True if wave was detected, False if stopped early
    """
    if status_callback:
        status_callback(f"Waiting for Wave {target_wave} to appear...")

    print(f"[wave_number_detector] Waiting for Wave {target_wave}...")

    while True:
        if check_stop_callback and check_stop_callback():
            print(f"[wave_number_detector] Stop requested while waiting for Wave {target_wave}")
            return False

        found, confidence = detect_specific_wave(target_wave)

        if found:
            print(f"[wave_number_detector] Wave {target_wave} DETECTED! (confidence: {confidence:.3f})")
            if status_callback:
                status_callback(f"Wave {target_wave} detected!")
            return True

        time.sleep(0.1)


def capture_yen_region():
    """Capture the yen display region from screen."""
    return _capture_region_bgr(YEN_REGION)


def _detect_number_with_templates(test_mask, templates, *, include_details: bool = False):
    """Find all digits in a binary mask using specified digit templates.

    Returns (detected_number_or_None, min_confidence_across_digits).
    """
    all_detections = []

    for digit, template in templates.items():
        t_h, t_w = template.shape[:2]

        if t_h > test_mask.shape[0] or t_w > test_mask.shape[1]:
            continue

        result = cv2.matchTemplate(test_mask, template, cv2.TM_CCOEFF_NORMED)

        locations = np.where(result >= CONFIDENCE_THRESHOLD)
        for y, x in zip(*locations):
            conf = result[y, x]
            all_detections.append((x, y, t_w, t_h, digit, conf))

    filtered = _non_maximum_suppression(all_detections)

    if filtered:
        number_str = "".join(str(d[4]) for d in filtered)
        min_conf = min(d[5] for d in filtered)
        details = _format_digit_detections(filtered)
        try:
            if include_details:
                return int(number_str), min_conf, details
            return int(number_str), min_conf
        except ValueError:
            if include_details:
                return None, 0, []
            return None, 0

    if include_details:
        return None, 0, []
    return None, 0


def detect_yen_amount(debug=False, *, include_details: bool = False):
    """
    Detect the current yen amount shown on screen.
    Captures the yen region, creates a yellow mask, and matches against yen digit templates.

    Returns:
        (amount, confidence) tuple where amount is int or None
    """
    started_at = perf_counter()
    try:
        ensure_templates_initialized()
        screenshot = capture_yen_region()

        yellow_mask = create_yellow_mask(screenshot)
        yellow_count = cv2.countNonZero(yellow_mask)

        if debug:
            print(f"[wave_number_detector] YEN DEBUG: Yellow mask pixels: {yellow_count}")

        if yellow_count < 10:
            if include_details:
                return None, 0, []
            return None, 0

        result = _detect_number_with_templates(
            yellow_mask,
            yen_digit_templates,
            include_details=include_details,
        )
        if include_details:
            detected, confidence, details = result
        else:
            detected, confidence = result

        if debug:
            print(f"[wave_number_detector] YEN DEBUG: Detected={detected}, confidence={confidence:.3f}")

        if include_details:
            return detected, confidence, details
        return detected, confidence
    finally:
        if _detection_profiler is not None:
            _detection_profiler.record("yen_amount", perf_counter() - started_at)


def wait_for_yen(target_amount, check_stop_callback=None, status_callback=None):
    """
    Continuously check for yen amount until it reaches or exceeds the target.

    Args:
        target_amount: The minimum yen amount to wait for
        check_stop_callback: Optional function that returns True if we should stop waiting
        status_callback: Optional function to call with status updates

    Returns:
        True if target yen reached, False if stopped early
    """
    if status_callback:
        status_callback(f"Waiting for Yen >= {target_amount:,}...")

    print(f"[wave_number_detector] Waiting for Yen >= {target_amount:,}...")

    last_detected = None
    while True:
        if check_stop_callback and check_stop_callback():
            print(f"[wave_number_detector] Stop requested while waiting for Yen >= {target_amount:,}")
            return False

        detected, confidence = detect_yen_amount()

        if detected is not None:
            if detected != last_detected:
                print(f"[wave_number_detector] Current yen: {detected:,} (target: {target_amount:,}, confidence: {confidence:.3f})")
                last_detected = detected
            if detected >= target_amount:
                print(f"[wave_number_detector] Yen target reached! {detected:,} >= {target_amount:,}")
                if status_callback:
                    status_callback(f"Yen target reached: {detected:,}")
                return True

        time.sleep(0.5)


if __name__ == "__main__":
    print("=" * 50)
    print("Wave Number Detector — Live Test")
    print("=" * 50)
    print(f"Region: {WAVE_REGION}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print("Press Ctrl+C to stop\n")

    init_wave_templates()

    if not digit_templates:
        print("No digit templates loaded. Exiting.")
    else:
        last_detected = None
        while True:
            try:
                screenshot = capture_wave_region()
                mask = create_white_mask(screenshot)
                detected, confidence = _detect_number(mask)

                if detected is not None:
                    if detected != last_detected:
                        print(f"Detected: {detected}  (confidence: {confidence:.3f})")
                        last_detected = detected
                else:
                    if last_detected is not None:
                        print("No number detected")
                        last_detected = None

                time.sleep(0.2)
            except KeyboardInterrupt:
                print("\nStopped.")
                break
