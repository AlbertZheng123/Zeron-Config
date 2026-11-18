import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.services.dungeon_card_selection import (
    ADDITIVE_TRIGGER_REGION,
    DUNGEON_PROBE_START_REGION,
    STARTER_CLICK_COOLDOWN,
    STARTER_FALLBACK_CLICK,
    STARTER_REFRESH_SEQUENCE,
    DungeonCardSelector,
    DungeonWaveCardMonitor,
)


class _DummyPyAutoGui:
    def __init__(self):
        self.clicks = []

    def moveTo(self, x, y):
        self.clicks.append(("moveTo", x, y))

    def click(self):
        self.clicks.append(("click",))


class _FakeWaveDetector:
    def __init__(self, wave=None, confidence=0.0):
        self.wave = wave
        self.confidence = confidence

    def detect_current_wave(self):
        return self.wave, self.confidence


class _FakeSelector:
    def __init__(self):
        self.match_calls = []

    def _card_template_available(self, _spec):
        return True

    def _best_card_match(self, spec, region):
        self.match_calls.append((spec.label, region))
        return None

    def _sleep_with_stop(self, seconds, _stop_requested):
        raise AssertionError(f"monitor should not sleep in non-blocking poll path (got {seconds})")

    def select_priority_card(self, *_args, **_kwargs):
        raise AssertionError("selection should not run before additive card UI is detected")


def test_starter_reroll_waits_between_each_restart_click(monkeypatch):
    selector = DungeonCardSelector()
    pyautogui = _DummyPyAutoGui()
    sleeps = []

    monkeypatch.setattr(selector, "_card_template_available", lambda _spec: True)
    monkeypatch.setattr(selector, "_detect_single_card", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(selector, "_wait_for_game_start", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(selector, "_sleep_with_stop", lambda seconds, _stop_requested: sleeps.append(seconds) or False)

    def _stop_after_one_cycle(_stop_requested):
        return len(sleeps) >= 1 + len(STARTER_REFRESH_SEQUENCE) + 2

    monkeypatch.setattr(selector, "_should_stop", _stop_after_one_cycle)

    assert selector.select_starter_card(pyautogui, detection_service=None, selected_card="Money Surge") is False

    expected_clicks = [STARTER_FALLBACK_CLICK, *STARTER_REFRESH_SEQUENCE]
    actual_clicks = [entry[1:] for entry in pyautogui.clicks if entry[0] == "moveTo"]
    assert actual_clicks == expected_clicks
    cooldown_sleeps = [seconds for seconds in sleeps if seconds == STARTER_CLICK_COOLDOWN]
    assert cooldown_sleeps == [STARTER_CLICK_COOLDOWN] * (1 + len(STARTER_REFRESH_SEQUENCE))


def test_wave_monitor_probe_start_poll_is_non_blocking(monkeypatch):
    selector = _FakeSelector()
    monitor = DungeonWaveCardMonitor(
        selector,
        pyautogui=None,
        wave_number_detector=_FakeWaveDetector(),
        settings={"dungeon_card_priorities": ["Damage (Common)"]},
    )
    monitor._armed_wave = 2
    monitor._additive_mode = False
    monitor._last_probe_at = 0.0

    monkeypatch.setattr("macro_app.services.dungeon_card_selection.time.time", lambda: 100.0)
    monkeypatch.setattr("macro_app.services.dungeon_card_selection.time.sleep", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("sleep should not be called")))

    assert monitor.handle_pending_selection() is True
    assert selector.match_calls == [("Dungeon Probe Start", DUNGEON_PROBE_START_REGION)]


def test_wave_monitor_additive_probe_is_non_blocking_until_ui_detected(monkeypatch):
    selector = _FakeSelector()
    monitor = DungeonWaveCardMonitor(
        selector,
        pyautogui=None,
        wave_number_detector=_FakeWaveDetector(),
        settings={"dungeon_card_priorities": ["Damage (Common)"]},
    )
    monitor._armed_wave = 2
    monitor._additive_mode = True
    monitor._last_probe_at = 0.0
    monitor._last_trigger_at = 0.0

    monkeypatch.setattr("macro_app.services.dungeon_card_selection.time.time", lambda: 100.0)
    monkeypatch.setattr("macro_app.services.dungeon_card_selection.time.sleep", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("sleep should not be called")))

    assert monitor.handle_pending_selection() is True
    assert selector.match_calls == [("Additive Cards", ADDITIVE_TRIGGER_REGION)]


def test_wave_monitor_additive_probe_counter_resets_when_wave_arms(monkeypatch):
    selector = _FakeSelector()
    monitor = DungeonWaveCardMonitor(
        selector,
        pyautogui=None,
        wave_number_detector=_FakeWaveDetector(wave=2, confidence=0.94),
        settings={"dungeon_card_priorities": ["Damage (Common)"]},
    )
    monitor._probe_count = 4
    monitor._last_wave_probe_at = 0.0

    monkeypatch.setattr("macro_app.services.dungeon_card_selection.time.time", lambda: 100.0)

    assert monitor._poll_once() is True
    assert monitor._armed_wave == 2
    assert monitor._probe_count == 0
    assert monitor._probe_start_count == 0


def test_wave_monitor_starts_background_polling_without_handle_calls(monkeypatch):
    selector = _FakeSelector()
    monitor = DungeonWaveCardMonitor(
        selector,
        pyautogui=None,
        wave_number_detector=_FakeWaveDetector(),
        settings={"dungeon_card_priorities": ["Damage (Common)"]},
    )
    call_count = {"value": 0}

    def _fake_poll_once():
        call_count["value"] += 1
        if call_count["value"] >= 3:
            monitor._stop_event.set()
        return True

    monkeypatch.setattr(monitor, "_poll_once", _fake_poll_once)

    monitor.start()
    deadline = time.time() + 1.0
    while call_count["value"] < 3 and time.time() < deadline:
        time.sleep(0.02)
    monitor.stop()

    assert call_count["value"] >= 3
