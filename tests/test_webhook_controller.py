import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from macro_app.controllers.webhook import WebhookController
from macro_app.services.webhook import WebhookService
from macro_app.state import AppState
from macro_app.ui_loader import load_main_window


def _app():
    app = QApplication.instance()
    return app or QApplication([])


def test_enable_from_url_updates_shared_webhook_state():
    _app()
    window = load_main_window()
    state = AppState()
    controller = WebhookController(window, state, WebhookService())

    assert controller.enable_from_url("https://discord.com/api/webhooks/123/abc") is True
    assert state.webhook.enabled is True
    assert state.webhook.url == "https://discord.com/api/webhooks/123/abc"


def test_event_ready_respects_reward_filter_trigger():
    _app()
    window = load_main_window()
    state = AppState()
    state.webhook.enabled = True
    state.webhook.url = "https://discord.com/api/webhooks/123/abc"
    state.webhook.triggers.reward_collected = True
    state.webhook.triggers.reward_type_filter = "gems"
    controller = WebhookController(window, state, WebhookService())

    ready, reason = controller.event_ready("reward_collected", rewards={"Gold": 50})
    assert ready is False
    assert reason == "trigger disabled"

    ready, reason = controller.event_ready("reward_collected", rewards={"gems": 10})
    assert ready is True
    assert reason == ""


def test_run_finish_payload_includes_rewards_as_full_width_field():
    _app()
    window = load_main_window()
    state = AppState()
    state.webhook.contents.rewards_this_run = True
    controller = WebhookController(window, state, WebhookService())

    payload, include_screenshot = controller._build_event_payload(
        "run_finish",
        match_result="VICTORY",
        rewards={"Gems": 30, "Gold": 75},
        context={
            "macro_name": "Farm",
            "gamemode": "Story",
            "map_name": "Namek",
            "elapsed": "1m 30s",
        },
    )

    reward_fields = [field for field in payload["embeds"][0]["fields"] if field["name"] == "🎁 REWARDS"]
    assert include_screenshot is False
    assert len(reward_fields) == 1
    assert reward_fields[0]["value"] == "+30 Gems\n+75 Gold"
    assert reward_fields[0]["inline"] is False


def test_run_finish_payload_omits_rewards_when_content_toggle_disabled():
    _app()
    window = load_main_window()
    state = AppState()
    state.webhook.contents.rewards_this_run = False
    controller = WebhookController(window, state, WebhookService())

    payload, _include_screenshot = controller._build_event_payload(
        "run_finish",
        match_result="VICTORY",
        rewards={"Gems": 30},
        context={"elapsed": "1m 30s"},
    )

    reward_fields = [field for field in payload["embeds"][0]["fields"] if field["name"] == "🎁 REWARDS"]
    assert reward_fields == []
