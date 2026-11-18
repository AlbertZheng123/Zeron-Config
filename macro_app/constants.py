"""Shared paths, page ids, and game constants for the macro app."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES_DIR = os.path.join(BASE_DIR, "references")
FONTS_DIR = os.path.join(REFERENCES_DIR, "fonts")

APP_NAME = "Zeron Config"
LEGACY_MACROS_FOLDER = os.path.join(BASE_DIR, "macros")
LEGACY_RUNTIME_OUTPUT_DIR = os.path.join(BASE_DIR, "runtime_output")


def _default_user_data_dir() -> str:
    if sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    if os.name == "nt":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, APP_NAME)
    return os.path.expanduser(f"~/.local/share/{APP_NAME}")


def _resolve_user_data_dir() -> str:
    override = os.environ.get("ZERON_CONFIG_HOME")
    candidates = [override] if override else []
    candidates.append(_default_user_data_dir())
    candidates.append(os.path.join(BASE_DIR, ".zeron_user_data"))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            return candidate
        except OSError:
            continue
    return os.path.join(BASE_DIR, ".zeron_user_data")


USER_DATA_DIR = _resolve_user_data_dir()
MACROS_FOLDER = os.path.join(USER_DATA_DIR, "macros")
RUNTIME_OUTPUT_DIR = os.path.join(USER_DATA_DIR, "runtime_output")
DEBUG_OUTPUT_DIR = os.path.join(RUNTIME_OUTPUT_DIR, "debug")
LOGS_FOLDER = os.path.join(RUNTIME_OUTPUT_DIR, "logs")
DATA_OUTPUT_DIR = os.path.join(RUNTIME_OUTPUT_DIR, "data")

MODE_FOLDERS = {
    "story": os.path.join(MACROS_FOLDER, "story"),
    "raids": os.path.join(MACROS_FOLDER, "raids"),
    "legend": os.path.join(MACROS_FOLDER, "legend"),
    "bossRush": os.path.join(MACROS_FOLDER, "bossRush"),
    "events": os.path.join(MACROS_FOLDER, "events"),
    "dungeon": os.path.join(MACROS_FOLDER, "dungeon"),
}

PAGE_OVERLAY = 0
PAGE_MAIN_MENU = 1
PAGE_ADVANCED_CREATE = 2
PAGE_LICENSE = 3

OVERLAY_SIZE = (1130, 730)
OVERLAY_POS = (0, 40)
COMPACT_SIZE = (800, 600)
ADVANCED_CREATE_SIZE = (1470, 860)

KEY_SAVE_PATH = os.path.expanduser("~/.anime_vanguards_key")

DISCORD_SCREENSHOT_REGION = (0, 40, 1200, 670)

VOTE_BUTTON_IMAGE = os.path.join(REFERENCES_DIR, "vote_start_button_ref.png")
VOTE_BUTTON_REGION = (641, 148, 718, 188)
VOTE_BUTTON_CONFIDENCE = 0.2

WAVE_COMPLETED_IMAGE = os.path.join(REFERENCES_DIR, "wave_completed_final_ref.png")
WAVE_COMPLETED_REGION = (846, 71, 869, 101)
WAVE_COMPLETED_CONFIDENCE = 0.6

REPLAY_IMAGE = os.path.join(REFERENCES_DIR, "replay_ref.png")
REPLAY_IMAGE_4 = os.path.join(REFERENCES_DIR, "replay_ref_4.png")
REPLAY_IMAGE_5 = os.path.join(REFERENCES_DIR, "replay_ref_5.png")
REPLAY_REGION = (190, 508, 720, 578)
REPLAY_CONFIDENCE = 0.6

UNIT_SLOT_REGIONS = {
    389: (357, 570, 422, 638),
    473: (441, 570, 506, 638),
    561: (529, 570, 594, 638),
    643: (611, 573, 676, 641),
    727: (695, 574, 760, 642),
    810: (778, 576, 843, 644),
}

UNIT_COORDINATES = {
    1: {"x": 389, "y": 604},
    2: {"x": 473, "y": 604},
    3: {"x": 561, "y": 604},
    4: {"x": 643, "y": 607},
    5: {"x": 727, "y": 608},
    6: {"x": 810, "y": 610},
}

MAP_IMAGE_REGISTRY = {
    "story": {
        "double_story_map": ["double dungeon"],
        "downtown_tokyo_story_map": ["downtown tokyo"],
        "edge_heaven_story_map": ["edge of heaven"],
        "frozen_port_story_map": ["frozen port"],
        "hill_swords_story_map": ["hill of swords"],
        "lebereo_story_map": ["lebereo"],
        "martial_story_map": ["martial"],
        "namek_story_map": ["namek"],
        "sand_story_map": ["sand village"],
        "shibuya_story_map": ["shibuya"],
        "spirit_story_map": ["spirit society"],
        "undeground_story_map": ["underground"],
    },
    "raids": {
        "happy_raid_map": ["happy"],
        "ruined_city_raid_map": ["ruined city"],
        "spider_raid_map": ["spider"],
    },
    "legend": {
        "burning_spirit_legend_map": ["burning spirit"],
        "crystal_legend_map": ["crystal"],
        "double_legend_map": ["double dungeon"],
        "golden_legend_map": ["golden castle"],
        "imprisoned_legend_map": ["imprisoned"],
        "kuinshi_legend_map": ["kuinshi"],
        "land_gods_legend_map": ["land of the gods"],
        "sand_legend_map": ["sand village"],
        "shibuya_legend_map": ["shibuya"],
        "shining_legend_map": ["shining castle"],
        "tokyo_railway_legend": ["tokyo railway"],
        "tracks_legend_map": ["tracks at the edge", "tracks"],
    },
    "bossRush": {
        "arin_boss_map": ["arin"],
        "igris_boss_map": ["igris"],
        "salter_boss_map": ["salter", "saltter", "saber alter"],
        "sukuna_boss_map": ["sukuna"],
    },
    "events": {
        "fall_event_map": ["fall"],
        "summer_event_map": ["summer"],
        "winter_event_map": ["winter"],
        "land_conquest_event_map": ["land conquest"],
    },
    "dungeon": {
        "anniversary_dungeon_map": ["anniversary"],
        "ant_island_dungeon_map": ["ant island"],
        "frozen_volcano_dungeon_map": ["frozen volcano"],
        "mountain_dungeon_map": ["mountain"],
    },
}

MODE_IMAGE_FOLDERS = {
    "story": os.path.join(BASE_DIR, "map_images", "story"),
    "raids": os.path.join(BASE_DIR, "map_images", "raid"),
    "legend": os.path.join(BASE_DIR, "map_images", "legend"),
    "bossRush": os.path.join(BASE_DIR, "map_images", "boss"),
    "events": os.path.join(BASE_DIR, "map_images", "event"),
    "dungeon": os.path.join(BASE_DIR, "map_images", "dungeon"),
}


def stylesheet_asset_url(path: str) -> str:
    """Return a packaged-safe stylesheet URL for a local asset."""
    return Path(path).resolve().as_posix()


def resolve_stylesheet_asset_urls(stylesheet: str) -> str:
    """Rewrite repo-relative stylesheet asset URLs to absolute local file URLs."""
    pattern = re.compile(r"url\((['\"]?)([^)'\"]+)\1\)")

    def _replace(match: re.Match[str]) -> str:
        asset_path = match.group(2).strip()
        if "://" in asset_path or asset_path.startswith(":/") or os.path.isabs(asset_path):
            return match.group(0)
        if asset_path.startswith(("references/", "ui_references/", "map_images/")):
            absolute = os.path.join(BASE_DIR, asset_path)
            if os.path.exists(absolute):
                return f"url({stylesheet_asset_url(absolute)})"
        return match.group(0)

    return pattern.sub(_replace, stylesheet)


def _copy_tree_contents(src: str, dst: str) -> None:
    if not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    for entry in os.listdir(src):
        src_path = os.path.join(src, entry)
        dst_path = os.path.join(dst, entry)
        if os.path.isdir(src_path):
            if not os.path.exists(dst_path):
                shutil.copytree(src_path, dst_path)
            else:
                _copy_tree_contents(src_path, dst_path)
        elif not os.path.exists(dst_path):
            shutil.copy2(src_path, dst_path)


def _same_path(path_a: str, path_b: str) -> bool:
    return os.path.normcase(os.path.abspath(path_a)) == os.path.normcase(os.path.abspath(path_b))


def ensure_app_directories() -> None:
    """Create writable user-data folders and merge bundled defaults without overwriting user data."""
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    if os.path.isdir(LEGACY_MACROS_FOLDER) and not _same_path(LEGACY_MACROS_FOLDER, MACROS_FOLDER):
        _copy_tree_contents(LEGACY_MACROS_FOLDER, MACROS_FOLDER)

    if os.path.isdir(LEGACY_RUNTIME_OUTPUT_DIR):
        legacy_logs = os.path.join(LEGACY_RUNTIME_OUTPUT_DIR, "logs")
        legacy_data = os.path.join(LEGACY_RUNTIME_OUTPUT_DIR, "data")
        if os.path.isdir(legacy_logs) and not os.path.exists(LOGS_FOLDER):
            _copy_tree_contents(legacy_logs, LOGS_FOLDER)
        if os.path.isdir(legacy_data) and not os.path.exists(DATA_OUTPUT_DIR):
            _copy_tree_contents(legacy_data, DATA_OUTPUT_DIR)

    os.makedirs(MACROS_FOLDER, exist_ok=True)
    os.makedirs(RUNTIME_OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
    for folder in MODE_FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
