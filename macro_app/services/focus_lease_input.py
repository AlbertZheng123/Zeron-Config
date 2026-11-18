"""DeskPad input proxy that briefly leases Roblox focus for real HID actions."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from macro_app.services.relative_positioning import (
    RelativePositioner,
    RelativePositioningError,
    find_roblox_process_id,
)

try:
    import AppKit
    from Quartz import (
        CGDisplayBounds,
        CGEventCreate,
        CGEventCreateMouseEvent,
        CGEventCreateScrollWheelEvent,
        CGEventGetLocation,
        CGEventPost,
        CGEventSetIntegerValueField,
        CGMainDisplayID,
        CGWarpMouseCursorPosition,
        CGPoint,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGEventOtherMouseDown,
        kCGEventOtherMouseUp,
        kCGEventRightMouseDown,
        kCGEventRightMouseUp,
        kCGHIDEventTap,
        kCGMouseButtonCenter,
        kCGMouseButtonLeft,
        kCGMouseButtonRight,
        kCGMouseEventClickState,
        kCGScrollEventUnitLine,
    )
except ImportError:  # pragma: no cover - unavailable on non-macOS test hosts.
    AppKit = None
    CGDisplayBounds = None
    CGEventCreate = None
    CGEventGetLocation = None
    CGMainDisplayID = None
    CGWarpMouseCursorPosition = None
    CGPoint = None


def _mouse_button_info(button: str) -> tuple[int, int, int]:
    normalized = str(button or "left").lower()
    if normalized == "right":
        return kCGMouseButtonRight, kCGEventRightMouseDown, kCGEventRightMouseUp
    if normalized == "middle":
        return kCGMouseButtonCenter, kCGEventOtherMouseDown, kCGEventOtherMouseUp
    return kCGMouseButtonLeft, kCGEventLeftMouseDown, kCGEventLeftMouseUp


def _post_hid_mouse_event(kind: str, x: float, y: float, button: str = "left") -> None:
    point = CGPoint(x, y)
    mouse_button, down_type, up_type = _mouse_button_info(button)
    event_type = {
        "move": kCGEventMouseMoved,
        "down": down_type,
        "up": up_type,
    }[kind]
    event = CGEventCreateMouseEvent(None, event_type, point, mouse_button)
    if kind in {"down", "up"}:
        CGEventSetIntegerValueField(event, kCGMouseEventClickState, 1)
    CGEventPost(kCGHIDEventTap, event)


def _post_hid_scroll(clicks: int, *, horizontal: bool = False) -> None:
    clicks = int(clicks)
    if clicks == 0:
        return
    remaining = clicks
    while remaining:
        step = max(-10, min(10, remaining))
        remaining -= step
        if horizontal:
            event = CGEventCreateScrollWheelEvent(
                None,
                kCGScrollEventUnitLine,
                2,
                0,
                step,
            )
        else:
            event = CGEventCreateScrollWheelEvent(
                None,
                kCGScrollEventUnitLine,
                1,
                step,
            )
        CGEventPost(kCGHIDEventTap, event)


def _call_on_macos_main_thread(action: Callable[[], Any], timeout: float = 2.0) -> Any:
    """Run AppKit work on the Cocoa main queue and return its result."""
    if AppKit is None or AppKit.NSThread.isMainThread():
        return action()

    completed = threading.Event()
    result: dict[str, Any] = {}

    def run() -> None:
        try:
            result["value"] = action()
        except BaseException as exc:  # Re-raise the original AppKit failure on the caller.
            result["error"] = exc
        finally:
            completed.set()

    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(run)
    if not completed.wait(max(0.1, timeout)):
        raise RelativePositioningError("DeskPad focus lease timed out on the macOS main thread")
    if "error" in result:
        raise result["error"]
    return result.get("value")


class RobloxFocusLease:
    """Activate off-main-display Roblox while an input gesture is in flight."""

    def __init__(
        self,
        positioner: RelativePositioner,
        *,
        activation_settle_seconds: float = 0.15,
        action_settle_seconds: float = 0.12,
        restore_settle_seconds: float = 0.05,
        sleep: Callable[[float], None] = time.sleep,
        main_thread_call: Callable[[Callable[[], Any]], Any] = _call_on_macos_main_thread,
    ) -> None:
        self._positioner = positioner
        self._activation_settle_seconds = max(0.0, activation_settle_seconds)
        self._action_settle_seconds = max(0.0, action_settle_seconds)
        self._restore_settle_seconds = max(0.0, restore_settle_seconds)
        self._sleep = sleep
        self._main_thread_call = main_thread_call
        self._lock = threading.RLock()
        self._active = False
        self._original_app = None
        self._original_cursor: tuple[float, float] | None = None

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    def is_required(self) -> bool:
        if AppKit is None or CGDisplayBounds is None or CGMainDisplayID is None:
            return False
        bounds = self._positioner.current_bounds()
        main_bounds = CGDisplayBounds(CGMainDisplayID())
        center_x = bounds.left + (bounds.width / 2)
        center_y = bounds.top + (bounds.height / 2)
        return not (
            main_bounds.origin.x <= center_x < main_bounds.origin.x + main_bounds.size.width
            and main_bounds.origin.y <= center_y < main_bounds.origin.y + main_bounds.size.height
        )

    def acquire(self) -> bool:
        with self._lock:
            if self._active:
                return True
            if not self.is_required():
                return False

            pid = find_roblox_process_id()

            def activate_roblox():
                roblox_app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if roblox_app is None:
                    raise RelativePositioningError(
                        f"DeskPad focus lease failed: Roblox process {pid} not available"
                    )
                workspace = AppKit.NSWorkspace.sharedWorkspace()
                original_app = workspace.frontmostApplication()
                cursor_event = CGEventCreate(None)
                original_cursor = None
                if cursor_event is not None:
                    cursor = CGEventGetLocation(cursor_event)
                    original_cursor = (float(cursor.x), float(cursor.y))
                options = (
                    AppKit.NSApplicationActivateAllWindows
                    | AppKit.NSApplicationActivateIgnoringOtherApps
                )
                accepted = bool(roblox_app.activateWithOptions_(options))
                return roblox_app, original_app, original_cursor, accepted

            try:
                roblox_app, original_app, original_cursor, accepted = self._main_thread_call(
                    activate_roblox
                )
                self._original_app = original_app
                self._original_cursor = original_cursor
                self._sleep(self._activation_settle_seconds)
                active = bool(self._main_thread_call(roblox_app.isActive))
                if not active:
                    raise RelativePositioningError(
                        "DeskPad focus lease failed: Roblox did not become active "
                        f"(request_accepted={accepted})"
                    )
                self._active = True
                return True
            except Exception:
                self._clear()
                raise

    def release(self) -> None:
        with self._lock:
            if not self._active:
                return
            original_app = self._original_app
            original_cursor = self._original_cursor
            try:
                self._sleep(self._action_settle_seconds)

                def restore_original_app() -> None:
                    if original_cursor is not None and CGWarpMouseCursorPosition is not None:
                        CGWarpMouseCursorPosition(CGPoint(*original_cursor))
                    if original_app is not None:
                        options = (
                            AppKit.NSApplicationActivateAllWindows
                            | AppKit.NSApplicationActivateIgnoringOtherApps
                        )
                        original_app.activateWithOptions_(options)

                self._main_thread_call(restore_original_app)
                self._sleep(self._restore_settle_seconds)
            finally:
                self._clear()

    def _clear(self) -> None:
        self._active = False
        self._original_app = None
        self._original_cursor = None


class FocusLeasePyAutoGUI:
    """Coordinate-safe pyautogui facade for Roblox on a virtual display."""

    def __init__(
        self,
        raw_module: Any,
        relative_module: Any,
        positioner: RelativePositioner,
        *,
        lease: RobloxFocusLease | None = None,
        debug_log: Callable[[str], None] | None = None,
    ) -> None:
        self._raw = raw_module
        self._relative = relative_module
        self._positioner = positioner
        self._lease = lease or RobloxFocusLease(positioner)
        self._debug_log = debug_log
        self._pending_point: tuple[int, int] | None = None

    @property
    def focus_lease_required(self) -> bool:
        return self._lease.is_required()

    def translate_point(self, x: int, y: int) -> tuple[int, int]:
        return self._positioner.translate_point(x, y)

    def translate_region(self, region: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return self._positioner.translate_region(region)

    def _lease_needed(self) -> bool:
        return bool(getattr(self._lease, "active", False)) or self._lease.is_required()

    def moveTo(self, x, y=None, *args, **kwargs):
        if y is None:
            return self._relative.moveTo(x, *args, **kwargs)
        if not self._lease_needed():
            return self._relative.moveTo(x, y, *args, **kwargs)

        self._lease.acquire()
        try:
            # Activation can change the window's reported Space/display bounds.
            # Resolve the target only after activation has fully settled.
            self._positioner.invalidate_cache()
            live_x, live_y = self.translate_point(int(x), int(y))
            self._pending_point = (live_x, live_y)
            if self._debug_log is not None:
                self._debug_log(
                    f"DeskPad HID move: base=({int(x)}, {int(y)}) "
                    f"live=({live_x}, {live_y})"
                )
            _post_hid_mouse_event("move", live_x, live_y)
            return None
        except Exception:
            self.release_focus_lease()
            raise

    def click(self, x=None, y=None, *args, **kwargs):
        if not self._lease_needed():
            return self._relative.click(x, y, *args, **kwargs)
        if x is not None and y is not None:
            self.moveTo(x, y)
        if self._pending_point is None:
            raise RelativePositioningError("DeskPad click has no translated target")

        live_x, live_y = self._pending_point
        self._lease.acquire()
        button = kwargs.pop("button", "left")
        clicks = max(1, int(kwargs.pop("clicks", 1)))
        interval = max(0.0, float(kwargs.pop("interval", 0.0)))
        try:
            if self._debug_log is not None:
                self._debug_log(
                    f"DeskPad HID click: live=({live_x}, {live_y}) "
                    f"button={button} clicks={clicks}"
                )
            for click_index in range(clicks):
                _post_hid_mouse_event("move", live_x, live_y, button)
                _post_hid_mouse_event("down", live_x, live_y, button)
                time.sleep(0.03)
                _post_hid_mouse_event("up", live_x, live_y, button)
                if click_index < clicks - 1 and interval:
                    time.sleep(interval)
            return None
        finally:
            self.release_focus_lease()

    def mouseDown(self, x=None, y=None, *args, **kwargs):
        if not self._lease_needed():
            if x is not None and y is not None:
                live_x, live_y = self.translate_point(int(x), int(y))
                return self._raw.mouseDown(x=live_x, y=live_y, *args, **kwargs)
            return self._raw.mouseDown(*args, **kwargs)
        if x is not None and y is not None:
            self.moveTo(x, y)
        self._lease.acquire()
        live_x, live_y = self._pending_point or (None, None)
        button = kwargs.pop("button", "left")
        try:
            if live_x is None or live_y is None:
                raise RelativePositioningError("DeskPad mouse down has no translated target")
            _post_hid_mouse_event("down", live_x, live_y, button)
            return None
        except Exception:
            self.release_focus_lease()
            raise

    def mouseUp(self, x=None, y=None, *args, **kwargs):
        if not self._lease_needed():
            if x is not None and y is not None:
                live_x, live_y = self.translate_point(int(x), int(y))
                return self._raw.mouseUp(x=live_x, y=live_y, *args, **kwargs)
            return self._raw.mouseUp(*args, **kwargs)
        if x is not None and y is not None:
            self.moveTo(x, y)
        live_x, live_y = self._pending_point or (None, None)
        button = kwargs.pop("button", "left")
        try:
            if live_x is None or live_y is None:
                raise RelativePositioningError("DeskPad mouse up has no translated target")
            _post_hid_mouse_event("up", live_x, live_y, button)
            return None
        finally:
            self.release_focus_lease()

    def scroll(self, clicks, x=None, y=None, *args, **kwargs):
        if not self._lease_needed():
            if x is not None and y is not None:
                live_x, live_y = self.translate_point(int(x), int(y))
                return self._raw.scroll(clicks, x=live_x, y=live_y, *args, **kwargs)
            return self._raw.scroll(clicks, *args, **kwargs)
        if x is not None and y is not None:
            self.moveTo(x, y)
        self._lease.acquire()
        try:
            _post_hid_scroll(clicks)
            return None
        finally:
            self.release_focus_lease()

    def hscroll(self, clicks, x=None, y=None, *args, **kwargs):
        if not self._lease_needed():
            if x is not None and y is not None:
                live_x, live_y = self.translate_point(int(x), int(y))
                return self._raw.hscroll(clicks, x=live_x, y=live_y, *args, **kwargs)
            return self._raw.hscroll(clicks, *args, **kwargs)
        if x is not None and y is not None:
            self.moveTo(x, y)
        self._lease.acquire()
        try:
            _post_hid_scroll(clicks, horizontal=True)
            return None
        finally:
            self.release_focus_lease()

    def keyDown(self, key, *args, **kwargs):
        self._lease.acquire()
        try:
            return self._raw.keyDown(key, *args, **kwargs)
        except Exception:
            self.release_focus_lease()
            raise

    def keyUp(self, key, *args, **kwargs):
        try:
            return self._raw.keyUp(key, *args, **kwargs)
        finally:
            self.release_focus_lease()

    def press(self, keys, *args, **kwargs):
        self._lease.acquire()
        try:
            return self._raw.press(keys, *args, **kwargs)
        finally:
            self.release_focus_lease()

    def write(self, message, *args, **kwargs):
        self._lease.acquire()
        try:
            return self._raw.write(message, *args, **kwargs)
        finally:
            self.release_focus_lease()

    def moveRel(self, xOffset=None, yOffset=None, *args, **kwargs):
        self._lease.acquire()
        try:
            return self._raw.moveRel(xOffset, yOffset, *args, **kwargs)
        finally:
            self.release_focus_lease()

    def release_focus_lease(self) -> None:
        self._lease.release()
        self._pending_point = None

    def __getattr__(self, name):
        return getattr(self._relative, name)
