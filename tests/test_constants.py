import os
import sys
import configparser
import shlex
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_app import constants


def _patch_app_dirs(monkeypatch, tmp_path):
    legacy_macros = tmp_path / "repo_macros"
    user_data = tmp_path / "user_data"
    macros_folder = user_data / "macros"
    runtime_output = user_data / "runtime_output"

    monkeypatch.setattr(constants, "LEGACY_MACROS_FOLDER", str(legacy_macros))
    monkeypatch.setattr(constants, "USER_DATA_DIR", str(user_data))
    monkeypatch.setattr(constants, "MACROS_FOLDER", str(macros_folder))
    monkeypatch.setattr(constants, "LEGACY_RUNTIME_OUTPUT_DIR", str(tmp_path / "legacy_runtime_output"))
    monkeypatch.setattr(constants, "RUNTIME_OUTPUT_DIR", str(runtime_output))
    monkeypatch.setattr(constants, "DEBUG_OUTPUT_DIR", str(runtime_output / "debug"))
    monkeypatch.setattr(constants, "LOGS_FOLDER", str(runtime_output / "logs"))
    monkeypatch.setattr(constants, "DATA_OUTPUT_DIR", str(runtime_output / "data"))
    monkeypatch.setattr(
        constants,
        "MODE_FOLDERS",
        {
            "story": str(macros_folder / "story"),
            "raids": str(macros_folder / "raids"),
            "legend": str(macros_folder / "legend"),
            "bossRush": str(macros_folder / "bossRush"),
            "events": str(macros_folder / "events"),
            "dungeon": str(macros_folder / "dungeon"),
        },
    )
    return legacy_macros, macros_folder


def test_ensure_app_directories_merges_new_bundled_macro_folders_for_existing_users(tmp_path, monkeypatch):
    legacy_macros, macros_folder = _patch_app_dirs(monkeypatch, tmp_path)

    hidden_village_seed = legacy_macros / "legend" / "Hidden Village" / "starter.json"
    hidden_village_seed.parent.mkdir(parents=True)
    hidden_village_seed.write_text('{"seed": true}', encoding="utf-8")

    existing_user_macro = macros_folder / "legend" / "Tokyo Railway" / "custom.json"
    existing_user_macro.parent.mkdir(parents=True)
    existing_user_macro.write_text('{"custom": true}', encoding="utf-8")

    constants.ensure_app_directories()

    assert (macros_folder / "legend" / "Hidden Village").is_dir()
    assert (macros_folder / "legend" / "Hidden Village" / "starter.json").read_text(encoding="utf-8") == '{"seed": true}'
    assert existing_user_macro.read_text(encoding="utf-8") == '{"custom": true}'


def test_ensure_app_directories_does_not_overwrite_existing_user_macro_files(tmp_path, monkeypatch):
    legacy_macros, macros_folder = _patch_app_dirs(monkeypatch, tmp_path)

    bundled_macro = legacy_macros / "legend" / "Hidden Village" / "starter.json"
    bundled_macro.parent.mkdir(parents=True)
    bundled_macro.write_text('{"bundled": true}', encoding="utf-8")

    user_macro = macros_folder / "legend" / "Hidden Village" / "starter.json"
    user_macro.parent.mkdir(parents=True)
    user_macro.write_text('{"user": true}', encoding="utf-8")

    constants.ensure_app_directories()

    assert user_macro.read_text(encoding="utf-8") == '{"user": true}'


def test_packaging_spec_includes_bundled_macro_seed_folder():
    project_root = Path(__file__).resolve().parents[1]
    spec = configparser.ConfigParser()
    spec.read(project_root / "pysidedeploy.spec")
    resources = {}
    for arg in shlex.split(spec["nuitka"]["extra_args"]):
        if arg.startswith("--include-data-dir="):
            source, destination = arg.removeprefix("--include-data-dir=").rsplit("=", 1)
            resources[destination] = (project_root / source).resolve()

    assert resources["macros"] == project_root / "macros"
    assert (resources["macros"] / "legend" / "Hidden Village").is_dir()
