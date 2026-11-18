from pathlib import Path

import cv2
import numpy as np

from macro_app.services.reward_detection import RewardDetector


def _write_template(path: Path, color: int) -> None:
    image = np.full((12, 14, 3), color, dtype=np.uint8)
    cv2.imwrite(str(path), image)


def test_reward_detector_caches_scaled_templates_for_common_and_mode_map(tmp_path):
    common_dir = tmp_path / "common"
    map_dir = tmp_path / "story" / "Planet Namek"
    common_dir.mkdir(parents=True)
    map_dir.mkdir(parents=True)

    _write_template(common_dir / "gold_ref.png", 90)
    _write_template(map_dir / "green_essence_ref.png", 180)

    detector = RewardDetector(reward_icons_dir=tmp_path)

    raw_templates = detector.load_reward_templates("story", "Planet Namek")
    assert set(raw_templates.keys()) == {"Gold", "Green Essence"}

    scaled_templates = detector.load_scaled_reward_templates("story", "Planet Namek")
    assert set(scaled_templates.keys()) == {"Gold", "Green Essence"}
    assert len(scaled_templates["Gold"]) > 1

    second_scaled = detector.load_scaled_reward_templates("story", "Planet Namek")
    assert second_scaled is scaled_templates
    assert second_scaled["Gold"][0] is scaled_templates["Gold"][0]


def test_parse_screen_rewards_no_longer_requires_pyautogui(monkeypatch):
    detector = RewardDetector()
    captured_regions = []

    def fake_capture(region):
        captured_regions.append(region)
        return np.zeros((10, 10, 3), dtype=np.uint8)

    def fake_parse_regions(reward_region_bgr, amount_region_bgr, mode, map_name):
        assert reward_region_bgr.shape == (10, 10, 3)
        assert amount_region_bgr.shape == (10, 10, 3)
        assert mode == "story"
        assert map_name == "Planet Namek"
        return "parsed"

    monkeypatch.setattr(detector, "_capture_region", fake_capture)
    monkeypatch.setattr(detector, "parse_regions", fake_parse_regions)

    result = detector.parse_screen_rewards("story", "Planet Namek")

    assert result == "parsed"
    assert captured_regions == [(210, 439, 664, 516), (219, 487, 666, 510)]


def test_reward_detector_matches_normalized_raid_folder_names(tmp_path):
    common_dir = tmp_path / "common"
    raid_dir = tmp_path / "raid" / "Ruined City"
    common_dir.mkdir(parents=True)
    raid_dir.mkdir(parents=True)

    _write_template(common_dir / "gold_ref.png", 90)
    _write_template(raid_dir / "green_essence_ref.png", 180)

    detector = RewardDetector(reward_icons_dir=tmp_path)

    raw_templates = detector.load_reward_templates("raids", "ruined city")

    assert set(raw_templates.keys()) == {"Gold", "Green Essence"}
