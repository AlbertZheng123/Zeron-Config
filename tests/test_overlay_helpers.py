import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app.controllers import overlay_helpers
from macro_app.controllers.overlay_helpers import built_in_maps_for_mode, get_macro_folder_for_mode, get_maps_for_mode, match_map_image
from macro_app.constants import MODE_FOLDERS


@pytest.fixture(autouse=True)
def mode_folders(tmp_path, monkeypatch):
    """Provide the existing folders these routing tests exercise."""
    for mode in MODE_FOLDERS:
        folder = tmp_path / mode
        folder.mkdir()
        monkeypatch.setitem(MODE_FOLDERS, mode, str(folder))
    for mode, names in {
        "legend": ["Burning Spirit Tree", "Tokyo Railway"],
        "raids": ["HAPPY Factory"],
        "story": ["Shibuya Station", "Double Dungeon"],
    }.items():
        for name in names:
            (tmp_path / mode / name).mkdir()


def test_get_macro_folder_for_mode_returns_mode_map_folder():
    folder = get_macro_folder_for_mode("story", "Shibuya")
    assert folder.startswith(MODE_FOLDERS["story"])


def test_get_macro_folder_for_mode_prefers_existing_legacy_folder_names():
    assert get_macro_folder_for_mode("legend", "Burning Spirit") == os.path.join(
        MODE_FOLDERS["legend"], "Burning Spirit Tree"
    )
    assert get_macro_folder_for_mode("raids", "Happy") == os.path.join(
        MODE_FOLDERS["raids"], "HAPPY Factory"
    )


def test_get_maps_for_mode_returns_list():
    maps = get_maps_for_mode("story")
    assert isinstance(maps, list)
    assert "Shibuya Station" in maps
    assert "Double Dungeon" in maps


def test_built_in_maps_for_mode_uses_registry():
    maps = built_in_maps_for_mode("dungeon")
    assert "Ant Island" in maps
    assert "Frozen Volcano" in maps


def test_built_in_maps_for_mode_prefers_existing_folder_display_names():
    maps = built_in_maps_for_mode("legend")
    assert "Burning Spirit Tree" in maps
    assert "Tokyo Railway" in maps


def test_match_map_image_returns_known_story_image():
    matched = match_map_image("story", "Double Dungeon")
    assert matched is not None
    assert matched.endswith(os.path.join("map_images", "story", "double_story_map.png"))


def test_match_map_image_returns_none_for_unknown_map():
    assert match_map_image("story", "does-not-exist") is None


def test_get_maps_for_mode_includes_custom_legend_folder_without_image(tmp_path, monkeypatch):
    legend_dir = tmp_path / "legend"
    hidden_village_dir = legend_dir / "Hidden Village"
    hidden_village_dir.mkdir(parents=True)

    monkeypatch.setitem(MODE_FOLDERS, "legend", str(legend_dir))

    maps = overlay_helpers.get_maps_for_mode("legend")

    assert "Hidden Village" in maps
    assert overlay_helpers.match_map_image("legend", "Hidden Village") is None
