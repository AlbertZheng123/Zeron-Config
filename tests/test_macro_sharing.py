import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.services.macro_sharing import MacroSharingError, MacroSharingService


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self._rows = [row for row in self._rows if row.get(key) == value]
        return self

    def limit(self, _count):
        return self

    def execute(self):
        return _FakeResult(self._rows[:1])


class _FakeClient:
    def __init__(self, rows):
        self._rows = rows

    def table(self, _name):
        return _FakeQuery(list(self._rows))


def test_normalize_share_code_uppercases_and_strips():
    assert MacroSharingService.normalize_share_code(" ab7kq2 ") == "AB7KQ2"


def test_validate_import_target_rejects_mode_mismatch():
    service = MacroSharingService()
    record = {"game_mode": "story", "map_name": "Shibuya"}
    with pytest.raises(MacroSharingError, match="Story / Shibuya"):
        service.validate_import_target(record, "raids", "Shibuya")


def test_validate_import_target_rejects_map_mismatch():
    service = MacroSharingService()
    record = {"game_mode": "story", "map_name": "Double Dungeon"}
    with pytest.raises(MacroSharingError, match="Double Dungeon"):
        service.validate_import_target(record, "story", "Shibuya")


def test_build_import_macro_path_handles_collisions(tmp_path):
    service = MacroSharingService()
    first = tmp_path / "farm_route.json"
    first.write_text("{}")
    second = tmp_path / "farm_route_AB7KQ2.json"
    second.write_text("{}")

    path = service.build_import_macro_path(str(tmp_path), "farm route", "ab7kq2")

    assert path.endswith(os.path.join(str(tmp_path), "farm_route_AB7KQ2_2.json"))


def test_normalize_macro_payload_converts_keys_and_compacts_tombstones():
    service = MacroSharingService()
    payload = {
        "units": {
            "1": {"name": "Goku", "placements": [[100, 200], None, [300, 400]]},
        },
        "setup_order": [{"cmd": "click", "x": 99, "y": 88}],
        "order": [
            {"cmd": "place", "slot": 1, "placement_index": 0},
            {"cmd": "place", "slot": 1, "placement_index": 2},
        ],
        "settings": {
            "replay": "stop",
            "anti_afk": False,
            "force_restart_wave_enabled": True,
            "force_restart_wave": 22,
            "wait_between_clicks": 0.35,
            "wait_between_key_presses": 0.45,
            "wait_between_steps": 1.2,
            "relative_positioning": True,
            "reposition_camera_on_start": True,
            "card_selection_legend": True,
            "legend_selected_card": "Quake",
            "card_selection_dungeon": True,
            "dungeon_starter_card": "Limit Break",
            "dungeon_card_priorities": ["Damage (Common)", "Strong (Common)"],
            "dungeon_max_buff_enabled": True,
            "dungeon_max_buff_percent": 100,
            "dungeon_max_debuff_enabled": True,
            "dungeon_max_debuff_percent": 200,
        },
    }

    normalized = service.normalize_macro_payload(payload)

    assert normalized["setup_order"] == [{"cmd": "click", "x": 99, "y": 88, "button": "left"}]
    assert normalized["units"][1]["placements"] == [[100, 200], [300, 400]]
    assert normalized["order"][1]["placement_index"] == 1
    assert normalized["settings"]["replay"] == "stop"
    assert normalized["settings"]["anti_afk"] is False
    assert normalized["settings"]["force_restart_wave_enabled"] is True
    assert normalized["settings"]["force_restart_wave"] == 22
    assert normalized["settings"]["wait_between_clicks"] == 0.35
    assert normalized["settings"]["wait_between_key_presses"] == 0.45
    assert normalized["settings"]["wait_between_steps"] == 1.2
    assert normalized["settings"]["relative_positioning"] is True
    assert normalized["settings"]["reposition_camera_on_start"] is True
    assert normalized["settings"]["card_selection_legend"] is True
    assert normalized["settings"]["legend_selected_card"] == "Quake"
    assert normalized["settings"]["card_selection_dungeon"] is True
    assert normalized["settings"]["dungeon_starter_card"] == "Limit Break"
    assert normalized["settings"]["dungeon_card_priorities"] == ["Damage (Common)", "Strong (Common)"]
    assert normalized["settings"]["dungeon_max_buff_enabled"] is True
    assert normalized["settings"]["dungeon_max_buff_percent"] == 100
    assert normalized["settings"]["dungeon_max_debuff_enabled"] is True
    assert normalized["settings"]["dungeon_max_debuff_percent"] == 200


def test_normalize_macro_payload_supports_current_runtime_commands_and_max_upgrade():
    service = MacroSharingService()
    payload = {
        "units": {
            "1": {"name": "Ainz", "placements": [[100, 200]]},
            "2": {"name": "Pride", "placements": [[300, 400]]},
        },
        "setup_order": [
            {"cmd": "priority", "slot": 2, "priority": "Bosses"},
            {"cmd": "sell", "slot": 2},
        ],
        "order": [
            {"cmd": "upgrade", "slot": 1, "placement_index": 0, "mode": "max"},
            {"cmd": "ability_main", "slot": 2, "unit": "Pride", "ability": "Lion's Sin", "ability_file": "pride_lion_sin_ref.png"},
            {"cmd": "ability_skele_king"},
            {"cmd": "ability_ainz_arcane", "sequence": [{"element": "Curse", "skill": "Create Greater Undead"}]},
            {"cmd": "ability_ainz_caloric", "target_unit": "Pride", "target_x": 111, "target_y": 222},
        ],
        "settings": {},
    }

    normalized = service.normalize_macro_payload(payload)

    assert normalized["setup_order"][0] == {"cmd": "priority", "slot": 2, "priority": "Bosses"}
    assert normalized["setup_order"][1] == {"cmd": "sell", "slot": 2}
    assert normalized["order"][0]["mode"] == "max"
    assert normalized["order"][1]["cmd"] == "ability_main"
    assert normalized["order"][2] == {"cmd": "ability_skele_king"}
    assert normalized["order"][3]["sequence"] == [{"element": "Curse", "skill": "Create Greater Undead"}]
    assert normalized["order"][4]["target_x"] == 111
    assert normalized["order"][4]["target_y"] == 222


def test_normalize_macro_payload_compacts_and_validates_setup_order_placements():
    service = MacroSharingService()
    payload = {
        "units": {
            "1": {"name": "Goku", "placements": [None, [300, 400]]},
        },
        "setup_order": [
            {"cmd": "place", "slot": 1, "placement_index": 1},
            {"cmd": "upgrade", "slot": 1, "placement_index": 1, "mode": "manual", "count": 2},
        ],
        "order": [],
        "settings": {},
    }

    normalized = service.normalize_macro_payload(payload)

    assert normalized["units"][1]["placements"] == [[300, 400]]
    assert normalized["setup_order"][0]["placement_index"] == 0
    assert normalized["setup_order"][1]["placement_index"] == 0


def test_fetch_shared_macro_returns_normalized_record():
    rows = [
        {
            "share_code": "AB7KQ2",
            "macro_name": "farm route",
            "game_mode": "story",
            "map_name": "Shibuya",
            "macro_json": {
                "units": {"1": {"name": "Goku", "placements": [[100, 200]]}},
                "setup_order": [{"cmd": "click", "x": 12, "y": 34}],
                "order": [{"cmd": "place", "slot": 1, "placement_index": 0}],
                "settings": {
                    "replay": "loop",
                    "anti_afk": True,
                    "force_restart_wave_enabled": True,
                    "force_restart_wave": 11,
                    "wait_between_clicks": 0.3,
                    "wait_between_key_presses": 0.4,
                    "wait_between_steps": 0.8,
                    "relative_positioning": True,
                    "reposition_camera_on_start": True,
                    "card_selection_legend": True,
                    "legend_selected_card": "Champion",
                    "card_selection_dungeon": True,
                    "dungeon_starter_card": "Money Surge",
                    "dungeon_card_priorities": ["Damage (Common)"],
                    "dungeon_max_buff_enabled": True,
                    "dungeon_max_buff_percent": 150,
                    "dungeon_max_debuff_enabled": False,
                    "dungeon_max_debuff_percent": 0,
                },
            },
        }
    ]
    service = MacroSharingService(client_getter=lambda: _FakeClient(rows))

    record = service.fetch_shared_macro("ab7kq2")

    assert record["share_code"] == "AB7KQ2"
    assert record["macro_name"] == "farm route"
    assert record["macro_json"]["units"][1]["placements"] == [[100, 200]]
    assert record["macro_json"]["settings"]["force_restart_wave_enabled"] is True
    assert record["macro_json"]["settings"]["force_restart_wave"] == 11
    assert record["macro_json"]["settings"]["wait_between_clicks"] == 0.3
    assert record["macro_json"]["settings"]["wait_between_key_presses"] == 0.4
    assert record["macro_json"]["settings"]["wait_between_steps"] == 0.8


def test_fetch_shared_macro_raises_when_code_missing():
    service = MacroSharingService(client_getter=lambda: _FakeClient([]))

    with pytest.raises(MacroSharingError, match="No shared macro found"):
        service.fetch_shared_macro("AB7KQ2")
