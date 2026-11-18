"""Dungeon card selection helpers for starter cards and wave-card priorities."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from mss import mss

from macro_app import constants
from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import RelativePositioner


BASE_DIR = Path(__file__).resolve().parents[2]
DUNGEON_CARDS_DIR = BASE_DIR / "references" / "dungeon_cards"
STARTER_CARDS_DIR = DUNGEON_CARDS_DIR / "starter_cards"
WAVE_CARDS_DIR = DUNGEON_CARDS_DIR / "wave_cards"
ADDITIVE_CARD_REF = DUNGEON_CARDS_DIR / "additive_cards_ref.png"
DUNGEON_PROBE_START_REF = BASE_DIR / "references" / "dungeon_probe_start_ref.png"

CARD_PICKER_REGION = (158, 206, 1023, 393)
ADDITIVE_TRIGGER_REGION = (547, 145, 652, 160)
DUNGEON_PROBE_START_REGION = constants.WAVE_COMPLETED_REGION
WAVE_COUNTER_REGION = (405, 85, 445, 118)
CARD_MATCH_THRESHOLD = 0.92
ADDITIVE_TRIGGER_THRESHOLD = 0.90
DUNGEON_PROBE_START_THRESHOLD = 0.90
WAVE_TRIGGER_TARGETS = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 30}
WAVE_POLL_INTERVAL = 5.0
PROBE_START_POLL_INTERVAL = 0.2
ADDITIVE_POLL_INTERVAL = 0.25
MONITOR_POLL_TICK = 0.05
WAVE_PROBE_LOG_EVERY = 3
PROBE_START_LOG_EVERY = 5
ADDITIVE_PROBE_LOG_EVERY = 5
CARD_CLICK_SETTLE_DELAY = 0.1
CARD_SELECTION_SETTLE_DELAY = 0.5
CARD_SELECTION_RESUME_DELAY = 1.0

STARTER_FALLBACK_CLICK = (600, 340)
STARTER_REFRESH_SEQUENCE = ((21, 650), (967, 324), (533, 415), (596, 405))
STARTER_CLICK_COOLDOWN = 0.5
STARTER_REFRESH_WAIT = 1.5
STARTER_POST_START_WAIT = 5.0


@dataclass(frozen=True)
class DungeonCardSpec:
    label: str
    file_path: Path | None
    kind: str  # buff / debuff / other / starter
    percent_increase: int
    enabled: bool = True


@dataclass(frozen=True)
class CardMatch:
    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


def _wave_card_file(relative_path: str) -> Path:
    return WAVE_CARDS_DIR / relative_path


WAVE_CARD_SPECS: dict[str, DungeonCardSpec] = {
    "Damage (Common)": DungeonCardSpec("Damage (Common)", _wave_card_file("buff/common_damage_ref.png"), "buff", 12),
    "Damage (Uncommon)": DungeonCardSpec("Damage (Uncommon)", _wave_card_file("buff/uncommon_damage_ref.png"), "buff", 18),
    "Cooldown (Common)": DungeonCardSpec("Cooldown (Common)", _wave_card_file("buff/common_cooldown_ref.png"), "buff", 5),
    "Cooldown (Uncommon)": DungeonCardSpec("Cooldown (Uncommon)", _wave_card_file("buff/uncommon_cooldown_ref.png"), "buff", 5),
    "Range (Common)": DungeonCardSpec("Range (Common)", _wave_card_file("buff/common_range_ref.png"), "buff", 10),
    "Range (Uncommon)": DungeonCardSpec("Range (Uncommon)", _wave_card_file("buff/uncommon_range_ref.png"), "buff", 20),
    "Loot (Common)": DungeonCardSpec("Loot (Common)", _wave_card_file("buff/common_loot_ref.png"), "buff", 0),
    "Loot (Uncommon)": DungeonCardSpec("Loot (Uncommon)", _wave_card_file("buff/uncommon_loot_ref.png"), "buff", 0),
    "Slayer (Common)": DungeonCardSpec("Slayer (Common)", _wave_card_file("buff/common_slayer_ref.png"), "buff", 50),
    "Slayer (Uncommon)": DungeonCardSpec("Slayer (Uncommon)", _wave_card_file("buff/uncommon_slayer_ref.png"), "buff", 75),
    "Press It (Uncommon)": DungeonCardSpec("Press It (Uncommon)", _wave_card_file("buff/uncommon_press_it_ref.png"), "buff", 50),
    "Harvest (Super Rare)": DungeonCardSpec("Harvest (Super Rare)", _wave_card_file("buff/harvest_ref.png"), "buff", 100),
    "Strong (Common)": DungeonCardSpec("Strong (Common)", _wave_card_file("debuff/common_strong_ref.png"), "debuff", 35),
    "Strong (Uncommon)": DungeonCardSpec("Strong (Uncommon)", _wave_card_file("debuff/uncommon_strong_ref.png"), "debuff", 55),
    "Strong (Rare)": DungeonCardSpec("Strong (Rare)", _wave_card_file("debuff/rare_strong_ref.png"), "debuff", 75),
    "Champions (Rare)": DungeonCardSpec("Champions (Rare)", _wave_card_file("debuff/champions_ref.png"), "debuff", 75),
    "Fast (Common)": DungeonCardSpec("Fast (Common)", _wave_card_file("debuff/common_fast_ref.png"), "debuff", 35),
    "Fast (Uncommon)": DungeonCardSpec("Fast (Uncommon)", _wave_card_file("debuff/uncommon_fast_ref.png"), "debuff", 55),
    "Fast (Rare)": DungeonCardSpec("Fast (Rare)", None, "debuff", 75, enabled=False),
    "Dodge (Common)": DungeonCardSpec("Dodge (Common)", _wave_card_file("debuff/common_dodge_ref.png"), "debuff", 35),
    "Dodge (Uncommon)": DungeonCardSpec("Dodge (Uncommon)", _wave_card_file("debuff/uncommon_dodge_ref.png"), "debuff", 55),
    "Dodge (Rare)": DungeonCardSpec("Dodge (Rare)", _wave_card_file("debuff/rare_dodge_ref.png"), "debuff", 75),
    "Planning Ahead (Super Rare)": DungeonCardSpec("Planning Ahead (Super Rare)", _wave_card_file("other/planning_ahead_ref.png"), "other", 0),
    "Precise Attack (Super Rare)": DungeonCardSpec("Precise Attack (Super Rare)", _wave_card_file("other/precise_attack_ref.png"), "other", 0),
}

STARTER_CARD_SPECS: dict[str, DungeonCardSpec] = {
    "Money Surge": DungeonCardSpec("Money Surge", STARTER_CARDS_DIR / "money_surge_ref.png", "starter", 0),
    "Fisticuffs": DungeonCardSpec("Fisticuffs", STARTER_CARDS_DIR / "fisticuffs_ref.png", "starter", 0),
    "Kings Burden": DungeonCardSpec("Kings Burden", STARTER_CARDS_DIR / "kings_burden_ref.png", "starter", 0),
    "Limit Break": DungeonCardSpec("Limit Break", STARTER_CARDS_DIR / "limit_break_ref.png", "starter", 0),
}

DUNGEON_PRIORITY_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Buffs",
        (
            "Damage (Common)",
            "Damage (Uncommon)",
            "Cooldown (Common)",
            "Cooldown (Uncommon)",
            "Range (Common)",
            "Range (Uncommon)",
            "Loot (Common)",
            "Loot (Uncommon)",
            "Slayer (Common)",
            "Slayer (Uncommon)",
            "Press It (Uncommon)",
            "Harvest (Super Rare)",
        ),
    ),
    (
        "Debuffs",
        (
            "Strong (Common)",
            "Strong (Uncommon)",
            "Strong (Rare)",
            "Fast (Common)",
            "Fast (Uncommon)",
            "Fast (Rare)",
            "Dodge (Common)",
            "Dodge (Uncommon)",
            "Dodge (Rare)",
        ),
    ),
    (
        "Other",
        (
            "Planning Ahead (Super Rare)",
            "Precise Attack (Super Rare)",
        ),
    ),
)


def get_dungeon_priority_specs() -> list[DungeonCardSpec]:
    return [WAVE_CARD_SPECS[label] for _group, labels in DUNGEON_PRIORITY_GROUPS for label in labels]


def base_card_label(label: str) -> str:
    if "(" not in label:
        return label.strip()
    return label.split("(", 1)[0].strip()


def family_card_specs(label: str) -> list[DungeonCardSpec]:
    target_base = base_card_label(label)
    return [
        spec
        for candidate_label, spec in WAVE_CARD_SPECS.items()
        if base_card_label(candidate_label) == target_base
    ]


class DungeonCardSelector:
    """Template matching helper for dungeon starter and wave card selection."""

    def __init__(self) -> None:
        self._template_cache: dict[tuple[str, float], tuple[np.ndarray, np.ndarray | None]] = {}
        self._screen_capture: mss | None = None
        self._scale_factor: float | None = None
        self._pyautogui = None
        self._relative_positioner: RelativePositioner | None = None
        self._detection_profiler: DetectionProfiler | None = None
        self._runtime_screen_capture = None

    def set_runtime_context(
        self,
        *,
        pyautogui_module=None,
        relative_positioner: RelativePositioner | None = None,
        detection_profiler: DetectionProfiler | None = None,
        screen_capture=None,
    ) -> None:
        self._pyautogui = pyautogui_module
        self._relative_positioner = relative_positioner
        self._detection_profiler = detection_profiler
        self._runtime_screen_capture = screen_capture

    def select_starter_card(self, pyautogui, detection_service, selected_card: str, *, log=None, stop_requested=None) -> bool:
        target_name = str(selected_card).strip()
        target_spec = STARTER_CARD_SPECS.get(target_name)
        if target_spec is None:
            if log:
                log(f"Dungeon starter selection skipped: unsupported card '{selected_card}'")
            return False

        if not self._card_template_available(target_spec):
            if log:
                log(f"Dungeon starter selection skipped: missing reference for '{target_name}'")
            return False

        while not self._should_stop(stop_requested):
            match = self._detect_single_card(target_spec, CARD_PICKER_REGION, CARD_MATCH_THRESHOLD)
            if match is not None:
                self._click_match(pyautogui, CARD_PICKER_REGION, match)
                if log:
                    log(f"Dungeon starter card selected: {target_name} ({match.confidence:.3f})")
                return True

            if log:
                log(f"Dungeon starter card '{target_name}' not found, rerolling...")

            self._move_and_click(pyautogui, *STARTER_FALLBACK_CLICK)
            if self._sleep_with_stop(STARTER_CLICK_COOLDOWN, stop_requested):
                return False
            if not self._wait_for_game_start(detection_service, log=log, stop_requested=stop_requested):
                return False
            if self._sleep_with_stop(STARTER_POST_START_WAIT, stop_requested):
                return False

            for x, y in STARTER_REFRESH_SEQUENCE:
                if self._should_stop(stop_requested):
                    return False
                self._move_and_click(pyautogui, x, y)
                if self._sleep_with_stop(STARTER_CLICK_COOLDOWN, stop_requested):
                    return False
            if self._sleep_with_stop(STARTER_REFRESH_WAIT, stop_requested):
                return False

        return False

    def select_priority_card(
        self,
        pyautogui,
        priority_labels: list[str],
        *,
        buff_total: int,
        debuff_total: int,
        max_buff_enabled: bool,
        max_buff_percent: int,
        max_debuff_enabled: bool,
        max_debuff_percent: int,
        log=None,
        stop_requested=None,
    ) -> tuple[bool, int, int]:
        overflow_candidates: list[tuple[DungeonCardSpec, CardMatch]] = []
        checked_rows: list[str] = []

        for idx, label in enumerate(priority_labels, start=1):
            if self._should_stop(stop_requested):
                return False, buff_total, debuff_total

            spec = WAVE_CARD_SPECS.get(label)
            if spec is None:
                checked_rows.append(f"  {idx}. {label}: missing spec")
                continue
            if not spec.enabled:
                checked_rows.append(f"  {idx}. {label}: disabled")
                continue
            if not self._card_template_available(spec):
                checked_rows.append(f"  {idx}. {label}: missing template")
                continue

            best_match = self._best_card_match(spec, CARD_PICKER_REGION)
            if best_match is None:
                checked_rows.append(f"  {idx}. {label}: no match data")
                continue

            checked_rows.append(f"  {idx}. {label}: conf={best_match.confidence:.3f}")
            if best_match.confidence < CARD_MATCH_THRESHOLD:
                continue

            recorded_spec, recorded_match = self._best_family_match(spec, CARD_PICKER_REGION)
            if recorded_spec is None or recorded_match is None:
                checked_rows.append(f"    -> family scan failed for {base_card_label(label)}")
                continue
            checked_rows.append(
                f"    -> recorded rarity: {recorded_spec.label} "
                f"(conf={recorded_match.confidence:.3f}, percent={recorded_spec.percent_increase}, kind={recorded_spec.kind})"
            )

            if self._would_exceed_limit(
                recorded_spec,
                buff_total,
                debuff_total,
                max_buff_enabled,
                max_buff_percent,
                max_debuff_enabled,
                max_debuff_percent,
            ):
                overflow_candidates.append((recorded_spec, recorded_match))
                continue

            if log:
                log("Dungeon priority scan order:")
                for row in checked_rows:
                    log(row)
            self._click_match(pyautogui, CARD_PICKER_REGION, recorded_match)
            buff_total, debuff_total = self._apply_percent(recorded_spec, buff_total, debuff_total)
            if log:
                log(
                    f"Dungeon wave card selected: {recorded_spec.label} "
                    f"(priority hit: {spec.label} {best_match.confidence:.3f}, "
                    f"recorded: {recorded_match.confidence:.3f}) "
                    f"[buff={buff_total}% debuff={debuff_total}%]"
                )
            return True, buff_total, debuff_total

        if overflow_candidates:
            chosen_spec, chosen_match = min(
                overflow_candidates,
                key=lambda item: (item[0].percent_increase, priority_labels.index(item[0].label)),
            )
            if log:
                log("Dungeon priority scan order:")
                for row in checked_rows:
                    log(row)
            self._click_match(pyautogui, CARD_PICKER_REGION, chosen_match)
            buff_total, debuff_total = self._apply_percent(chosen_spec, buff_total, debuff_total)
            if log:
                log(
                    f"Dungeon wave card fallback selected: {chosen_spec.label} ({chosen_match.confidence:.3f}) "
                    f"[buff={buff_total}% debuff={debuff_total}%]"
                )
            return True, buff_total, debuff_total

        if log:
            if checked_rows:
                log("Dungeon priority scan order:")
                for row in checked_rows:
                    log(row)
            log("Dungeon wave cards detected: no configured priority card found.")
        return False, buff_total, debuff_total

    def _best_family_match(
        self,
        trigger_spec: DungeonCardSpec,
        region: tuple[int, int, int, int],
    ) -> tuple[DungeonCardSpec | None, CardMatch | None]:
        best_spec: DungeonCardSpec | None = None
        best_match: CardMatch | None = None
        for family_spec in family_card_specs(trigger_spec.label):
            if not self._card_template_available(family_spec):
                continue
            match = self._best_card_match(family_spec, region)
            if match is None or match.confidence < CARD_MATCH_THRESHOLD:
                continue
            if best_match is None or match.confidence > best_match.confidence:
                best_spec = family_spec
                best_match = match
        if best_spec is None or best_match is None:
            return trigger_spec, self._best_card_match(trigger_spec, region)
        return best_spec, best_match

    def create_wave_card_monitor(
        self,
        pyautogui,
        wave_number_detector,
        settings: dict,
        *,
        log=None,
        stop_requested=None,
    ) -> "DungeonWaveCardMonitor":
        return DungeonWaveCardMonitor(
            self,
            pyautogui,
            wave_number_detector,
            settings,
            log=log,
            stop_requested=stop_requested,
        )

    def _compute_scale_factor(self) -> float:
        if self._scale_factor is not None:
            return self._scale_factor
        pyautogui_module = self._pyautogui
        if pyautogui_module is None:
            import pyautogui as pyautogui_module

        screenshot = pyautogui_module.screenshot()
        screen_w, _ = pyautogui_module.size()
        self._scale_factor = screenshot.size[0] / screen_w
        return self._scale_factor

    def _get_screen_capture(self) -> mss:
        if self._screen_capture is None:
            self._screen_capture = mss()
        return self._screen_capture

    def _capture_region(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._runtime_screen_capture is not None:
            return self._runtime_screen_capture.capture_base_region_bgr(region)
        if self._relative_positioner is not None:
            region = self._relative_positioner.translate_region(region)
        left, top, right, bottom = region
        shot = self._get_screen_capture().grab(
            {"left": left, "top": top, "width": right - left, "height": bottom - top}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)

    def _load_template(self, spec: DungeonCardSpec, scale_factor: float) -> tuple[np.ndarray, np.ndarray | None] | None:
        if spec.file_path is None or not spec.file_path.exists():
            return None
        cache_key = (str(spec.file_path), round(scale_factor, 3))
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        image = cv2.imread(str(spec.file_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            return None

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

        self._template_cache[cache_key] = (image, mask)
        return image, mask

    def _detect_single_card(
        self,
        spec: DungeonCardSpec,
        region: tuple[int, int, int, int],
        threshold: float,
    ) -> CardMatch | None:
        match = self._best_card_match(spec, region)
        if match is None or match.confidence < threshold:
            return None
        return match

    def _best_card_match(
        self,
        spec: DungeonCardSpec,
        region: tuple[int, int, int, int],
    ) -> CardMatch | None:
        profiler = self._detection_profiler
        if profiler is not None:
            with profiler.track("dungeon_card_match"):
                return self._best_card_match_impl(spec, region)
        return self._best_card_match_impl(spec, region)

    def _best_card_match_impl(
        self,
        spec: DungeonCardSpec,
        region: tuple[int, int, int, int],
    ) -> CardMatch | None:
        if not self._card_template_available(spec):
            return None

        scale_factor = self._compute_scale_factor()
        template_info = self._load_template(spec, scale_factor)
        if template_info is None:
            return None

        template, mask = template_info
        region_bgr = self._capture_region(region)
        if region_bgr.shape[0] < template.shape[0] or region_bgr.shape[1] < template.shape[1]:
            return None

        if mask is not None:
            result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
        else:
            result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        template_h, template_w = template.shape[:2]
        return CardMatch(spec.label, int(max_loc[0]), int(max_loc[1]), template_w, template_h, float(max_val))

    @staticmethod
    def _card_template_available(spec: DungeonCardSpec) -> bool:
        return bool(spec.enabled and spec.file_path is not None and spec.file_path.exists())

    @staticmethod
    def _would_exceed_limit(
        spec: DungeonCardSpec,
        buff_total: int,
        debuff_total: int,
        max_buff_enabled: bool,
        max_buff_percent: int,
        max_debuff_enabled: bool,
        max_debuff_percent: int,
    ) -> bool:
        if spec.kind == "buff" and max_buff_enabled:
            return buff_total + spec.percent_increase > max_buff_percent
        if spec.kind == "debuff" and max_debuff_enabled:
            return debuff_total + spec.percent_increase > max_debuff_percent
        return False

    @staticmethod
    def _apply_percent(spec: DungeonCardSpec, buff_total: int, debuff_total: int) -> tuple[int, int]:
        if spec.kind == "buff":
            buff_total += spec.percent_increase
        elif spec.kind == "debuff":
            debuff_total += spec.percent_increase
        return buff_total, debuff_total

    @staticmethod
    def _move_and_click(pyautogui, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)
        time.sleep(CARD_CLICK_SETTLE_DELAY)
        pyautogui.click()

    @staticmethod
    def _click_match(pyautogui, region: tuple[int, int, int, int], match: CardMatch) -> None:
        click_x = region[0] + match.x + (match.width // 2)
        click_y = region[1] + match.y + (match.height // 2)
        pyautogui.moveTo(click_x, click_y)
        time.sleep(CARD_CLICK_SETTLE_DELAY)
        pyautogui.click()
        time.sleep(0.3)

    @staticmethod
    def _sleep_with_stop(seconds: float, stop_requested) -> bool:
        end = time.time() + seconds
        while time.time() < end:
            if DungeonCardSelector._should_stop(stop_requested):
                return True
            time.sleep(0.1)
        return False

    @staticmethod
    def _should_stop(stop_requested) -> bool:
        return bool(stop_requested and stop_requested())

    @staticmethod
    def _wait_for_game_start(detection_service, *, log=None, stop_requested=None) -> bool:
        if log:
            log("Dungeon starter reroll: waiting for Game Start...")
        while not DungeonCardSelector._should_stop(stop_requested):
            if detection_service.detect_and_click_vote_button():
                if log:
                    log("Dungeon starter reroll: Game Start detected!")
                return True
            time.sleep(0.1)
        return False


class DungeonWaveCardMonitor:
    """Polled handler that picks dungeon wave cards by priority when the UI appears."""

    def __init__(
        self,
        selector: DungeonCardSelector,
        pyautogui,
        wave_number_detector,
        settings: dict,
        *,
        log=None,
        stop_requested=None,
    ) -> None:
        self.selector = selector
        self.pyautogui = pyautogui
        self.wave_number_detector = wave_number_detector
        self.log = log
        self.stop_requested = stop_requested
        self.buff_total = 0
        self.debuff_total = 0
        self.priority_labels = list(settings.get("dungeon_card_priorities", []))
        self.max_buff_enabled = bool(settings.get("dungeon_max_buff_enabled", False))
        self.max_buff_percent = int(settings.get("dungeon_max_buff_percent", 0) or 0)
        self.max_debuff_enabled = bool(settings.get("dungeon_max_debuff_enabled", False))
        self.max_debuff_percent = int(settings.get("dungeon_max_debuff_percent", 0) or 0)
        self._probe_start_spec = DungeonCardSpec(
            "Dungeon Probe Start",
            DUNGEON_PROBE_START_REF,
            "other",
            0,
        )
        self._trigger_spec = DungeonCardSpec("Additive Cards", ADDITIVE_CARD_REF, "other", 0)
        self._last_trigger_at = 0.0
        self._last_wave_probe_at = 0.0
        self._last_probe_at = 0.0
        self._wave_probe_count = 0
        self._probe_start_count = 0
        self._missing_trigger_logged = False
        self._missing_probe_start_logged = False
        self._enabled = bool(self.priority_labels)
        self._probe_count = 0
        self._armed_wave: int | None = None
        self._additive_mode = False
        self._handled_waves: set[int] = set()
        self._last_logged_wave: int | None = None
        self._selection_pending = False
        self._selection_in_progress = False
        self._selection_completed_count = 0
        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._poll_thread: threading.Thread | None = None

    def start(self) -> None:
        if self.log:
            if self._enabled:
                self.log(
                    f"Dungeon wave-card monitor active: wave polling every {WAVE_POLL_INTERVAL:.1f}s, "
                    f"probe-start region={DUNGEON_PROBE_START_REGION}, "
                    f"additive probing every {ADDITIVE_POLL_INTERVAL:.2f}s"
                )
            else:
                self.log("Dungeon wave-card priority watcher skipped: no priorities configured.")
        if not self._enabled:
            return
        self._stop_event.clear()
        if self._poll_thread is None or not self._poll_thread.is_alive():
            self._poll_thread = threading.Thread(
                target=self._poll_loop,
                name="DungeonWaveCardMonitor",
                daemon=True,
            )
            self._poll_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._poll_thread is not None and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=0.5)

    def handle_pending_selection(self) -> bool:
        if self._should_stop():
            return False
        if not self._enabled:
            return True
        if self._poll_thread is None or not self._poll_thread.is_alive():
            if not self._poll_once():
                return False

        with self._state_lock:
            if not self._selection_pending or self._selection_in_progress:
                return True
            self._selection_in_progress = True
            current_wave = self._armed_wave
        if self.log:
            self.log(f"Dungeon additive selection servicing started on macro thread (wave {current_wave}).")

        if self.selector._sleep_with_stop(CARD_SELECTION_SETTLE_DELAY, self._should_stop):
            with self._state_lock:
                self._selection_in_progress = False
            return False
        selected, self.buff_total, self.debuff_total = self.selector.select_priority_card(
            self.pyautogui,
            self.priority_labels,
            buff_total=self.buff_total,
            debuff_total=self.debuff_total,
            max_buff_enabled=self.max_buff_enabled,
            max_buff_percent=self.max_buff_percent,
            max_debuff_enabled=self.max_debuff_enabled,
            max_debuff_percent=self.max_debuff_percent,
            log=self.log,
            stop_requested=self._should_stop,
        )
        if selected:
            if self.selector._sleep_with_stop(CARD_SELECTION_RESUME_DELAY, self._should_stop):
                with self._state_lock:
                    self._selection_in_progress = False
                return False
            with self._state_lock:
                self._last_trigger_at = time.time()
                completed_wave = self._armed_wave
                if self._armed_wave is not None:
                    self._handled_waves.add(self._armed_wave)
                self._armed_wave = None
                self._additive_mode = False
                self._last_wave_probe_at = time.time()
                self._probe_start_count = 0
                self._probe_count = 0
                self._selection_pending = False
                self._selection_in_progress = False
                self._selection_completed_count += 1
            if completed_wave == 30:
                self._enabled = False
                self._stop_event.set()
                if self.log:
                    self.log("Dungeon wave-card monitor completed wave 30 and is now stopping.")
            elif self.log:
                self.log(f"Dungeon additive selection servicing completed for wave {completed_wave}.")
        else:
            with self._state_lock:
                self._selection_in_progress = False
            if self.log:
                self.log(
                    f"Dungeon additive selection servicing did not find a configured card for wave {current_wave}; "
                    "waiting for next interrupt check."
                )
        return not self._should_stop()

    def _should_stop(self) -> bool:
        return bool(self._stop_event.is_set() or (self.stop_requested and self.stop_requested()))

    def selection_completed_count(self) -> int:
        with self._state_lock:
            return self._selection_completed_count

    def wave30_completed(self) -> bool:
        with self._state_lock:
            return 30 in self._handled_waves

    def is_enabled(self) -> bool:
        with self._state_lock:
            return self._enabled

    def has_pending_selection(self) -> bool:
        with self._state_lock:
            return self._selection_pending or self._selection_in_progress

    def _poll_loop(self) -> None:
        while not self._should_stop():
            if not self._poll_once():
                return
            self._stop_event.wait(MONITOR_POLL_TICK)

    def _poll_once(self) -> bool:
        if self._should_stop():
            return False
        if not self._enabled:
            return True
        if not self.selector._card_template_available(self._trigger_spec):
            if self.log and not self._missing_trigger_logged:
                self.log("Dungeon wave-card watcher skipped: missing additive_cards_ref.png")
                self._missing_trigger_logged = True
            self._enabled = False
            return True
        if not self.selector._card_template_available(self._probe_start_spec):
            if self.log and not self._missing_probe_start_logged:
                self.log("Dungeon wave-card watcher skipped: missing dungeon_probe_start_ref.png")
                self._missing_probe_start_logged = True
            self._enabled = False
            return True

        with self._state_lock:
            if self._selection_pending or self._selection_in_progress:
                return True
            armed_wave = self._armed_wave
            additive_mode = self._additive_mode
            last_wave_probe_at = self._last_wave_probe_at
            last_probe_at = self._last_probe_at
            last_trigger_at = self._last_trigger_at

        now = time.time()
        if armed_wave is None:
            if now - last_wave_probe_at < WAVE_POLL_INTERVAL:
                return True
            with self._state_lock:
                self._last_wave_probe_at = now
                self._wave_probe_count += 1
                probe_count = self._wave_probe_count
            current_wave, confidence = self._detect_current_wave()
            if self.log and (
                probe_count == 1
                or current_wave != self._last_logged_wave
                or probe_count % WAVE_PROBE_LOG_EVERY == 0
            ):
                self.log(
                    f"Dungeon wave probe #{probe_count}: wave={current_wave} "
                    f"conf={confidence:.3f}"
                )
                self._last_logged_wave = current_wave
            if (
                current_wave is not None
                and current_wave in WAVE_TRIGGER_TARGETS
                and current_wave not in self._handled_waves
            ):
                with self._state_lock:
                    self._armed_wave = current_wave
                    self._additive_mode = False
                    self._last_probe_at = 0.0
                    self._probe_start_count = 0
                    self._probe_count = 0
                if self.log:
                    self.log(f"Dungeon additive trigger armed for wave {current_wave}. Waiting for probe-start signal...")
            return True

        if not additive_mode:
            if now - last_probe_at < PROBE_START_POLL_INTERVAL:
                return True
            with self._state_lock:
                self._last_probe_at = now
                armed_wave = self._armed_wave
            probe_start_match = self.selector._best_card_match(
                self._probe_start_spec,
                DUNGEON_PROBE_START_REGION,
            )
            probe_start_conf = probe_start_match.confidence if probe_start_match is not None else 0.0
            with self._state_lock:
                self._probe_start_count += 1
                probe_start_count = self._probe_start_count
            if self.log and self._should_log_probe(
                probe_start_count,
                probe_start_conf,
                DUNGEON_PROBE_START_THRESHOLD,
                PROBE_START_LOG_EVERY,
            ):
                self.log(
                    f"Dungeon probe-start check #{probe_start_count} (wave {armed_wave}): "
                    f"conf={probe_start_conf:.3f} threshold={DUNGEON_PROBE_START_THRESHOLD:.3f}"
                )

            if probe_start_match is not None and probe_start_conf >= DUNGEON_PROBE_START_THRESHOLD:
                with self._state_lock:
                    self._additive_mode = True
                    self._last_probe_at = 0.0
                    self._probe_count = 0
                    armed_wave = self._armed_wave
                if self.log:
                    self.log(
                        f"Dungeon probe-start detected for wave {armed_wave} "
                        f"(conf={probe_start_conf:.3f}). Beginning additive scan..."
                    )
            return True

        if now - last_probe_at < ADDITIVE_POLL_INTERVAL:
            return True
        if now - last_trigger_at < 2.0:
            return True

        with self._state_lock:
            self._last_probe_at = now
            armed_wave = self._armed_wave
            self._probe_count += 1
            probe_count = self._probe_count
        best_trigger_match = self.selector._best_card_match(self._trigger_spec, ADDITIVE_TRIGGER_REGION)
        best_conf = best_trigger_match.confidence if best_trigger_match is not None else 0.0
        if self.log and self._should_log_probe(
            probe_count,
            best_conf,
            ADDITIVE_TRIGGER_THRESHOLD,
            ADDITIVE_PROBE_LOG_EVERY,
        ):
            self.log(
                f"Dungeon additive probe #{probe_count} (wave {armed_wave}): "
                f"conf={best_conf:.3f} threshold={ADDITIVE_TRIGGER_THRESHOLD:.3f}"
            )

        if best_trigger_match is None or best_conf < ADDITIVE_TRIGGER_THRESHOLD:
            return True

        with self._state_lock:
            self._selection_pending = True
            armed_wave = self._armed_wave
        if self.log:
            self.log(
                f"Dungeon additive card UI detected for wave {armed_wave} "
                f"(conf={best_conf:.3f}). Resolving card selection..."
            )
            self.log(f"Dungeon additive selection request queued for wave {armed_wave}.")
        return True

    def _detect_current_wave(self) -> tuple[int | None, float]:
        detector = self.wave_number_detector
        if all(
            hasattr(detector, attr)
            for attr in ("ensure_templates_initialized", "create_white_mask", "_detect_number")
        ):
            detector.ensure_templates_initialized()
            screenshot = self.selector._capture_region(WAVE_COUNTER_REGION)
            screenshot_mask = detector.create_white_mask(screenshot)
            white_count = cv2.countNonZero(screenshot_mask)
            if white_count < 10:
                return None, 0.0
            detected, confidence = detector._detect_number(screenshot_mask)
            return detected, confidence
        return detector.detect_current_wave()

    @staticmethod
    def _should_log_probe(count: int, confidence: float, threshold: float, every: int) -> bool:
        return count == 1 or confidence >= threshold or count % every == 0
