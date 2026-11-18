"""Discord webhook helpers."""

from __future__ import annotations

import io
import json

import cv2
import numpy as np
import requests
from mss import mss

from macro_app.constants import DISCORD_SCREENSHOT_REGION
from macro_app.services.relative_positioning import RelativePositioningError, RelativePositioner


def capture_screenshot_for_discord(
    region: tuple[int, int, int, int] | None = None,
    *,
    relative_positioner: RelativePositioner | None = None,
    screen_capture=None,
):
    """Capture the configured screenshot region and return PNG bytes."""
    left, top, right, bottom = region or DISCORD_SCREENSHOT_REGION
    if screen_capture is not None:
        screenshot_bgr = screen_capture.capture_base_region_bgr((left, top, right, bottom))
        screenshot = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2RGB)
        success, encoded = cv2.imencode(".png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))
        if not success:
            raise RuntimeError("Failed to encode Discord screenshot")
        img_buffer = io.BytesIO()
        img_buffer.write(encoded.tobytes())
        img_buffer.seek(0)
        return img_buffer
    if relative_positioner is not None:
        left, top, right, bottom = relative_positioner.translate_region((left, top, right, bottom))
    width = right - left
    height = bottom - top

    with mss() as capture:
        shot = capture.grab({"left": left, "top": top, "width": width, "height": height})
    screenshot = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2RGB)
    success, encoded = cv2.imencode(".png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))
    if not success:
        raise RuntimeError("Failed to encode Discord screenshot")
    img_buffer = io.BytesIO()
    img_buffer.write(encoded.tobytes())
    img_buffer.seek(0)
    return img_buffer


class WebhookService:
    """Send optional screenshot notifications to Discord."""

    EMBED_COLORS = {
        "VICTORY": 0x10B981,
        "DEFEAT": 0xEF4444,
    }

    def __init__(self) -> None:
        self._runtime_screen_capture = None

    def set_screen_capture(self, screen_capture) -> None:
        self._runtime_screen_capture = screen_capture

    def send_payload(
        self,
        url: str,
        enabled: bool,
        payload: dict,
        *,
        include_screenshot: bool = False,
        screenshot_region: tuple[int, int, int, int] | None = None,
        relative_positioner: RelativePositioner | None = None,
    ) -> bool:
        if not enabled or not url:
            print("Discord webhook not enabled or URL not set")
            return False

        try:
            if include_screenshot:
                print("Capturing screenshot for Discord...")
                img_buffer = capture_screenshot_for_discord(
                    screenshot_region,
                    relative_positioner=relative_positioner,
                    screen_capture=self._runtime_screen_capture,
                )
                files = {"file": ("macro_screenshot.png", img_buffer, "image/png")}
                response = requests.post(
                    url,
                    data={"payload_json": json.dumps(payload)},
                    files=files,
                    timeout=(5, 10),
                )
            else:
                response = requests.post(url, json=payload, timeout=(5, 10))

            if response.status_code in [200, 204]:
                print("Discord notification sent")
                return True

            print(f"Discord notification failed: {response.status_code} - {response.text}")
            return False
        except Exception as exc:
            if isinstance(exc, RelativePositioningError):
                raise
            print(f"Discord notification error: {exc}")
            return False

    def send(
        self,
        url: str,
        enabled: bool,
        message: str,
        include_screenshot: bool = True,
        *,
        screenshot_region: tuple[int, int, int, int] | None = None,
        relative_positioner: RelativePositioner | None = None,
    ) -> bool:
        payload = {"content": message}
        return self.send_payload(
            url,
            enabled,
            payload,
            include_screenshot=include_screenshot,
            screenshot_region=screenshot_region,
            relative_positioner=relative_positioner,
        )

    def send_result_embed(
        self,
        url: str,
        enabled: bool,
        *,
        match_result: str,
        rewards: dict[str, int],
        gamemode: str,
        map_name: str,
        elapsed: str,
        screenshot_region: tuple[int, int, int, int] | None = None,
        relative_positioner: RelativePositioner | None = None,
    ) -> bool:
        result_key = (match_result or "").strip().upper() or "VICTORY"
        reward_lines = "\n".join(f"+{amount} {name}" for name, amount in rewards.items()) if rewards else "None"
        embed = {
            "title": "Zeron Config",
            "description": "",
            "color": self.EMBED_COLORS.get(result_key, self.EMBED_COLORS["VICTORY"]),
            "image": {"url": "attachment://macro_screenshot.png"},
            "fields": [
                {
                    "name": "🏁 **MATCH RESULTS**",
                    "value": result_key,
                    "inline": True,
                },
                {
                    "name": "\u200b",
                    "value": "\u200b",
                    "inline": True,
                },
                {
                    "name": "⏱️ **TIME ELAPSED**",
                    "value": elapsed,
                    "inline": True,
                },
                {
                    "name": "🗓️ **TASK**",
                    "value": f"{gamemode} - {map_name}",
                    "inline": True,
                },
                {
                    "name": "\u200b",
                    "value": "\u200b",
                    "inline": True,
                },
                {
                    "name": "🎁 **REWARDS**",
                    "value": reward_lines,
                    "inline": True,
                },
            ],
            "footer": {"text": "Zeron Config"},
        }
        payload = {"content": "", "embeds": [embed]}
        return self.send_payload(
            url,
            enabled,
            payload,
            include_screenshot=True,
            screenshot_region=screenshot_region,
            relative_positioner=relative_positioner,
        )
