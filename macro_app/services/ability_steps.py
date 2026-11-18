"""Ability-step discovery and execution helpers."""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from mss import mss

from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import normalize_saved_roblox_point

BASE_DIR = Path(__file__).resolve().parents[2]
ABILITIES_DIR = BASE_DIR / "references" / "abilities"
AINZ_DIR = ABILITIES_DIR / "ainz"
AINZ_ARCANE_DIR = AINZ_DIR / "arcane"

ABILITY_REGION = (363, 222, 477, 523)
AUTO_ABILITY_REGION = (424, 230, 476, 486)
AINZ_ARCANE_REGION = (343, 281, 656, 513)

ABILITY_THRESHOLD = 0.95
AUTO_ABILITY_THRESHOLD = 0.90
AINZ_OPTION_THRESHOLD = 0.90

BACK_TO_ELEMENT_MENU = (380, 270)
AINZ_CONFIRM = (790, 495)
WORLD_ITEMS_TARGET = (544, 517)
CALORIC_UNIT_INPUT = (387, 245)
CALORIC_UNIT_CONFIRM = (368, 315)
CALORIC_PLACE_CONFIRM = (486, 383)
MAIN_ABILITY_CONFIRM = (362, 250)
ABILITY_END_CONFIRM = (362, 247)

MAIN_UNIT_FOLDERS = {
    "Broly": "broly",
    "Pride": "pride",
    "Alucard": "alucard",
    "Shanks": "shanks",
    "Erza": "erza",
    "Griffith": "griffith",
    "Lleft": "lleft",
    "Whitebeard": "whitebeard",
    "Guts": "guts",
    "Doffy": "doffy",
    "Toji": "toji",
    "Sukuna": "sukuna",
    "Skele King": "skele king",
}

UNIT_NAME_ALIASES = {
    "broly": "Broly",
    "pride": "Pride",
    "alucard": "Alucard",
    "shanks": "Shanks",
    "ainz": "Ainz",
    "griffith": "Griffith",
    "lleft": "Lleft",
    "whitebeard": "Whitebeard",
    "guts": "Guts",
    "doffy": "Doffy",
    "toji": "Toji",
    "sukuna": "Sukuna",
    "skele_king": "Skele King",
}

MAIN_UNIT_ABILITIES = {
    "Alucard": (("Constraint 0", "alucard_constraint_zero_ref.png"),),
    "Shanks": (("Conqueror's Haki", "shanks_conqueror_ref.png"),),
    "Broly": (("Wrathful Clash", "broly_wrathful_clash_ref.png"),),
    "Pride": (("Lion's Sin", "pride_lion_sin_ref.png"), ("Ultimate", "pride_ultimate_ref.png")),
    "Erza": (("Requip", "erza_requip_ref.png"),),
    "Griffith": (("I sacrifice", "griffith_sacrifice_ref.png"),),
    "Lleft": (
        ("Love shot", "lleft_love_shot_ref.png"),
        ("Shotgun Loop", "lleft_shotgun_loop_ref.png"),
    ),
    "Whitebeard": (("Nuke", "whitebeard_nuke_ref.png"),),
    "Guts": (("Berserker", "guts_berserker_ref.png"),),
    "Doffy": (
        ("Conquerors Aura", "doffy_conquerors_aura_ref.png"),
        ("Puppet Master", "doffy_puppet_master_ref.png"),
        ("String Dominion", "doffy_string_dominion_ref.png"),
    ),
    "Toji": (("Cursed Inventory", "toji_cursed_inventory_ref.png"),),
    "Sukuna": (("Sinister Sanctum", "sukuna_sinister_sanctum_ref.png"),),
    "Skele King": (("Hell", "skele_hell_ref.png"),),
}

ARCANE_ELEMENTS = ("Curse", "Unbound")
ARCANE_SKILLS = {
    "Curse": ("Create Greater Undead", "Supreme Summoning"),
    "Unbound": ("Haste", "Rage"),
}
ARCANE_SKILL_COORDS = {
    "Curse": {
        "Create Greater Undead": (635, 308),
        "Supreme Summoning": (627, 364),
    },
    "Unbound": {
        "Haste": (626, 307),
        "Rage": (626, 355),
    },
}

AINZ_WORLD_ITEMS_REF = AINZ_DIR / "ainz_world_items_ref.png"
SKELE_ABILITY_REF = ABILITIES_DIR / "skele king" / "skele_string_ref.png"
AUTO_ABILITY_OFF_REF = ABILITIES_DIR / "auto_ability_off_ref.png"

MOUSE_SETTLE_DELAY = 0.2
ABILITY_DETECTION_SETTLE_DELAY = 0.12


def format_display_name(raw_name: str) -> str:
    return " ".join(part.capitalize() for part in raw_name.split("_"))


def slugify_display_name(display_name: str) -> str:
    return display_name.strip().lower().replace(" ", "_")


def canonical_unit_name(name: str) -> str:
    return UNIT_NAME_ALIASES.get(slugify_display_name(name), name.strip())


def folder_name_for_unit(name: str) -> str | None:
    canonical = canonical_unit_name(name)
    return MAIN_UNIT_FOLDERS.get(canonical)


def list_main_unit_abilities(unit_display_name: str) -> list[tuple[str, str]]:
    canonical = canonical_unit_name(unit_display_name)
    return list(MAIN_UNIT_ABILITIES.get(canonical, ()))


def get_main_ability_template_path(unit_display_name: str, filename: str) -> Path:
    folder_name = folder_name_for_unit(unit_display_name)
    if folder_name is None:
        raise KeyError(unit_display_name)
    return ABILITIES_DIR / folder_name / filename


def get_ainz_element_template(element_name: str) -> Path:
    return AINZ_ARCANE_DIR / f"ainz_{slugify_display_name(element_name)}_ref.png"


def _compute_scale_factor(pyautogui_module: Any) -> float:
    screenshot = pyautogui_module.screenshot()
    screen_w, _ = pyautogui_module.size()
    return screenshot.size[0] / screen_w


def _capture_region(pyautogui_module: Any, region: tuple[int, int, int, int]) -> np.ndarray:
    left, top, right, bottom = region
    screenshot = pyautogui_module.screenshot(region=(left, top, right - left, bottom - top))
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def _load_template(path: Path, scale_factor: float) -> tuple[np.ndarray, np.ndarray | None]:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Could not read template: {path}")

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

    return image, mask


def _detect_template(
    region_bgr: np.ndarray,
    template: np.ndarray,
    mask: np.ndarray | None,
) -> tuple[float, tuple[int, int], int, int]:
    if mask is not None:
        result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
    else:
        result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return float(max_val), (int(max_loc[0]), int(max_loc[1])), int(template.shape[1]), int(template.shape[0])


def _move_and_click(pyautogui_module: Any, x: int, y: int, *, context=None, settle: float = MOUSE_SETTLE_DELAY) -> bool:
    if context is not None:
        if not context.wait_before_action():
            return False
    pyautogui_module.moveTo(x, y)
    time.sleep(settle)
    pyautogui_module.click()
    if context is not None:
        context.record_action("click")
    return True


class AbilityStepService:
    """Execute the different ability-related macro steps."""

    def __init__(self) -> None:
        self._scale_factor_cache: float | None = None
        self._detection_profiler: DetectionProfiler | None = None
        self._screen_capture: mss | None = None
        self._runtime_screen_capture = None
        self._skele_runtime_prepared = False

    def set_detection_profiler(self, profiler: DetectionProfiler | None) -> None:
        self._detection_profiler = profiler

    def set_screen_capture(self, screen_capture) -> None:
        self._runtime_screen_capture = screen_capture

    def _scale_factor(self, pyautogui_module: Any) -> float:
        if self._scale_factor_cache is None:
            self._scale_factor_cache = _compute_scale_factor(pyautogui_module)
        return self._scale_factor_cache

    def _detect_and_click(
        self,
        *,
        pyautogui_module: Any,
        context,
        template_path: Path,
        region: tuple[int, int, int, int],
        threshold: float,
        log,
        label: str,
    ) -> bool:
        return self._detect_and_click_impl(
            pyautogui_module=pyautogui_module,
            context=context,
            template_path=template_path,
            region=region,
            threshold=threshold,
            log=log,
            label=label,
        )

    def _detect_and_click_impl(
        self,
        *,
        pyautogui_module: Any,
        context,
        template_path: Path,
        region: tuple[int, int, int, int],
        threshold: float,
        log,
        label: str,
    ) -> bool:
        if not template_path.exists():
            if log:
                log(f"{label}: missing template {template_path.name}")
            return False

        template, mask = _load_template(template_path, self._scale_factor(pyautogui_module))
        time.sleep(ABILITY_DETECTION_SETTLE_DELAY)
        started_at = time.perf_counter()
        region_bgr = self._capture_region(region, context.relative_positioner)
        confidence, location, width, height = _detect_template(region_bgr, template, mask)
        if self._detection_profiler is not None:
            self._detection_profiler.record(f"ability:{label}", time.perf_counter() - started_at)
        if log:
            log(f"{label}: conf={confidence:.3f}")
        if confidence < threshold:
            return False

        left, top, _, _ = region
        click_x = left + location[0] + (width // 2)
        click_y = top + location[1] + (height // 2)
        return _move_and_click(pyautogui_module, click_x, click_y, context=context)

    def _get_screen_capture(self) -> mss:
        if self._screen_capture is None:
            self._screen_capture = mss()
        return self._screen_capture

    def _capture_region(self, region: tuple[int, int, int, int], relative_positioner=None) -> np.ndarray:
        if self._runtime_screen_capture is not None:
            return self._runtime_screen_capture.capture_base_region_bgr(region)
        if relative_positioner is not None:
            region = relative_positioner.translate_region(region)
        left, top, right, bottom = region
        shot = self._get_screen_capture().grab(
            {"left": left, "top": top, "width": right - left, "height": bottom - top}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)

    def prepare_skele_strings_runtime(self, log=None) -> bool:
        if self._skele_runtime_prepared:
            return True
        try:
            import jam_detector_test as jam_base

            ready = jam_base._init_stream()
        except Exception as exc:
            if log:
                log(f"Skele: Strings setup failed: {exc}")
            return False
        if not ready:
            if log:
                log("Skele: Strings setup failed")
            return False
        self._skele_runtime_prepared = True
        if log:
            log("Skele: Strings runtime prepared")
        return True

    @staticmethod
    def _find_first_placement(units: dict | None, slot: int) -> tuple[int, int] | None:
        if not units or slot not in units:
            return None
        placements = units[slot].get("placements", [])
        if not placements:
            return None
        placement = placements[0]
        if not isinstance(placement, (list, tuple)) or len(placement) < 2:
            return None
        return int(placement[0]), int(placement[1])

    @staticmethod
    def _find_slot_by_unit_name(units: dict | None, expected_name: str) -> int | None:
        if not units:
            return None
        target = slugify_display_name(expected_name)
        for slot, unit_data in units.items():
            current_name = slugify_display_name(unit_data.get("name", ""))
            if current_name == target or target in current_name:
                return int(slot)
        return None

    def _click_unit_placement(self, context, *, slot: int | None = None, unit_name: str = "", label: str = "Unit") -> bool:
        pyautogui_module = context.pyautogui
        log = context.log
        units = context.units
        resolved_slot = slot
        if resolved_slot is None and unit_name:
            resolved_slot = self._find_slot_by_unit_name(units, unit_name)
        if resolved_slot is None:
            if log:
                log(f"{label}: unit slot not found")
            return False

        placement = self._find_first_placement(units, resolved_slot)
        if placement is None:
            if log:
                log(f"{label}: no saved placement for Unit {resolved_slot}")
            return False

        target_x, target_y, converted = normalize_saved_roblox_point(
            context.relative_positioner,
            placement[0],
            placement[1],
        )
        if converted and log:
            log(
                f"{label}: legacy DeskPad placement normalized "
                f"({placement[0]}, {placement[1]}) -> ({target_x}, {target_y})"
            )
        return _move_and_click(pyautogui_module, target_x, target_y, context=context)

    def execute_main(self, instruction: dict, context) -> bool:
        pyautogui_module = context.pyautogui
        log = context.log
        unit_name = instruction.get("unit", "")
        slot = instruction.get("slot")

        if not self._click_unit_placement(context, slot=slot, unit_name=unit_name, label=unit_name or "Ability unit"):
            return True

        if instruction.get("auto"):
            clicked = self._detect_and_click(
                pyautogui_module=pyautogui_module,
                context=context,
                template_path=AUTO_ABILITY_OFF_REF,
                region=AUTO_ABILITY_REGION,
                threshold=AUTO_ABILITY_THRESHOLD,
                log=log,
                label="Auto Ability Off",
            )
            if log:
                log("Auto ability toggled" if clicked else "Auto ability toggle not found")
            if clicked:
                if not _move_and_click(pyautogui_module, *MAIN_ABILITY_CONFIRM, context=context):
                    return False
            return True

        ability_file = instruction.get("ability_file", "")
        if not unit_name or not ability_file:
            if log:
                log("Main ability step skipped: missing unit or ability")
            return True

        try:
            template_path = get_main_ability_template_path(unit_name, ability_file)
        except KeyError:
            if log:
                log(f"{unit_name} ability step skipped: unsupported unit mapping")
            return True
        clicked = self._detect_and_click(
            pyautogui_module=pyautogui_module,
            context=context,
            template_path=template_path,
            region=ABILITY_REGION,
            threshold=ABILITY_THRESHOLD,
            log=log,
            label=f"{unit_name} {instruction.get('ability', '')}".strip(),
        )
        if log and not clicked:
            log(f"{unit_name} ability not found")
        if clicked:
            if not _move_and_click(pyautogui_module, *MAIN_ABILITY_CONFIRM, context=context):
                return False
        return True

    def execute_skele_king(self, context) -> bool:
        pyautogui_module = context.pyautogui
        log = context.log

        if not self._click_unit_placement(context, unit_name="Skele King", label="Skele: Strings"):
            return True

        clicked = self._detect_and_click(
            pyautogui_module=pyautogui_module,
            context=context,
            template_path=SKELE_ABILITY_REF,
            region=ABILITY_REGION,
            threshold=ABILITY_THRESHOLD,
            log=log,
            label="Skele: Strings",
        )
        if not clicked:
            if log:
                log("Skele: Strings ability not found")
            return True

        if log:
            log("Skele: Strings jam detector started (in-process)")

        try:
            import jam_detector_test as jam_base
            import jam_detector_complete_test as jam_complete

            self._skele_runtime_prepared = True
            completed = jam_complete.run_auto_session(
                relative=hasattr(pyautogui_module, "translate_point"),
                stop_requested=context.stop_requested,
            )
        except Exception as exc:
            if log:
                log(f"Skele: Strings jam detector error: {exc}")
            return False

        if not completed:
            if log:
                log("Skele: Strings jam detector stopped before completion")
            return False
        if log:
            log("Skele: Strings jam detector completed")
        return True

    def execute_ainz_arcane(self, instruction: dict, context) -> bool:
        pyautogui_module = context.pyautogui
        log = context.log

        sequence = [row for row in instruction.get("sequence", []) if row.get("element") and row.get("skill")]
        if not sequence:
            if log:
                log("Ainz Arcane skipped: no element/skill rows configured")
            return True

        if not self._click_unit_placement(context, unit_name="Ainz", label="Ainz"):
            return True

        opened = self._detect_and_click(
            pyautogui_module=pyautogui_module,
            context=context,
            template_path=AINZ_DIR / "ainz_arcane_ref.png",
            region=ABILITY_REGION,
            threshold=ABILITY_THRESHOLD,
            log=log,
            label="Ainz Arcane",
        )
        if not opened:
            if log:
                log("Ainz Arcane ability not found")
            return True

        current_element: str | None = None
        for index, row in enumerate(sequence):
            element = row["element"]
            skill = row["skill"]

            if current_element != element:
                found_element = self._detect_and_click(
                    pyautogui_module=pyautogui_module,
                    context=context,
                    template_path=get_ainz_element_template(element),
                    region=AINZ_ARCANE_REGION,
                    threshold=AINZ_OPTION_THRESHOLD,
                    log=log,
                    label=f"Ainz {element}",
                )
                if not found_element:
                    if log:
                        log(f"Ainz element not found: {element}")
                    return True
                current_element = element

            coords = ARCANE_SKILL_COORDS.get(element, {}).get(skill)
            if coords is None:
                if log:
                    log(f"Ainz skill coords missing for {element} / {skill}")
                continue

            if log:
                log(f"Ainz skill: {element} / {skill}")
            if not _move_and_click(pyautogui_module, *coords, context=context):
                return False

            next_row = sequence[index + 1] if index + 1 < len(sequence) else None
            if next_row is not None and next_row.get("element") == current_element:
                continue

            if not _move_and_click(pyautogui_module, *BACK_TO_ELEMENT_MENU, context=context):
                return False
            current_element = None

        if not _move_and_click(pyautogui_module, *AINZ_CONFIRM, context=context):
            return False
        if log:
            log("Ainz Arcane confirmed")
        return True

    def execute_ainz_caloric(self, instruction: dict, context) -> bool:
        pyautogui_module = context.pyautogui
        log = context.log

        if not self._click_unit_placement(context, unit_name="Ainz", label="Ainz"):
            return True

        opened = self._detect_and_click(
            pyautogui_module=pyautogui_module,
            context=context,
            template_path=AINZ_WORLD_ITEMS_REF,
            region=ABILITY_REGION,
            threshold=ABILITY_THRESHOLD,
            log=log,
            label="Ainz World Items",
        )
        if not opened:
            if log:
                log("Ainz World Items ability not found")
            return True

        if not _move_and_click(pyautogui_module, *WORLD_ITEMS_TARGET, context=context):
            return False
        if not _move_and_click(pyautogui_module, *CALORIC_UNIT_INPUT, context=context):
            return False
        pyautogui_module.write(instruction.get("target_unit", ""), interval=0.02)
        time.sleep(MOUSE_SETTLE_DELAY)
        if not _move_and_click(pyautogui_module, *CALORIC_UNIT_CONFIRM, context=context):
            return False
        if not _move_and_click(pyautogui_module, *CALORIC_PLACE_CONFIRM, context=context):
            return False
        target_x = instruction.get("target_x")
        target_y = instruction.get("target_y")
        if target_x is not None and target_y is not None:
            target_x, target_y, converted = normalize_saved_roblox_point(
                context.relative_positioner,
                int(target_x),
                int(target_y),
            )
            if converted and log:
                log(f"Ainz Caloric legacy DeskPad target normalized to ({target_x}, {target_y})")
            if not _move_and_click(pyautogui_module, target_x, target_y, context=context):
                return False
        if not _move_and_click(pyautogui_module, *ABILITY_END_CONFIRM, context=context):
            return False
        if log:
            log(f"Ainz Caloric Stone target: {instruction.get('target_unit', '')}")
        return True
