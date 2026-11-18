import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.controllers.advanced_editor import UNIT_NAME_OPTIONS
from macro_app.services.ability_steps import get_main_ability_template_path, list_main_unit_abilities
from wave_number_detector import CONFIDENCE_THRESHOLD


def test_live_yen_confidence_threshold_matches_release_setting():
    assert CONFIDENCE_THRESHOLD == 0.60


def test_new_main_unit_ability_mappings_exist():
    assert ("Hell", "skele_hell_ref.png") in list_main_unit_abilities("Skele King")
    assert ("Nuke", "whitebeard_nuke_ref.png") in list_main_unit_abilities("Whitebeard")
    assert ("I sacrifice", "griffith_sacrifice_ref.png") in list_main_unit_abilities("Griffith")
    assert ("Shotgun Loop", "lleft_shotgun_loop_ref.png") in list_main_unit_abilities("Lleft")
    assert ("Sinister Sanctum", "sukuna_sinister_sanctum_ref.png") in list_main_unit_abilities("Sukuna")


def test_new_main_unit_ability_templates_resolve_to_real_files():
    assert get_main_ability_template_path("Skele King", "skele_hell_ref.png").exists()
    assert get_main_ability_template_path("Whitebeard", "whitebeard_nuke_ref.png").exists()
    assert get_main_ability_template_path("Doffy", "doffy_string_dominion_ref.png").exists()


def test_unit_dropdown_options_include_requested_units():
    for unit_name in (
        "VSJW",
        "Griffith",
        "Doffy",
        "Skele King",
        "Hellkiller",
        "Valentine",
    ):
        assert unit_name in UNIT_NAME_OPTIONS
