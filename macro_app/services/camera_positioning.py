"""Camera positioning helpers for macro start setup."""

from __future__ import annotations

import time

try:
    from Quartz import (
        CGAssociateMouseAndMouseCursorPosition,
        CGEventCreateMouseEvent,
        CGEventGetLocation,
        CGEventPost,
        CGEventSetIntegerValueField,
        CGEventSourceCreate,
        CGEventSourceSetLocalEventsSuppressionInterval,
        kCGEventMouseMoved,
        kCGEventSourceStateHIDSystemState,
        kCGHIDEventTap,
        kCGMouseEventDeltaX,
        kCGMouseEventDeltaY,
    )
except ImportError:
    CGAssociateMouseAndMouseCursorPosition = None
    CGEventCreateMouseEvent = None


GAME_FOCUS_CLICK = (452, 352)
CAMERA_FOCUS_CLICK = GAME_FOCUS_CLICK
CAMERA_SETTINGS_CLICK = (17, 650)
CAMERA_TELEPORT_SPAWN_CLICK = (964, 363)
CAMERA_SETTINGS_CLOSE_CLICK = (1024, 147)
CAMERA_DRAG_START = (600, 350)
CAMERA_ZOOM_IN_SECONDS = 1.2
CAMERA_ZOOM_OUT_SECONDS = 1.6
CAMERA_LOOK_DOWN_Y = 900
CAMERA_LOOK_DOWN_DURATION = 0.55
CLICK_SETTLE_SECONDS = 0.1
SETTINGS_OPEN_TO_TELEPORT_DELAY = 1.0
TELEPORT_POSITION_TO_CLICK_DELAY = 1.0


def reposition_camera(pyautogui, *, log=None, stop_requested=None) -> bool:
    """Zoom in, look down, and zoom out before macro steps begin."""

    def should_stop() -> bool:
        return bool(stop_requested and stop_requested())

    if should_stop():
        return False

    if log:
        log("Repositioning camera...")

    _move_and_click(pyautogui, *CAMERA_SETTINGS_CLICK)
    time.sleep(SETTINGS_OPEN_TO_TELEPORT_DELAY)

    if should_stop():
        return False

    pyautogui.moveTo(*CAMERA_TELEPORT_SPAWN_CLICK)
    time.sleep(TELEPORT_POSITION_TO_CLICK_DELAY)
    pyautogui.click()
    time.sleep(0.6)

    if should_stop():
        return False

    _move_and_click(pyautogui, *CAMERA_SETTINGS_CLOSE_CLICK)
    time.sleep(0.3)

    if should_stop():
        return False

    if not _hold_key(pyautogui, "i", CAMERA_ZOOM_IN_SECONDS, stop_requested=should_stop):
        return False

    time.sleep(0.25)
    if should_stop():
        return False

    _look_down(pyautogui, CAMERA_LOOK_DOWN_Y, CAMERA_LOOK_DOWN_DURATION)

    time.sleep(0.25)
    if should_stop():
        return False

    return _hold_key(pyautogui, "o", CAMERA_ZOOM_OUT_SECONDS, stop_requested=should_stop)


def _hold_key(pyautogui, key: str, seconds: float, *, stop_requested) -> bool:
    pyautogui.keyDown(key)
    started_at = time.time()
    try:
        while time.time() - started_at < seconds:
            if stop_requested():
                return False
            time.sleep(0.05)
    finally:
        pyautogui.keyUp(key)
    return True


def _move_and_click(pyautogui, x: int, y: int) -> None:
    pyautogui.moveTo(x, y)
    time.sleep(CLICK_SETTLE_SECONDS)
    pyautogui.click()


def _look_down(pyautogui, delta_y: int, duration: float) -> None:
    release_focus_lease = getattr(pyautogui, "release_focus_lease", None)
    try:
        pyautogui.moveTo(*CAMERA_DRAG_START)
        time.sleep(0.2)
        if _quartz_locked_relative_move(pyautogui, delta_y, duration):
            return
        pyautogui.moveRel(0, delta_y, duration=duration)
    finally:
        if callable(release_focus_lease):
            release_focus_lease()


def _quartz_locked_relative_move(pyautogui, delta_y: int, duration: float) -> bool:
    if CGEventCreateMouseEvent is None or CGAssociateMouseAndMouseCursorPosition is None:
        return False

    source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
    if source is not None:
        CGEventSourceSetLocalEventsSuppressionInterval(source, 0)

    start_point = CAMERA_DRAG_START
    translate_point = getattr(pyautogui, "translate_point", None)
    if callable(translate_point):
        start_point = translate_point(*CAMERA_DRAG_START)

    start_event = CGEventCreateMouseEvent(source, kCGEventMouseMoved, start_point, 0)
    fixed_location = CGEventGetLocation(start_event)
    steps = max(30, int(duration * 180))
    sleep_per_step = duration / steps if steps else 0
    movement_per_step = delta_y / steps
    carried = 0.0

    CGAssociateMouseAndMouseCursorPosition(False)
    try:
        for _ in range(steps):
            carried += movement_per_step
            step_y = int(round(carried))
            carried -= step_y
            if step_y:
                event = CGEventCreateMouseEvent(source, kCGEventMouseMoved, fixed_location, 0)
                CGEventSetIntegerValueField(event, kCGMouseEventDeltaX, 0)
                CGEventSetIntegerValueField(event, kCGMouseEventDeltaY, step_y)
                CGEventPost(kCGHIDEventTap, event)
            time.sleep(sleep_per_step)
    finally:
        CGAssociateMouseAndMouseCursorPosition(True)
        pyautogui.moveTo(*CAMERA_DRAG_START)

    return True
