import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("cv2")

from macro_app.services.macro_execution import MacroExecutionContext, MacroExecutionService
from macro_app.services.relative_positioning import RelativePositioner, RobloxWindowBounds
from wave_number_detector import YEN_REGION


class _FakeWaveDetector:
    def __init__(self, detections):
        self._detections = list(detections)
        self.detect_calls = 0
        self.translator = None

    def set_region_translator(self, translator):
        self.translator = translator

    def detect_yen_amount(self):
        self.detect_calls += 1
        if self.detect_calls <= len(self._detections):
            return self._detections[self.detect_calls - 1]
        return self._detections[-1]


class _FakeDetection:
    def __init__(self, vote_after=None):
        self.vote_after = vote_after
        self.calls = 0

    def detect_and_click_vote_button(self):
        self.calls += 1
        return self.vote_after is not None and self.calls >= self.vote_after


class _FakePyAutoGui:
    def __init__(self):
        self.calls = []

    def moveTo(self, x, y):
        self.calls.append(("moveTo", x, y))

    def click(self):
        self.calls.append(("click",))

    def mouseDown(self, *, button):
        self.calls.append(("mouseDown", button))

    def mouseUp(self, *, button):
        self.calls.append(("mouseUp", button))


def test_wait_yen_refreshes_relative_bounds_every_poll(monkeypatch):
    bounds_calls = {"count": 0}

    def _counted_bounds():
        bounds_calls["count"] += 1
        return RobloxWindowBounds(left=200, top=140, right=1400, bottom=770)

    detector = _FakeWaveDetector([(50, 0.82), (125, 0.91)])
    positioner = RelativePositioner(window_finder=_counted_bounds)
    context = MacroExecutionContext(
        detection=None,
        wave_number_detector=detector,
        pyautogui=None,
        stop_requested=lambda: False,
        relative_positioner=positioner,
    )
    service = MacroExecutionService()

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._wait_yen({"amount": 100}, context) is True
    assert detector.detect_calls == 2
    assert bounds_calls["count"] >= 1
    assert bounds_calls["count"] <= 2
    assert detector.translator is not None


def test_wait_yen_stays_on_base_region_when_relative_positioning_is_disabled(monkeypatch):
    detector = _FakeWaveDetector([(40, 0.74), (120, 0.88)])
    detector.clear_calls = 0

    def _clear_region_translator():
        detector.translator = None
        detector.clear_calls += 1

    detector.clear_region_translator = _clear_region_translator
    context = MacroExecutionContext(
        detection=None,
        wave_number_detector=detector,
        pyautogui=None,
        stop_requested=lambda: False,
        relative_positioner=None,
    )
    service = MacroExecutionService()

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._wait_yen({"amount": 100}, context) is True
    assert detector.detect_calls == 2
    assert detector.translator is None
    assert detector.clear_calls == 2


def test_yen_detection_region_matches_calibrated_runtime_region():
    assert YEN_REGION == (527, 535, 663, 558)


def test_wait_start_continues_polling_until_stopped(monkeypatch):
    logs = []
    statuses = []
    polls = {"count": 0}

    def _stop_requested():
        polls["count"] += 1
        return polls["count"] > 305

    context = MacroExecutionContext(
        detection=_FakeDetection(vote_after=None),
        wave_number_detector=None,
        pyautogui=None,
        stop_requested=_stop_requested,
        log=logs.append,
        status_callback=statuses.append,
    )
    service = MacroExecutionService()

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._wait_start(context) is False
    assert logs == ["Waiting for Game Start..."]
    assert statuses == ["Waiting for Game Start..."]
    assert context.detection.calls > 1


def test_wait_start_returns_true_when_vote_button_is_detected(monkeypatch):
    logs = []
    statuses = []
    context = MacroExecutionContext(
        detection=_FakeDetection(vote_after=3),
        wave_number_detector=None,
        pyautogui=None,
        stop_requested=lambda: False,
        log=logs.append,
        status_callback=statuses.append,
    )
    service = MacroExecutionService()
    context.record_action = lambda _action: None

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._wait_start(context) is True
    assert "Game Start detected!" in logs
    assert "Game Start detected!" in statuses


def test_run_click_uses_explicit_right_mouse_button(monkeypatch):
    pyautogui = _FakePyAutoGui()
    context = MacroExecutionContext(
        detection=None,
        wave_number_detector=None,
        pyautogui=pyautogui,
        stop_requested=lambda: False,
    )
    context.record_action = lambda _action: None
    service = MacroExecutionService()

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._run_click(context, 100, 200, button="right") is True
    assert pyautogui.calls == [
        ("moveTo", 100, 200),
        ("mouseDown", "right"),
        ("mouseUp", "right"),
    ]


def test_run_click_can_service_interrupt_during_preclick_settle(monkeypatch):
    pyautogui = _FakePyAutoGui()
    interrupt_events = []
    call_counter = {"count": 0}
    selection_count = {"value": 0}

    def _interrupt_handler():
        call_counter["count"] += 1
        if call_counter["count"] == 2:
            interrupt_events.append("selection-handled")
            selection_count["value"] += 1
        return True

    context = MacroExecutionContext(
        detection=None,
        wave_number_detector=None,
        pyautogui=pyautogui,
        stop_requested=lambda: False,
        interrupt_handler=_interrupt_handler,
        interrupt_state_getter=lambda: selection_count["value"],
    )
    context.record_action = lambda _action: None
    service = MacroExecutionService()

    monkeypatch.setattr("macro_app.services.macro_execution.time.sleep", lambda *_args, **_kwargs: None)

    assert service._run_click(context, 100, 200, button="left") is True
    assert interrupt_events == ["selection-handled"]
    assert pyautogui.calls == [
        ("moveTo", 100, 200),
        ("moveTo", 100, 200),
        ("click",),
    ]


def test_place_normalizes_legacy_deskpad_global_placement(monkeypatch):
    positioner = RelativePositioner(
        window_finder=lambda: RobloxWindowBounds(-1246, -7, -46, 623),
        cache_ttl_seconds=0.0,
    )
    logs = []
    context = MacroExecutionContext(
        detection=None,
        wave_number_detector=None,
        pyautogui=None,
        stop_requested=lambda: False,
        relative_positioner=positioner,
        log=logs.append,
    )
    service = MacroExecutionService()
    clicks = []
    monkeypatch.setattr(service, "_run_click", lambda _context, x, y, **_kwargs: clicks.append((x, y)) or True)

    completed = service._place(
        {"cmd": "place", "slot": 1, "placement_index": 0},
        {1: {"placements": [[-543, 335]]}},
        context,
    )

    assert completed is True
    assert clicks == [(389, 604), (703, 382), (360, 250)]
    assert any("legacy DeskPad placement normalized" in message for message in logs)
