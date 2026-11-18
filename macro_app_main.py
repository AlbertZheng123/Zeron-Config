#!/usr/bin/env python3
"""Macro app entrypoint and composition root."""

from __future__ import annotations

import os
import sys

import supabase_client
import wave_number_detector
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication
from pynput import keyboard as pynput_keyboard

from macro_app.constants import FONTS_DIR, PAGE_OVERLAY, ensure_app_directories
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


def load_fonts() -> None:
    """Load bundled fonts before the stylesheet is reapplied."""
    for font_file in [
        "SpaceMono-Regular.ttf",
        "SpaceMono-Italic.ttf",
        "SpaceMono-Bold.ttf",
        "SpaceMono-BoldItalic.ttf",
        "Rajdhani-Bold.ttf",
        "Rajdhani-SemiBold.ttf",
        "IBMPlexSans-Regular.ttf",
        "IBMPlexSans-Medium.ttf",
        "IBMPlexSans-SemiBold.ttf",
        "Inter-Regular.ttf",
        "Inter-Medium.ttf",
        "Inter-SemiBold.ttf",
        "Inter-Bold.ttf",
    ]:
        font_path = os.path.join(FONTS_DIR, font_file)
        if not os.path.exists(font_path):
            continue
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"Loaded font: {font_file} -> {families}")
        else:
            print(f"Failed to load font: {font_file}")


def main() -> None:
    app = QApplication(sys.argv)
    ensure_app_directories()

    window = load_main_window()

    load_fonts()
    window.setStyleSheet(window.styleSheet())

    state = AppState()
    overlay_widgets = build_overlay_widgets(window)
    advanced_widgets = build_advanced_widgets(window)

    detection_service = DetectionService()
    macro_execution_service = MacroExecutionService()
    sharing_service = MacroSharingService()
    webhook_service = WebhookService()

    navigation = NavigationController(app, window, state)
    status_controller = StatusController(overlay_widgets.status_label, window.mainStatusLabel)
    webhook_controller = WebhookController(window, state, webhook_service)
    main_menu_controller = MainMenuController(window)
    overlay_controller = OverlayController(window, state, overlay_widgets, navigation, sharing_service)
    advanced_editor = AdvancedEditorController(
        window,
        state,
        advanced_widgets,
        navigation,
        status_controller,
        detection_service,
        macro_execution_service,
        webhook_controller,
        wave_number_detector,
    )
    overlay_controller.set_advanced_editor(advanced_editor)
    overlay_controller.set_webhook_controller(webhook_controller)
    webhook_controller.set_overlay_controller(overlay_controller)
    advanced_editor.set_overlay_controller(overlay_controller)
    advanced_editor.set_main_menu_controller(main_menu_controller)

    webhook_controller.bind()
    main_menu_controller.bind(
        stop_macro=advanced_editor.stop_macro,
        open_advanced_create=advanced_editor.go_to_advanced_create_from_main_menu,
        edit_selected_macro=advanced_editor.edit_selected_main_menu_macro,
    )
    overlay_controller.bind()
    advanced_editor.bind()
    navigation.on_overlay_enter(overlay_controller.refresh_all_overlay_stats)
    def on_main_menu_enter() -> None:
        main_menu_controller.refresh_macro_list()
        status_controller.set_running(state.macro_is_running)

    navigation.on_main_menu_enter(on_main_menu_enter)
    navigation.on_advanced_enter(advanced_editor.on_enter_advanced_page)

    window.advCloseButton.clicked.connect(app.quit)
    stop_shortcut = QShortcut(QKeySequence("Escape"), window)
    stop_shortcut.activated.connect(advanced_editor.handle_escape)

    control_keys = {
        pynput_keyboard.Key.ctrl,
        pynput_keyboard.Key.ctrl_l,
        pynput_keyboard.Key.ctrl_r,
    }
    ctrl_pressed = {"active": False}
    hotkey_latch = {"s": False, "p": False}
    start_hotkey_chars = {"s", "\x13"}
    stop_hotkey_chars = {"p", "\x10"}

    def on_hotkey_press(key):
        key_char = getattr(key, "char", None)
        normalized_char = key_char.lower() if isinstance(key_char, str) else None

        if key in control_keys:
            ctrl_pressed["active"] = True
            return

        if key_char == "'":
            if state.macro_is_running:
                state.macro_stop_requested = True
                state.stop_triggered_by_key = True
                print("\n" + "!" * 50)
                print("   [STOP KEY] ' pressed - stopping macro...")
                print("!" * 50)
            return

        if ctrl_pressed["active"] and normalized_char in start_hotkey_chars:
            if hotkey_latch["s"]:
                return
            hotkey_latch["s"] = True
            if not state.macro_is_running:
                state.start_triggered_by_key = True
                print("\n" + "=" * 50)
                print("   [HOTKEY] Ctrl+S pressed - start requested")
                print("=" * 50)
            return

        if ctrl_pressed["active"] and normalized_char in stop_hotkey_chars:
            if hotkey_latch["p"]:
                return
            hotkey_latch["p"] = True
            if state.macro_is_running:
                state.macro_stop_requested = True
                state.stop_triggered_by_key = True
                print("\n" + "!" * 50)
                print("   [HOTKEY] Ctrl+P pressed - stop requested")
                print("!" * 50)
            return

    def on_hotkey_release(key):
        key_char = getattr(key, "char", None)
        normalized_char = key_char.lower() if isinstance(key_char, str) else None

        if key in control_keys:
            ctrl_pressed["active"] = False
            hotkey_latch["s"] = False
            hotkey_latch["p"] = False
            return

        if normalized_char in start_hotkey_chars:
            hotkey_latch["s"] = False
            return

        if normalized_char in stop_hotkey_chars:
            hotkey_latch["p"] = False
            return

    stop_key_listener_started = False

    def start_stop_key_listener():
        nonlocal stop_key_listener_started
        if stop_key_listener_started:
            return
        try:
            listener = pynput_keyboard.Listener(on_press=on_hotkey_press, on_release=on_hotkey_release)
            listener.daemon = True
            listener.start()
            stop_key_listener_started = True
            print("Global hotkey listener initialized (press Ctrl+S to start, Ctrl+P or ' to stop)")
        except Exception as exc:
            print(f"Warning: Could not start stop key listener: {exc}")
            print("You can still use the macro buttons in the app")

    test_font = QFont("Inter")
    font_info = QFontInfo(test_font)
    resolved = font_info.family()
    if resolved.lower().startswith("inter"):
        print(f"[Font] Inter loaded successfully: {resolved}")
    else:
        print(f"[Font] Inter not found — fell back to: {resolved}")

    navigation.go_to_page(PAGE_OVERLAY)

    window.show()

    def deferred_startup_warmup():
        print("Initializing detection templates...")
        detection_service.init_templates()
        print("Initializing wave number detection templates...")
        wave_number_detector.init_wave_templates()
        supabase_client.init_cache()
        start_stop_key_listener()

    QTimer.singleShot(0, deferred_startup_warmup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
