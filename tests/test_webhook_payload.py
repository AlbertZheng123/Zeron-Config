import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.controllers.webhook import WebhookController
from macro_app.state import AppState


class _DummyStatusBar:
    def showMessage(self, _message: str) -> None:
        pass


class _DummyWindow:
    def __init__(self) -> None:
        self.statusbar = _DummyStatusBar()


class _DummyWebhookService:
    EMBED_COLORS = {
        "VICTORY": 0x10B981,
        "DEFEAT": 0xEF4444,
    }


def test_run_finish_payload_includes_rewards_as_full_width_field():
    state = AppState()
    state.webhook.contents.rewards_this_run = True
    controller = WebhookController(_DummyWindow(), state, _DummyWebhookService())

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
    state = AppState()
    state.webhook.contents.rewards_this_run = False
    controller = WebhookController(_DummyWindow(), state, _DummyWebhookService())

    payload, _include_screenshot = controller._build_event_payload(
        "run_finish",
        match_result="VICTORY",
        rewards={"Gems": 30},
        context={"elapsed": "1m 30s"},
    )

    reward_fields = [field for field in payload["embeds"][0]["fields"] if field["name"] == "🎁 REWARDS"]
    assert reward_fields == []


def test_run_finish_payload_omits_rewards_field_when_rewards_are_empty():
    state = AppState()
    state.webhook.contents.rewards_this_run = True
    controller = WebhookController(_DummyWindow(), state, _DummyWebhookService())

    payload, _include_screenshot = controller._build_event_payload(
        "run_finish",
        match_result="VICTORY",
        rewards={},
        context={"elapsed": "1m 30s"},
    )

    reward_fields = [field for field in payload["embeds"][0]["fields"] if field["name"] == "🎁 REWARDS"]
    assert reward_fields == []
