"""Helpers for loading the compiled main window UI."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from macro_app.constants import resolve_stylesheet_asset_urls
from macro_app.ui_generated import Ui_MainWindow


def load_main_window() -> QMainWindow:
    """Build the main window from the compiled UI module.

    The legacy code expects widget object names to be available directly on the
    window instance, so we mirror the generated UI attributes back onto the
    `QMainWindow`.
    """
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.setStyleSheet(resolve_stylesheet_asset_urls(window.styleSheet()))
    for name, value in vars(ui).items():
        if name.startswith("_"):
            continue
        setattr(window, name, value)
    window._compiled_ui = ui
    return window
