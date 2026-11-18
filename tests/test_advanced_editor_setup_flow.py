import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("PySide6")

import macro_json
from PySide6.QtWidgets import QApplication

from macro_app.controllers.advanced_editor import AdvancedEditorController
from macro_app.controllers.main_menu import MainMenuController
from macro_app.controllers.navigation import NavigationController
from macro_app.controllers.overlay import OverlayController
from macro_app.controllers.status import StatusController
from macro_app.controllers.webhook import WebhookController
from macro_app.services.detection import DetectionService
from macro_app.services.macro_execution import MacroExecutionService
from macro_app.services.macro_sharing import MacroSharingService
from macro_app.services.webhook import WebhookService
from macro_app.state import AppState
from macro_app.ui_loader import load_main_window
from macro_app.ui_maps import build_advanced_widgets, build_overlay_widgets
import wave_number_detector


def _app():
    app = QApplication.instance()
    return app or QApplication([])


def _build_editor():
    app = _app()
    window = load_main_window()

    state = AppState()
    overlay_widgets = build_overlay_widgets(window)
    advanced_widgets = build_advanced_widgets(window)

    navigation = NavigationController(app, window, state)
    status = StatusController(overlay_widgets.status_label, window.mainStatusLabel)
    webhook_controller = WebhookController(window, state, WebhookService())
    main_menu = MainMenuController(window)
    overlay = OverlayController(window, state, overlay_widgets, navigation, MacroSharingService())
    advanced = AdvancedEditorController(
        window,
        state,
        advanced_widgets,
        navigation,
        status,
        DetectionService(),
        MacroExecutionService(),
        webhook_controller,
        wave_number_detector,
    )

    overlay.set_advanced_editor(advanced)
    overlay.set_webhook_controller(webhook_controller)
    webhook_controller.set_overlay_controller(overlay)
    advanced.set_overlay_controller(overlay)
    advanced.set_main_menu_controller(main_menu)

    webhook_controller.bind()
    main_menu.bind(
        stop_macro=advanced.stop_macro,
        open_advanced_create=advanced.go_to_advanced_create_from_main_menu,
        edit_selected_macro=advanced.edit_selected_main_menu_macro,
    )
    overlay.bind()
    advanced.bind()
    return advanced


def test_setup_steps_round_trip_and_rebuild_in_setup_section(tmp_path):
    advanced = _build_editor()
    advanced.clear_advanced_steps()
    advanced.switch_step_section("setup", show_status=False)
    advanced.switch_advanced_tab("raw")

    advanced.window.advClickXInput.setText("111")
    advanced.window.advClickYInput.setText("222")
    advanced.add_advanced_click_step()

    assert advanced.current_macro["setup_order"] == [{"cmd": "click", "x": 111, "y": 222, "button": "left"}]
    assert advanced.current_macro["order"] == []

    macro_path = tmp_path / "setup_round_trip.json"
    macro_json.save_macro(advanced.current_macro, str(macro_path))

    assert advanced.load_macro_from_path(
        str(macro_path),
        mode="story",
        map_name="Shibuya",
        macro_name="setup_round_trip",
        origin="main_menu",
    )
    assert advanced.current_macro["setup_order"] == [{"cmd": "click", "x": 111, "y": 222, "button": "left"}]

    advanced.switch_step_section("setup", show_status=False)
    visible_rows = []
    for index in range(advanced.advanced_scroll_layout.count()):
        item = advanced.advanced_scroll_layout.itemAt(index)
        if not item or not item.widget():
            continue
        step_data = item.widget().property("step_data")
        if step_data is not None:
            visible_rows.append(step_data)

    assert visible_rows == [{"cmd": "click", "x": 111, "y": 222, "button": "left"}]
