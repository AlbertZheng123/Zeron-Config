import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from macro_json import create_empty_macro, save_macro, load_macro, format_step_display


def test_create_empty_macro_has_6_units():
    m = create_empty_macro()
    assert len(m["units"]) == 6
    for i in range(1, 7):
        assert m["units"][i]["name"] == ""
        assert m["units"][i]["placements"] == []


def test_create_empty_macro_has_empty_order():
    m = create_empty_macro()
    assert m["setup_order"] == []
    assert m["order"] == []


def test_create_empty_macro_has_default_settings():
    m = create_empty_macro()
    assert m["settings"]["replay"] == "loop"
    assert m["settings"]["anti_afk"] is True
    assert m["settings"]["force_restart_wave_enabled"] is False
    assert m["settings"]["force_restart_wave"] == 0
    assert m["settings"]["wait_between_clicks"] == 0.2
    assert m["settings"]["wait_between_key_presses"] == 0.2
    assert m["settings"]["wait_between_steps"] == 0.0
    assert m["settings"]["relative_positioning"] is False
    assert m["settings"]["reposition_camera_on_start"] is False
    assert m["settings"]["card_selection_legend"] is False
    assert m["settings"]["legend_selected_card"] == "Immunity"
    assert m["settings"]["card_selection_dungeon"] is False
    assert m["settings"]["dungeon_card_priorities"] == []
    assert m["settings"]["dungeon_max_buff_enabled"] is False
    assert m["settings"]["dungeon_max_buff_percent"] == 0
    assert m["settings"]["dungeon_max_debuff_enabled"] is False
    assert m["settings"]["dungeon_max_debuff_percent"] == 0
    assert m["settings"]["dungeon_starter_card"] == "Money Surge"
    assert m["settings"]["odyssey_macro_enabled"] is False
    assert m["settings"]["odyssey_auto_card_selection"] is True
    assert m["settings"]["odyssey_auto_pick_card"] is True
    assert m["settings"]["odyssey_card_priorities"] == []
    assert m["settings"]["odyssey_auto_character_card"] is False
    assert m["settings"]["odyssey_character"] == "Madara"
    assert m["settings"]["odyssey_character_card_priorities"] == []
    assert m["settings"]["odyssey_auto_next_room"] is True
    assert m["settings"]["odyssey_room_priorities"] == ["Normal", "Shop", "Boss"]
    assert m["settings"]["odyssey_check_treasure_room"] is False
    assert m["settings"]["odyssey_check_unit_reward"] is False
    assert m["settings"]["odyssey_auto_shop_room"] is False
    assert m["settings"]["odyssey_auto_memoria_selection"] is False
    assert m["settings"]["odyssey_memoria_priorities"] == []
    assert m["settings"]["odyssey_only_buy_when_enough"] is True


def test_save_and_load_roundtrip(tmp_path):
    m = create_empty_macro()
    m["units"][1]["name"] = "Goku"
    m["units"][1]["placements"] = [[200, 300], None, [400, 500]]
    m["setup_order"] = [{"cmd": "click", "x": 111, "y": 222}]
    m["order"] = [
        {"cmd": "place", "slot": 1, "placement_index": 0},
        {"cmd": "place", "slot": 1, "placement_index": 2},
        {"cmd": "wait_wave", "wave": 3},
    ]
    m["settings"]["replay"] = "stop"
    m["settings"]["force_restart_wave_enabled"] = True
    m["settings"]["force_restart_wave"] = 19
    m["settings"]["wait_between_clicks"] = 0.35
    m["settings"]["wait_between_key_presses"] = 0.45
    m["settings"]["wait_between_steps"] = 1.2
    m["settings"]["relative_positioning"] = True
    m["settings"]["reposition_camera_on_start"] = True
    m["settings"]["card_selection_legend"] = True
    m["settings"]["legend_selected_card"] = "Thrice"
    m["settings"]["card_selection_dungeon"] = True
    m["settings"]["dungeon_card_priorities"] = ["Damage (Common)", "Strong (Common)"]
    m["settings"]["dungeon_max_buff_enabled"] = True
    m["settings"]["dungeon_max_buff_percent"] = 100
    m["settings"]["dungeon_max_debuff_enabled"] = True
    m["settings"]["dungeon_max_debuff_percent"] = 200
    m["settings"]["dungeon_starter_card"] = "Limit Break"
    m["settings"]["odyssey_macro_enabled"] = True
    m["settings"]["odyssey_auto_card_selection"] = False
    m["settings"]["odyssey_auto_pick_card"] = False
    m["settings"]["odyssey_card_priorities"] = ["Ambush", "Extended Duration"]
    m["settings"]["odyssey_auto_character_card"] = True
    m["settings"]["odyssey_character"] = "Madara"
    m["settings"]["odyssey_character_card_priorities"] = ["Layered Slumber"]
    m["settings"]["odyssey_auto_next_room"] = True
    m["settings"]["odyssey_room_priorities"] = ["Boss", "Normal", "Shop"]
    m["settings"]["odyssey_check_treasure_room"] = True
    m["settings"]["odyssey_check_unit_reward"] = True
    m["settings"]["odyssey_auto_shop_room"] = True
    m["settings"]["odyssey_auto_memoria_selection"] = True
    m["settings"]["odyssey_memoria_priorities"] = ["Range", "Speed"]
    m["settings"]["odyssey_only_buy_when_enough"] = False

    path = str(tmp_path / "test_macro.json")
    save_macro(m, path)

    loaded = load_macro(path)
    assert loaded["units"][1]["name"] == "Goku"
    assert loaded["setup_order"] == [{"cmd": "click", "x": 111, "y": 222}]
    # Nulls compacted on load, indices reindexed
    assert loaded["units"][1]["placements"] == [[200, 300], [400, 500]]
    assert len(loaded["order"]) == 3
    assert loaded["order"][0] == {"cmd": "place", "slot": 1, "placement_index": 0}
    assert loaded["order"][1] == {"cmd": "place", "slot": 1, "placement_index": 1}  # was 2, reindexed to 1
    assert loaded["settings"]["replay"] == "stop"
    assert loaded["settings"]["force_restart_wave_enabled"] is True
    assert loaded["settings"]["force_restart_wave"] == 19
    assert loaded["settings"]["wait_between_clicks"] == 0.35
    assert loaded["settings"]["wait_between_key_presses"] == 0.45
    assert loaded["settings"]["wait_between_steps"] == 1.2
    assert loaded["settings"]["relative_positioning"] is True
    assert loaded["settings"]["reposition_camera_on_start"] is True
    assert loaded["settings"]["card_selection_legend"] is True
    assert loaded["settings"]["legend_selected_card"] == "Thrice"
    assert loaded["settings"]["card_selection_dungeon"] is True
    assert loaded["settings"]["dungeon_card_priorities"] == ["Damage (Common)", "Strong (Common)"]
    assert loaded["settings"]["dungeon_max_buff_enabled"] is True
    assert loaded["settings"]["dungeon_max_buff_percent"] == 100
    assert loaded["settings"]["dungeon_max_debuff_enabled"] is True
    assert loaded["settings"]["dungeon_max_debuff_percent"] == 200
    assert loaded["settings"]["dungeon_starter_card"] == "Limit Break"
    assert loaded["settings"]["odyssey_macro_enabled"] is True
    assert loaded["settings"]["odyssey_auto_card_selection"] is False
    assert loaded["settings"]["odyssey_auto_pick_card"] is False
    assert loaded["settings"]["odyssey_card_priorities"] == ["Ambush", "Extended Duration"]
    assert loaded["settings"]["odyssey_auto_character_card"] is True
    assert loaded["settings"]["odyssey_character"] == "Madara"
    assert loaded["settings"]["odyssey_character_card_priorities"] == ["Layered Slumber"]
    assert loaded["settings"]["odyssey_auto_next_room"] is True
    assert loaded["settings"]["odyssey_room_priorities"] == ["Boss", "Normal", "Shop"]
    assert loaded["settings"]["odyssey_check_treasure_room"] is True
    assert loaded["settings"]["odyssey_check_unit_reward"] is True
    assert loaded["settings"]["odyssey_auto_shop_room"] is True
    assert loaded["settings"]["odyssey_auto_memoria_selection"] is True
    assert loaded["settings"]["odyssey_memoria_priorities"] == ["Range", "Speed"]
    assert loaded["settings"]["odyssey_only_buy_when_enough"] is False


def test_load_macro_converts_string_keys(tmp_path):
    m = create_empty_macro()
    m["units"][3]["name"] = "Naruto"

    path = str(tmp_path / "test_keys.json")
    save_macro(m, path)
    loaded = load_macro(path)
    assert 3 in loaded["units"]
    assert loaded["units"][3]["name"] == "Naruto"


def test_display_click():
    assert format_step_display({"cmd": "click", "x": 500, "y": 300}) == ("CLICK", "X: 500   Y: 300")


def test_display_place():
    units = {1: {"name": "Goku", "placements": [[200, 300]]}}
    result = format_step_display({"cmd": "place", "slot": 1, "placement_index": 0}, units)
    assert result == ("PLACE", "Goku #0  \u2192 (200, 300)")


def test_display_place_until_empty():
    units = {1: {"name": "Goku", "placements": [[200, 300]]}}
    result = format_step_display({"cmd": "place", "slot": 1, "placement_index": 0, "until_empty": True}, units)
    assert result == ("PLACE", "Goku #0  \u2192 (200, 300)  \u221e")


def test_display_upgrade_auto():
    units = {1: {"name": "Goku", "placements": [[200, 300]]}}
    result = format_step_display({"cmd": "upgrade", "slot": 1, "placement_index": 0, "mode": "auto"}, units)
    assert result == ("UPGRADE", "Goku #0  Auto")


def test_display_upgrade_manual():
    units = {2: {"name": "Naruto", "placements": [[400, 500]]}}
    result = format_step_display({"cmd": "upgrade", "slot": 2, "placement_index": 0, "mode": "manual", "count": 3}, units)
    assert result == ("UPGRADE", "Naruto #0  3x")


def test_display_wait_seconds():
    assert format_step_display({"cmd": "wait_seconds", "seconds": 2.5}) == ("WAIT", "2.5 seconds")


def test_display_wait_wave():
    assert format_step_display({"cmd": "wait_wave", "wave": 5}) == ("WAIT", "Round Completed  Wave 5")


def test_display_wait_start():
    assert format_step_display({"cmd": "wait_start"}) == ("WAIT", "Game Start")


def test_display_wait_yen():
    assert format_step_display({"cmd": "wait_yen", "amount": 500}) == ("WAIT", "Yen \u2265 500")


def test_display_key_press():
    assert format_step_display({"cmd": "key_press", "key": "e", "times": 1}) == ("KEY PRESS", "e")


def test_display_key_press_multi():
    assert format_step_display({"cmd": "key_press", "key": "e", "times": 3}) == ("KEY PRESS", "e  \u00d73")


def test_display_key_hold():
    assert format_step_display({"cmd": "key_hold", "key": "w", "seconds": 3.0}) == ("KEY HOLD", "w  3.0s")


def test_display_skele_strings_ability():
    assert format_step_display({"cmd": "ability_skele_king"}) == ("ABILITY", "Skele: Strings")
