import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import macro_app.controllers.main_menu as main_menu_module
from macro_app.controllers.main_menu import MainMenuController
from macro_app.ui_loader import load_main_window


def _app():
    app = QApplication.instance()
    return app or QApplication([])


def test_refresh_macro_list_recursively_lists_mode_map_macros(monkeypatch, tmp_path):
    roots = {
        "story": str(tmp_path / "story"),
        "legend": str(tmp_path / "legend"),
    }
    os.makedirs(tmp_path / "story" / "Planet Namek", exist_ok=True)
    os.makedirs(tmp_path / "legend" / "Tokyo Railway", exist_ok=True)
    (tmp_path / "story" / "Planet Namek" / "testing.json").write_text("{}", encoding="utf-8")
    (tmp_path / "legend" / "Tokyo Railway" / "burning.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main_menu_module, "MODE_FOLDERS", roots)

    window = load_main_window()
    controller = MainMenuController(window)
    controller.refresh_macro_list()

    texts = [window.macroList.item(i).text() for i in range(window.macroList.count())]
    assert texts == [
        "Story / Planet Namek / testing",
        "Legend / Tokyo Railway / burning",
    ]

    first_item = window.macroList.item(0)
    first_data = first_item.data(Qt.UserRole)
    assert first_data["mode"] == "story"
    assert first_data["map_name"] == "Planet Namek"
    assert first_data["macro_name"] == "testing"
    assert first_data["path"].endswith(os.path.join("story", "Planet Namek", "testing.json"))
