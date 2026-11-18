import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QFrame, QLabel

from macro_app.controllers.advanced_editor import AdvancedEditorController
from macro_app.controllers.main_menu import MainMenuController
from macro_app.controllers.navigation import NavigationController
from macro_app.controllers.overlay import OverlayController, _reward_stats_pixmap
from macro_app.controllers.status import StatusController
from macro_app.controllers.webhook import WebhookController
from macro_app.services.detection import DetectionService
from macro_app.services.macro_execution import MacroExecutionService
from macro_app.services.macro_sharing import MacroSharingService
from macro_app.services.webhook import WebhookService
from macro_app.state import AppState
from macro_app.ui_loader import load_main_window
from macro_app.ui_maps import build_advanced_widgets, build_overlay_widgets


def _app():
    app = QApplication.instance()
    return app or QApplication([])


def test_ui_and_controllers_smoke():
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
        object(),
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

    assert window.overlayScrollArea.widget() is window.overlayContent
    assert window.stackedWidget.widget(0) is window.overlayPage
    assert window.mainStatusLabel is not None
    assert state.editor.advanced_scroll_layout is not None
    assert overlay._settings_debug_toggle is not None

    advanced.current_macro["order"] = [
        {"cmd": "wait_seconds", "seconds": 1},
        {"cmd": "wait_seconds", "seconds": 2},
    ]
    advanced.rebuild_visible_step_rows()
    separators = window.advancedStepsScrollContent.findChildren(QFrame, "stepDropSeparator")
    badges = [
        item.widget().findChild(QLabel, "stepNumBadge").text()
        for item_index in range(state.editor.advanced_scroll_layout.count())
        if (item := state.editor.advanced_scroll_layout.itemAt(item_index))
        and item.widget()
        and item.widget().property("step_data") is not None
        and item.widget().findChild(QLabel, "stepNumBadge")
    ]
    assert len(separators) == 3
    assert badges == ["1", "2"]

    overlay._settings_debug_toggle.click()
    assert state.debug_console_mode is True

    overlay._settings_debug_toggle.click()
    assert state.debug_console_mode is False


def test_reward_stats_pixmap_resolves_newly_mapped_reward_icons():
    _app()

    assert _reward_stats_pixmap("Auric Coin") is not None
    assert _reward_stats_pixmap("Makima") is not None
    assert _reward_stats_pixmap("Fused Spirit Orb") is not None
    assert _reward_stats_pixmap("Red Key") is not None
