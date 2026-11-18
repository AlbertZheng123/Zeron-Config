"""Detection helpers for image matching and slot state checks."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime

import cv2
import numpy as np
import pyautogui
from mss import mss

from macro_app import constants
from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.relative_positioning import RelativePositioningError, RelativePositioner


class DetectionService:
    """Owns detection template setup and screen matching logic."""

    def __init__(self) -> None:
        self._templates: dict[str, np.ndarray] = {}
        self._scale_factor = 1.0
        self._yen_zero_template: np.ndarray | None = None
        self._screen_capture: mss | None = None
        self._pyautogui = pyautogui
        self._relative_positioner: RelativePositioner | None = None
        self._runtime_screen_capture = None
        self._detection_profiler: DetectionProfiler | None = None
        self._templates_initialized = False
        self._template_init_lock = threading.Lock()
        self._last_vote_probe = "unavailable"
        self._last_detection_error: str | None = None
        self._vote_debug_saved = False

    def set_runtime_context(
        self,
        *,
        pyautogui_module=None,
        relative_positioner: RelativePositioner | None = None,
        detection_profiler: DetectionProfiler | None = None,
        screen_capture=None,
    ) -> None:
        self._pyautogui = pyautogui_module or pyautogui
        self._relative_positioner = relative_positioner
        self._detection_profiler = detection_profiler
        self._runtime_screen_capture = screen_capture
        if screen_capture is not None:
            self._vote_debug_saved = False

    def _get_screen_capture(self) -> mss:
        if self._screen_capture is None:
            self._screen_capture = mss()
        return self._screen_capture

    def _capture_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._runtime_screen_capture is not None:
            return self._runtime_screen_capture.capture_region_bgr(region)
        left, top, right, bottom = region
        width = right - left
        height = bottom - top
        shot = self._get_screen_capture().grab(
            {"left": left, "top": top, "width": width, "height": height}
        )
        return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)

    def _capture_base_region_bgr(self, region: tuple[int, int, int, int]) -> np.ndarray:
        if self._runtime_screen_capture is not None:
            return self._runtime_screen_capture.capture_base_region_bgr(region)
        translated = self._relative_positioner.translate_region(region) if self._relative_positioner else region
        return self._capture_region_bgr(translated)

    def init_templates(self) -> None:
        """Pre-load and cache all template images, scaled for the display."""
        if self._templates_initialized:
            return
        with self._template_init_lock:
            if self._templates_initialized:
                return

            test_shot = self._pyautogui.screenshot()
            screen_w, _ = self._pyautogui.size()
            self._scale_factor = test_shot.size[0] / screen_w
            print(f"[detection] Scale factor: {self._scale_factor}")

            template_configs = [
                ("vote_button", constants.VOTE_BUTTON_IMAGE),
                ("wave_completed", constants.WAVE_COMPLETED_IMAGE),
                ("replay", constants.REPLAY_IMAGE),
                ("replay_4", constants.REPLAY_IMAGE_4),
                ("replay_5", constants.REPLAY_IMAGE_5),
            ]

            for name, path in template_configs:
                template = cv2.imread(path)
                if template is None:
                    print(f"[detection] WARNING: Could not load {path}")
                    continue

                if self._scale_factor > 1:
                    new_w = int(template.shape[1] / self._scale_factor)
                    new_h = int(template.shape[0] / self._scale_factor)
                    template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

                self._templates[name] = template
                print(f"[detection] Loaded '{name}': {template.shape[1]}x{template.shape[0]}")

            self._templates_initialized = True

    def detect_image(self, template_name: str, region: tuple[int, int, int, int], confidence: float = 0.7):
        """Detect an image in a region using OpenCV template matching."""
        profiler = self._detection_profiler
        track_name = f"detection:{template_name}"
        if profiler is not None:
            with profiler.track(track_name):
                return self._detect_image_impl(template_name, region, confidence)
        return self._detect_image_impl(template_name, region, confidence)

    def _detect_image_impl(self, template_name: str, region: tuple[int, int, int, int], confidence: float = 0.7):
        if not self._templates_initialized:
            self.init_templates()
        if template_name not in self._templates:
            print(f"[detection] Template '{template_name}' not loaded")
            return (False, 0, 0, 0, 0, 0)

        template = self._templates[template_name]
        left, top, _, _ = region

        try:
            self._last_detection_error = None
            screenshot_bgr = self._capture_base_region_bgr(region)

            if screenshot_bgr.shape[0] < template.shape[0] or screenshot_bgr.shape[1] < template.shape[1]:
                return (False, 0, 0, 0, 0, 0)

            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                template_h, template_w = template.shape[:2]
                center_x = left + max_loc[0] + template_w // 2
                center_y = top + max_loc[1] + template_h // 2
                return (True, center_x, center_y, template_w, template_h, max_val)

            return (False, 0, 0, 0, 0, max_val)
        except RelativePositioningError:
            raise
        except Exception as exc:
            self._last_detection_error = f"{type(exc).__name__}: {exc}"
            print(f"[detection] Error: {exc}")
            return (False, 0, 0, 0, 0, 0)

    def detect_any_image(self, template_names: tuple[str, ...], region: tuple[int, int, int, int], confidence: float = 0.7):
        """Detect the best match among several template names."""
        best = (False, 0, 0, 0, 0, 0, "")
        for template_name in template_names:
            found, center_x, center_y, width, height, conf = self.detect_image(template_name, region, confidence)
            if conf > best[5]:
                best = (found, center_x, center_y, width, height, conf, template_name)
            if found:
                return (found, center_x, center_y, width, height, conf, template_name)
        return best

    def detect_and_click_vote_button(self) -> bool:
        """Detect the vote button and click it."""
        found, center_x, center_y, _, _, conf = self.detect_image(
            "vote_button",
            constants.VOTE_BUTTON_REGION,
            constants.VOTE_BUTTON_CONFIDENCE,
        )
        padded_conf = 0.0
        if not found and self._runtime_screen_capture is not None:
            left, top, right, bottom = constants.VOTE_BUTTON_REGION
            padded_region = (left - 30, top - 30, right + 30, bottom + 30)
            found, center_x, center_y, _, _, padded_conf = self.detect_image(
                "vote_button",
                padded_region,
                constants.VOTE_BUTTON_CONFIDENCE,
            )
        diagnostics = {}
        capture_name = "none"
        if self._runtime_screen_capture is not None:
            capture_name = type(self._runtime_screen_capture).__name__
            get_diagnostics = getattr(self._runtime_screen_capture, "diagnostics", None)
            if callable(get_diagnostics):
                diagnostics = get_diagnostics()
        frame_count = diagnostics.get("frame_count")
        frame_age = diagnostics.get("frame_age")
        frame_summary = ""
        if frame_count is not None:
            age_summary = f"{frame_age:.2f}s" if frame_age is not None else "unknown"
            frame_summary = f" frames={frame_count} frame_age={age_summary}"
        self._last_vote_probe = (
            f"exact={conf:.3f} padded={padded_conf:.3f} "
            f"threshold={constants.VOTE_BUTTON_CONFIDENCE:.3f} capture={capture_name}"
            f"{frame_summary}"
        )
        if self._last_detection_error:
            self._last_vote_probe += f" error={self._last_detection_error}"
        if found:
            selected_confidence = max(conf, padded_conf)
            print(f"[detection] Vote button FOUND (conf={selected_confidence:.3f})")
            self._pyautogui.moveTo(center_x, center_y)
            time.sleep(0.2)
            self._pyautogui.click()
            return True
        return False

    def vote_probe_summary(self) -> str:
        return self._last_vote_probe

    def save_vote_debug_snapshot(self) -> str:
        if self._vote_debug_saved:
            return ""
        self._vote_debug_saved = True
        output_dir = os.path.join(
            constants.DEBUG_OUTPUT_DIR,
            "game_start",
            datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        os.makedirs(output_dir, exist_ok=True)
        regions = {
            "full_window": (0, 40, 1200, 670),
            "vote_exact": constants.VOTE_BUTTON_REGION,
            "vote_padded": (
                constants.VOTE_BUTTON_REGION[0] - 30,
                constants.VOTE_BUTTON_REGION[1] - 30,
                constants.VOTE_BUTTON_REGION[2] + 30,
                constants.VOTE_BUTTON_REGION[3] + 30,
            ),
        }
        try:
            for label, region in regions.items():
                image = self._capture_base_region_bgr(region)
                cv2.imwrite(os.path.join(output_dir, f"{label}.png"), image)
            template = self._templates.get("vote_button")
            if template is not None:
                cv2.imwrite(os.path.join(output_dir, "vote_template_scaled.png"), template)
        except Exception as exc:
            error_path = os.path.join(output_dir, "capture_error.txt")
            with open(error_path, "w", encoding="utf-8") as file:
                file.write(f"{type(exc).__name__}: {exc}\n")
        return output_dir

    def wait_for_wave_completed(self, check_stop_fn=None) -> str:
        """Wait for wave completed, returning wave_completed, failed, or stopped."""
        start_time = time.time()
        timeout_seconds = 300

        while True:
            if check_stop_fn and check_stop_fn():
                return "stopped"

            found, _, _, _, _, conf = self.detect_image(
                "wave_completed",
                constants.WAVE_COMPLETED_REGION,
                constants.WAVE_COMPLETED_CONFIDENCE,
            )
            if found:
                print(f"[detection] Wave completed detected! (conf={conf:.3f})")
                return "wave_completed"

            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                print(f"[detection] Wave timeout ({timeout_seconds}s). Checking for replay...")
                replay_found, _, _, _, _, _, replay_template = self.detect_any_image(
                    ("replay", "replay_4", "replay_5"),
                    constants.REPLAY_REGION,
                    constants.REPLAY_CONFIDENCE,
                )
                if replay_found:
                    print(f"[detection] FAILURE - Replay button found ({replay_template})!")
                    return "failed"
                start_time = time.time()
                print("[detection] No replay found. Continuing to wait...")

            time.sleep(0.1)

    @staticmethod
    def create_yellow_mask(img):
        """Create a binary mask of yellow/gold pixels."""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, (15, 80, 150), (45, 255, 255))

    def _load_yen_zero_template(self):
        """Load and cache the yellow zero template used for empty-slot detection."""
        ref_path = os.path.join(constants.REFERENCES_DIR, "yen_of_unit_ref.png")
        img = cv2.imread(ref_path)
        if img is None:
            print("[is_equip_slot_empty] WARNING: Could not load yen_of_unit_ref.png")
            return None

        test_shot = self._pyautogui.screenshot()
        screen_w, _ = self._pyautogui.size()
        scale = test_shot.size[0] / screen_w
        if scale > 1:
            new_w = int(img.shape[1] / scale)
            new_h = int(img.shape[0] / scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        mask = self.create_yellow_mask(img)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("[is_equip_slot_empty] WARNING: No yellow contours in yen_of_unit_ref.png")
            return None

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        bx1, by1, bx2, by2 = x, y, x + w, y + h
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            if cx < bx2 and cx + cw > bx1:
                bx1, by1 = min(bx1, cx), min(by1, cy)
                bx2, by2 = max(bx2, cx + cw), max(by2, cy + ch)

        pad = 2
        crop_x1 = max(0, bx1 - pad)
        crop_y1 = max(0, by1 - pad)
        crop_x2 = min(mask.shape[1], bx2 + pad)
        crop_y2 = min(mask.shape[0], by2 + pad)
        template = mask[crop_y1:crop_y2, crop_x1:crop_x2]

        print(f"[is_equip_slot_empty] Loaded '0' template: {template.shape[1]}x{template.shape[0]} (scale={scale})")
        return template

    def is_equip_slot_empty(self, equip_x: int, equip_y: int) -> bool:
        """Return True when the equip slot looks empty."""
        return self._is_equip_slot_empty_impl(equip_x, equip_y)

    def _is_equip_slot_empty_impl(self, equip_x: int, equip_y: int) -> bool:
        region = constants.UNIT_SLOT_REGIONS.get(equip_x)
        if region is None:
            print(f"[is_equip_slot_empty] WARNING: No slot region for equip_x={equip_x}")
            return False

        if self._yen_zero_template is None:
            self._yen_zero_template = self._load_yen_zero_template()
            if self._yen_zero_template is None:
                return False

        template = self._yen_zero_template
        t_h, t_w = template.shape[:2]

        try:
            started_at = time.perf_counter()
            screenshot_bgr = self._capture_base_region_bgr(region)
            yellow_mask = self.create_yellow_mask(screenshot_bgr)

            if yellow_mask.shape[0] < t_h or yellow_mask.shape[1] < t_w:
                if self._detection_profiler is not None:
                    self._detection_profiler.record("equip_slot_empty", time.perf_counter() - started_at)
                return True

            result = cv2.matchTemplate(yellow_mask, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if self._detection_profiler is not None:
                self._detection_profiler.record("equip_slot_empty", time.perf_counter() - started_at)

            is_empty = max_val < 0.70
            if is_empty:
                print(f"[is_equip_slot_empty] Slot at ({equip_x}, {equip_y}) is EMPTY (no '0' found, conf={max_val:.3f})")
            return is_empty
        except RelativePositioningError:
            raise
        except Exception as exc:
            print(f"[is_equip_slot_empty] Detection error: {exc}")
            return False
