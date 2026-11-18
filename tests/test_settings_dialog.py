"""Tests for the settings popup dialog."""

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

# Need a QApplication instance for widget tests
app = QApplication.instance() or QApplication(sys.argv)

from macro_app.dialogs.settings_dialog import SettingsDialog


def test_dialog_defaults():
    """Dialog opens with provided settings reflected in controls."""
    dialog = SettingsDialog(
        settings={
            "replay": "loop",
            "anti_afk": False,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": True,
            "force_restart_wave": 27,
            "wait_between_clicks": 0.3,
            "wait_between_key_presses": 0.4,
            "wait_between_steps": 0.8,
            "relative_positioning": True,
            "reposition_camera_on_start": True,
            "card_selection_legend": True,
            "legend_selected_card": "Quake",
            "card_selection_dungeon": True,
            "dungeon_starter_card": "Limit Break",
            "dungeon_card_priorities": ["Damage (Common)", "Strong (Common)"],
            "dungeon_max_buff_enabled": True,
            "dungeon_max_buff_percent": 150,
            "dungeon_max_debuff_enabled": True,
            "dungeon_max_debuff_percent": 300,
            "odyssey_macro_enabled": True,
            "odyssey_auto_card_selection": False,
            "odyssey_auto_pick_card": False,
            "odyssey_card_priorities": ["Ambush", "Extended Duration"],
            "odyssey_auto_character_card": True,
            "odyssey_character": "Madara",
            "odyssey_character_card_priorities": ["Layered Slumber"],
            "odyssey_auto_next_room": True,
            "odyssey_room_priorities": ["Boss", "Shop", "Normal"],
            "odyssey_check_treasure_room": True,
            "odyssey_check_unit_reward": True,
            "odyssey_auto_shop_room": True,
            "odyssey_auto_memoria_selection": True,
            "odyssey_memoria_priorities": ["Range", "Speed"],
            "odyssey_only_buy_when_enough": False,
        }
    )
    assert dialog.loop_radio.isChecked() is True
    assert dialog.stop_radio.isChecked() is False
    assert dialog.anti_afk_checkbox.isChecked() is False
    assert dialog.force_restart_wave_checkbox.isChecked() is True
    assert dialog.force_restart_wave_input.text() == "27"
    assert dialog.wait_between_clicks_input.text() == "0.3"
    assert dialog.wait_between_key_input.text() == "0.4"
    assert dialog.wait_between_steps_input.text() == "0.8"
    assert dialog.relative_positioning_checkbox.isChecked() is True
    assert dialog.reposition_camera_checkbox.isChecked() is True
    assert dialog.legend_card_checkbox.isChecked() is True
    assert dialog.legend_card_combo.currentText() == "Quake"
    assert dialog.dungeon_card_checkbox.isChecked() is True
    assert dialog.dungeon_starter_combo.currentText() == "Limit Break"
    assert dialog.dungeon_priority_list.count() == 2
    assert dialog.dungeon_max_buff_checkbox.isChecked() is True
    assert dialog.dungeon_max_buff_input.text() == "150"
    assert dialog.dungeon_max_debuff_checkbox.isChecked() is True
    assert dialog.dungeon_max_debuff_input.text() == "300"
    assert dialog.odyssey_macro_checkbox.isChecked() is True
    assert dialog.odyssey_content.isHidden() is False
    assert dialog.odyssey_auto_pick_checkbox.isChecked() is False
    assert dialog.odyssey_card_priority_list.count() == 2
    assert dialog.odyssey_auto_character_card_checkbox.isChecked() is True
    assert dialog.odyssey_character_combo.currentText() == "Madara"
    assert dialog.odyssey_character_card_priority_list.count() == 1
    assert dialog.odyssey_auto_next_checkbox.isChecked() is True
    assert dialog.odyssey_check_treasure_checkbox.isChecked() is True
    assert dialog.odyssey_check_unit_reward_checkbox.isChecked() is True
    assert dialog.odyssey_auto_shop_checkbox.isChecked() is True
    assert dialog.odyssey_auto_memoria_checkbox.isChecked() is True
    assert dialog.odyssey_memoria_priority_list.count() == 2
    assert "Damage" in dialog.odyssey_memoria_priority_options
    assert "All I got" in dialog.odyssey_memoria_priority_options
    assert dialog.odyssey_only_buy_when_enough_checkbox.isChecked() is False
    assert dialog.odyssey_priority_1_combo.currentText() == "Boss"
    assert dialog.odyssey_priority_2_combo.currentText() == "Shop"
    assert dialog.odyssey_priority_3_combo.currentText() == "Normal"


def test_dialog_stop_mode():
    """Dialog reflects stop mode when passed."""
    dialog = SettingsDialog(
        settings={
            "replay": "stop",
            "anti_afk": True,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": False,
            "force_restart_wave": 0,
            "wait_between_clicks": 0.2,
            "wait_between_key_presses": 0.2,
            "wait_between_steps": 0.0,
            "relative_positioning": False,
            "reposition_camera_on_start": False,
            "card_selection_legend": False,
            "legend_selected_card": "Immunity",
            "card_selection_dungeon": False,
            "dungeon_starter_card": "Money Surge",
            "dungeon_card_priorities": [],
            "dungeon_max_buff_enabled": False,
            "dungeon_max_buff_percent": 0,
            "dungeon_max_debuff_enabled": False,
            "dungeon_max_debuff_percent": 0,
        }
    )
    assert dialog.loop_radio.isChecked() is False
    assert dialog.stop_radio.isChecked() is True
    assert dialog.anti_afk_checkbox.isChecked() is True
    assert dialog.force_restart_wave_checkbox.isChecked() is False
    assert dialog.force_restart_wave_input.isEnabled() is False
    assert dialog.relative_positioning_checkbox.isChecked() is False
    assert dialog.reposition_camera_checkbox.isChecked() is False
    assert dialog.legend_card_checkbox.isChecked() is False
    assert dialog.legend_card_combo.isEnabled() is False
    assert dialog.dungeon_card_checkbox.isChecked() is False
    assert dialog.dungeon_content.isEnabled() is False
    assert dialog.odyssey_macro_checkbox.isChecked() is False
    assert dialog.odyssey_content.isHidden() is True
    assert dialog.odyssey_auto_pick_checkbox.isChecked() is True
    assert dialog.odyssey_card_priority_section.isHidden() is False
    assert dialog.odyssey_auto_character_card_checkbox.isChecked() is False
    assert dialog.odyssey_character_card_section.isHidden() is True
    assert dialog.odyssey_check_treasure_checkbox.isChecked() is False
    assert dialog.odyssey_check_unit_reward_checkbox.isChecked() is False
    assert dialog.odyssey_auto_shop_checkbox.isChecked() is False
    assert dialog.odyssey_auto_memoria_checkbox.isChecked() is False
    assert dialog.odyssey_memoria_section.isHidden() is True
    assert dialog.odyssey_priority_1_combo.currentText() == "Normal"
    assert dialog.odyssey_priority_2_combo.currentText() == "Shop"
    assert dialog.odyssey_priority_3_combo.currentText() == "Boss"


def test_get_settings_returns_current_state():
    """get_settings() reflects control state, not initial settings."""
    dialog = SettingsDialog(
        settings={
            "replay": "loop",
            "anti_afk": False,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": False,
            "force_restart_wave": 0,
            "wait_between_clicks": 0.2,
            "wait_between_key_presses": 0.2,
            "wait_between_steps": 0.0,
            "relative_positioning": False,
            "reposition_camera_on_start": False,
            "card_selection_legend": False,
            "legend_selected_card": "Immunity",
            "card_selection_dungeon": False,
            "dungeon_starter_card": "Money Surge",
            "dungeon_card_priorities": [],
            "dungeon_max_buff_enabled": False,
            "dungeon_max_buff_percent": 0,
            "dungeon_max_debuff_enabled": False,
            "dungeon_max_debuff_percent": 0,
        }
    )
    # Simulate user changing settings
    dialog.stop_radio.setChecked(True)
    dialog.anti_afk_checkbox.setChecked(True)
    dialog.force_restart_wave_checkbox.setChecked(True)
    dialog.force_restart_wave_input.setText("15")
    dialog.wait_between_clicks_input.setText("0.35")
    dialog.wait_between_key_input.setText("0.45")
    dialog.wait_between_steps_input.setText("1.2")
    dialog.relative_positioning_checkbox.setChecked(True)
    dialog.reposition_camera_checkbox.setChecked(True)
    dialog.legend_card_checkbox.setChecked(True)
    dialog.legend_card_combo.setCurrentText("Exploding")
    dialog.dungeon_card_checkbox.setChecked(True)
    dialog.dungeon_starter_combo.setCurrentText("Kings Burden")
    dialog._add_priority_item("Damage (Common)")
    dialog._add_priority_item("Strong (Common)")
    dialog.dungeon_max_buff_checkbox.setChecked(True)
    dialog.dungeon_max_buff_input.setText("250")
    dialog.dungeon_max_debuff_checkbox.setChecked(True)
    dialog.dungeon_max_debuff_input.setText("300")
    dialog.odyssey_macro_checkbox.setChecked(True)
    dialog.odyssey_auto_pick_checkbox.setChecked(False)
    dialog._add_generic_priority_item(
        dialog.odyssey_card_priority_list,
        dialog.odyssey_card_priority_items_layout,
        "Ambush",
    )
    dialog.odyssey_auto_character_card_checkbox.setChecked(True)
    dialog._add_generic_priority_item(
        dialog.odyssey_character_card_priority_list,
        dialog.odyssey_character_card_priority_items_layout,
        "Layered Slumber",
    )
    dialog.odyssey_auto_next_checkbox.setChecked(True)
    dialog.odyssey_check_treasure_checkbox.setChecked(True)
    dialog.odyssey_check_unit_reward_checkbox.setChecked(True)
    dialog.odyssey_auto_shop_checkbox.setChecked(True)
    dialog.odyssey_auto_memoria_checkbox.setChecked(True)
    dialog._add_generic_priority_item(
        dialog.odyssey_memoria_priority_list,
        dialog.odyssey_memoria_priority_items_layout,
        "Range",
    )
    dialog.odyssey_only_buy_when_enough_checkbox.setChecked(False)
    dialog.odyssey_priority_1_combo.setCurrentText("Boss")
    dialog.odyssey_priority_2_combo.setCurrentText("Normal")
    dialog.odyssey_priority_3_combo.setCurrentText("Shop")
    result = dialog.get_settings()
    assert result == {
        "replay": "stop",
        "anti_afk": True,
        "check_placed": False,
        "disable_chat": False,
        "force_restart_wave_enabled": True,
        "force_restart_wave": 15,
        "wait_between_clicks": 0.35,
        "wait_between_key_presses": 0.45,
        "wait_between_steps": 1.2,
        "relative_positioning": True,
        "reposition_camera_on_start": True,
        "card_selection_legend": True,
        "legend_selected_card": "Exploding",
        "card_selection_dungeon": True,
        "dungeon_starter_card": "Kings Burden",
        "dungeon_card_priorities": ["Damage (Common)", "Strong (Common)"],
        "dungeon_max_buff_enabled": True,
        "dungeon_max_buff_percent": 250,
        "dungeon_max_debuff_enabled": True,
        "dungeon_max_debuff_percent": 300,
        "odyssey_macro_enabled": True,
        "odyssey_auto_card_selection": False,
        "odyssey_auto_pick_card": False,
        "odyssey_card_priorities": ["Ambush"],
        "odyssey_auto_character_card": True,
        "odyssey_character": "Madara",
        "odyssey_character_card_priorities": ["Layered Slumber"],
        "odyssey_auto_next_room": True,
        "odyssey_room_priorities": ["Boss", "Normal", "Shop"],
        "odyssey_check_treasure_room": True,
        "odyssey_check_unit_reward": True,
        "odyssey_auto_shop_room": True,
        "odyssey_auto_memoria_selection": True,
        "odyssey_memoria_priorities": ["Range"],
        "odyssey_only_buy_when_enough": False,
    }


def test_save_sets_saved_flag():
    """Clicking save sets the saved flag."""
    dialog = SettingsDialog(
        settings={
            "replay": "loop",
            "anti_afk": False,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": False,
            "force_restart_wave": 0,
            "wait_between_clicks": 0.2,
            "wait_between_key_presses": 0.2,
            "wait_between_steps": 0.0,
            "relative_positioning": False,
            "reposition_camera_on_start": False,
            "card_selection_legend": False,
            "legend_selected_card": "Immunity",
            "card_selection_dungeon": False,
            "dungeon_starter_card": "Money Surge",
            "dungeon_card_priorities": [],
            "dungeon_max_buff_enabled": False,
            "dungeon_max_buff_percent": 0,
            "dungeon_max_debuff_enabled": False,
            "dungeon_max_debuff_percent": 0,
        }
    )
    assert dialog.saved is False
    dialog.save_button.click()
    assert dialog.saved is True


def test_close_does_not_set_saved_flag():
    """Clicking close does not set the saved flag."""
    dialog = SettingsDialog(
        settings={
            "replay": "loop",
            "anti_afk": False,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": False,
            "force_restart_wave": 0,
            "wait_between_clicks": 0.2,
            "wait_between_key_presses": 0.2,
            "wait_between_steps": 0.0,
            "relative_positioning": False,
            "reposition_camera_on_start": False,
            "card_selection_legend": False,
            "legend_selected_card": "Immunity",
            "card_selection_dungeon": False,
            "dungeon_starter_card": "Money Surge",
            "dungeon_card_priorities": [],
            "dungeon_max_buff_enabled": False,
            "dungeon_max_buff_percent": 0,
            "dungeon_max_debuff_enabled": False,
            "dungeon_max_debuff_percent": 0,
        }
    )
    dialog.close_button.click()
    assert dialog.saved is False
