"""Webhook controller for the webhook entry points and runtime notifications."""

from __future__ import annotations

from macro_app.constants import DISCORD_SCREENSHOT_REGION
from macro_app.services.reward_stats import normalize_reward_name


class WebhookController:
    """Keep webhook inputs in sync, validate settings, and send runtime events."""

    def __init__(self, window, state, webhook_service) -> None:
        self.window = window
        self.state = state
        self.webhook_service = webhook_service
        self.overlay_controller = None

    def set_overlay_controller(self, overlay_controller) -> None:
        self.overlay_controller = overlay_controller

    def bind(self) -> None:
        self.window.webhookToggleButton.clicked.connect(self.toggle_main)
        self.window.webhookUrlInput.editingFinished.connect(self.on_main_url_changed)
        self.window.webhookTestButton.clicked.connect(self.test_main)
        self.window.overlayWebhookToggleButton.clicked.connect(self.toggle_overlay)
        self.window.overlayWebhookUrlInput.editingFinished.connect(self.on_overlay_url_changed)
        self.window.overlayWebhookTestButton.clicked.connect(self.test_overlay)
        self.sync_ui()

    def sync_ui(self) -> None:
        for toggle_btn, url_input in [
            (self.window.webhookToggleButton, self.window.webhookUrlInput),
            (self.window.overlayWebhookToggleButton, self.window.overlayWebhookUrlInput),
        ]:
            toggle_btn.setText("Enabled" if self.state.webhook.enabled else "Disabled")
            toggle_btn.setProperty("enabled_state", self.state.webhook.enabled)
            toggle_btn.style().unpolish(toggle_btn)
            toggle_btn.style().polish(toggle_btn)
            url_input.setEnabled(not self.state.webhook.enabled)
            url_input.setText(self.state.webhook.url)
        if self.overlay_controller is not None:
            self.overlay_controller.sync_integrations_ui()

    def validate_url(self, url: str) -> tuple[bool, str]:
        normalized = (url or "").strip()
        if not normalized:
            return False, "Please enter a Discord webhook URL first!"
        if not normalized.startswith("https://discord.com/api/webhooks/"):
            return False, "Invalid webhook URL. Must start with https://discord.com/api/webhooks/"
        return True, ""

    def set_url(self, url: str) -> None:
        self.state.webhook.url = (url or "").strip()
        self.sync_ui()

    def enable_from_url(self, url: str) -> bool:
        normalized = (url or "").strip()
        valid, message = self.validate_url(normalized)
        if not valid:
            self.window.statusbar.showMessage(message)
            return False
        self.state.webhook.url = normalized
        self.state.webhook.enabled = True
        self.window.statusbar.showMessage("Discord webhook enabled!")
        print(f"Discord webhook enabled: {self.state.webhook.url[:50]}...")
        self.sync_ui()
        return True

    def disable(self) -> None:
        self.state.webhook.enabled = False
        self.window.statusbar.showMessage("Discord webhook disabled")
        print("Discord webhook disabled")
        self.sync_ui()

    def toggle_main(self) -> None:
        self._toggle(self.window.webhookUrlInput.text().strip())

    def toggle_overlay(self) -> None:
        self._toggle(self.window.overlayWebhookUrlInput.text().strip())

    def _toggle(self, url: str) -> None:
        if not self.state.webhook.enabled:
            self.enable_from_url(url)
        else:
            self.disable()

    def on_main_url_changed(self) -> None:
        if not self.state.webhook.enabled:
            self.set_url(self.window.webhookUrlInput.text().strip())

    def on_overlay_url_changed(self) -> None:
        if not self.state.webhook.enabled:
            self.set_url(self.window.overlayWebhookUrlInput.text().strip())

    def test_main(self) -> None:
        self.test_url(self.window.webhookUrlInput.text().strip())

    def test_overlay(self) -> None:
        self.test_url(self.window.overlayWebhookUrlInput.text().strip())

    def test_url(self, url: str) -> bool:
        normalized = (url or "").strip()
        valid, message = self.validate_url(normalized)
        if not valid:
            self.window.statusbar.showMessage(message)
            return False

        self.state.webhook.url = normalized
        self.window.statusbar.showMessage("Sending test message...")
        payload = {
            "content": "Testing Webhook",
        }
        success = self.webhook_service.send_payload(normalized, True, payload, include_screenshot=False)
        if success:
            self.window.statusbar.showMessage("Test message sent successfully!")
            print("Test webhook message sent successfully")
        else:
            self.window.statusbar.showMessage("Test failed")
        self.sync_ui()
        return success

    def send_runtime_notification(self, message: str, include_screenshot: bool = True) -> bool:
        return self.webhook_service.send(
            self.state.webhook.url,
            self.state.webhook.enabled,
            message,
            include_screenshot=include_screenshot,
        )

    def send_treasure_room_notification(
        self,
        *,
        macro_name: str,
        gamemode: str,
        map_name: str,
        session_run_count: int,
        relative_positioner=None,
    ) -> bool:
        if not self.state.webhook.enabled or not self.state.webhook.url:
            return False

        mention, allowed_mentions = self._manual_ping_prefix()
        content = f"{mention} Treasure room detected!".strip()
        payload: dict = {
            "content": content,
            "embeds": [
                {
                    "title": "Zeron Config",
                    "description": "Treasure Room Detected",
                    "color": 0xFACC15,
                    "fields": [
                        {"name": "🧩 MACRO", "value": macro_name or "Unknown", "inline": True},
                        {"name": "🎮 GAMEMODE", "value": gamemode or "Unknown", "inline": True},
                        {"name": "🗺️ MAP", "value": map_name or "Unknown", "inline": True},
                        {"name": "🔁 SESSION RUN COUNT", "value": str(session_run_count), "inline": True},
                    ],
                    "footer": {"text": "Zeron Config"},
                }
            ],
        }
        if allowed_mentions is not None:
            payload["allowed_mentions"] = {"parse": [], **allowed_mentions}
        include_screenshot = bool(self.state.webhook.contents.screenshot)
        if include_screenshot:
            payload["embeds"][0]["image"] = {"url": "attachment://macro_screenshot.png"}
        return self.webhook_service.send_payload(
            self.state.webhook.url,
            self.state.webhook.enabled,
            payload,
            include_screenshot=include_screenshot,
            screenshot_region=DISCORD_SCREENSHOT_REGION,
            relative_positioner=relative_positioner,
        )

    def _manual_ping_prefix(self) -> tuple[str, dict | None]:
        target_id = (self.state.webhook.ping.target_id or "").strip()
        if not target_id:
            return "", None

        cleaned = target_id
        mention_type = "user"
        if cleaned.lower().startswith("role:"):
            cleaned = cleaned.split(":", 1)[1].strip()
            mention_type = "role"
        elif cleaned.startswith("&"):
            cleaned = cleaned[1:].strip()
            mention_type = "role"

        if not cleaned.isdigit():
            return "", None
        if mention_type == "role":
            return f"<@&{cleaned}>", {"roles": [cleaned]}
        return f"<@{cleaned}>", {"users": [cleaned]}

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    @staticmethod
    def _format_percentage(numerator: int, denominator: int) -> str:
        if denominator <= 0:
            return "0%"
        return f"{(numerator / denominator) * 100:.1f}%"

    @staticmethod
    def _normalized_result(match_result: str) -> str:
        result = (match_result or "").strip().upper()
        if result in {"DEFEAT", "FAILED", "FAILURE"}:
            return "DEFEAT"
        if result in {"VICTORY", "SUCCESS", "SUCCEEDED"}:
            return "VICTORY"
        return result or "UNKNOWN"

    def _ping_prefix(self, event_type: str, rewards: dict[str, int] | None = None) -> tuple[str, dict | None]:
        ping = self.state.webhook.ping
        target_id = (ping.target_id or "").strip()
        if not target_id:
            return "", None

        should_ping = False
        if event_type == "run_fail" and ping.failures_only:
            should_ping = True
        elif event_type == "stage_complete" and ping.stage_completion:
            should_ping = True
        elif event_type == "reward_collected" and ping.select_reward and rewards:
            should_ping = self._reward_amount(rewards, ping.reward_type) > 0

        if not should_ping:
            return "", None

        cleaned = target_id
        mention_type = "user"
        if cleaned.lower().startswith("role:"):
            cleaned = cleaned.split(":", 1)[1].strip()
            mention_type = "role"
        elif cleaned.startswith("&"):
            cleaned = cleaned[1:].strip()
            mention_type = "role"

        if not cleaned.isdigit():
            return "", None

        if mention_type == "role":
            return f"<@&{cleaned}>", {"roles": [cleaned]}
        return f"<@{cleaned}>", {"users": [cleaned]}

    def _build_embed_fields(self, *, match_result: str | None = None, rewards: dict[str, int] | None = None, context: dict) -> list[dict]:
        contents = self.state.webhook.contents
        fields: list[dict] = []

        def add_field(name: str, value: str, *, inline: bool = True) -> None:
            value = (value or "").strip()
            if value:
                fields.append({"name": name, "value": value, "inline": inline})

        if contents.result and match_result:
            add_field("🏁 MATCH RESULTS", match_result)
        if contents.macro_name and context.get("macro_name"):
            add_field("🧩 MACRO", context["macro_name"])
        if contents.gamemode and context.get("gamemode"):
            add_field("🎮 GAMEMODE", context["gamemode"])
        if contents.map and context.get("map_name"):
            add_field("🗺️ MAP", context["map_name"])
        if contents.run_duration and context.get("elapsed"):
            add_field("⏱️ TIME ELAPSED", context["elapsed"])
        if contents.session_run_count and context.get("session_run_count") is not None:
            add_field("🔁 SESSION RUN COUNT", str(context["session_run_count"]))
        if contents.win_rate and context.get("win_rate"):
            add_field("📈 WIN RATE", context["win_rate"])
        if contents.rewards_this_run and rewards:
            reward_lines = "\n".join(f"+{amount} {name}" for name, amount in rewards.items())
            add_field("🎁 REWARDS", reward_lines, inline=False)
        if contents.rewards_per_hour and context.get("rewards_per_hour"):
            add_field("⚡ REWARDS / HOUR", context["rewards_per_hour"], inline=False)

        return fields

    def _build_event_payload(self, event_type: str, *, match_result: str | None = None, rewards: dict[str, int] | None = None, context: dict | None = None) -> tuple[dict, bool]:
        context = context or {}
        normalized_result = self._normalized_result(match_result or "")
        mention_prefix, allowed_mentions = self._ping_prefix(event_type, rewards)
        event_titles = {
            "run_start": "Run Started",
            "run_finish": "Run Finished",
            "run_fail": "Run Failed",
            "reward_collected": "Reward Collected",
            "stage_complete": "Stage Completed",
        }
        title = event_titles.get(event_type, "Macro Update")
        if event_type == "run_finish" and normalized_result == "VICTORY":
            color = self.webhook_service.EMBED_COLORS["VICTORY"]
        elif event_type == "run_fail" or normalized_result == "DEFEAT":
            color = self.webhook_service.EMBED_COLORS["DEFEAT"]
        else:
            color = 0x6B7280

        payload: dict = {
            "content": mention_prefix,
            "embeds": [
                {
                    "title": "Zeron Config",
                    "description": title,
                    "color": color,
                    "fields": self._build_embed_fields(match_result=normalized_result if match_result else None, rewards=rewards, context=context),
                    "footer": {"text": "Zeron Config"},
                }
            ],
        }
        if allowed_mentions is not None:
            payload["allowed_mentions"] = {"parse": [], **allowed_mentions}

        include_screenshot = bool(self.state.webhook.contents.screenshot and event_type in {"run_finish", "run_fail"})
        if include_screenshot:
            payload["embeds"][0]["image"] = {"url": "attachment://macro_screenshot.png"}
        return payload, include_screenshot

    def _event_enabled(self, event_type: str, rewards: dict[str, int] | None = None) -> bool:
        triggers = self.state.webhook.triggers
        if event_type == "run_start":
            return triggers.run_start
        if event_type == "run_finish":
            return triggers.run_finish
        if event_type == "run_fail":
            return triggers.run_fail
        if event_type == "stage_complete":
            return triggers.stage_complete
        if event_type == "reward_collected":
            if not triggers.reward_collected:
                return False
            if not rewards:
                return False
            return self._reward_amount(rewards, triggers.reward_type_filter) > 0
        return False

    @staticmethod
    def _reward_amount(rewards: dict[str, int] | None, reward_key: str) -> int:
        if not rewards:
            return 0
        normalized_filter = normalize_reward_name(reward_key) or reward_key
        total = 0
        for reward_name, amount in rewards.items():
            if (normalize_reward_name(str(reward_name)) or str(reward_name)) != normalized_filter:
                continue
            try:
                total += int(amount)
            except (TypeError, ValueError):
                continue
        return total

    def send_event(self, event_type: str, *, match_result: str | None = None, rewards: dict[str, int] | None = None, context: dict | None = None, relative_positioner=None) -> bool:
        ready, _reason = self.event_ready(event_type, rewards=rewards)
        if not ready:
            return False
        payload, include_screenshot = self._build_event_payload(
            event_type,
            match_result=match_result,
            rewards=rewards,
            context=context,
        )
        return self.webhook_service.send_payload(
            self.state.webhook.url,
            self.state.webhook.enabled,
            payload,
            include_screenshot=include_screenshot,
            screenshot_region=DISCORD_SCREENSHOT_REGION,
            relative_positioner=relative_positioner,
        )

    def event_ready(self, event_type: str, *, rewards: dict[str, int] | None = None) -> tuple[bool, str]:
        if not self.state.webhook.enabled:
            return False, "webhook disabled"
        if not self.state.webhook.url:
            return False, "webhook URL missing"
        if not self._event_enabled(event_type, rewards):
            return False, "trigger disabled"
        return True, ""

    def send_runtime_result_notification(
        self,
        match_result: str,
        rewards: dict[str, int],
        *,
        gamemode: str,
        map_name: str,
        elapsed_seconds: float,
        relative_positioner=None,
        macro_name: str = "",
        session_run_count: int = 0,
        win_rate: str = "",
        rewards_per_hour: str = "",
    ) -> bool:
        normalized_result = self._normalized_result(match_result)
        event_type = "run_fail" if normalized_result == "DEFEAT" else "run_finish"
        return self.send_event(
            event_type,
            match_result=normalized_result,
            rewards=rewards,
            context={
                "macro_name": macro_name,
                "gamemode": gamemode,
                "map_name": map_name,
                "elapsed": self._format_elapsed(elapsed_seconds),
                "session_run_count": session_run_count,
                "win_rate": win_rate,
                "rewards_per_hour": rewards_per_hour,
            },
            relative_positioner=relative_positioner,
        )

    def send_run_started_notification(
        self,
        *,
        macro_name: str,
        gamemode: str,
        map_name: str,
        session_run_count: int,
    ) -> bool:
        return self.send_event(
            "run_start",
            context={
                "macro_name": macro_name,
                "gamemode": gamemode,
                "map_name": map_name,
                "session_run_count": session_run_count,
            },
        )

    def send_reward_collected_notification(
        self,
        rewards: dict[str, int],
        *,
        macro_name: str,
        gamemode: str,
        map_name: str,
        elapsed_seconds: float,
        session_run_count: int,
        win_rate: str = "",
        rewards_per_hour: str = "",
        relative_positioner=None,
    ) -> bool:
        return self.send_event(
            "reward_collected",
            rewards=rewards,
            context={
                "macro_name": macro_name,
                "gamemode": gamemode,
                "map_name": map_name,
                "elapsed": self._format_elapsed(elapsed_seconds),
                "session_run_count": session_run_count,
                "win_rate": win_rate,
                "rewards_per_hour": rewards_per_hour,
            },
            relative_positioner=relative_positioner,
        )

    def send_stage_completed_notification(
        self,
        *,
        wave: int,
        macro_name: str,
        gamemode: str,
        map_name: str,
        session_run_count: int,
    ) -> bool:
        return self.send_event(
            "stage_complete",
            context={
                "macro_name": macro_name,
                "gamemode": gamemode,
                "map_name": map_name,
                "session_run_count": session_run_count,
                "elapsed": f"Wave {wave}",
            },
        )

    def runtime_notification_ready(self) -> tuple[bool, str]:
        if not self.state.webhook.enabled:
            return False, "webhook disabled"
        if not self.state.webhook.url:
            return False, "webhook URL missing"
        return True, ""
