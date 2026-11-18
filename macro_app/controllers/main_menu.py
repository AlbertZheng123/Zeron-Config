"""Main menu controller."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from macro_app.constants import MODE_FOLDERS

MODE_DISPLAY_NAMES = {
    "story": "Story",
    "raids": "Raids",
    "legend": "Legend",
    "bossRush": "Boss Rush",
    "events": "Events",
    "dungeon": "Dungeon",
}


class MainMenuController:
    """Own main-menu-only state and bindings."""

    def __init__(self, window) -> None:
        self.window = window

    def bind(self, *, stop_macro, open_advanced_create, edit_selected_macro) -> None:
        self.window.stopMacroButton.clicked.connect(stop_macro)
        self.window.advancedCreateButton.clicked.connect(open_advanced_create)
        self.window.editAdvancedButton.clicked.connect(edit_selected_macro)

    def refresh_macro_list(self) -> None:
        self.window.macroList.clear()
        macro_count = 0
        for mode, root_folder in MODE_FOLDERS.items():
            if not os.path.isdir(root_folder):
                continue
            mode_display = MODE_DISPLAY_NAMES.get(mode, mode)
            for map_name in sorted(os.listdir(root_folder)):
                map_folder = os.path.join(root_folder, map_name)
                if not os.path.isdir(map_folder) or map_name.startswith("."):
                    continue
                for filename in sorted(os.listdir(map_folder)):
                    if not filename.endswith(".json"):
                        continue
                    macro_name = filename[:-5]
                    item = QListWidgetItem(f"{mode_display} / {map_name} / {macro_name}")
                    item.setData(
                        Qt.UserRole,
                        {
                            "path": os.path.join(map_folder, filename),
                            "mode": mode,
                            "map_name": map_name,
                            "macro_name": macro_name,
                        },
                    )
                    self.window.macroList.addItem(item)
                    macro_count += 1
        print(f"Found {macro_count} saved macros")
