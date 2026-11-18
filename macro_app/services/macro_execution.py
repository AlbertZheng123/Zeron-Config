"""Macro execution service with injected dependencies."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import cv2
import macro_json
import numpy as np
from mss import mss

from macro_app.constants import REFERENCES_DIR, UNIT_COORDINATES
from macro_app.services.ability_steps import AbilityStepService
from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import (
    RelativePositioner,
    RelativePositioningError,
    normalize_saved_roblox_point,
)

PRIORITY_CLICK_POINT = (161, 423)
PRIORITY_CLICK_COUNTS = {
    "First": 0,
    "Closest": 1,
    "Last": 2,
    "Strongest": 3,
    "Weakest": 4,
    "Bosses": 5,
}
UNIT_PLACED_VERIFY_REGION = (346, 235, 379, 266)
UNIT_PLACED_REF = Path(REFERENCES_DIR) / "unit_placed_ref.png"
UNIT_PLACED_THRESHOLD = 0.90
UNIT_PLACED_TRIES = 3


@dataclass
class MacroExecutionContext:
    detection: Any
    wave_number_detector: Any
    pyautogui: Any
    stop_requested: Callable[[], bool]
    units: Any | None = None
    interrupt_handler: Callable[[], bool] | None = None
    interrupt_state_getter: Callable[[], int] | None = None
    status_callback: Callable[[str], None] | None = None
    log: Callable[[str], None] | None = None
    check_placed: bool = False
    relative_positioner: RelativePositioner | None = None
    wait_between_clicks: float = 0.2
    wait_between_key_presses: float = 0.2
    wait_between_steps: float = 0.0
    pending_action_wait_type: str | None = None
    last_completed_step_action_type: str | None = None
    apply_initial_step_wait: bool = False
    detection_profiler: DetectionProfiler | None = None
    event_callback: Callable[[str, dict], None] | None = None
    debug_console_mode: bool = False
    screen_capture: Any | None = None
    _last_interrupt_state_seen: int = 0
    _interrupt_serviced_since_last_action: bool = False

    def __post_init__(self) -> None:
        if self.interrupt_state_getter is not None:
            self._last_interrupt_state_seen = int(self.interrupt_state_getter())

    def can_continue(self) -> bool:
        if self.stop_requested():
            return False
        if self.interrupt_handler is None:
            return True
        can_continue = bool(self.interrupt_handler())
        if self.interrupt_state_getter is not None:
            current_state = int(self.interrupt_state_getter())
            if current_state != self._last_interrupt_state_seen:
                self._last_interrupt_state_seen = current_state
                self._interrupt_serviced_since_last_action = True
        return can_continue

    def consume_interrupt_service_flag(self) -> bool:
        serviced = self._interrupt_serviced_since_last_action
        self._interrupt_serviced_since_last_action = False
        return serviced

    def sleep_interruptibly(self, seconds: float) -> bool:
        seconds = max(0.0, float(seconds))
        elapsed = 0.0
        while elapsed < seconds:
            if not self.can_continue():
                return False
            sleep_time = min(0.05, seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
        return True

    def start_step(self, previous_step_action_type: str | None) -> bool:
        self.pending_action_wait_type = None
        if previous_step_action_type == "click":
            if not self.sleep_interruptibly(self.wait_between_clicks):
                return False
        elif previous_step_action_type == "key":
            if not self.sleep_interruptibly(self.wait_between_key_presses):
                return False
        if not self.sleep_interruptibly(self.wait_between_steps):
            return False
        return True

    def wait_before_action(self) -> bool:
        if self.pending_action_wait_type == "click":
            if not self.sleep_interruptibly(self.wait_between_clicks):
                return False
        elif self.pending_action_wait_type == "key":
            if not self.sleep_interruptibly(self.wait_between_key_presses):
                return False
        self.pending_action_wait_type = None
        return True

    def record_action(self, action_type: str) -> None:
        self.pending_action_wait_type = action_type

    def finish_step(self) -> str | None:
        self.last_completed_step_action_type = self.pending_action_wait_type
        self.pending_action_wait_type = None
        return self.last_completed_step_action_type


class MacroExecutionService:
    """Execute macro steps using injected services."""

    def __init__(self) -> None:
        self.ability_steps = AbilityStepService()
        self._screen_capture: mss | None = None
        self._unit_placed_template_cache: tuple[np.ndarray, np.ndarray | None] | None = None
        self._current_relative_positioner: RelativePositioner | None = None
        self._current_screen_capture = None

    def execute_steps(self, order, units, context: MacroExecutionContext) -> bool:
        self._current_relative_positioner = context.relative_positioner
        self._current_screen_capture = context.screen_capture
        self.ability_steps.set_detection_profiler(context.detection_profiler)
        self.ability_steps.set_screen_capture(context.screen_capture)
        try:
            previous_step_action_type = context.last_completed_step_action_type
            for index, instruction in enumerate(order):
                if (
                    (index == 0 and context.apply_initial_step_wait)
                    or index > 0
                ) and not context.start_step(previous_step_action_type):
                    return False
                if not self._process_interrupts(context):
                    print("Macro stopped by user")
                    return False

                cmd = instruction["cmd"]
                step_desc = macro_json.format_step_display(instruction, units)
                step_label = f"{step_desc[0]}: {step_desc[1]}"

                if context.status_callback:
                    context.status_callback(f"Step {index + 1}: {step_label}")

                print(f"Executing: {step_label}")
                if context.log:
                    context.log(f"Step {index + 1}/{len(order)}: {step_label}")

                if cmd == "click":
                    if not self._run_click(
                        context,
                        instruction["x"],
                        instruction["y"],
                        button=instruction.get("button", "left"),
                    ):
                        return False
                elif cmd == "wait_seconds":
                    if not self._wait_seconds(instruction.get("seconds", 1.0), context):
                        return False
                elif cmd == "wait_wave":
                    if not self._wait_wave(instruction, context):
                        return False
                elif cmd == "wait_start":
                    if not self._wait_start(context):
                        return False
                elif cmd == "wait_yen":
                    if not self._wait_yen(instruction, context):
                        return False
                elif cmd == "key_press":
                    if not self._key_press(instruction, context):
                        return False
                elif cmd == "key_hold":
                    if not self._key_hold(instruction, context):
                        return False
                elif cmd == "place":
                    if not self._place(instruction, units, context):
                        return False
                elif cmd == "upgrade":
                    if not self._upgrade(instruction, units, context):
                        return False
                elif cmd == "sell":
                    if not self._sell(instruction, units, context):
                        return False
                elif cmd == "priority":
                    if not self._priority(instruction, units, context):
                        return False
                elif cmd == "ability_main":
                    if not self.ability_steps.execute_main(instruction, context):
                        return False
                elif cmd == "ability_skele_king":
                    if not self.ability_steps.execute_skele_king(context):
                        return False
                elif cmd == "ability_ainz_arcane":
                    if not self.ability_steps.execute_ainz_arcane(instruction, context):
                        return False
                elif cmd == "ability_ainz_caloric":
                    if not self.ability_steps.execute_ainz_caloric(instruction, context):
                        return False
                else:
                    print(f"Unknown command: {cmd}")

                previous_step_action_type = context.finish_step()

            return True
        finally:
            self.ability_steps.set_detection_profiler(None)
            self.ability_steps.set_screen_capture(None)
            self._current_relative_positioner = None
            self._current_screen_capture = None

    def _run_click(self, context: MacroExecutionContext, x: int, y: int, *, button: str = "left") -> bool:
        if not context.wait_before_action():
            return False
        if not self._process_interrupts(context):
            return False
        while True:
            context.pyautogui.moveTo(x, y)
            if not context.sleep_interruptibly(0.2):
                return False
            if not context.consume_interrupt_service_flag():
                break
        normalized_button = "right" if str(button).lower() == "right" else "left"
        if normalized_button == "right":
            context.pyautogui.mouseDown(button="right")
            if not context.sleep_interruptibly(0.05):
                context.pyautogui.mouseUp(button="right")
                return False
            context.pyautogui.mouseUp(button="right")
        else:
            context.pyautogui.click()
        context.record_action("click")
        return True

    @staticmethod
    def _process_interrupts(context: MacroExecutionContext) -> bool:
        return context.can_continue()

    def _wait_seconds(self, seconds: float, context: MacroExecutionContext) -> bool:
        elapsed = 0.0
        while elapsed < seconds:
            if not self._process_interrupts(context):
                return False
            sleep_time = min(0.1, seconds - elapsed)
            if not context.sleep_interruptibly(sleep_time):
                return False
            elapsed += sleep_time
        return True

    def _wait_wave(self, instruction: dict, context: MacroExecutionContext) -> bool:
        target_wave = instruction.get("wave", 0)
        print(f"Waiting for Wave {target_wave} to appear...")
        if context.log:
            context.log(f"Waiting for Wave {target_wave}...")
        if context.status_callback:
            context.status_callback(f"Waiting for Wave {target_wave}...")

        def wait_check() -> bool:
            return not self._process_interrupts(context)

        wave_found = context.wave_number_detector.wait_for_wave(
            target_wave,
            check_stop_callback=wait_check,
        )
        if not wave_found:
            return False

        print(f"Wave {target_wave} number found!")
        if context.log:
            context.log(f"Wave {target_wave} number found. Waiting for completion...")
        if context.status_callback:
            context.status_callback(f"Wave {target_wave} found. Waiting for completion...")
        print(f"Wave {target_wave} detected! Now waiting for wave to complete...")
        result = context.detection.wait_for_wave_completed(check_stop_fn=wait_check)
        if result == "failed":
            print("Wave failed (replay button detected)")
            return False
        if result == "stopped" or context.stop_requested():
            print("Macro stopped during wave wait")
            return False

        if context.log:
            context.log(f"Wave {target_wave} completed indicator found.")
        if context.status_callback:
            context.status_callback(f"Wave {target_wave} completed indicator found.")
        print(f"Wave {target_wave} completed!")
        if context.log:
            context.log(f"Wave {target_wave} completed!")
        if context.status_callback:
            context.status_callback(f"Wave {target_wave} completed!")
        if context.event_callback is not None:
            context.event_callback("stage_complete", {"wave": target_wave})
        return True

    def _wait_start(self, context: MacroExecutionContext) -> bool:
        print("Waiting for game start (detecting vote button)...")
        if context.log:
            context.log("Waiting for Game Start...")
        if context.status_callback:
            context.status_callback("Waiting for Game Start...")

        attempts = 0
        while True:
            if not self._process_interrupts(context):
                return False
            attempts += 1
            if context.detection.detect_and_click_vote_button():
                context.record_action("click")
                print("Vote button found and clicked!")
                if context.log:
                    context.log("Game Start detected!")
                if context.status_callback:
                    context.status_callback("Game Start detected!")
                return True
            if attempts % 50 == 0:
                probe_summary = getattr(context.detection, "vote_probe_summary", lambda: "unavailable")()
                if probe_summary != "unavailable":
                    print(f"Vote button not found yet ({probe_summary})")
                    if context.log:
                        context.log(f"Game Start probe: {probe_summary}")
                        save_snapshot = getattr(context.detection, "save_vote_debug_snapshot", None)
                        if callable(save_snapshot):
                            snapshot_dir = save_snapshot()
                            if snapshot_dir:
                                context.log(f"Game Start debug capture: {snapshot_dir}")
                    if context.status_callback:
                        context.status_callback("Waiting for Game Start...")
            if not context.sleep_interruptibly(0.1):
                return False

    def _wait_yen(self, instruction: dict, context: MacroExecutionContext) -> bool:
        target_yen = instruction.get("amount", 0)
        print(f"Waiting for Yen >= {target_yen:,}...")
        if context.log:
            context.log(f"Waiting for Yen >= {target_yen:,}...")
        if context.status_callback:
            context.status_callback(f"Waiting for Yen >= {target_yen:,}...")

        yen_positioner = context.relative_positioner

        while True:
            if not self._process_interrupts(context):
                return False

            if yen_positioner is not None:
                try:
                    # Re-query live Roblox bounds on every poll so OCR regions track window moves.
                    yen_positioner.current_bounds()
                    context.wave_number_detector.set_region_translator(yen_positioner.translate_region)
                except RelativePositioningError:
                    if context.relative_positioner is not None:
                        raise
                    context.wave_number_detector.clear_region_translator()
            else:
                context.wave_number_detector.clear_region_translator()

            try:
                detected, confidence, digit_details = context.wave_number_detector.detect_yen_amount(include_details=True)
            except TypeError:
                detected, confidence = context.wave_number_detector.detect_yen_amount()
                digit_details = []
            digit_summary = (
                ", ".join(
                    f"{detail['digit']}:{detail['confidence']:.3f}"
                    for detail in digit_details
                )
                if digit_details
                else "none"
            )
            if detected is not None:
                if context.debug_console_mode:
                    message = (
                        f"[macro_execution] Yen poll: detected={detected:,} "
                        f"target={target_yen:,} confidence={confidence:.3f} digits=[{digit_summary}]"
                    )
                    print(message)
                    if context.log:
                        context.log(message)
                if detected >= target_yen:
                    break
            else:
                if context.debug_console_mode:
                    message = (
                        f"[macro_execution] Yen poll: detected=None "
                        f"target={target_yen:,} confidence={confidence:.3f} digits=[{digit_summary}]"
                    )
                    print(message)
                    if context.log:
                        context.log(message)

            if not context.sleep_interruptibly(0.5):
                return False

        print(f"Yen target {target_yen:,} reached!")
        if context.log:
            context.log(f"Yen target {target_yen:,} reached!")
        if context.status_callback:
            context.status_callback(f"Yen target {target_yen:,} reached!")
        return True

    @staticmethod
    def _key_press(instruction: dict, context: MacroExecutionContext) -> bool:
        key = instruction.get("key", "t")
        times = instruction.get("times", 1)
        for _ in range(times):
            if not MacroExecutionService._press_key(context, key):
                return False
        return True

    @staticmethod
    def _key_hold(instruction: dict, context: MacroExecutionContext) -> bool:
        key = instruction.get("key", "t")
        duration = instruction.get("seconds", 1.0)
        if not context.wait_before_action():
            return False
        context.pyautogui.keyDown(key)
        elapsed = 0.0
        while elapsed < duration:
            if not MacroExecutionService._process_interrupts(context):
                context.pyautogui.keyUp(key)
                return False
            sleep_time = min(0.1, duration - elapsed)
            if not context.sleep_interruptibly(sleep_time):
                context.pyautogui.keyUp(key)
                return False
            elapsed += sleep_time
        context.pyautogui.keyUp(key)
        context.record_action("key")
        return True

    @staticmethod
    def _press_key(context: MacroExecutionContext, key: str) -> bool:
        if not context.wait_before_action():
            return False
        if not MacroExecutionService._process_interrupts(context):
            return False
        context.pyautogui.press(key)
        context.record_action("key")
        return True

    def _place(self, instruction: dict, units: dict, context: MacroExecutionContext) -> bool:
        slot = instruction["slot"]
        placement_index = instruction["placement_index"]
        equip_coords = UNIT_COORDINATES[slot]
        equip_x = equip_coords["x"]
        equip_y = equip_coords["y"]
        until_empty = instruction.get("until_empty", False)

        placement = None
        placements = units.get(slot, {}).get("placements", [])
        if placement_index < len(placements):
            placement = placements[placement_index]
        if placement is None:
            print(f"Skipping place step: no placement coords for slot {slot} index {placement_index}")
            return True

        place_x, place_y = self._runtime_placement_point(placement, context, slot)
        if until_empty:
            place_count = 0
            while True:
                if not self._process_interrupts(context):
                    return False
                current_place_x = place_x + (place_count * 40)
                if not self._place_once_with_optional_verification(
                    context,
                    equip_x,
                    equip_y,
                    current_place_x,
                    place_y,
                ):
                    return False
                place_count += 1
                if not context.sleep_interruptibly(0.3):
                    return False
                if context.detection.is_equip_slot_empty(equip_x, equip_y):
                    print(f"Equip slot empty after {place_count} placement(s)")
                    if context.log:
                        context.log(f"Placed {place_count} unit(s) until empty")
                    if context.status_callback:
                        context.status_callback(f"Placed {place_count} unit(s) until empty")
                    break
            return True

        return self._place_once_with_optional_verification(context, equip_x, equip_y, place_x, place_y)

    def _upgrade(self, instruction: dict, units: dict, context: MacroExecutionContext) -> bool:
        slot = instruction["slot"]
        placement_index = instruction["placement_index"]
        mode = instruction.get("mode", "manual")
        upgrade_count = instruction.get("count", 1)

        placement = None
        placements = units.get(slot, {}).get("placements", [])
        if placement_index < len(placements):
            placement = placements[placement_index]
        if placement is None:
            print(f"Skipping upgrade step: no placement coords for slot {slot} index {placement_index}")
            return True

        placed_x, placed_y = self._runtime_placement_point(placement, context, slot)
        if not self._run_click(context, placed_x, placed_y):
            return False

        if mode == "auto":
            if not self._press_key(context, "z"):
                return False
        elif mode == "max":
            if not self._run_click(context, 364, 504):
                return False
            if not self._run_click(context, 365, 250):
                return False
        else:
            upgrades_done = 0
            wait_iterations = 0
            max_wait_iterations = 300
            while upgrades_done < upgrade_count:
                if not self._process_interrupts(context):
                    return False
                try:
                    started_at = time.perf_counter()
                    green_value = self._capture_green_channel(112, 465)
                    if context.detection_profiler is not None:
                        context.detection_profiler.record("upgrade_button_check", time.perf_counter() - started_at)
                    if green_value >= 120:
                        if not self._run_click(context, 112, 465):
                            return False
                        upgrades_done += 1
                        wait_iterations = 0
                        print(f"Upgrade {upgrades_done}/{upgrade_count} complete")
                    else:
                        wait_iterations += 1
                        if wait_iterations >= max_wait_iterations:
                            print(f"Timeout waiting for upgrade button (done {upgrades_done}/{upgrade_count})")
                            break
                        if not context.sleep_interruptibly(0.1):
                            return False
                except Exception as exc:
                    if isinstance(exc, RelativePositioningError):
                        raise
                    print(f"Error checking upgrade button: {exc}")
                    if not context.sleep_interruptibly(0.1):
                        return False

        if not self._run_click(context, 360, 250):
            return False
        return True

    @staticmethod
    def _first_placement(units: dict, slot: int):
        placements = units.get(slot, {}).get("placements", [])
        if not placements:
            return None
        placement = placements[0]
        if not isinstance(placement, (list, tuple)) or len(placement) < 2:
            return None
        return int(placement[0]), int(placement[1])

    @staticmethod
    def _runtime_placement_point(placement, context: MacroExecutionContext, slot: int) -> tuple[int, int]:
        x, y, converted = normalize_saved_roblox_point(
            context.relative_positioner,
            int(placement[0]),
            int(placement[1]),
        )
        if converted and context.log:
            context.log(
                f"Unit {slot} legacy DeskPad placement normalized: "
                f"({placement[0]}, {placement[1]}) -> ({x}, {y})"
            )
        return x, y

    def _sell(self, instruction: dict, units: dict, context: MacroExecutionContext) -> bool:
        slot = int(instruction["slot"])
        placement = self._first_placement(units, slot)
        if placement is None:
            if context.log:
                context.log(f"Sell skipped: no placement found for Unit {slot}")
            return True

        placement = self._runtime_placement_point(placement, context, slot)
        if not self._run_click(context, placement[0], placement[1]):
            return False
        if not self._press_key(context, "x"):
            return False
        return True

    def _priority(self, instruction: dict, units: dict, context: MacroExecutionContext) -> bool:
        slot = int(instruction["slot"])
        priority = str(instruction.get("priority", "First"))
        placement = self._first_placement(units, slot)
        if placement is None:
            if context.log:
                context.log(f"Priority skipped: no placement found for Unit {slot}")
            return True

        placement = self._runtime_placement_point(placement, context, slot)
        if not self._run_click(context, placement[0], placement[1]):
            return False

        clicks = PRIORITY_CLICK_COUNTS.get(priority, 0)
        for index in range(clicks):
            if not self._run_click(context, PRIORITY_CLICK_POINT[0], PRIORITY_CLICK_POINT[1]):
                return False
            if index < clicks - 1:
                elapsed = 0.0
                while elapsed < 0.5:
                    if not self._process_interrupts(context):
                        return False
                    sleep_time = min(0.1, 0.5 - elapsed)
                    if not context.sleep_interruptibly(sleep_time):
                        return False
                    elapsed += sleep_time
        return True

    def _place_once_with_optional_verification(
        self,
        context: MacroExecutionContext,
        equip_x: int,
        equip_y: int,
        place_x: int,
        place_y: int,
    ) -> bool:
        if not context.check_placed:
            if not self._run_click(context, equip_x, equip_y):
                return False
            if not self._run_click(context, place_x, place_y):
                return False
            if not self._run_click(context, 360, 250):
                return False
            return True

        for attempt in range(1, UNIT_PLACED_TRIES + 1):
            if not self._run_click(context, equip_x, equip_y):
                return False
            if not self._run_click(context, place_x, place_y):
                return False
            if not context.sleep_interruptibly(0.6):
                return False

            detected, confidence = self._verify_unit_placed(context)
            if context.log:
                context.log(
                    f"Check Placed attempt {attempt}/{UNIT_PLACED_TRIES}: "
                    f"conf={confidence:.3f}"
                )
            if detected:
                if not self._run_click(context, 360, 250):
                    return False
                return True

            if attempt < UNIT_PLACED_TRIES:
                if not self._press_key(context, "q"):
                    return False
                if not context.sleep_interruptibly(0.4):
                    return False

        if context.log:
            context.log("Check Placed failed after 3 tries. Stopping macro.")
        return False

    def _verify_unit_placed(self, context: MacroExecutionContext) -> tuple[bool, float]:
        return self._verify_unit_placed_impl(context)

    def _verify_unit_placed_impl(self, context: MacroExecutionContext) -> tuple[bool, float]:
        template_info = self._load_unit_placed_template(context)
        if template_info is None:
            if context.log:
                context.log("Check Placed skipped: missing unit_placed_ref.png")
            return True, 0.0

        template, mask = template_info
        started_at = time.perf_counter()
        region_bgr = self._capture_region(UNIT_PLACED_VERIFY_REGION)
        if region_bgr.shape[0] < template.shape[0] or region_bgr.shape[1] < template.shape[1]:
            if context.detection_profiler is not None:
                context.detection_profiler.record("unit_placed_verify", time.perf_counter() - started_at)
            return False, 0.0

        if mask is not None:
            result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
        else:
            result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if context.detection_profiler is not None:
            context.detection_profiler.record("unit_placed_verify", time.perf_counter() - started_at)
        confidence = float(max_val)
        return confidence >= UNIT_PLACED_THRESHOLD, confidence

    def _capture_green_channel(self, x: int, y: int) -> int:
        if self._current_screen_capture is not None:
            pixel = self._current_screen_capture.capture_base_region_bgr((x, y, x + 1, y + 1))[0, 0]
            return int(pixel[1])
        if self._current_relative_positioner is not None:
            x, y = self._current_relative_positioner.translate_point(x, y)
        if self._screen_capture is None:
            self._screen_capture = mss()
        shot = self._screen_capture.grab({"left": x, "top": y, "width": 1, "height": 1})
        pixel = np.array(shot)[0, 0]
        return int(pixel[1])

    def _load_unit_placed_template(self, context: MacroExecutionContext) -> tuple[np.ndarray, np.ndarray | None] | None:
        if self._unit_placed_template_cache is not None:
            return self._unit_placed_template_cache
        if not UNIT_PLACED_REF.exists():
            return None

        image = cv2.imread(str(UNIT_PLACED_REF), cv2.IMREAD_UNCHANGED)
        if image is None:
            return None

        mask = None
        if image.ndim == 3 and image.shape[2] == 4:
            mask = image[:, :, 3]
            image = image[:, :, :3]

        screenshot = context.pyautogui.screenshot()
        screen_w, _ = context.pyautogui.size()
        scale_factor = screenshot.size[0] / screen_w
        if scale_factor > 1:
            new_width = max(1, int(image.shape[1] / scale_factor))
            new_height = max(1, int(image.shape[0] / scale_factor))
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            if mask is not None:
                mask = cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_AREA)

        self._unit_placed_template_cache = (image, mask)
        return self._unit_placed_template_cache

    def _capture_region(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._current_screen_capture is not None:
            return self._current_screen_capture.capture_base_region_bgr(region)
        if self._current_relative_positioner is not None:
            region = self._current_relative_positioner.translate_region(region)
        left, top, right, bottom = region
        if self._screen_capture is None:
            self._screen_capture = mss()
        shot = self._screen_capture.grab(
            {"left": left, "top": top, "width": right - left, "height": bottom - top}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
