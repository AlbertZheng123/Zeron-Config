"""Legend start-card detection and selection helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from mss import mss

from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import RelativePositioner


BASE_DIR = Path(__file__).resolve().parents[2]
CARDS_DIR = BASE_DIR / "references" / "legend_cards"
LEGEND_CARD_OPTIONS = ("Immunity", "Champion", "Revitalize", "Thrice", "Quake", "Exploding")
LEGEND_CARD_REGION = (133, 205, 1050, 359)
LEGEND_CARD_THRESHOLD = 0.95
LEGEND_CARD_OVERLAP_THRESHOLD = 0.25
LEGEND_CARD_SCROLL_AMOUNT = 20
LEGEND_CARD_RIGHT_REPEATS = 12
LEGEND_CARD_LEFT_REPEATS = 12
LEGEND_CARD_SCROLL_DELAY = 0.08
LEGEND_CARD_SETTLE_DELAY = 0.5
LEGEND_CARD_CLICK_SETTLE_DELAY = 0.1
LEGEND_CARD_POST_SELECTION_DELAY = 0.9
LEGEND_DETECTION_SETTLE_DELAY = 0.12


@dataclass(frozen=True)
class CardMatch:
    name: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


class LegendCardSelector:
    """Detect and click a selected legend card after carousel scrolling."""

    def __init__(self) -> None:
        self._templates_cache: dict[float, dict[str, tuple[np.ndarray, np.ndarray | None]]] = {}
        self._relative_positioner: RelativePositioner | None = None
        self._detection_profiler: DetectionProfiler | None = None
        self._screen_capture: mss | None = None
        self._runtime_screen_capture = None

    def set_runtime_context(
        self,
        *,
        relative_positioner: RelativePositioner | None = None,
        detection_profiler: DetectionProfiler | None = None,
        screen_capture=None,
    ) -> None:
        self._relative_positioner = relative_positioner
        self._detection_profiler = detection_profiler
        self._runtime_screen_capture = screen_capture

    def select_card(
        self,
        pyautogui,
        selected_card: str,
        *,
        log=None,
        stop_requested=None,
    ) -> bool:
        target_name = str(selected_card).strip()
        if target_name not in LEGEND_CARD_OPTIONS:
            if log:
                log(f"Legend card selection skipped: unsupported card '{selected_card}'")
            return False

        def should_stop() -> bool:
            return bool(stop_requested and stop_requested())

        if log:
            log(f"Legend card selection: {target_name}")

        if should_stop():
            return False

        self._horizontal_scroll(pyautogui, abs(LEGEND_CARD_SCROLL_AMOUNT), LEGEND_CARD_RIGHT_REPEATS, should_stop)
        time.sleep(LEGEND_CARD_SETTLE_DELAY)
        if should_stop():
            return False

        right_matches = self.detect_visible_cards(pyautogui)
        right_match = self._find_match(right_matches, target_name)
        if right_match is not None:
            self._click_match(pyautogui, right_match)
            time.sleep(LEGEND_CARD_POST_SELECTION_DELAY)
            if log:
                log(f"Legend card selected on right: {target_name} ({right_match.confidence:.3f})")
            return True

        if log:
            self._log_visible_cards(log, "right", right_matches)
            log(f"{target_name} not on right side, scrolling left...")

        self._horizontal_scroll(pyautogui, -abs(LEGEND_CARD_SCROLL_AMOUNT), LEGEND_CARD_LEFT_REPEATS, should_stop)
        time.sleep(LEGEND_CARD_SETTLE_DELAY)
        if should_stop():
            return False

        left_matches = self.detect_visible_cards(pyautogui)
        left_match = self._find_match(left_matches, target_name)
        if left_match is not None:
            self._click_match(pyautogui, left_match)
            time.sleep(LEGEND_CARD_POST_SELECTION_DELAY)
            if log:
                log(f"Legend card selected on left: {target_name} ({left_match.confidence:.3f})")
            return True

        if log:
            self._log_visible_cards(log, "left", left_matches)
            log(f"Legend card not found: {target_name}")
        return False

    def detect_visible_cards(self, pyautogui_module=None) -> list[CardMatch]:
        return self._detect_visible_cards_impl(pyautogui_module)

    def _detect_visible_cards_impl(self, pyautogui_module=None) -> list[CardMatch]:
        pyautogui_module = pyautogui_module or self._default_pyautogui()
        scale_factor = self._compute_scale_factor(pyautogui_module)
        time.sleep(LEGEND_DETECTION_SETTLE_DELAY)
        started_at = time.perf_counter()
        region_bgr = self._capture_region(LEGEND_CARD_REGION)
        templates = self._load_templates(scale_factor)
        matches = self._match_templates(region_bgr, templates, LEGEND_CARD_THRESHOLD)
        if self._detection_profiler is not None:
            self._detection_profiler.record("legend_cards", time.perf_counter() - started_at)
        return sorted(matches, key=lambda match: match.x)

    @staticmethod
    def _default_pyautogui():
        import pyautogui

        return pyautogui

    def _compute_scale_factor(self, pyautogui_module) -> float:
        screenshot = pyautogui_module.screenshot()
        screen_w, _ = pyautogui_module.size()
        return screenshot.size[0] / screen_w

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

    def _load_templates(self, scale_factor: float) -> dict[str, tuple[np.ndarray, np.ndarray | None]]:
        cache_key = round(scale_factor, 3)
        cached = self._templates_cache.get(cache_key)
        if cached is not None:
            return cached

        templates: dict[str, tuple[np.ndarray, np.ndarray | None]] = {}
        for path in sorted(CARDS_DIR.glob("*.png")):
            image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if image is None:
                continue

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

            display_name = path.stem.replace("_start_ref", "").replace("_", " ").title()
            templates[display_name] = (image, mask)

        self._templates_cache[cache_key] = templates
        return templates

    def _match_templates(
        self,
        region_bgr: np.ndarray,
        templates: dict[str, tuple[np.ndarray, np.ndarray | None]],
        threshold: float,
    ) -> list[CardMatch]:
        matches: list[CardMatch] = []
        for name, (template, mask) in templates.items():
            if region_bgr.shape[0] < template.shape[0] or region_bgr.shape[1] < template.shape[1]:
                continue

            if mask is not None:
                result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
            else:
                result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val < threshold:
                continue

            template_h, template_w = template.shape[:2]
            matches.append(
                CardMatch(
                    name=name,
                    x=int(max_loc[0]),
                    y=int(max_loc[1]),
                    width=template_w,
                    height=template_h,
                    confidence=float(max_val),
                )
            )
        return self._non_maximum_suppression(matches)

    def _non_maximum_suppression(self, matches: list[CardMatch]) -> list[CardMatch]:
        kept: list[CardMatch] = []
        for match in sorted(matches, key=lambda item: item.confidence, reverse=True):
            if any(self._overlap_ratio(match, existing) > LEGEND_CARD_OVERLAP_THRESHOLD for existing in kept):
                continue
            kept.append(match)
        return kept

    @staticmethod
    def _overlap_ratio(left: CardMatch, right: CardMatch) -> float:
        x1 = max(left.x, right.x)
        y1 = max(left.y, right.y)
        x2 = min(left.x + left.width, right.x + right.width)
        y2 = min(left.y + left.height, right.y + right.height)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        overlap = (x2 - x1) * (y2 - y1)
        smaller = max(1, min(left.width * left.height, right.width * right.height))
        return overlap / smaller

    @staticmethod
    def _find_match(matches: list[CardMatch], selected_card: str) -> CardMatch | None:
        for match in matches:
            if match.name == selected_card:
                return match
        return None

    @staticmethod
    def _log_visible_cards(log, side: str, matches: list[CardMatch]) -> None:
        if not matches:
            log(f"Legend cards visible on {side}: none")
            return
        summary = ", ".join(f"{match.name} ({match.confidence:.3f})" for match in matches)
        log(f"Legend cards visible on {side}: {summary}")

    @staticmethod
    def _horizontal_scroll(pyautogui, amount: int, repeats: int, should_stop) -> None:
        for _ in range(repeats):
            if should_stop():
                return
            pyautogui.hscroll(amount)
            time.sleep(LEGEND_CARD_SCROLL_DELAY)

    @staticmethod
    def _click_match(pyautogui, match: CardMatch) -> None:
        click_x = LEGEND_CARD_REGION[0] + match.x + (match.width // 2)
        click_y = LEGEND_CARD_REGION[1] + match.y + (match.height // 2)
        pyautogui.moveTo(click_x, click_y)
        time.sleep(LEGEND_CARD_CLICK_SETTLE_DELAY)
        pyautogui.click()
        time.sleep(0.3)
