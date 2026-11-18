"""Reward screen parsing with scoped icon matching and RapidOCR amounts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from mss import mss

from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import RelativePositioner

BASE_DIR = Path(__file__).resolve().parents[2]
REWARD_ICONS_DIR = BASE_DIR / "references" / "reward_icons"

REWARD_REGION = (210, 439, 664, 516)
AMOUNT_REGION = (219, 487, 666, 510)
REWARD_CONFIDENCE_THRESHOLD = 0.70
REWARD_TEMPLATE_SCALES = (1.0, 0.9, 0.8, 0.75, 0.67, 0.5)

MODE_FOLDER_CANDIDATES = {
    "story": ("story",),
    "legend": ("legend",),
    "raids": ("raids", "raid"),
    "raid": ("raid", "raids"),
    "bossRush": ("bossRush", "boss_rush", "boss"),
    "events": ("events", "event"),
    "event": ("event", "events"),
    "dungeon": ("dungeon", "dungeons"),
    "dungeons": ("dungeons", "dungeon"),
}


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())

REWARD_NAME_OVERRIDES = {
    "blood_swords": "Blood Sword",
    "bone": "Doggy Bone",
    "doggy_bone": "Doggy Bone",
    "gems": "Gems",
    "gold": "Gold",
    "green_essence": "Green Essence",
    "grenade": "Grenade",
    "memoria_rr": "Memoria Reroll",
    "rainbow_essence_stone": "Rainbow Essence Stone",
    "shackled_memoria": "Shackled Memoria",
    "super_stat": "Super Stat Chip",
    "trait_rr": "Trait Reroll",
}


@dataclass(frozen=True)
class RewardIconDetection:
    x: int
    y: int
    width: int
    height: int
    name: str
    confidence: float
    source: str


@dataclass(frozen=True)
class RewardAmountDetection:
    x: float
    right: float
    value: int
    text: str
    confidence: float
    has_x_prefix: bool


@dataclass(frozen=True)
class RewardParseResult:
    rewards: dict[str, int]
    icons: list[RewardIconDetection]
    amounts: list[RewardAmountDetection]
    warning: str | None = None

    @property
    def ok(self) -> bool:
        return self.warning is None


class RewardDetector:
    """Detect visible reward icons and pair them with RapidOCR amount labels."""

    def __init__(self, reward_icons_dir: Path = REWARD_ICONS_DIR, *, ocr_scale: int = 5) -> None:
        self.reward_icons_dir = reward_icons_dir
        self.ocr_scale = ocr_scale
        self._reader = None
        self._template_cache: dict[tuple[str | None, str | None], dict[str, np.ndarray]] = {}
        self._scaled_template_cache: dict[tuple[str | None, str | None], dict[str, tuple[np.ndarray, ...]]] = {}
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

    def parse_screen_rewards(self, mode: str | None, map_name: str | None) -> RewardParseResult:
        profiler = self._detection_profiler
        if profiler is not None:
            with profiler.track("reward_parse"):
                return self._parse_screen_rewards_impl(mode, map_name)
        return self._parse_screen_rewards_impl(mode, map_name)

    def _parse_screen_rewards_impl(self, mode: str | None, map_name: str | None) -> RewardParseResult:
        reward_region_bgr = self._capture_region(REWARD_REGION)
        amount_region_bgr = self._capture_region(AMOUNT_REGION)
        return self.parse_regions(reward_region_bgr, amount_region_bgr, mode, map_name)

    def parse_regions(
        self,
        reward_region_bgr: np.ndarray,
        amount_region_bgr: np.ndarray,
        mode: str | None,
        map_name: str | None,
    ) -> RewardParseResult:
        templates = self.load_scaled_reward_templates(mode, map_name)
        icons = self.detect_reward_icons(reward_region_bgr, templates)
        amounts = self.detect_amounts(amount_region_bgr)

        if len(icons) != len(amounts):
            warning = (
                f"Reward parse count mismatch: icons={len(icons)} amounts={len(amounts)}. "
                "Stats were not updated."
            )
            return RewardParseResult({}, icons, amounts, warning)

        rewards: dict[str, int] = {}
        for icon, amount in zip(icons, amounts):
            rewards[icon.name] = rewards.get(icon.name, 0) + amount.value
        return RewardParseResult(rewards, icons, amounts)

    def load_reward_templates(self, mode: str | None, map_name: str | None) -> dict[str, np.ndarray]:
        cache_key = (mode, map_name)
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        templates: dict[str, np.ndarray] = {}
        for folder in self._template_folders(mode, map_name):
            for path in sorted(folder.glob("*_ref.png")):
                if path.name == "bone_menu_ref.png":
                    continue
                image = cv2.imread(str(path))
                if image is None:
                    continue
                templates[self._reward_name_from_template_path(path)] = image

        self._template_cache[cache_key] = templates
        return templates

    def load_scaled_reward_templates(self, mode: str | None, map_name: str | None) -> dict[str, tuple[np.ndarray, ...]]:
        cache_key = (mode, map_name)
        if cache_key in self._scaled_template_cache:
            return self._scaled_template_cache[cache_key]

        raw_templates = self.load_reward_templates(mode, map_name)
        scaled_templates = {
            reward_name: tuple(self._scale_template(template, scale) for scale in REWARD_TEMPLATE_SCALES)
            for reward_name, template in raw_templates.items()
        }
        self._scaled_template_cache[cache_key] = scaled_templates
        return scaled_templates

    def detect_reward_icons(
        self,
        reward_region_bgr: np.ndarray,
        templates: dict[str, tuple[np.ndarray, ...]],
    ) -> list[RewardIconDetection]:
        detections: list[RewardIconDetection] = []
        for reward_name, scaled_variants in templates.items():
            for scaled_template in scaled_variants:
                template_height, template_width = scaled_template.shape[:2]
                if template_height > reward_region_bgr.shape[0] or template_width > reward_region_bgr.shape[1]:
                    continue

                result = cv2.matchTemplate(reward_region_bgr, scaled_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= REWARD_CONFIDENCE_THRESHOLD)
                for y, x in zip(*locations):
                    detections.append(
                        RewardIconDetection(
                            x=int(x),
                            y=int(y),
                            width=template_width,
                            height=template_height,
                            name=reward_name,
                            confidence=float(result[y, x]),
                            source=reward_name,
                        )
                    )
        return self._non_maximum_suppression(detections)

    def detect_amounts(self, amount_region_bgr: np.ndarray) -> list[RewardAmountDetection]:
        processed = self._preprocess_for_ocr(amount_region_bgr)
        results = self._run_rapidocr(processed)
        candidates: list[RewardAmountDetection] = []
        for text, confidence, bbox in results:
            amount = self._extract_amount_value(text)
            if amount is None:
                continue
            value, has_x_prefix = amount
            if value is None:
                continue
            candidates.append(
                RewardAmountDetection(
                    x=self._bbox_left(bbox),
                    right=self._bbox_right(bbox),
                    value=value,
                    text=text,
                    confidence=confidence,
                    has_x_prefix=has_x_prefix,
                )
            )
        return self._filter_amount_candidates(candidates)

    def _template_folders(self, mode: str | None, map_name: str | None) -> list[Path]:
        folders: list[Path] = []
        common = self.reward_icons_dir / "common"
        if common.is_dir():
            folders.append(common)

        if mode and map_name:
            mode_candidates = MODE_FOLDER_CANDIDATES.get(mode, (mode,))
            normalized_map = _normalize_name(map_name)
            for mode_folder_name in mode_candidates:
                base_folder = self.reward_icons_dir / mode_folder_name
                if not base_folder.is_dir():
                    continue
                direct_folder = base_folder / map_name
                if direct_folder.is_dir():
                    folders.append(direct_folder)
                    break
                matched_folder = None
                for child in sorted(base_folder.iterdir()):
                    if not child.is_dir():
                        continue
                    normalized_child = _normalize_name(child.name)
                    if normalized_child == normalized_map:
                        matched_folder = child
                        break
                    if normalized_map and (
                        normalized_map in normalized_child or normalized_child in normalized_map
                    ):
                        matched_folder = child
                        break
                if matched_folder is not None:
                    folders.append(matched_folder)
                    break
        return folders

    def _get_reader(self):
        if self._reader is not None:
            return self._reader

        from rapidocr import RapidOCR

        self._reader = RapidOCR(
            params={
                "Global.use_cls": False,
                "Global.text_score": 0.1,
                "Global.min_height": 10,
                "Global.log_level": "warning",
            }
        )
        return self._reader

    def _run_rapidocr(self, image: np.ndarray) -> list[tuple[str, float, list[list[float]]]]:
        output = self._get_reader()(image)
        if len(output) == 0 or output.txts is None or output.scores is None or output.boxes is None:
            return []
        parsed: list[tuple[str, float, list[list[float]]]] = []
        for text, confidence, bbox in zip(output.txts, output.scores, output.boxes):
            parsed.append((str(text), float(confidence), np.asarray(bbox).tolist()))
        return parsed

    def _preprocess_for_ocr(self, amount_region_bgr: np.ndarray) -> np.ndarray:
        return cv2.resize(
            amount_region_bgr,
            (amount_region_bgr.shape[1] * self.ocr_scale, amount_region_bgr.shape[0] * self.ocr_scale),
            interpolation=cv2.INTER_CUBIC,
        )

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

    @staticmethod
    def _scale_template(template: np.ndarray, scale: float) -> np.ndarray:
        if scale == 1.0:
            return template
        scaled_width = max(1, int(template.shape[1] * scale))
        scaled_height = max(1, int(template.shape[0] * scale))
        return cv2.resize(template, (scaled_width, scaled_height), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _reward_name_from_template_path(path: Path) -> str:
        stem = re.sub(r"(?:_rewards?|_reward)?_ref$", "", path.stem)
        if stem in REWARD_NAME_OVERRIDES:
            return REWARD_NAME_OVERRIDES[stem]
        return stem.replace("_", " ").title()

    @staticmethod
    def _extract_amount_value(text: str) -> tuple[int, bool] | None:
        compact = re.sub(r"[^xX×0-9]+", "", text)
        if not compact:
            return None
        prefixed = re.search(r"[xX×]+(\d+)", compact)
        if prefixed:
            return int(prefixed.group(1)), True
        digits = re.search(r"\d+", compact)
        if digits:
            return int(digits.group(0)), False
        return None

    @staticmethod
    def _bbox_left(bbox: list[list[float]]) -> float:
        return min(point[0] for point in bbox)

    @staticmethod
    def _bbox_right(bbox: list[list[float]]) -> float:
        return max(point[0] for point in bbox)

    @staticmethod
    def _x_overlap_ratio(left: RewardAmountDetection, right: RewardAmountDetection) -> float:
        if left.right <= left.x or right.right <= right.x:
            return 0.0
        overlap = max(0.0, min(left.right, right.right) - max(left.x, right.x))
        width = max(1.0, min(left.right - left.x, right.right - right.x))
        return overlap / width

    @classmethod
    def _filter_amount_candidates(cls, candidates: list[RewardAmountDetection]) -> list[RewardAmountDetection]:
        x_prefixed = [candidate for candidate in candidates if candidate.has_x_prefix]
        if x_prefixed:
            kept = list(x_prefixed)
            for candidate in candidates:
                if candidate.has_x_prefix:
                    continue
                if any(cls._x_overlap_ratio(candidate, existing) > 0.35 for existing in x_prefixed):
                    continue
                if candidate.confidence >= 0.85:
                    kept.append(candidate)
            return sorted(kept, key=lambda item: item.x)

        kept: list[RewardAmountDetection] = []
        candidates = sorted(candidates, key=lambda item: (item.x, -item.confidence))
        for candidate in candidates:
            if candidate.confidence < 0.35:
                continue
            if kept and abs(candidate.x - kept[-1].x) < 15:
                if candidate.confidence > kept[-1].confidence:
                    kept[-1] = candidate
                continue
            kept.append(candidate)
        return sorted(kept, key=lambda item: item.x)

    @staticmethod
    def _overlap_ratio(left: RewardIconDetection, right: RewardIconDetection) -> float:
        x1 = max(left.x, right.x)
        y1 = max(left.y, right.y)
        x2 = min(left.x + left.width, right.x + right.width)
        y2 = min(left.y + left.height, right.y + right.height)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        overlap = (x2 - x1) * (y2 - y1)
        smaller_area = max(1, min(left.width * left.height, right.width * right.height))
        return overlap / smaller_area

    @classmethod
    def _non_maximum_suppression(cls, detections: list[RewardIconDetection], threshold: float = 0.3) -> list[RewardIconDetection]:
        kept: list[RewardIconDetection] = []
        for detection in sorted(detections, key=lambda item: item.confidence, reverse=True):
            if any(cls._overlap_ratio(detection, existing) > threshold for existing in kept):
                continue
            kept.append(detection)
        return sorted(kept, key=lambda item: item.x)
