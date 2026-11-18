"""Victory/defeat detection on the replay screen."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import cv2
import numpy as np
from mss import mss

from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import RelativePositioner

BASE_DIR = Path(__file__).resolve().parents[2]
MATCH_RESULTS_DIR = BASE_DIR / "references" / "match_results"
MATCH_RESULT_REGION = (274, 146, 382, 184)
MATCH_RESULT_LABELS = {
    "VICTORY": MATCH_RESULTS_DIR / "victory_ref.png",
    "DEFEAT": MATCH_RESULTS_DIR / "failed_ref.png",
}


@dataclass(frozen=True)
class MatchResultDetection:
    label: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


class MatchResultDetector:
    """Template-match the result banner to classify a run as victory or defeat."""

    def __init__(self) -> None:
        self._template_cache: dict[float, dict[str, tuple[np.ndarray, np.ndarray | None]]] = {}
        self._detection_profiler: DetectionProfiler | None = None
        self._relative_positioner: RelativePositioner | None = None
        self._screen_capture: mss | None = None
        self._runtime_screen_capture = None

    def set_detection_profiler(self, profiler: DetectionProfiler | None) -> None:
        self._detection_profiler = profiler

    def set_runtime_context(
        self,
        *,
        relative_positioner: RelativePositioner | None = None,
        screen_capture=None,
    ) -> None:
        self._relative_positioner = relative_positioner
        self._runtime_screen_capture = screen_capture

    def detect_screen_result(self, *, pyautogui_module=None) -> MatchResultDetection:
        return self._detect_screen_result_impl(pyautogui_module=pyautogui_module)

    def _detect_screen_result_impl(self, *, pyautogui_module=None) -> MatchResultDetection:
        if pyautogui_module is None:
            import pyautogui as pyautogui_module

        scale_factor = self._compute_scale_factor(pyautogui_module)
        started_at = time.perf_counter()
        region_bgr = self._capture_region(MATCH_RESULT_REGION)
        result = self.detect_region_result(region_bgr, scale_factor)
        if self._detection_profiler is not None:
            self._detection_profiler.record("match_result", time.perf_counter() - started_at)
        return result

    def detect_region_result(self, region_bgr: np.ndarray, scale_factor: float = 1.0) -> MatchResultDetection:
        templates = self._load_templates(scale_factor)
        best: MatchResultDetection | None = None
        for label, (template, mask) in templates.items():
            if region_bgr.shape[0] < template.shape[0] or region_bgr.shape[1] < template.shape[1]:
                continue

            if mask is not None:
                result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCORR_NORMED, mask=mask)
            else:
                result = cv2.matchTemplate(region_bgr, template, cv2.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            candidate = MatchResultDetection(
                label=label,
                confidence=float(max_val),
                x=int(max_loc[0]),
                y=int(max_loc[1]),
                width=int(template.shape[1]),
                height=int(template.shape[0]),
            )
            if best is None or candidate.confidence > best.confidence:
                best = candidate

        if best is None:
            return MatchResultDetection("UNKNOWN", 0.0, 0, 0, 0, 0)
        return best

    @staticmethod
    def _compute_scale_factor(pyautogui) -> float:
        screenshot = pyautogui.screenshot()
        screen_w, _ = pyautogui.size()
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
        cached = self._template_cache.get(cache_key)
        if cached is not None:
            return cached

        templates: dict[str, tuple[np.ndarray, np.ndarray | None]] = {}
        for label, path in MATCH_RESULT_LABELS.items():
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

            templates[label] = (image, mask)

        self._template_cache[cache_key] = templates
        return templates
