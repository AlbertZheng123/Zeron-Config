import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.controllers.advanced_editor_helpers import (
    build_macro_save_path,
    compact_macro_placement,
    get_invalid_upgrade_order_indices,
    move_instruction_to_drop_index,
    parse_advanced_step_data,
    retarget_place_instruction,
)
from macro_app.controllers.overlay_helpers import get_macro_folder_for_mode


def test_get_invalid_upgrade_order_indices_returns_only_matching_upgrades():
    order = [
        {"cmd": "upgrade", "slot": 1, "placement_index": 0, "mode": "auto"},
        {"cmd": "place", "slot": 1, "placement_index": 0},
        {"cmd": "upgrade", "slot": 1, "placement_index": 1, "mode": "auto"},
        {"cmd": "upgrade", "slot": 2, "placement_index": 0, "mode": "auto"},
    ]

    assert get_invalid_upgrade_order_indices(order, 1, 0) == [0]


def test_move_instruction_to_drop_index_moves_last_between_middle_steps():
    order = [
        {"cmd": "wait_seconds", "seconds": 3},
        {"cmd": "place", "slot": 1},
        {"cmd": "place", "slot": 2},
        {"cmd": "wait_wave", "wave": 5},
        {"cmd": "place", "slot": 3},
    ]

    assert move_instruction_to_drop_index(order, 4, 2) is True

    assert [step["cmd"] for step in order] == [
        "wait_seconds",
        "place",
        "place",
        "place",
        "wait_wave",
    ]
    assert order[2]["slot"] == 3


def test_move_instruction_to_drop_index_adjusts_when_moving_downward():
    order = [{"cmd": "a"}, {"cmd": "b"}, {"cmd": "c"}, {"cmd": "d"}]

    assert move_instruction_to_drop_index(order, 1, 4) is True

    assert [step["cmd"] for step in order] == ["a", "c", "d", "b"]


def test_move_instruction_to_drop_index_treats_adjacent_self_drop_as_noop():
    order = [{"cmd": "a"}, {"cmd": "b"}, {"cmd": "c"}]

    assert move_instruction_to_drop_index(order, 1, 2) is False

    assert [step["cmd"] for step in order] == ["a", "b", "c"]


def test_compact_macro_placement_removes_and_reindexes_order():
    macro = {
        "units": {
            1: {"name": "Goku", "placements": [[10, 20], [30, 40], [50, 60]]},
            2: {"name": "", "placements": []},
            3: {"name": "", "placements": []},
            4: {"name": "", "placements": []},
            5: {"name": "", "placements": []},
            6: {"name": "", "placements": []},
        },
        "order": [
            {"cmd": "place", "slot": 1, "placement_index": 0},
            {"cmd": "upgrade", "slot": 1, "placement_index": 2, "mode": "auto"},
            {"cmd": "place", "slot": 1, "placement_index": 2},
        ],
        "settings": {"replay": "loop", "anti_afk": True},
    }

    compact_macro_placement(macro, 1, 1)

    assert macro["units"][1]["placements"] == [[10, 20], [50, 60]]
    assert macro["order"][1]["placement_index"] == 1
    assert macro["order"][2]["placement_index"] == 1


def test_parse_advanced_step_data_reads_place_coordinates_from_macro():
    macro = {
        "units": {
            1: {"name": "Goku", "placements": [[123, 456]]},
            2: {"name": "", "placements": []},
            3: {"name": "", "placements": []},
            4: {"name": "", "placements": []},
            5: {"name": "", "placements": []},
            6: {"name": "", "placements": []},
        }
    }

    parsed = parse_advanced_step_data(
        {"cmd": "place", "slot": 1, "placement_index": 0, "until_empty": True},
        macro,
    )

    assert parsed["type"] == "place"
    assert parsed["place_x"] == "123"
    assert parsed["place_y"] == "456"
    assert parsed["until_empty"] is True


def test_build_macro_save_path_uses_overlay_context_when_present():
    expected = os.path.join(get_macro_folder_for_mode("story", "Shibuya"), "farm.json")
    assert build_macro_save_path("farm", "story", "Shibuya") == expected


def test_build_macro_save_path_requires_mode_and_map():
    with pytest.raises(ValueError, match="mode and map"):
        build_macro_save_path("farm", None, None)


def test_retarget_place_instruction_updates_same_slot_coordinates_only():
    macro = {
        "units": {
            1: {"name": "Goku", "placements": [[10, 20]]},
            2: {"name": "Naruto", "placements": []},
            3: {"name": "", "placements": []},
            4: {"name": "", "placements": []},
            5: {"name": "", "placements": []},
            6: {"name": "", "placements": []},
        },
        "setup_order": [],
        "order": [{"cmd": "place", "slot": 1, "placement_index": 0}],
        "settings": {"replay": "loop", "anti_afk": True},
    }

    updated = retarget_place_instruction(
        macro,
        order_key="order",
        order_index=0,
        new_slot=1,
        new_x=123,
        new_y=456,
        until_empty=True,
    )

    assert macro["units"][1]["placements"] == [[123, 456]]
    assert updated == {"cmd": "place", "slot": 1, "placement_index": 0, "until_empty": True}


def test_retarget_place_instruction_moves_related_upgrades_to_new_slot():
    macro = {
        "units": {
            1: {"name": "Goku", "placements": [[10, 20], [30, 40]]},
            2: {"name": "Naruto", "placements": [[50, 60]]},
            3: {"name": "", "placements": []},
            4: {"name": "", "placements": []},
            5: {"name": "", "placements": []},
            6: {"name": "", "placements": []},
        },
        "setup_order": [
            {"cmd": "upgrade", "slot": 1, "placement_index": 0, "mode": "auto"},
        ],
        "order": [
            {"cmd": "place", "slot": 1, "placement_index": 0},
            {"cmd": "upgrade", "slot": 1, "placement_index": 0, "mode": "manual", "count": 2},
            {"cmd": "place", "slot": 1, "placement_index": 1},
        ],
        "settings": {"replay": "loop", "anti_afk": True},
    }

    updated = retarget_place_instruction(
        macro,
        order_key="order",
        order_index=0,
        new_slot=2,
        new_x=777,
        new_y=888,
        until_empty=False,
    )

    assert macro["units"][1]["placements"] == [[30, 40]]
    assert macro["units"][2]["placements"] == [[50, 60], [777, 888]]
    assert updated == {"cmd": "place", "slot": 2, "placement_index": 1}
    assert macro["setup_order"][0]["slot"] == 2
    assert macro["setup_order"][0]["placement_index"] == 1
    assert macro["order"][1]["slot"] == 2
    assert macro["order"][1]["placement_index"] == 1
    assert macro["order"][2]["placement_index"] == 0
