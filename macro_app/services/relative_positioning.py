"""Helpers for translating macro coordinates relative to the Roblox window."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

try:
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListExcludeDesktopElements,
        kCGWindowListOptionOnScreenOnly,
    )
except ImportError:  # pragma: no cover - Quartz unavailable on non-macOS test hosts.
    CGWindowListCopyWindowInfo = None
    kCGNullWindowID = 0
    kCGWindowListExcludeDesktopElements = 0
    kCGWindowListOptionOnScreenOnly = 0


BASE_ROBLOX_LEFT = 0
BASE_ROBLOX_TOP = 40
BASE_ROBLOX_RIGHT = 1200
BASE_ROBLOX_BOTTOM = 670


class RelativePositioningError(RuntimeError):
    """Raised when the live Roblox window cannot be resolved."""


def _is_roblox_owner(owner_name: str) -> bool:
    """Match the real Roblox process, never another app with a Roblox-titled window."""
    return str(owner_name or "").strip().lower().startswith("roblox")


@dataclass(frozen=True)
class RobloxWindowBounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def find_roblox_window_bounds() -> RobloxWindowBounds:
    """Return the largest visible Roblox window on screen."""
    if CGWindowListCopyWindowInfo is None:
        raise RelativePositioningError("Relative positioning failed: Quartz window API unavailable")

    windows = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
    )

    candidates: list[tuple[int, int, int, int, int, float]] = []
    for window in windows:
        owner_name = str(window.get("kCGWindowOwnerName", ""))
        if not _is_roblox_owner(owner_name):
            continue

        bounds = window.get("kCGWindowBounds", {})
        left = int(bounds.get("X", 0))
        top = int(bounds.get("Y", 0))
        width = int(bounds.get("Width", 0))
        height = int(bounds.get("Height", 0))
        if width <= 0 or height <= 0:
            continue

        layer = int(window.get("kCGWindowLayer", 0))
        alpha = float(window.get("kCGWindowAlpha", 1.0))
        candidates.append((left, top, width, height, layer, alpha))

    if not candidates:
        raise RelativePositioningError("Relative positioning failed: Roblox window not found")

    left, top, width, height, _, _ = max(
        candidates,
        key=lambda item: (item[2] * item[3], -item[4], item[5]),
    )
    return RobloxWindowBounds(left=left, top=top, right=left + width, bottom=top + height)


def find_roblox_process_id() -> int:
    """Return the PID owning the largest visible Roblox window."""
    if CGWindowListCopyWindowInfo is None:
        raise RelativePositioningError("Relative positioning failed: Quartz window API unavailable")

    windows = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
    )
    candidates: list[tuple[int, int, int, float]] = []
    for window in windows:
        owner_name = str(window.get("kCGWindowOwnerName", ""))
        if not _is_roblox_owner(owner_name):
            continue
        bounds = window.get("kCGWindowBounds", {})
        width = int(bounds.get("Width", 0))
        height = int(bounds.get("Height", 0))
        pid = int(window.get("kCGWindowOwnerPID", 0))
        if width <= 0 or height <= 0 or pid <= 0:
            continue
        layer = int(window.get("kCGWindowLayer", 0))
        alpha = float(window.get("kCGWindowAlpha", 1.0))
        candidates.append((width * height, pid, layer, alpha))
    if not candidates:
        raise RelativePositioningError("Relative positioning failed: Roblox process not found")
    _, pid, _, _ = max(candidates, key=lambda item: (item[0], -item[2], item[3]))
    return pid


class RelativePositioner:
    """Translate base macro coordinates against the live Roblox window."""

    def __init__(
        self,
        *,
        window_finder: Callable[[], RobloxWindowBounds] | None = None,
        cache_ttl_seconds: float = 0.15,
    ) -> None:
        self._window_finder = window_finder or find_roblox_window_bounds
        self._cache_ttl_seconds = max(0.0, float(cache_ttl_seconds))
        self._cached_bounds: RobloxWindowBounds | None = None
        self._cached_bounds_at = 0.0

    def current_bounds(self) -> RobloxWindowBounds:
        now = time.monotonic()
        if (
            self._cached_bounds is not None
            and (now - self._cached_bounds_at) <= self._cache_ttl_seconds
        ):
            return self._cached_bounds
        bounds = self._window_finder()
        self._cached_bounds = bounds
        self._cached_bounds_at = now
        return bounds

    def invalidate_cache(self) -> None:
        """Force the next translation to query Quartz for current window bounds."""
        self._cached_bounds = None
        self._cached_bounds_at = 0.0

    @staticmethod
    def _translate_point_with_bounds(bounds: RobloxWindowBounds, x: int, y: int) -> tuple[int, int]:
        relative_x = x - BASE_ROBLOX_LEFT
        relative_y = y - BASE_ROBLOX_TOP
        return bounds.left + relative_x, bounds.top + relative_y

    def translate_point(self, x: int, y: int) -> tuple[int, int]:
        bounds = self.current_bounds()
        return self._translate_point_with_bounds(bounds, x, y)

    def translate_region(self, region: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        bounds = self.current_bounds()
        left, top = self._translate_point_with_bounds(bounds, region[0], region[1])
        right, bottom = self._translate_point_with_bounds(bounds, region[2], region[3])
        return left, top, right, bottom

    def translate_point_back_to_base(self, x: int, y: int) -> tuple[int, int]:
        bounds = self.current_bounds()
        relative_x = x - bounds.left
        relative_y = y - bounds.top
        return BASE_ROBLOX_LEFT + relative_x, BASE_ROBLOX_TOP + relative_y


def normalize_saved_roblox_point(
    positioner: RelativePositioner | None,
    x: int,
    y: int,
) -> tuple[int, int, bool]:
    """Convert a legacy global point when it maps inside the live Roblox window."""
    x = int(x)
    y = int(y)
    if positioner is None:
        return x, y, False
    if BASE_ROBLOX_LEFT <= x <= BASE_ROBLOX_RIGHT and BASE_ROBLOX_TOP <= y <= BASE_ROBLOX_BOTTOM:
        return x, y, False
    base_x, base_y = positioner.translate_point_back_to_base(x, y)
    if (
        BASE_ROBLOX_LEFT <= base_x <= BASE_ROBLOX_RIGHT
        and BASE_ROBLOX_TOP <= base_y <= BASE_ROBLOX_BOTTOM
    ):
        return base_x, base_y, True
    return x, y, False


class RelativePyAutoGUI:
    """Proxy pyautogui while translating coordinates against the Roblox window."""

    def __init__(self, raw_module, positioner: RelativePositioner) -> None:
        self._raw = raw_module
        self._positioner = positioner

    def translate_point(self, x: int, y: int) -> tuple[int, int]:
        return self._positioner.translate_point(x, y)

    def translate_region(self, region: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return self._positioner.translate_region(region)

    def moveTo(self, x, y=None, *args, **kwargs):
        if y is None:
            return self._raw.moveTo(x, *args, **kwargs)
        live_x, live_y = self._positioner.translate_point(int(x), int(y))
        return self._raw.moveTo(live_x, live_y, *args, **kwargs)

    def click(self, x=None, y=None, *args, **kwargs):
        if x is not None and y is not None:
            live_x, live_y = self._positioner.translate_point(int(x), int(y))
            return self._raw.click(live_x, live_y, *args, **kwargs)
        return self._raw.click(*args, **kwargs)

    def screenshot(self, region=None, *args, **kwargs):
        if region is None:
            return self._raw.screenshot(*args, **kwargs)

        left, top, width, height = region
        live_left, live_top = self._positioner.translate_point(int(left), int(top))
        return self._raw.screenshot(region=(live_left, live_top, int(width), int(height)), *args, **kwargs)

    def moveRel(self, xOffset=None, yOffset=None, *args, **kwargs):
        return self._raw.moveRel(xOffset, yOffset, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._raw, name)
