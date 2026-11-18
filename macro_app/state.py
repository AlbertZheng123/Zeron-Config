"""Runtime state containers for the macro app."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

import macro_json

from macro_app.constants import UNIT_COORDINATES


@dataclass
class OverlayContext:
    mode: Optional[str] = None
    map_name: Optional[str] = None


@dataclass
class WebhookTriggerState:
    run_start: bool = False
    run_finish: bool = True
    run_fail: bool = True
    reward_collected: bool = False
    stage_complete: bool = False
    reward_type_filter: str = "gems"


@dataclass
class WebhookContentState:
    macro_name: bool = True
    gamemode: bool = True
    map: bool = True
    result: bool = True
    run_duration: bool = True
    session_run_count: bool = False
    win_rate: bool = False
    rewards_this_run: bool = True
    rewards_per_hour: bool = False
    screenshot: bool = False


@dataclass
class WebhookPingState:
    target_id: str = ""
    failures_only: bool = True
    select_reward: bool = False
    reward_type: str = "gems"
    stage_completion: bool = False


@dataclass
class WebhookState:
    enabled: bool = False
    url: str = ""
    triggers: WebhookTriggerState = field(default_factory=WebhookTriggerState)
    contents: WebhookContentState = field(default_factory=WebhookContentState)
    ping: WebhookPingState = field(default_factory=WebhookPingState)


@dataclass
class SessionWebhookState:
    current_macro_name: str = ""
    gamemode: str = ""
    map_name: str = ""
    session_started_at: float = 0.0
    started_runs: int = 0
    completed_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    reward_totals: dict[str, int] = field(default_factory=dict)
    last_run_rewards: dict[str, int] = field(default_factory=dict)


@dataclass
class RecordingState:
    active: bool = False
    listener: Any = None
    coords: Optional[tuple[int, int]] = None
    timer: Any = None
    target: str = "place"


@dataclass
class EditingState:
    active: bool = False
    row: Any = None
    step_type: Optional[str] = None
    original_data: Optional[dict] = None


@dataclass
class InsertState:
    active: bool = False
    position: Optional[int] = None
    separator: Any = None


@dataclass
class EditorState:
    current_macro: dict = field(default_factory=macro_json.create_empty_macro)
    step_section: str = "loop"
    advanced_step_counter: int = 0
    advanced_wave_counter: int = 0
    raw_steps_mode: bool = False
    current_tab: str = "units"
    frameless_active: bool = False
    editing: EditingState = field(default_factory=EditingState)
    insert: InsertState = field(default_factory=InsertState)
    recording_place_click: RecordingState = field(default_factory=RecordingState)
    recording_adv_click: RecordingState = field(default_factory=RecordingState)
    original_button_texts: dict = field(
        default_factory=lambda: {
            "upgrade": "Add Upgrade Step",
            "place": "Add Place Step",
            "sell": "Add Sell Step",
            "priority": "Add Priority Step",
            "wait": "Add Wait Step",
            "click": "Add Click Step",
            "key": "Add Key Step",
            "ability_main": "Add Ability Step",
            "ability_skele_king": "Add Ability Step",
            "ability_ainz_arcane": "Add Skill Selection",
            "ability_ainz_caloric": "Add Caloric Step",
        }
    )
    adv_log_queue: deque = field(default_factory=deque)
    adv_log_poll_timer: Any = None
    advanced_scroll_layout: Any = None


@dataclass
class AppState:
    overlay: OverlayContext = field(default_factory=OverlayContext)
    webhook: WebhookState = field(default_factory=WebhookState)
    editor: EditorState = field(default_factory=EditorState)
    debug_console_mode: bool = False
    macro_stop_requested: bool = False
    start_triggered_by_key: bool = False
    stop_triggered_by_key: bool = False
    macro_is_running: bool = False
    macro_thread: Any = None
    stop_key_timer: Any = None
    current_user_key: Optional[str] = None
    editing_macro_name: Optional[str] = None
    last_saved_macro_path: Optional[str] = None
    advanced_origin: str = "overlay"
    session_run_counts: dict = field(default_factory=dict)
    session_webhook: SessionWebhookState = field(default_factory=SessionWebhookState)
    pending_overlay_stats_modes: set[str] = field(default_factory=set)
    unit_data: dict = field(
        default_factory=lambda: {
            slot: {"name": "", "x": coords["x"], "y": coords["y"]}
            for slot, coords in UNIT_COORDINATES.items()
        }
    )
