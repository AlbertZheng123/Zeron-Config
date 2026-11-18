#!/usr/bin/env python3
"""Jam detector with Skele Complete monitoring and auto-exit."""

from __future__ import annotations

import threading
import time
from pathlib import Path
import argparse

import cv2
import numpy as np
import pyautogui
from pynput import keyboard

import jam_detector_test as base
from macro_app.services.relative_positioning import RelativePositioner, RelativePyAutoGUI


BASE_DIR = Path(__file__).resolve().parent
COMPLETE_TEMPLATE_PATH = BASE_DIR / "references" / "abilities" / "skele_complete_ref.png"
COMPLETE_REGION = (775, 561, 798, 601)
COMPLETE_CONFIDENCE = 0.90
EXIT_CLICK = (780, 220)
CLICK_DELAY = 0.2
MONITOR_INTERVAL = 0.08

_complete_template = None
_complete_monitor_started = False
_complete_stop = threading.Event()
_session_done = threading.Event()
_auto_start = False
_pyautogui = pyautogui


def compute_scale_factor() -> float:
    screenshot = _pyautogui.screenshot()
    screen_w, _ = _pyautogui.size()
    return screenshot.size[0] / screen_w


def load_template(path: Path, scale_factor: float) -> tuple[np.ndarray, np.ndarray | None]:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Could not read template: {path}")

    mask = None
    if image.ndim == 3 and image.shape[2] == 4:
        mask = image[:, :, 3]
        image = image[:, :, :3]

    if scale_factor > 1:
        new_width = max(1, int(image.shape[1] / scale_factor))
        new_height = max(1, int(image.shape[0] / scale_factor))
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        if mask is not None:
            mask = cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return image, mask


def capture_region(region: tuple[int, int, int, int]) -> np.ndarray:
    left, top, right, bottom = region
    screenshot = _pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def detect_template(
    region_bgr: np.ndarray,
    template: np.ndarray,
    mask: np.ndarray | None,
) -> tuple[float, tuple[int, int]]:
    if mask is not None:
        result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
    else:
        result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return float(max_val), (int(max_loc[0]), int(max_loc[1]))


def move_and_click(x: int, y: int) -> None:
    _pyautogui.moveTo(x, y)
    time.sleep(CLICK_DELAY)
    _pyautogui.click()


def _ensure_complete_template() -> tuple[np.ndarray, np.ndarray | None]:
    global _complete_template
    if _complete_template is None:
        scale_factor = compute_scale_factor()
        _complete_template = load_template(COMPLETE_TEMPLATE_PATH, scale_factor)
        template, _ = _complete_template
        print(f"[JAM COMPLETE] Loaded template: {template.shape[1]}x{template.shape[0]} at scale {scale_factor:.2f}")
    return _complete_template


def _complete_monitor_worker() -> None:
    template, mask = _ensure_complete_template()
    while not _complete_stop.is_set():
        if not base._active:
            time.sleep(MONITOR_INTERVAL)
            continue

        try:
            region_bgr = capture_region(COMPLETE_REGION)
            confidence, location = detect_template(region_bgr, template, mask)
            if confidence >= COMPLETE_CONFIDENCE:
                print(
                    f"[JAM COMPLETE] Detected skele complete "
                    f"(conf={confidence:.3f}, x={location[0]}, y={location[1]})"
                )
                base._stop()
                print(f"[JAM COMPLETE] Clicking exit at {EXIT_CLICK}")
                move_and_click(*EXIT_CLICK)
                time.sleep(0.5)
                if _auto_start:
                    _session_done.set()
        except Exception as exc:
            print(f"[JAM COMPLETE] Monitor error: {exc}")
            time.sleep(0.25)
            continue

        time.sleep(MONITOR_INTERVAL)


def _ensure_complete_monitor() -> None:
    global _complete_monitor_started, _complete_stop
    if _complete_monitor_started and not _complete_stop.is_set():
        return
    if _complete_stop.is_set():
        _complete_stop = threading.Event()
    worker = threading.Thread(target=_complete_monitor_worker, daemon=True, name="jam.complete.monitor")
    worker.start()
    _complete_monitor_started = True


def _on_press(key) -> None:
    try:
        if key.char == "p":
            base._start()
        elif key.char == "o":
            base._stop()
            if _auto_start:
                _session_done.set()
        elif key.char == "6":
            print("  [manual] queueing F tap through worker")
            base._input_queue.put(("down", "f"))
            base._input_queue.put(("up", "f"))
    except AttributeError:
        pass


def run(*, auto_start: bool = False, relative: bool = False) -> None:
    global _auto_start, _pyautogui
    _auto_start = auto_start
    _pyautogui = RelativePyAutoGUI(pyautogui, RelativePositioner()) if relative else pyautogui
    _session_done.clear()
    _complete_stop.clear()

    print("=" * 50)
    print("  Skele King Jam Detector + Complete Exit")
    print("=" * 50)
    print()
    print(f"  Capture: {base.SOURCE_WIDTH}x{base.CAPTURE_HEIGHT}px at ({base.SOURCE_X}, {base.CAPTURE_TOP_Y})")
    print(f"  Complete check region: {COMPLETE_REGION}")
    print(f"  Complete confidence threshold: {COMPLETE_CONFIDENCE:.2f}")
    print(f"  Exit click: {EXIT_CLICK}")
    print()

    if not base._init_stream():
        return

    _ensure_complete_monitor()

    print()
    print("  [P] Start detection")
    print("  [O] Stop / pause detection")
    print("  [6] Manual F tap through worker")
    print("  [Ctrl+C] Quit")
    print()

    listener = keyboard.Listener(on_press=_on_press)
    listener.start()
    if auto_start:
        base._start()

    try:
        if auto_start:
            while not _session_done.is_set():
                time.sleep(0.1)
            listener.stop()
        else:
            listener.join()
    except KeyboardInterrupt:
        print("\n[JAM COMPLETE] Exited.")
    finally:
        base._stop()
        base._tap_stop.set()
        _complete_stop.set()
        try:
            listener.stop()
        except Exception:
            pass


def run_auto_session(*, relative: bool = False, stop_requested=None) -> bool:
    """Run one auto-start jam session entirely in-process.

    Returns True when the jam completed normally and False when an external stop
    request interrupted the session before completion.
    """
    global _auto_start, _pyautogui
    _auto_start = True
    _pyautogui = RelativePyAutoGUI(pyautogui, RelativePositioner()) if relative else pyautogui
    _session_done.clear()
    _complete_stop.clear()

    if not base._init_stream():
        return False

    _ensure_complete_monitor()
    base._start()

    try:
        while not _session_done.is_set():
            if stop_requested is not None and stop_requested():
                return False
            time.sleep(0.1)
        return True
    finally:
        base._stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Jam detector with auto-complete exit.")
    parser.add_argument("--auto-start", action="store_true", help="Start detection immediately and exit on O or completion.")
    parser.add_argument("--relative", action="store_true", help="Translate click/screenshot coordinates relative to the Roblox window.")
    args = parser.parse_args()
    run(auto_start=args.auto_start, relative=args.relative)


if __name__ == "__main__":
    main()
