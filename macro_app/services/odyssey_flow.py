"""Odyssey next-room selection flow."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from mss import mss

from macro_app.constants import REFERENCES_DIR
from macro_app.services.relative_positioning import RelativePositioner

ODYSSEY_NEXT_REGION = (47, 116, 93, 167)
ODYSSEY_MAP_REGION = (48, 184, 1153, 451)
ODYSSEY_END_REGION = (465, 85, 735, 130)
ODYSSEY_SELECT_REGION = (0, 40, 1200, 670)
ODYSSEY_NORMAL_CARD_REGIONS = (
    (240, 210, 438, 420),
    (500, 210, 698, 420),
    (760, 210, 958, 420),
)
ODYSSEY_CHARACTER_HEADER_REGION = (386, 87, 817, 130)
ODYSSEY_CHARACTER_CARD_REGIONS = (
    (253, 363, 440, 398),
    (499, 365, 705, 398),
    (754, 357, 961, 401),
)
ODYSSEY_CHARACTER_CARD_CONFIRM_CLICK = (550, 623)
ODYSSEY_END_CONTINUE_CLICK = (335, 334)
ODYSSEY_END_CLICK_DELAY_SECONDS = 0.5
ODYSSEY_SCROLL_POINT = (258, 532)
ODYSSEY_SCROLL_AMOUNT = -2
ODYSSEY_SHOP_CANCEL_REGION = (541, 389, 657, 424)
ODYSSEY_MEMORIA_SHOP_OPEN_CLICK = (578, 361)
ODYSSEY_MEMORIA_SCROLL_AMOUNT = -50
ODYSSEY_MEMORIA_SLOT_REGIONS = (
    (438, 247, 498, 287),
    (436, 322, 501, 391),
    (435, 416, 501, 487),
)
ODYSSEY_MEMORIA_PREBUY_CLICK = (390, 598)
ODYSSEY_MEMORIA_SLOT_CLICKS = (
    (719, 275),
    (715, 375),
    (719, 472),
)
ODYSSEY_MEMORIA_CLOSE_CLICK = (764, 188)
ODYSSEY_NOT_ENOUGH_COINS_REGION = (537, 391, 660, 423)
ODYSSEY_NOT_ENOUGH_COINS_OK_CLICK = (606, 403)
TREASURE_ROOM_REGION = (450, 204, 644, 240)
TREASURE_ROOM_DETECTION_DELAY_SECONDS = 3.0
AREAS_REGION = (54, 284, 144, 454)
CLAIM_REWARDS_REGION = (478, 167, 718, 202)
TREASURE_INITIAL_CLICK = (792, 234)
TREASURE_CLOSE_CLICK = (1136, 168)
TREASURE_CONFIRM_CLICK = (710, 530)
TREASURE_AREAS_SEARCH_CLICK = (523, 196)
TREASURE_AREAS_SEARCH_TEXT = "odyssey"
TREASURE_AREAS_SELECT_CLICK = (192, 420)
TREASURE_PRE_AREAS_DETECTION_CLICKS = (
    (593, 509),
    (902, 193),
)
TREASURE_PRE_AREAS_WAIT_SECONDS = 17.0
CLAIM_REWARDS_CLICK = (601, 538)
SHOP_STAGE_CLICKS = (
    (715, 294),
    (720, 380),
    (717, 465),
    (763, 190),
)
TREASURE_POST_INTERACT_CLICKS = (
    (444, 541),
    (836, 535),
    (80, 477),
)

ODYSSEY_NEXT_THRESHOLD = 0.70
ODYSSEY_END_THRESHOLD = 0.70
ODYSSEY_NODE_THRESHOLD = 0.68
ODYSSEY_SELECT_THRESHOLD = 0.70
ODYSSEY_SHOP_CANCEL_THRESHOLD = 0.70
ODYSSEY_CARD_THRESHOLD = 0.55
ODYSSEY_CHARACTER_HEADER_THRESHOLD = 0.70
ODYSSEY_CHARACTER_CARD_THRESHOLD = 0.55
ODYSSEY_MEMORIA_THRESHOLD = 0.70
ODYSSEY_NOT_ENOUGH_COINS_THRESHOLD = 0.70
TREASURE_ROOM_THRESHOLD = 0.70
AREAS_THRESHOLD = 0.70
CLAIM_REWARDS_THRESHOLD = 0.70

NEXT_TEMPLATE_SCALES = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45)
NODE_TEMPLATE_SCALES = (1.15, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45)
WIDE_BUTTON_TEMPLATE_SCALES = (1.2, 1.15, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45)
ODYSSEY_ROOM_TYPES = ("Normal", "Shop", "Boss")
DEFAULT_ROOM_PRIORITIES = ("Normal", "Shop", "Boss")
_ROOM_TYPE_TO_TEMPLATE = {
    "Normal": "normal",
    "Shop": "shop",
    "Boss": "boss",
}
_TEMPLATE_TO_ROOM_TYPE = {value: key for key, value in _ROOM_TYPE_TO_TEMPLATE.items()}
_TEMPLATE_TO_ROOM_TYPE["elite_boss"] = "Elite Boss"
ODYSSEY_CARD_REFS = {
    "Ambush": "ambush_card_odyssey_ref.png",
    "Precision Optics": "precision_optics_card_odyssey_ref.png",
    "Boxing Gloves": "boxing_gloves_card_odyssey_ref.png",
    "Serrated Tips": "serrated_tips_card_odyssey_ref.png",
    "Military Training": "military_training_card_odyssey_ref.png",
    "Concussive Blast": "concussive_blast_card_odyssey_ref.png",
    "Adrenaline Shot": "adrenaline_shot_card_odyssey_ref.png",
    "Affinity": "affinity_card_odyssey_ref.png",
    "Infection": "infection_card_odyssey_ref.png",
    "Numbing Agent": "numbing_agent_card_odyssey_ref.png",
    "The Best Defense": "the_best_defense_card_odyssey_ref.png",
    "Extended Duration": "extended_duration_card_odyssey_ref.png",
    "Slayer Rounds": "slayer_rounds_card_odyssey_ref.png",
    "Treasure Map Fragment": "treasure_map_fragment_card_odyssey_ref.png",
    "Resource Overflow": "resource_overflow_card_odyssey_ref.png",
    "Double Tap": "double_tap_card_odyssey_ref.png",
    "Potent Toxins": "potent_toxins_card_odyssey_ref.png",
}
ODYSSEY_MEMORIA_REFS = {
    "Range": "range_memoria_odyssey_ref.png",
    "Damage": "damage_memoria_odyssey_ref.png",
    "Speed": "speed_memoria_odyssey_ref.png",
    "All I got": "all_i_got_memoria_odyssey_ref.png",
    "Artist Blessing": "artist_blessing_memoria_odyssey_ref.png",
    "Late Night Shift": "late_night_shift_memoria_odyssey_ref.png",
    "Drops of Serenity": "drops_of_serenity_memoria_odyssey_ref.png",
    "Gambling Fanatic": "gambling_fanatic_memoria_odyssey_ref.png",
    "Water Goddess": "water_goddess_memoria_odyssey_ref.png",
    "Young Entrepreneur": "young_entrepreneur_memoria_odyssey_ref.png",
}
ODYSSEY_CHARACTER_CARD_REFS = {
    "Madara": {
        "Ninjutsu Payout": "ninjutsu_payout_character_card_odyssey_ref.png",
        "Stacked Afflictions": "stacked_afflictions_character_card_odyssey_ref.png",
        "Shared Ninjutsu": "shared_ninjutsu_character_card_odyssey_ref.png",
        "Layered Slumber": "layered_slumber_character_card_odyssey_ref.png",
    }
}


@dataclass(frozen=True)
class OdysseyMatch:
    name: str
    x: int
    y: int
    w: int
    h: int
    confidence: float
    scale: float = 1.0

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2


@dataclass(frozen=True)
class OdysseyCandidateScore:
    match: OdysseyMatch
    corridor_score: float
    dotted_pixels: int
    distance: float
    accepted: bool
    reason: str


class OdysseyFlowService:
    """Select the next Odyssey room using the tested dotted-line strategy."""

    def __init__(self) -> None:
        self._screen_capture: mss | None = None
        self._templates: dict[str, np.ndarray] = {}
        self.last_selected_node_type: str | None = None
        self.equipped_memoria: str | None = None
        self._runtime_screen_capture = None

    def set_screen_capture(self, screen_capture) -> None:
        self._runtime_screen_capture = screen_capture

    def advance_to_next_room(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None = None,
        wait_for_end: bool = False,
        skip_end_check: bool = False,
        card_priorities: list[str] | tuple[str, ...] | None = None,
        auto_character_card: bool = False,
        character: str = "Madara",
        character_card_priorities: list[str] | tuple[str, ...] | None = None,
        skip_card_selection: bool = False,
        room_priorities: list[str] | tuple[str, ...] | None = None,
        check_treasure_room: bool = False,
        treasure_room_callback: Callable[[], None] | None = None,
        log: Callable[[str], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> bool:
        """Move from Odyssey map/end screen into the next room."""
        stop_requested = stop_requested or (lambda: False)
        self._load_templates()
        self.last_selected_node_type = None
        normalized_priorities = self.normalize_room_priorities(room_priorities)

        if skip_end_check:
            self._log(log, "Odyssey end check skipped. Going straight to next-room icon detection.")
        elif wait_for_end:
            if not self._wait_for_end_and_continue(
                pyautogui_module,
                relative_positioner,
                log,
                stop_requested,
                click_continue=skip_card_selection,
            ):
                return False
            if not self._select_card_after_end(
                pyautogui_module,
                relative_positioner=relative_positioner,
                card_priorities=card_priorities,
                auto_character_card=auto_character_card,
                character=character,
                character_card_priorities=character_card_priorities,
                skip_card_selection=skip_card_selection,
                log=log,
                stop_requested=stop_requested,
            ):
                return False
        else:
            if not self._check_end_once_and_continue(pyautogui_module, relative_positioner, log, stop_requested):
                return False

        if not self._wait_for_next_icon(relative_positioner, log, stop_requested):
            return False

        selected = self._wait_for_connected_node(relative_positioner, log, stop_requested, normalized_priorities)
        if selected is None:
            return False
        self.last_selected_node_type = self._display_room_type(selected.match.name)

        self._log(
            log,
            "Odyssey selected connected node: "
            f"type={self.last_selected_node_type} local={selected.match.center} "
            f"conf={selected.match.confidence:.3f} scale={selected.match.scale:.2f} "
            f"corridor={selected.corridor_score:.4f}",
        )
        click_x = ODYSSEY_MAP_REGION[0] + selected.match.center[0]
        click_y = ODYSSEY_MAP_REGION[1] + selected.match.center[1]
        pyautogui_module.moveTo(click_x, click_y)
        time.sleep(0.2)
        pyautogui_module.click()
        time.sleep(0.5)

        pyautogui_module.moveTo(*ODYSSEY_SCROLL_POINT)
        time.sleep(0.2)
        pyautogui_module.scroll(ODYSSEY_SCROLL_AMOUNT)
        time.sleep(0.5)

        if not self._wait_for_select_floor(pyautogui_module, relative_positioner, log, stop_requested):
            return False
        if check_treasure_room:
            return self._handle_treasure_room_if_present(
                pyautogui_module,
                relative_positioner,
                log,
                stop_requested,
                treasure_room_callback,
            )
        return self._sleep_interruptibly(1.0, stop_requested)

    def wait_for_end_and_continue(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None = None,
        card_priorities: list[str] | tuple[str, ...] | None = None,
        auto_character_card: bool = False,
        character: str = "Madara",
        character_card_priorities: list[str] | tuple[str, ...] | None = None,
        skip_card_selection: bool = False,
        log: Callable[[str], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> bool:
        """Wait for the Odyssey end card and click continue without selecting the next room."""
        self._load_templates()
        stop_requested = stop_requested or (lambda: False)
        if not self._wait_for_end_and_continue(
            pyautogui_module,
            relative_positioner,
            log,
            stop_requested,
            click_continue=skip_card_selection,
        ):
            return False
        return self._select_card_after_end(
            pyautogui_module,
            relative_positioner=relative_positioner,
            card_priorities=card_priorities,
            auto_character_card=auto_character_card,
            character=character,
            character_card_priorities=character_card_priorities,
            skip_card_selection=skip_card_selection,
            log=log,
            stop_requested=stop_requested,
        )

    def _select_card_after_end(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None,
        card_priorities: list[str] | tuple[str, ...] | None,
        auto_character_card: bool,
        character: str,
        character_card_priorities: list[str] | tuple[str, ...] | None,
        skip_card_selection: bool,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        if skip_card_selection:
            self._log(log, "Odyssey card selection skipped: previous room was Elite Boss.")
            return True
        if auto_character_card and self._character_card_screen_visible(relative_positioner, log):
            return self._select_priority_card(
                pyautogui_module,
                ODYSSEY_CHARACTER_CARD_REFS.get(character, {}),
                character_card_priorities,
                ODYSSEY_CHARACTER_CARD_REGIONS,
                ODYSSEY_CHARACTER_CARD_THRESHOLD,
                "character card",
                relative_positioner=relative_positioner,
                log=log,
                stop_requested=stop_requested,
                confirm_click=ODYSSEY_CHARACTER_CARD_CONFIRM_CLICK,
                confirm_delay=1.0,
            )
        return self._select_priority_card(
            pyautogui_module,
            ODYSSEY_CARD_REFS,
            card_priorities,
            ODYSSEY_NORMAL_CARD_REGIONS,
            ODYSSEY_CARD_THRESHOLD,
            "card",
            relative_positioner=relative_positioner,
            log=log,
            stop_requested=stop_requested,
        )

    def _character_card_screen_visible(
        self,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
    ) -> bool:
        match = self._detect_optional_best(
            "character_specific_header",
            "character_specific_odyssey_ref.png",
            ODYSSEY_CHARACTER_HEADER_REGION,
            WIDE_BUTTON_TEMPLATE_SCALES,
            relative_positioner,
        )
        if match is None:
            self._log(log, "Odyssey character-card header reference missing; skipping character-card check.")
            return False
        self._log(
            log,
            f"Odyssey character-card header probe: conf={match.confidence:.3f} "
            f"threshold={ODYSSEY_CHARACTER_HEADER_THRESHOLD:.3f}",
        )
        return match.confidence >= ODYSSEY_CHARACTER_HEADER_THRESHOLD

    def _select_priority_card(
        self,
        pyautogui_module,
        card_refs: dict[str, str],
        priorities: list[str] | tuple[str, ...] | None,
        regions: tuple[tuple[int, int, int, int], ...],
        threshold: float,
        label: str,
        *,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
        confirm_click: tuple[int, int] | None = None,
        confirm_delay: float = 0.0,
    ) -> bool:
        normalized_priorities = [str(item) for item in priorities or [] if str(item) in card_refs]
        if not normalized_priorities:
            self._log(log, f"Odyssey {label} selection has no configured priorities. Clicking nothing.")
            return True
        for card_name in normalized_priorities:
            filename = card_refs[card_name]
            best_match: OdysseyMatch | None = None
            best_region: tuple[int, int, int, int] | None = None
            for region in regions:
                match = self._detect_optional_best(
                    f"{label}:{card_name}",
                    filename,
                    region,
                    WIDE_BUTTON_TEMPLATE_SCALES,
                    relative_positioner,
                    use_grayscale=True,
                )
                if match is None:
                    self._log(log, f"Odyssey {label} ref missing for {card_name}: {filename}")
                    break
                if best_match is None or match.confidence > best_match.confidence:
                    best_match = match
                    best_region = region
            if best_match is None or best_region is None:
                continue
            self._log(
                log,
                f"Odyssey {label} priority check {card_name}: conf={best_match.confidence:.3f} "
                f"scale={best_match.scale:.2f} threshold={threshold:.3f} "
                f"region={best_region} center=({best_region[0] + best_match.center[0]}, "
                f"{best_region[1] + best_match.center[1]})",
            )
            if best_match.confidence < threshold:
                continue
            click_point = (
                best_region[0] + best_match.center[0],
                best_region[1] + best_match.center[1],
            )
            self._log(log, f"Odyssey selecting {label}: {card_name} at {click_point}.")
            pyautogui_module.moveTo(*click_point)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if confirm_click is not None:
                if not self._sleep_interruptibly(confirm_delay, stop_requested):
                    return False
                self._log(log, f"Odyssey confirming {label} at {confirm_click}.")
                pyautogui_module.moveTo(*confirm_click)
                time.sleep(0.2)
                if stop_requested():
                    return False
                pyautogui_module.click()
            return self._sleep_interruptibly(0.5, stop_requested)
        self._log(log, f"No configured Odyssey {label} matched. Clicking nothing.")
        return True

    def claim_unit_reward_if_present(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None = None,
        log: Callable[[str], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> bool:
        """Claim the Boss-stage unit reward prompt if it appears."""
        stop_requested = stop_requested or (lambda: False)
        self._load_templates()
        if stop_requested():
            return False
        match = self._detect_best("claim_rewards", CLAIM_REWARDS_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
        self._log(
            log,
            f"Odyssey unit reward check: conf={match.confidence:.3f} "
            f"scale={match.scale:.2f} threshold={CLAIM_REWARDS_THRESHOLD:.3f}",
        )
        if match.confidence < CLAIM_REWARDS_THRESHOLD:
            self._log(log, "Odyssey unit reward prompt not detected.")
            return True
        self._log(log, f"Odyssey unit reward prompt detected. Clicking claim at {CLAIM_REWARDS_CLICK}.")
        pyautogui_module.moveTo(*CLAIM_REWARDS_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        return self._sleep_interruptibly(0.5, stop_requested)

    def run_shop_stage_shortcut(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None = None,
        log: Callable[[str], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> bool:
        """Run the Shop-room click sequence instead of macro steps."""
        stop_requested = stop_requested or (lambda: False)
        self._load_templates()
        self._log(log, "Odyssey Shop stage selected. Running shop shortcut instead of macro steps.")
        if not self._sleep_interruptibly(2.0, stop_requested):
            return False
        for index, point in enumerate(SHOP_STAGE_CLICKS, start=1):
            self._log(log, f"Odyssey shop shortcut click #{index}: {point}")
            pyautogui_module.moveTo(*point)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if index <= 3 and not self._handle_shop_cancel_if_present(
                pyautogui_module,
                relative_positioner,
                log,
                stop_requested,
            ):
                return False
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False
        self._log(log, "Odyssey Shop shortcut completed. Next loop will skip Odyssey end detection.")
        return True

    def run_memoria_shop_selection(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None = None,
        memoria_priorities: list[str] | tuple[str, ...] | None = None,
        only_buy_when_enough: bool = True,
        log: Callable[[str], None] | None = None,
        stop_requested: Callable[[], bool] | None = None,
    ) -> bool:
        """Run shop-only Memoria selection, then close the shop flow."""
        stop_requested = stop_requested or (lambda: False)
        self._load_templates()
        priorities = [str(item) for item in memoria_priorities or [] if str(item) in ODYSSEY_MEMORIA_REFS]
        self._log(log, f"Odyssey Memoria shop selection active. Priorities={priorities}")
        if not self._sleep_interruptibly(5.0, stop_requested):
            return False
        pyautogui_module.moveTo(*ODYSSEY_MEMORIA_SHOP_OPEN_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        if not self._sleep_interruptibly(0.5, stop_requested):
            return False
        pyautogui_module.scroll(ODYSSEY_MEMORIA_SCROLL_AMOUNT)
        if not self._sleep_interruptibly(0.8, stop_requested):
            return False

        purchased = self._attempt_memoria_purchase(
            pyautogui_module,
            relative_positioner=relative_positioner,
            priorities=priorities,
            only_buy_when_enough=only_buy_when_enough,
            log=log,
            stop_requested=stop_requested,
        )
        if not purchased:
            return False
        self._log(log, f"Odyssey Memoria selection closing at {ODYSSEY_MEMORIA_CLOSE_CLICK}.")
        pyautogui_module.moveTo(*ODYSSEY_MEMORIA_CLOSE_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        return self._sleep_interruptibly(0.5, stop_requested)

    def _attempt_memoria_purchase(
        self,
        pyautogui_module,
        *,
        relative_positioner: RelativePositioner | None,
        priorities: list[str],
        only_buy_when_enough: bool,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        if not priorities:
            self._log(log, "No Odyssey Memoria priorities configured. Buying nothing.")
            return True
        current_rank = priorities.index(self.equipped_memoria) if self.equipped_memoria in priorities else len(priorities)
        attempted_slots: set[int] = set()
        while True:
            candidates = self._detect_memoria_candidates(relative_positioner, priorities, attempted_slots, log)
            candidates = [candidate for candidate in candidates if candidate[0] < current_rank]
            if not candidates:
                self._log(
                    log,
                    "No detected Odyssey Memoria improves current equipped priority "
                    f"({self.equipped_memoria or 'none'}).",
                )
                return True
            rank, slot_index, label, confidence = candidates[0]
            self._log(
                log,
                f"Trying Odyssey Memoria {label} from slot {slot_index + 1} "
                f"(conf={confidence:.3f}, rank={rank}).",
            )
            pyautogui_module.moveTo(*ODYSSEY_MEMORIA_PREBUY_CLICK)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False
            pyautogui_module.moveTo(*ODYSSEY_MEMORIA_SLOT_CLICKS[slot_index])
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False
            if only_buy_when_enough and self._not_enough_coins_visible(relative_positioner, log):
                self._log(log, f"Not enough Odyssey coins for {label}; trying next detected Memoria.")
                pyautogui_module.moveTo(*ODYSSEY_NOT_ENOUGH_COINS_OK_CLICK)
                time.sleep(0.2)
                if stop_requested():
                    return False
                pyautogui_module.click()
                if not self._sleep_interruptibly(0.5, stop_requested):
                    return False
                attempted_slots.add(slot_index)
                continue
            self.equipped_memoria = label
            self._log(log, f"Equipped Odyssey Memoria tracked for session: {label}.")
            return True

    def _detect_memoria_candidates(
        self,
        relative_positioner: RelativePositioner | None,
        priorities: list[str],
        attempted_slots: set[int],
        log: Callable[[str], None] | None,
    ) -> list[tuple[int, int, str, float]]:
        candidates: list[tuple[int, int, str, float]] = []
        for slot_index, region in enumerate(ODYSSEY_MEMORIA_SLOT_REGIONS):
            if slot_index in attempted_slots:
                continue
            best_label = ""
            best_rank = len(priorities)
            best_confidence = 0.0
            for rank, label in enumerate(priorities):
                filename = ODYSSEY_MEMORIA_REFS[label]
                match = self._detect_optional_best(
                    f"memoria:{label}",
                    filename,
                    region,
                    WIDE_BUTTON_TEMPLATE_SCALES,
                    relative_positioner,
                )
                if match is None:
                    self._log(log, f"Odyssey Memoria ref missing for {label}: {filename}")
                    continue
                if match.confidence >= ODYSSEY_MEMORIA_THRESHOLD and (
                    rank < best_rank or (rank == best_rank and match.confidence > best_confidence)
                ):
                    best_label = label
                    best_rank = rank
                    best_confidence = match.confidence
            if best_label:
                candidates.append((best_rank, slot_index, best_label, best_confidence))
        candidates.sort(key=lambda candidate: (candidate[0], candidate[1], -candidate[3]))
        return candidates

    def _not_enough_coins_visible(
        self,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
    ) -> bool:
        match = self._detect_optional_best(
            "not_enough_odyssey_coins",
            "not_enough_odyssey_coins_ref.png",
            ODYSSEY_NOT_ENOUGH_COINS_REGION,
            WIDE_BUTTON_TEMPLATE_SCALES,
            relative_positioner,
        )
        if match is None:
            self._log(log, "Not-enough-Odyssey-coins reference missing; treating purchase as successful.")
            return False
        self._log(
            log,
            f"Not enough Odyssey coins probe: conf={match.confidence:.3f} "
            f"threshold={ODYSSEY_NOT_ENOUGH_COINS_THRESHOLD:.3f}",
        )
        return match.confidence >= ODYSSEY_NOT_ENOUGH_COINS_THRESHOLD

    def _handle_shop_cancel_if_present(
        self,
        pyautogui_module,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        match = self._detect_best("shop_cancel", ODYSSEY_SHOP_CANCEL_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
        click_point = (
            ODYSSEY_SHOP_CANCEL_REGION[0] + match.center[0],
            ODYSSEY_SHOP_CANCEL_REGION[1] + match.center[1],
        )
        self._log(
            log,
            f"Odyssey shop cancel check: conf={match.confidence:.3f} "
            f"scale={match.scale:.2f} threshold={ODYSSEY_SHOP_CANCEL_THRESHOLD:.3f} center={click_point}",
        )
        if match.confidence < ODYSSEY_SHOP_CANCEL_THRESHOLD:
            return True
        self._log(log, f"Odyssey shop cancel detected. Clicking {click_point}.")
        pyautogui_module.moveTo(*click_point)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        return self._sleep_interruptibly(0.5, stop_requested)

    def _wait_for_end_and_continue(
        self,
        pyautogui_module,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
        *,
        click_continue: bool = True,
    ) -> bool:
        self._log(log, "Odyssey waiting for end screen...")
        last_log_at = 0.0
        while not stop_requested():
            match = self._detect_best("end", ODYSSEY_END_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
            now = time.time()
            if now - last_log_at >= 2.0 or match.confidence >= ODYSSEY_END_THRESHOLD:
                last_log_at = now
                self._log(
                    log,
                    f"Odyssey end probe: conf={match.confidence:.3f} "
                    f"scale={match.scale:.2f} threshold={ODYSSEY_END_THRESHOLD:.3f}",
                )
            if match.confidence >= ODYSSEY_END_THRESHOLD:
                if click_continue:
                    return self._click_end_continue(pyautogui_module, log, stop_requested)
                self._log(
                    log,
                    "Odyssey end detected. Auto Card selection will scan cards without the old pre-click.",
                )
                return self._sleep_interruptibly(ODYSSEY_END_CLICK_DELAY_SECONDS, stop_requested)
            time.sleep(0.5)
        return False

    def _check_end_once_and_continue(
        self,
        pyautogui_module,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        if stop_requested():
            return False
        match = self._detect_best("end", ODYSSEY_END_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
        self._log(
            log,
            f"Odyssey end precheck: conf={match.confidence:.3f} "
            f"scale={match.scale:.2f} threshold={ODYSSEY_END_THRESHOLD:.3f}",
        )
        if match.confidence >= ODYSSEY_END_THRESHOLD:
            return self._click_end_continue(pyautogui_module, log, stop_requested)
        return True

    def _click_end_continue(
        self,
        pyautogui_module,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        self._log(
            log,
            f"Odyssey end detected. Waiting {ODYSSEY_END_CLICK_DELAY_SECONDS:g}s, "
            f"then clicking continue at {ODYSSEY_END_CONTINUE_CLICK}.",
        )
        if not self._sleep_interruptibly(ODYSSEY_END_CLICK_DELAY_SECONDS, stop_requested):
            return False
        pyautogui_module.moveTo(*ODYSSEY_END_CONTINUE_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        return self._sleep_interruptibly(1.0, stop_requested)

    def _wait_for_next_icon(
        self,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        self._log(log, "Odyssey waiting for next-room icon...")
        last_log_at = 0.0
        while not stop_requested():
            match = self._detect_best("next", ODYSSEY_NEXT_REGION, NEXT_TEMPLATE_SCALES, relative_positioner)
            now = time.time()
            if now - last_log_at >= 2.0 or match.confidence >= ODYSSEY_NEXT_THRESHOLD:
                last_log_at = now
                self._log(
                    log,
                    f"Odyssey next probe: conf={match.confidence:.3f} "
                    f"scale={match.scale:.2f} threshold={ODYSSEY_NEXT_THRESHOLD:.3f}",
                )
            if match.confidence >= ODYSSEY_NEXT_THRESHOLD:
                return True
            time.sleep(0.5)
        return False

    def _wait_for_connected_node(
        self,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
        room_priorities: tuple[str, str, str],
    ) -> OdysseyCandidateScore | None:
        last_log_at = 0.0
        while not stop_requested():
            map_bgr = self._capture_region_bgr(ODYSSEY_MAP_REGION, relative_positioner)
            current = self._detect_current_node(map_bgr, min_area=80)
            current_method = "green mask"
            if current is None:
                fallback_mask = self._create_current_ring_fallback_mask(map_bgr)
                current = self._detect_current_node_from_mask(fallback_mask, min_area=80)
                current_method = "pale-ring fallback"
            if current is None:
                now = time.time()
                if now - last_log_at >= 2.0:
                    last_log_at = now
                    self._log(log, "Odyssey current ring not detected yet.")
                time.sleep(0.5)
                continue

            current_center = (current[0], current[1])
            elite_matches = self._match_many_optional(
                "elite_boss",
                "ainz_elite_room_ref.png",
                map_bgr,
                ODYSSEY_NODE_THRESHOLD,
                NODE_TEMPLATE_SCALES,
                log,
            )
            normal_matches = self._match_many("normal", map_bgr, ODYSSEY_NODE_THRESHOLD, NODE_TEMPLATE_SCALES)
            shop_matches = self._match_many("shop", map_bgr, ODYSSEY_NODE_THRESHOLD, NODE_TEMPLATE_SCALES)
            boss_matches = self._match_many("boss", map_bgr, ODYSSEY_NODE_THRESHOLD, NODE_TEMPLATE_SCALES)
            all_matches = sorted(
                elite_matches + normal_matches + shop_matches + boss_matches,
                key=lambda match: (match.center[0], match.center[1], -match.confidence),
            )
            dotted_mask = self._create_dotted_line_mask(map_bgr)
            scored = [
                self._score_corridor(dotted_mask, current_center, match)
                for match in all_matches
            ]
            selected = self._select_best_connected(scored, room_priorities)
            now = time.time()
            if now - last_log_at >= 2.0 or selected is not None:
                last_log_at = now
                self._log(
                    log,
                    f"Odyssey node scan: current={current_center} via {current_method} "
                    f"elite={len(elite_matches)} normal={len(normal_matches)} "
                    f"shop={len(shop_matches)} boss={len(boss_matches)} "
                    f"connected={sum(1 for score in scored if score.accepted)} priorities={list(room_priorities)}",
                )
                for index, score in enumerate(scored[:8], start=1):
                    self._log(
                        log,
                        "Odyssey candidate "
                        f"#{index}: type={self._display_room_type(score.match.name)} center={score.match.center} "
                        f"conf={score.match.confidence:.3f} scale={score.match.scale:.2f} "
                        f"corridor={score.corridor_score:.4f} accepted={score.accepted} reason={score.reason}",
                    )
            if selected is not None:
                return selected
            time.sleep(0.5)
        return None

    def _wait_for_select_floor(
        self,
        pyautogui_module,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
    ) -> bool:
        self._log(log, "Odyssey waiting for Select Floor button...")
        last_log_at = 0.0
        while not stop_requested():
            match = self._detect_best("select", ODYSSEY_SELECT_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
            base_x = ODYSSEY_SELECT_REGION[0] + match.center[0]
            base_y = ODYSSEY_SELECT_REGION[1] + match.center[1]
            now = time.time()
            if now - last_log_at >= 2.0 or match.confidence >= ODYSSEY_SELECT_THRESHOLD:
                last_log_at = now
                self._log(
                    log,
                    f"Odyssey select probe: conf={match.confidence:.3f} "
                    f"scale={match.scale:.2f} threshold={ODYSSEY_SELECT_THRESHOLD:.3f} global=({base_x}, {base_y})",
                )
            if match.confidence >= ODYSSEY_SELECT_THRESHOLD:
                pyautogui_module.moveTo(base_x, base_y)
                time.sleep(0.2)
                if stop_requested():
                    return False
                pyautogui_module.click()
                self._log(log, "Odyssey Select Floor clicked.")
                return True
            time.sleep(0.5)
        return False

    def _handle_treasure_room_if_present(
        self,
        pyautogui_module,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
        treasure_room_callback: Callable[[], None] | None,
    ) -> bool:
        self._log(
            log,
            f"Treasure room check waiting {TREASURE_ROOM_DETECTION_DELAY_SECONDS:g}s before detection.",
        )
        if not self._sleep_interruptibly(TREASURE_ROOM_DETECTION_DELAY_SECONDS, stop_requested):
            return False
        match = self._detect_best("treasure_room", TREASURE_ROOM_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
        self._log(
            log,
            f"Treasure room check: conf={match.confidence:.3f} "
            f"scale={match.scale:.2f} threshold={TREASURE_ROOM_THRESHOLD:.3f}",
        )
        if match.confidence < TREASURE_ROOM_THRESHOLD:
            self._log(log, "Treasure room not detected. Continuing macro steps.")
            return True

        self._log(log, "Treasure room detected. Running treasure-room collection sequence.")
        pyautogui_module.moveTo(*TREASURE_INITIAL_CLICK)
        time.sleep(0.2)
        pyautogui_module.click()
        if treasure_room_callback is not None:
            treasure_room_callback()
        if not self._sleep_interruptibly(0.5, stop_requested):
            return False
        for point in (TREASURE_CLOSE_CLICK, TREASURE_CONFIRM_CLICK):
            pyautogui_module.moveTo(*point)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False

        self._log(log, f"Treasure room waiting {TREASURE_PRE_AREAS_WAIT_SECONDS:g}s before areas detection.")
        if not self._sleep_interruptibly(TREASURE_PRE_AREAS_WAIT_SECONDS, stop_requested):
            return False
        for point in TREASURE_PRE_AREAS_DETECTION_CLICKS:
            self._log(log, f"Treasure room pre-areas click at {point}.")
            pyautogui_module.moveTo(*point)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False

        areas_match = self._wait_for_areas_button(relative_positioner, log, stop_requested)
        if areas_match is None:
            self._log(log, "Treasure room areas button was not detected. Stopping treasure sequence.")
            return False
        areas_click = (AREAS_REGION[0] + areas_match.center[0], AREAS_REGION[1] + areas_match.center[1])
        self._log(
            log,
            f"Treasure areas detected: conf={areas_match.confidence:.3f} "
            f"scale={areas_match.scale:.2f}; clicking {areas_click}."
        )
        pyautogui_module.moveTo(*areas_click)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        if not self._sleep_interruptibly(1.0, stop_requested):
            return False

        self._log(log, f"Treasure room clicking areas search at {TREASURE_AREAS_SEARCH_CLICK}.")
        pyautogui_module.moveTo(*TREASURE_AREAS_SEARCH_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        if not self._sleep_interruptibly(0.5, stop_requested):
            return False

        self._log(log, f"Treasure room typing area search text: {TREASURE_AREAS_SEARCH_TEXT!r}.")
        pyautogui_module.write(TREASURE_AREAS_SEARCH_TEXT, interval=0.03)
        if not self._sleep_interruptibly(0.5, stop_requested):
            return False

        self._log(log, f"Treasure room selecting Odyssey area at {TREASURE_AREAS_SELECT_CLICK}.")
        pyautogui_module.moveTo(*TREASURE_AREAS_SELECT_CLICK)
        time.sleep(0.2)
        if stop_requested():
            return False
        pyautogui_module.click()
        if not self._sleep_interruptibly(0.5, stop_requested):
            return False

        self._log(log, "Treasure room movement: holding W for 6 seconds.")
        pyautogui_module.keyDown("w")
        if not self._sleep_interruptibly(6.0, stop_requested):
            pyautogui_module.keyUp("w")
            return False
        pyautogui_module.keyUp("w")
        pyautogui_module.press("e")
        if not self._sleep_interruptibly(3.0, stop_requested):
            return False
        for point in TREASURE_POST_INTERACT_CLICKS:
            pyautogui_module.moveTo(*point)
            time.sleep(0.2)
            if stop_requested():
                return False
            pyautogui_module.click()
            if not self._sleep_interruptibly(0.5, stop_requested):
                return False
        self._log(log, "Treasure room sequence completed. Starting macro steps again.")
        return True

    def _wait_for_areas_button(
        self,
        relative_positioner: RelativePositioner | None,
        log: Callable[[str], None] | None,
        stop_requested: Callable[[], bool],
        *,
        timeout_seconds: float = 15.0,
    ) -> OdysseyMatch | None:
        start = time.time()
        last_log_at = 0.0
        while not stop_requested() and time.time() - start <= timeout_seconds:
            match = self._detect_best("areas", AREAS_REGION, WIDE_BUTTON_TEMPLATE_SCALES, relative_positioner)
            now = time.time()
            if now - last_log_at >= 2.0 or match.confidence >= AREAS_THRESHOLD:
                last_log_at = now
                self._log(
                    log,
                    f"Treasure areas probe: conf={match.confidence:.3f} "
                    f"scale={match.scale:.2f} threshold={AREAS_THRESHOLD:.3f}",
                )
            if match.confidence >= AREAS_THRESHOLD:
                return match
            time.sleep(0.5)
        return None

    def _detect_best(
        self,
        template_name: str,
        region: tuple[int, int, int, int],
        scales: tuple[float, ...],
        relative_positioner: RelativePositioner | None,
    ) -> OdysseyMatch:
        region_bgr = self._capture_region_bgr(region, relative_positioner)
        return self._match_best(template_name, region_bgr, scales)

    def _capture_region_bgr(
        self,
        region: tuple[int, int, int, int],
        relative_positioner: RelativePositioner | None,
    ) -> np.ndarray:
        if self._runtime_screen_capture is not None:
            return self._runtime_screen_capture.capture_base_region_bgr(region)
        capture_region = relative_positioner.translate_region(region) if relative_positioner is not None else region
        left, top, right, bottom = capture_region
        shot = self._get_screen_capture().grab(
            {"left": left, "top": top, "width": right - left, "height": bottom - top}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)

    def _get_screen_capture(self) -> mss:
        if self._screen_capture is None:
            self._screen_capture = mss()
        return self._screen_capture

    def _load_templates(self) -> None:
        refs = {
            "next": "odyssey_next_ref.png",
            "normal": "odyssey_normal_ref.png",
            "shop": "odyssey_shop_ref.png",
            "boss": "odyssey_boss_ref.png",
            "end": "odyssey_end_ref.png",
            "select": "select_floor_ref.png",
            "shop_cancel": "odyssey_cancel_ref.png",
            "treasure_room": "treasure_room_ref.png",
            "areas": "areas_ref.png",
            "claim_rewards": "claim_rewards_ref.png",
        }
        if all(name in self._templates for name in refs):
            return
        for name, filename in refs.items():
            if name in self._templates:
                continue
            if not self._load_template_file(name, filename):
                raise RuntimeError(f"Could not load Odyssey reference: {filename}")

    def _load_template_file(self, template_name: str, filename: str) -> bool:
        if template_name in self._templates:
            return True
        image = cv2.imread(str(Path(REFERENCES_DIR) / filename), cv2.IMREAD_COLOR)
        if image is None:
            return False
        self._templates[template_name] = image
        return True

    def _detect_optional_best(
        self,
        template_name: str,
        filename: str,
        region: tuple[int, int, int, int],
        scales: tuple[float, ...],
        relative_positioner: RelativePositioner | None,
        *,
        use_grayscale: bool = False,
    ) -> OdysseyMatch | None:
        if not self._load_template_file(template_name, filename):
            return None
        region_bgr = self._capture_region_bgr(region, relative_positioner)
        color_match = self._match_best(template_name, region_bgr, scales)
        if not use_grayscale:
            return color_match
        gray_match = self._match_best(template_name, region_bgr, scales, grayscale=True)
        return gray_match if gray_match.confidence > color_match.confidence else color_match

    def _match_best(
        self,
        template_name: str,
        region_bgr: np.ndarray,
        scales: tuple[float, ...],
        *,
        grayscale: bool = False,
    ) -> OdysseyMatch:
        template = self._templates[template_name]
        best: OdysseyMatch | None = None
        search_region = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY) if grayscale else region_bgr
        region_h, region_w = search_region.shape[:2]
        for scale in scales:
            scaled = self._resize_template(template, scale)
            if scaled is None:
                continue
            if grayscale:
                scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
            h, w = scaled.shape[:2]
            if h > region_h or w > region_w:
                continue
            result = cv2.matchTemplate(search_region, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            match = OdysseyMatch(template_name, max_loc[0], max_loc[1], w, h, float(max_val), scale)
            if best is None or match.confidence > best.confidence:
                best = match
        return best or OdysseyMatch(template_name, 0, 0, 0, 0, 0.0)

    def _match_many(
        self,
        template_name: str,
        region_bgr: np.ndarray,
        threshold: float,
        scales: tuple[float, ...],
        *,
        max_matches: int = 20,
        nms_distance: int = 28,
    ) -> list[OdysseyMatch]:
        template = self._templates[template_name]
        region_h, region_w = region_bgr.shape[:2]
        raw: list[OdysseyMatch] = []
        for scale in scales:
            scaled = self._resize_template(template, scale)
            if scaled is None:
                continue
            h, w = scaled.shape[:2]
            if h > region_h or w > region_w:
                continue
            result = cv2.matchTemplate(region_bgr, scaled, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(result >= threshold)
            raw.extend(
                OdysseyMatch(template_name, int(x), int(y), w, h, float(result[y, x]), scale)
                for y, x in zip(ys, xs)
            )
        raw.sort(key=lambda item: item.confidence, reverse=True)
        kept: list[OdysseyMatch] = []
        for match in raw:
            center = match.center
            if any(math.hypot(center[0] - kept_match.center[0], center[1] - kept_match.center[1]) < nms_distance for kept_match in kept):
                continue
            kept.append(match)
            if len(kept) >= max_matches:
                break
        return kept

    def _match_many_optional(
        self,
        template_name: str,
        filename: str,
        region_bgr: np.ndarray,
        threshold: float,
        scales: tuple[float, ...],
        log: Callable[[str], None] | None,
        *,
        max_matches: int = 20,
        nms_distance: int = 28,
    ) -> list[OdysseyMatch]:
        if not self._load_template_file(template_name, filename):
            self._log(log, f"Optional Odyssey room reference missing: {filename}")
            return []
        return self._match_many(
            template_name,
            region_bgr,
            threshold,
            scales,
            max_matches=max_matches,
            nms_distance=nms_distance,
        )

    @staticmethod
    def _resize_template(template: np.ndarray, scale: float) -> np.ndarray | None:
        h, w = template.shape[:2]
        scaled_w = max(1, int(round(w * scale)))
        scaled_h = max(1, int(round(h * scale)))
        if scaled_w < 3 or scaled_h < 3:
            return None
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        return cv2.resize(template, (scaled_w, scaled_h), interpolation=interpolation)

    @staticmethod
    def _create_green_current_mask(map_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(map_bgr, cv2.COLOR_BGR2HSV)
        # The active/current ring is rendered as warm yellow/green. Hovered or
        # already selected future nodes can be cyan/blue, so keep this mask
        # below blue hues to avoid using the wrong node as the source.
        mask = cv2.inRange(hsv, (16, 35, 55), (78, 255, 255))
        kernel = np.ones((3, 3), np.uint8)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    @staticmethod
    def _create_current_ring_fallback_mask(map_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(map_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        pale_ring_or_lines = cv2.bitwise_and(cv2.inRange(s, 0, 175), cv2.inRange(v, 80, 255))
        red = cv2.bitwise_or(cv2.inRange(hsv, (0, 70, 70), (15, 255, 255)), cv2.inRange(hsv, (165, 70, 70), (179, 255, 255)))
        blue_or_cyan = cv2.bitwise_and(cv2.inRange(h, 80, 135), cv2.inRange(s, 25, 255))
        mask = cv2.bitwise_and(pale_ring_or_lines, cv2.bitwise_not(cv2.bitwise_or(red, blue_or_cyan)))
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return cv2.dilate(mask, kernel, iterations=1)

    @classmethod
    def _detect_current_node(cls, map_bgr: np.ndarray, *, min_area: int) -> tuple[int, int, float] | None:
        return cls._detect_current_node_from_mask(cls._create_green_current_mask(map_bgr), min_area=min_area)

    @staticmethod
    def _detect_current_node_from_mask(mask: np.ndarray, *, min_area: int) -> tuple[int, int, float] | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        viable: list[tuple[float, np.ndarray]] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w < 28 or h < 28 or w > 190 or h > 190:
                continue
            aspect = w / max(1, h)
            if aspect < 0.45 or aspect > 2.2:
                continue
            extent = area / max(1, w * h)
            if extent < 0.04:
                continue
            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * math.pi * area / (perimeter * perimeter)) if perimeter else 0.0
            viable.append((area + circularity * 400.0, contour))
        if not viable:
            return None
        contour = max(viable, key=lambda item: item[0])[1]
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            x, y, w, h = cv2.boundingRect(contour)
            return x + w // 2, y + h // 2, float(cv2.contourArea(contour))
        return int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"]), float(cv2.contourArea(contour))

    @staticmethod
    def _create_dotted_line_mask(map_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(map_bgr, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        pale_lines = cv2.bitwise_and(cv2.inRange(s, 0, 155), cv2.inRange(v, 85, 245))
        green = cv2.inRange(hsv, (35, 45, 70), (95, 255, 255))
        red = cv2.bitwise_or(cv2.inRange(hsv, (0, 70, 70), (15, 255, 255)), cv2.inRange(hsv, (165, 70, 70), (179, 255, 255)))
        mask = cv2.bitwise_and(pale_lines, cv2.bitwise_not(cv2.bitwise_or(green, red)))
        kernel = np.ones((2, 2), np.uint8)
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    @staticmethod
    def _score_corridor(
        dotted_mask: np.ndarray,
        current_center: tuple[int, int],
        match: OdysseyMatch,
        *,
        corridor_width: int = 24,
        endpoint_skip: int = 34,
        min_upward_px: int = 18,
        min_corridor_score: float = 0.025,
        segment_count: int = 8,
        min_path_coverage: float = 0.38,
        source_segment_count: int = 3,
        min_source_segments: int = 1,
        min_segment_dotted_pixels: int = 6,
        max_consecutive_empty_segments: int = 3,
        min_source_ray_pixels: int = 8,
        max_source_ray_angle_degrees: float = 18.0,
    ) -> OdysseyCandidateScore:
        cx, cy = current_center
        tx, ty = match.center
        distance = math.hypot(tx - cx, ty - cy)
        if ty >= cy - min_upward_px:
            return OdysseyCandidateScore(match, 0.0, 0, distance, False, "candidate is not above current node")
        if distance <= endpoint_skip * 2:
            return OdysseyCandidateScore(match, 0.0, 0, distance, False, "candidate is too close to score corridor")

        corridor = np.zeros_like(dotted_mask)
        cv2.line(corridor, (cx, cy), (tx, ty), 255, corridor_width)
        cv2.circle(corridor, (cx, cy), endpoint_skip, 0, -1)
        cv2.circle(corridor, (tx, ty), endpoint_skip, 0, -1)
        corridor_pixels = cv2.countNonZero(corridor)
        dotted_pixels = cv2.countNonZero(cv2.bitwise_and(dotted_mask, corridor))
        corridor_score = dotted_pixels / max(1, corridor_pixels)
        segment_hits = OdysseyFlowService._score_corridor_segments(
            dotted_mask,
            current_center,
            (tx, ty),
            corridor_width=max(8, corridor_width // 2),
            endpoint_skip=endpoint_skip,
            segment_count=segment_count,
            min_segment_dotted_pixels=min_segment_dotted_pixels,
        )
        covered_segments = sum(1 for hit in segment_hits if hit)
        source_hits = sum(1 for hit in segment_hits[:source_segment_count] if hit)
        path_coverage = covered_segments / max(1, len(segment_hits))
        longest_empty_run = OdysseyFlowService._longest_false_run(segment_hits)
        source_ray_pixels = OdysseyFlowService._count_source_ray_pixels(
            dotted_mask,
            current_center,
            (tx, ty),
            min_radius=max(28, endpoint_skip - 8),
            max_radius=max(58, endpoint_skip + 32),
            max_angle_degrees=max_source_ray_angle_degrees,
        )
        if corridor_score < min_corridor_score:
            accepted = False
            reason = f"corridor score below threshold ({corridor_score:.4f} < {min_corridor_score:.4f})"
        elif source_ray_pixels < min_source_ray_pixels:
            accepted = False
            reason = (
                "no direct dotted branch from current ring "
                f"(ray pixels {source_ray_pixels} < {min_source_ray_pixels})"
            )
        elif source_hits < min_source_segments:
            accepted = False
            reason = f"no dotted path leaving current node (source hits {source_hits}/{source_segment_count})"
        elif path_coverage < min_path_coverage:
            accepted = False
            reason = f"path segment coverage below threshold ({path_coverage:.2f} < {min_path_coverage:.2f})"
        elif longest_empty_run > max_consecutive_empty_segments:
            accepted = False
            reason = f"path has too large a gap ({longest_empty_run} empty segments)"
        else:
            accepted = True
            reason = (
                "connected "
                f"(segments {covered_segments}/{len(segment_hits)}, "
                f"source {source_hits}/{source_segment_count}, ray {source_ray_pixels})"
            )
        return OdysseyCandidateScore(match, corridor_score, dotted_pixels, distance, accepted, reason)

    @staticmethod
    def _count_source_ray_pixels(
        dotted_mask: np.ndarray,
        current_center: tuple[int, int],
        target_center: tuple[int, int],
        *,
        min_radius: int,
        max_radius: int,
        max_angle_degrees: float,
    ) -> int:
        cx, cy = current_center
        tx, ty = target_center
        target_dx = tx - cx
        target_dy = ty - cy
        target_distance = math.hypot(target_dx, target_dy)
        if target_distance <= 0:
            return 0
        target_angle = math.atan2(target_dy, target_dx)
        ys, xs = np.nonzero(dotted_mask)
        if len(xs) == 0:
            return 0
        dx = xs.astype(np.float32) - float(cx)
        dy = ys.astype(np.float32) - float(cy)
        distances = np.hypot(dx, dy)
        annulus = (distances >= float(min_radius)) & (distances <= float(max_radius)) & (dy < 0)
        if not np.any(annulus):
            return 0
        angles = np.arctan2(dy[annulus], dx[annulus])
        angle_delta = np.abs(np.arctan2(np.sin(angles - target_angle), np.cos(angles - target_angle)))
        return int(np.count_nonzero(angle_delta <= math.radians(max_angle_degrees)))

    @staticmethod
    def _score_corridor_segments(
        dotted_mask: np.ndarray,
        current_center: tuple[int, int],
        target_center: tuple[int, int],
        *,
        corridor_width: int,
        endpoint_skip: int,
        segment_count: int,
        min_segment_dotted_pixels: int,
    ) -> list[bool]:
        cx, cy = current_center
        tx, ty = target_center
        dx = tx - cx
        dy = ty - cy
        distance = math.hypot(dx, dy)
        if distance <= endpoint_skip * 2 or segment_count <= 0:
            return []
        ux = dx / distance
        uy = dy / distance
        usable_distance = max(1.0, distance - endpoint_skip * 2)
        hits: list[bool] = []
        for index in range(segment_count):
            start_distance = endpoint_skip + usable_distance * index / segment_count
            end_distance = endpoint_skip + usable_distance * (index + 1) / segment_count
            start = (int(round(cx + ux * start_distance)), int(round(cy + uy * start_distance)))
            end = (int(round(cx + ux * end_distance)), int(round(cy + uy * end_distance)))
            segment_mask = np.zeros_like(dotted_mask)
            cv2.line(segment_mask, start, end, 255, corridor_width)
            dotted_pixels = cv2.countNonZero(cv2.bitwise_and(dotted_mask, segment_mask))
            hits.append(dotted_pixels >= min_segment_dotted_pixels)
        return hits

    @staticmethod
    def _longest_false_run(values: list[bool]) -> int:
        longest = 0
        current = 0
        for value in values:
            if value:
                longest = max(longest, current)
                current = 0
            else:
                current += 1
        return max(longest, current)

    @staticmethod
    def normalize_room_priorities(room_priorities: list[str] | tuple[str, ...] | None) -> tuple[str, str, str]:
        normalized: list[str] = []
        raw_priorities = room_priorities or DEFAULT_ROOM_PRIORITIES
        for raw_priority in raw_priorities:
            text = str(raw_priority).strip().lower()
            for option in ODYSSEY_ROOM_TYPES:
                if text == option.lower() and option not in normalized:
                    normalized.append(option)
                    break
        for option in DEFAULT_ROOM_PRIORITIES:
            if option not in normalized:
                normalized.append(option)
        return tuple(normalized[:3])  # type: ignore[return-value]

    @staticmethod
    def _select_best_connected(
        scores: list[OdysseyCandidateScore],
        room_priorities: tuple[str, str, str],
    ) -> OdysseyCandidateScore | None:
        accepted = [score for score in scores if score.accepted]
        if not accepted:
            return None
        elite_candidates = [score for score in accepted if score.match.name == "elite_boss"]
        if elite_candidates:
            return sorted(elite_candidates, key=lambda score: (score.match.center[0], score.match.center[1]))[0]
        for room_type in room_priorities:
            template_name = _ROOM_TYPE_TO_TEMPLATE[room_type]
            candidates = [score for score in accepted if score.match.name == template_name]
            if candidates:
                return sorted(candidates, key=lambda score: (score.match.center[0], score.match.center[1]))[0]
        return sorted(accepted, key=lambda score: (score.match.center[0], score.match.center[1]))[0]

    @staticmethod
    def _region_center(region: tuple[int, int, int, int]) -> tuple[int, int]:
        left, top, right, bottom = region
        return (left + right) // 2, (top + bottom) // 2

    @staticmethod
    def _display_room_type(template_name: str) -> str:
        return _TEMPLATE_TO_ROOM_TYPE.get(template_name, template_name.title())

    @staticmethod
    def _sleep_interruptibly(seconds: float, stop_requested: Callable[[], bool]) -> bool:
        elapsed = 0.0
        while elapsed < seconds:
            if stop_requested():
                return False
            sleep_time = min(0.05, seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
        return True

    @staticmethod
    def _log(log: Callable[[str], None] | None, message: str) -> None:
        if log is not None:
            log(message)
        else:
            print(message)
