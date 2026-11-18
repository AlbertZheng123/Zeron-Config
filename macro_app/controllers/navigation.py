"""Navigation and window state controller."""

from __future__ import annotations

import subprocess

try:
    from ApplicationServices import (
        AXIsProcessTrusted,
        AXIsProcessTrustedWithOptions,
        AXUIElementCopyAttributeValue,
        AXUIElementCreateApplication,
        AXUIElementSetAttributeValue,
        AXValueCreate,
        kAXTrustedCheckOptionPrompt,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXValueCGPointType,
        kAXValueCGSizeType,
        kAXWindowsAttribute,
    )
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListExcludeDesktopElements,
        kCGWindowListOptionOnScreenOnly,
    )
    from Quartz.CoreGraphics import CGPointMake, CGSizeMake
except ImportError:  # pragma: no cover - non-macOS or unavailable bridge
    AXIsProcessTrusted = None
    AXIsProcessTrustedWithOptions = None
    AXUIElementCopyAttributeValue = None
    AXUIElementCreateApplication = None
    AXUIElementSetAttributeValue = None
    AXValueCreate = None
    kAXTrustedCheckOptionPrompt = None
    kAXPositionAttribute = None
    kAXSizeAttribute = None
    kAXValueCGPointType = None
    kAXValueCGSizeType = None
    kAXWindowsAttribute = None
    CGWindowListCopyWindowInfo = None
    kCGNullWindowID = 0
    kCGWindowListExcludeDesktopElements = 0
    kCGWindowListOptionOnScreenOnly = 0
    CGPointMake = None
    CGSizeMake = None

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QRegion

from macro_app.constants import (
    ADVANCED_CREATE_SIZE,
    COMPACT_SIZE,
    OVERLAY_POS,
    OVERLAY_SIZE,
    PAGE_ADVANCED_CREATE,
    PAGE_MAIN_MENU,
    PAGE_OVERLAY,
)


class NavigationController:
    """Own page changes, geometry, and frameless state."""

    def __init__(self, app, window, state) -> None:
        self.app = app
        self.window = window
        self.state = state
        self._on_overlay_enter = []
        self._on_main_menu_enter = []
        self._on_advanced_enter = []
        self._pending_roblox_resize = False
        self._accessibility_prompt_requested = False

    @staticmethod
    def _find_roblox_pid() -> int | None:
        if CGWindowListCopyWindowInfo is None:
            return None
        try:
            windows = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID,
            )
        except Exception as exc:
            print(f"Could not enumerate windows for Roblox resize: {exc}")
            return None
        if not windows:
            return None

        best_pid = None
        best_score = None
        for window in windows:
            owner_name = str(window.get("kCGWindowOwnerName", ""))
            window_name = str(window.get("kCGWindowName", ""))
            if "Roblox" not in owner_name and "Roblox" not in window_name:
                continue
            bounds = window.get("kCGWindowBounds", {})
            width = int(bounds.get("Width", 0))
            height = int(bounds.get("Height", 0))
            if width <= 0 or height <= 0:
                continue
            layer = int(window.get("kCGWindowLayer", 0))
            alpha = float(window.get("kCGWindowAlpha", 1.0))
            score = (width * height, -layer, alpha)
            if best_score is None or score > best_score:
                best_score = score
                best_pid = int(window.get("kCGWindowOwnerPID", 0)) or None
        return best_pid

    def _resize_roblox_window_accessibility(self) -> bool:
        if (
            AXIsProcessTrusted is None
            or AXUIElementCreateApplication is None
            or AXUIElementCopyAttributeValue is None
            or AXUIElementSetAttributeValue is None
            or AXValueCreate is None
            or CGPointMake is None
            or CGSizeMake is None
        ):
            return False

        try:
            if not AXIsProcessTrusted():
                if (
                    not self._accessibility_prompt_requested
                    and AXIsProcessTrustedWithOptions is not None
                    and kAXTrustedCheckOptionPrompt is not None
                ):
                    self._accessibility_prompt_requested = True
                    try:
                        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
                        print(
                            "Roblox resize needs Accessibility permission. "
                            "macOS should now prompt to allow Zeron Config."
                        )
                    except Exception as prompt_exc:
                        print(f"Could not request Accessibility prompt for Roblox resize: {prompt_exc}")
                else:
                    print(
                        "Roblox resize skipped: accessibility access is not granted for this app. "
                        "Enable Zeron Config under System Settings > Privacy & Security > Accessibility."
                    )
                return False
        except Exception as exc:
            print(f"Could not verify accessibility trust for Roblox resize: {exc}")
            return False

        pid = NavigationController._find_roblox_pid()
        if pid is None:
            print("Roblox resize skipped: Roblox window/process not found.")
            return False

        try:
            app_ref = AXUIElementCreateApplication(pid)
            windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute)
            if not windows:
                print("Roblox resize skipped: no accessible Roblox windows found.")
                return False
            window_ref = windows[0]
            position_value = AXValueCreate(kAXValueCGPointType, CGPointMake(0, 40))
            size_value = AXValueCreate(kAXValueCGSizeType, CGSizeMake(1200, 630))
            position_result = AXUIElementSetAttributeValue(window_ref, kAXPositionAttribute, position_value)
            size_result = AXUIElementSetAttributeValue(window_ref, kAXSizeAttribute, size_value)
            if position_result != 0 or size_result != 0:
                print(
                    "Roblox accessibility resize failed: "
                    f"position_result={position_result}, size_result={size_result}"
                )
                return False
            print("Roblox window resized via accessibility API.")
            return True
        except Exception as exc:
            print(f"Could not resize Roblox via accessibility API: {exc}")
            return False

    @staticmethod
    def _resize_roblox_window_applescript() -> bool:
        script = """
        tell application "System Events"
            set rl to (first process whose name contains "Roblox")
            tell rl
                set position of window 1 to {0, 40}
                set size of window 1 to {1200, 630}
            end tell
        end tell
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as exc:
            print(f"Could not resize Roblox with AppleScript: {exc}")
            return False
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            detail = stderr or stdout or "unknown AppleScript error"
            print(f"Roblox AppleScript resize failed: {detail}")
            return False
        print("Roblox window resized via AppleScript.")
        return True

    def on_overlay_enter(self, callback) -> None:
        self._on_overlay_enter.append(callback)

    def on_main_menu_enter(self, callback) -> None:
        self._on_main_menu_enter.append(callback)

    def on_advanced_enter(self, callback) -> None:
        self._on_advanced_enter.append(callback)

    def resize_roblox_window(self) -> None:
        if self._resize_roblox_window_accessibility():
            return
        self._resize_roblox_window_applescript()

    def _deferred_resize_roblox_window(self) -> None:
        self._pending_roblox_resize = False
        if self.window.stackedWidget.currentIndex() != PAGE_ADVANCED_CREATE:
            return
        self.resize_roblox_window()

    def _stacked_height_for_window(self, window_height: int) -> int:
        status_bar = self.window.statusBar()
        status_height = status_bar.sizeHint().height() if status_bar is not None else 0
        return max(0, window_height - status_height)

    def go_to_page(self, index: int) -> None:
        self.window.stackedWidget.setCurrentIndex(index)

        if index == PAGE_ADVANCED_CREATE:
            if not self.state.editor.frameless_active:
                self.window.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
                self.state.editor.frameless_active = True
            self.window.setGeometry(OVERLAY_POS[0], OVERLAY_POS[1], ADVANCED_CREATE_SIZE[0], ADVANCED_CREATE_SIZE[1])
            self.window.stackedWidget.setGeometry(0, 0, ADVANCED_CREATE_SIZE[0], ADVANCED_CREATE_SIZE[1])
            right_panel = QRegion(QRect(1200, 0, 270, 630))
            bottom_strip = QRegion(QRect(0, 630, 1470, 230))
            self.window.setMask(right_panel.united(bottom_strip))
            self.window.show()
            if not self._pending_roblox_resize:
                self._pending_roblox_resize = True
                QTimer.singleShot(0, self._deferred_resize_roblox_window)
            for callback in self._on_advanced_enter:
                callback()
        else:
            was_frameless = self.state.editor.frameless_active
            if was_frameless:
                self.window.setWindowFlags(Qt.Window)
                self.state.editor.frameless_active = False

            if index == PAGE_OVERLAY:
                avail = self.app.primaryScreen().availableGeometry()
                win_h = min(OVERLAY_SIZE[1], avail.height())
                self.window.setGeometry(avail.x(), avail.y(), OVERLAY_SIZE[0], win_h)
                self.window.stackedWidget.setGeometry(0, 0, OVERLAY_SIZE[0], self._stacked_height_for_window(win_h))
            else:
                self.window.resize(COMPACT_SIZE[0], COMPACT_SIZE[1])
                self.window.stackedWidget.setGeometry(
                    0,
                    0,
                    COMPACT_SIZE[0],
                    self._stacked_height_for_window(COMPACT_SIZE[1]),
                )
                screen = self.app.primaryScreen().geometry()
                x = (screen.width() - COMPACT_SIZE[0]) // 2
                y = (screen.height() - COMPACT_SIZE[1]) // 2
                self.window.move(x, y)

            if was_frameless:
                self.window.show()
                self.window.clearMask()

            if index == PAGE_OVERLAY:
                for callback in self._on_overlay_enter:
                    callback()
            elif index == PAGE_MAIN_MENU:
                for callback in self._on_main_menu_enter:
                    callback()

        print(f"Switched to page {index}")
