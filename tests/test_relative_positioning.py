import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import macro_app.services.relative_positioning as relative_positioning_module
from macro_app.services.relative_positioning import (
    RelativePositioner,
    RobloxWindowBounds,
    find_roblox_process_id,
    find_roblox_window_bounds,
    normalize_saved_roblox_point,
)


def _quartz_window(owner, title, pid, x, y, width, height):
    return {
        "kCGWindowOwnerName": owner,
        "kCGWindowName": title,
        "kCGWindowOwnerPID": pid,
        "kCGWindowBounds": {
            "X": x,
            "Y": y,
            "Width": width,
            "Height": height,
        },
        "kCGWindowLayer": 0,
        "kCGWindowAlpha": 1.0,
    }


def test_window_lookup_ignores_larger_deskpad_window_titled_roblox(monkeypatch):
    windows = [
        _quartz_window("DeskPad", "Roblox", 456, -1280, 0, 1280, 720),
        _quartz_window("Roblox", "", 123, 45, 88, 1200, 630),
    ]
    monkeypatch.setattr(
        relative_positioning_module,
        "CGWindowListCopyWindowInfo",
        lambda *_args: windows,
    )

    assert find_roblox_window_bounds() == RobloxWindowBounds(45, 88, 1245, 718)
    assert find_roblox_process_id() == 123


def test_relative_positioner_caches_live_bounds_briefly(monkeypatch):
    calls = {"count": 0}

    def _finder():
        calls["count"] += 1
        return RobloxWindowBounds(left=10, top=20, right=1210, bottom=690)

    time_values = iter([100.0, 100.05, 100.10, 100.30])
    monkeypatch.setattr("macro_app.services.relative_positioning.time.monotonic", lambda: next(time_values))

    positioner = RelativePositioner(window_finder=_finder, cache_ttl_seconds=0.15)

    first = positioner.current_bounds()
    second = positioner.current_bounds()
    third = positioner.current_bounds()
    fourth = positioner.current_bounds()

    assert first == second == third == fourth
    assert calls["count"] == 2


def test_relative_positioner_cache_can_be_invalidated(monkeypatch):
    bounds = [RobloxWindowBounds(10, 20, 1210, 650)]
    positioner = RelativePositioner(window_finder=lambda: bounds[0], cache_ttl_seconds=10.0)

    assert positioner.translate_point(100, 100) == (110, 80)
    bounds[0] = RobloxWindowBounds(-1240, 0, -40, 630)
    assert positioner.translate_point(100, 100) == (110, 80)

    positioner.invalidate_cache()
    assert positioner.translate_point(100, 100) == (-1140, 60)


def test_legacy_deskpad_global_point_is_normalized_to_base_coordinates():
    positioner = RelativePositioner(
        window_finder=lambda: RobloxWindowBounds(-1246, -7, -46, 623),
        cache_ttl_seconds=0.0,
    )

    assert normalize_saved_roblox_point(positioner, -543, 335) == (703, 382, True)
    assert normalize_saved_roblox_point(positioner, 703, 382) == (703, 382, False)
