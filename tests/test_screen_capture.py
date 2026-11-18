from __future__ import annotations

import numpy as np
import pytest

import macro_app.services.focus_lease_input as focus_lease_module
from macro_app.services.focus_lease_input import FocusLeasePyAutoGUI
from macro_app import constants
from macro_app.services.detection import DetectionService
from macro_app.services.relative_positioning import RelativePositioner, RobloxWindowBounds
from macro_app.services.screen_capture import ScreenCaptureError, ScreenCaptureKitWindowStream


def _deskpad_positioner() -> RelativePositioner:
    return RelativePositioner(
        window_finder=lambda: RobloxWindowBounds(
            left=-1243,
            top=-1,
            right=-43,
            bottom=629,
        ),
        cache_ttl_seconds=0.0,
    )


def test_window_stream_crops_global_negative_region_from_window_frame():
    positioner = _deskpad_positioner()
    stream = ScreenCaptureKitWindowStream(positioner)
    frame = np.zeros((630, 1200, 3), dtype=np.uint8)
    frame[45:78, 405:445] = (11, 22, 33)
    stream._store_frame(frame)

    live_region = positioner.translate_region((405, 85, 445, 118))
    crop = stream.capture_region_bgr(live_region)

    assert crop.shape == (33, 40, 3)
    assert np.all(crop == (11, 22, 33))


def test_window_stream_base_crop_is_independent_of_global_window_position():
    current_bounds = [RobloxWindowBounds(-1243, -1, -43, 629)]
    positioner = RelativePositioner(
        window_finder=lambda: current_bounds[0],
        cache_ttl_seconds=0.0,
    )
    stream = ScreenCaptureKitWindowStream(positioner)
    frame = np.zeros((630, 1200, 3), dtype=np.uint8)
    frame[108:148, 641:718] = (12, 34, 56)
    stream._store_frame(frame)

    first = stream.capture_base_region_bgr(constants.VOTE_BUTTON_REGION)
    current_bounds[0] = RobloxWindowBounds(-900, 80, 300, 710)
    second = stream.capture_base_region_bgr(constants.VOTE_BUTTON_REGION)

    assert np.array_equal(first, second)
    assert np.all(first == (12, 34, 56))


def test_window_stream_rejects_regions_outside_roblox():
    positioner = _deskpad_positioner()
    stream = ScreenCaptureKitWindowStream(positioner)
    stream._store_frame(np.zeros((630, 1200, 3), dtype=np.uint8))

    with pytest.raises(ScreenCaptureError, match="outside Roblox bounds"):
        stream.capture_region_bgr((-1300, -1, -1290, 9))


def test_window_stream_selects_actual_roblox_pid_over_deskpad_viewer_title():
    class _Size:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    class _Frame:
        def __init__(self, width, height):
            self.size = _Size(width, height)

    class _Owner:
        def __init__(self, name, pid):
            self._name = name
            self._pid = pid

        def applicationName(self):
            return self._name

        def processID(self):
            return self._pid

    class _Window:
        def __init__(self, owner, title, width, height):
            self._owner = owner
            self._title = title
            self._frame = _Frame(width, height)

        def owningApplication(self):
            return self._owner

        def title(self):
            return self._title

        def frame(self):
            return self._frame

    roblox = _Window(_Owner("Roblox", 123), "", 1200, 630)
    deskpad_viewer = _Window(_Owner("DeskPad", 456), "Roblox", 1400, 900)

    class _Content:
        @staticmethod
        def windows():
            return [deskpad_viewer, roblox]

    selected = ScreenCaptureKitWindowStream._find_roblox_window(_Content(), 123)

    assert selected is roblox


class _FakeLease:
    def __init__(self, required: bool = True) -> None:
        self.required = required
        self.acquire_calls = 0
        self.release_calls = 0
        self.active = False

    def is_required(self) -> bool:
        return self.required

    def acquire(self) -> bool:
        if self.active:
            return True
        self.acquire_calls += 1
        self.active = self.required
        return self.required

    def release(self) -> None:
        self.release_calls += 1
        self.active = False


class _FakeRawPyAutoGUI:
    def __init__(self) -> None:
        self.calls = []

    def moveTo(self, *args, **kwargs):
        self.calls.append(("moveTo", args, kwargs))

    def click(self, *args, **kwargs):
        self.calls.append(("click", args, kwargs))


class _FakeRelativePyAutoGUI:
    def __init__(self) -> None:
        self.calls = []

    def moveTo(self, *args, **kwargs):
        self.calls.append(("moveTo", args, kwargs))

    def click(self, *args, **kwargs):
        self.calls.append(("click", args, kwargs))


def test_focus_lease_click_uses_exact_translated_unit_coordinate(monkeypatch):
    raw = _FakeRawPyAutoGUI()
    relative = _FakeRelativePyAutoGUI()
    lease = _FakeLease(required=True)
    events = []
    monkeypatch.setattr(
        focus_lease_module,
        "_post_hid_mouse_event",
        lambda kind, x, y, button="left": events.append((kind, x, y, button)),
    )
    wrapper = FocusLeasePyAutoGUI(
        raw,
        relative,
        _deskpad_positioner(),
        lease=lease,
    )

    wrapper.moveTo(389, 604)
    lease.required = False
    wrapper.click()

    expected = (-854, 563)
    assert events == [
        ("move", *expected, "left"),
        ("move", *expected, "left"),
        ("down", *expected, "left"),
        ("up", *expected, "left"),
    ]
    assert raw.calls == []
    assert lease.acquire_calls == 1
    assert lease.release_calls == 1
    assert relative.calls == []


def test_focus_lease_wrapper_preserves_normal_relative_path():
    raw = _FakeRawPyAutoGUI()
    relative = _FakeRelativePyAutoGUI()
    lease = _FakeLease(required=False)
    wrapper = FocusLeasePyAutoGUI(
        raw,
        relative,
        _deskpad_positioner(),
        lease=lease,
    )

    wrapper.moveTo(389, 604)
    wrapper.click()

    assert relative.calls == [
        ("moveTo", (389, 604), {}),
        ("click", (None, None), {}),
    ]
    assert raw.calls == []


def test_focus_lease_translates_target_only_after_activation(monkeypatch):
    raw = _FakeRawPyAutoGUI()
    relative = _FakeRelativePyAutoGUI()
    lease = _FakeLease(required=True)
    translation_states = []
    events = []

    class _Positioner:
        def invalidate_cache(self):
            events.append(("invalidate",))

        def translate_point(self, x, y):
            translation_states.append(lease.active)
            return (-500, 300)

        @staticmethod
        def translate_region(region):
            return region

    monkeypatch.setattr(
        focus_lease_module,
        "_post_hid_mouse_event",
        lambda kind, x, y, button="left": events.append((kind, x, y, button)),
    )
    wrapper = FocusLeasePyAutoGUI(raw, relative, _Positioner(), lease=lease)

    wrapper.moveTo(600, 350)

    assert translation_states == [True]
    assert events == [("invalidate",), ("move", -500, 300, "left")]
    wrapper.release_focus_lease()


def test_appkit_work_is_dispatched_to_main_operation_queue(monkeypatch):
    calls = []

    class _FakeThread:
        @staticmethod
        def isMainThread():
            return False

    class _FakeQueue:
        def addOperationWithBlock_(self, block):
            calls.append("queued")
            block()

    class _FakeOperationQueue:
        @staticmethod
        def mainQueue():
            return _FakeQueue()

    class _FakeAppKit:
        NSThread = _FakeThread
        NSOperationQueue = _FakeOperationQueue

    monkeypatch.setattr(focus_lease_module, "AppKit", _FakeAppKit)

    result = focus_lease_module._call_on_macos_main_thread(lambda: "activated")

    assert result == "activated"
    assert calls == ["queued"]


def test_vote_detection_uses_deskpad_padded_fallback():
    service = DetectionService()
    service._templates_initialized = True
    template = np.array(
        [
            [[0, 20, 40], [20, 40, 60], [40, 60, 80]],
            [[60, 80, 100], [80, 100, 120], [100, 120, 140]],
            [[120, 140, 160], [140, 160, 180], [160, 180, 200]],
        ],
        dtype=np.uint8,
    )
    service._templates["vote_button"] = template

    class _Capture:
        def __init__(self):
            self.regions = []

        def capture_region_bgr(self, region):
            self.regions.append(region)
            left, top, right, bottom = region
            image = np.zeros((bottom - top, right - left, 3), dtype=np.uint8)
            if len(self.regions) == 2:
                image[12:15, 16:19] = template
            return image

        def capture_base_region_bgr(self, region):
            return self.capture_region_bgr(region)

        @staticmethod
        def diagnostics():
            return {"frame_count": 20, "frame_age": 0.01}

    class _PyAutoGUI:
        def __init__(self):
            self.calls = []

        def moveTo(self, x, y):
            self.calls.append(("moveTo", x, y))

        def click(self):
            self.calls.append(("click",))

    capture = _Capture()
    pyautogui = _PyAutoGUI()
    service._runtime_screen_capture = capture
    service._pyautogui = pyautogui

    assert service.detect_and_click_vote_button() is True
    assert len(capture.regions) == 2
    assert capture.regions[0] == constants.VOTE_BUTTON_REGION
    assert "frames=20" in service.vote_probe_summary()
    assert pyautogui.calls[-1] == ("click",)
