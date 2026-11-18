"""Advanced editor and macro runner controller."""

from __future__ import annotations

import collections
import copy
import html
import os
import re
import threading
import time

import macro_json
from macro_app.dialogs.settings_dialog import SettingsDialog
from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRect, QSize, QTimer, Qt, QStringListModel
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from macro_app.constants import PAGE_ADVANCED_CREATE, PAGE_MAIN_MENU, PAGE_OVERLAY, REPLAY_CONFIDENCE, REPLAY_REGION, UNIT_COORDINATES
from macro_app.controllers.advanced_editor_helpers import (
    build_macro_save_path,
    compact_macro_placement,
    get_invalid_upgrade_order_indices,
    move_instruction_to_drop_index,
    parse_advanced_step_data,
    retarget_place_instruction,
)
from macro_app.controllers.overlay_helpers import get_maps_for_mode
from macro_app.services.camera_positioning import GAME_FOCUS_CLICK, reposition_camera
from macro_app.services.detection_profile import DetectionProfiler
from macro_app.services.dungeon_card_selection import DungeonCardSelector
from macro_app.services.legend_card_selection import LegendCardSelector
from macro_app.services.match_result_detection import MatchResultDetection, MatchResultDetector
from macro_app.services.odyssey_flow import OdysseyFlowService
from macro_app.services.ability_steps import ARCANE_ELEMENTS, ARCANE_SKILLS, MAIN_UNIT_FOLDERS, list_main_unit_abilities
from macro_app.services.macro_execution import MacroExecutionContext
from macro_app.services.reward_detection import RewardDetector, RewardParseResult
from macro_app.services.reward_stats import RewardStatsStore
from macro_app.services.relative_positioning import RelativePositioner, RelativePositioningError, RelativePyAutoGUI
from macro_app.services.focus_lease_input import FocusLeasePyAutoGUI
from macro_app.services.screen_capture import RuntimeScreenCapture, ScreenCaptureError
from macro_app.services.run_logs import MacroRunLogger

UNIT_NAME_OPTIONS = list(
    dict.fromkeys(
        [
            "Ainz",
            "Shanks",
            "Alucard",
            "Rukia",
            "Ichigo (New)",
            "Broly",
            "Pride",
            "Dio",
            "Erza",
            "Reze",
            "Trunks",
            "Denji",
            "Makima",
            "Brook",
            "Sasuke",
            "Speedwagon",
            "Takorada",
            "Nami",
            "Ulquiorra",
            "Luffy",
            "Whitebeard",
            "Aizen (New)",
            "Aizen (Old)",
            "Ichigo (Old)",
            "Mob",
            "Cid",
            "VSJW",
            "Boo",
            "Griffith",
            "Lleft",
            "Rogita",
            "Guts",
            "Doffy",
            "Toji",
            "Haruka Rin",
            "Fubuki",
            "Sukuna",
            "Ghost Girl",
            "Hollowseph",
            "Law",
            "Ace",
            "Hellkiller",
            "Manipulator",
            "Vegito (Super)",
            "Choso",
            "Ice Manipulator",
            "Trash Gamer",
            "Freizo",
            "Skele King",
            "Cha-In",
            "Tengen",
            "Saber",
            "Salter",
            "Valentine",
        ]
    )
)

START_MACRO_BUTTON_TEXT = "Start Macro (Ctrl+S)"
STOP_MACRO_BUTTON_TEXT = "Stop Macro (Ctrl+P)"
RECORD_PLACE_CLICK_TEXT = "Record Click"
SKELE_STRINGS_LABEL = "Skele: Strings"
FORCE_RESTART_POLL_INTERVAL_SECONDS = 5.0
FORCE_RESTART_CLICK_INTERVAL_SECONDS = 1.0
FORCE_RESTART_CLICK_SEQUENCE = (
    (20, 645),
    (963, 318),
    (529, 414),
    (596, 400),
)

TARGET_PRIORITY_OPTIONS = [
    "First",
    "Closest",
    "Last",
    "Strongest",
    "Weakest",
    "Bosses",
]

_STEP_NAV_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}
_STEP_NAV_ICON_PATHS = {
    "user": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "user_icon.png")),
    "cube": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "upgrade_icon.png")),
    "clock": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "timer_icon.png")),
    "list": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "list_icon_png.png")),
    "bolt": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "abilites_icon.png")),
    "gear": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "steps_nav", "settings_icon.png")),
}


def _step_nav_color(value: str) -> QColor:
    normalized = value.strip()
    match = re.fullmatch(
        r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9]*\.?[0-9]+)\s*\)",
        normalized,
        re.IGNORECASE,
    )
    if match:
        red, green, blue, alpha = match.groups()
        alpha_value = float(alpha)
        alpha_channel = max(0, min(255, round(alpha_value * 255))) if alpha_value <= 1.0 else max(0, min(255, round(alpha_value)))
        return QColor(int(red), int(green), int(blue), alpha_channel)
    return QColor(normalized)


def _step_nav_icon(name: str, color: str, size: int = 14) -> QIcon:
    key = (name, color, size)
    cached = _STEP_NAV_ICON_CACHE.get(key)
    if cached is not None:
        return cached

    icon_color = _step_nav_color(color)
    icon_path = _STEP_NAV_ICON_PATHS.get(name)
    if icon_path and os.path.exists(icon_path):
        source = QPixmap(icon_path)
        if not source.isNull():
            scaled = source.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            x = max(0, (size - scaled.width()) // 2)
            y = max(0, (size - scaled.height()) // 2)
            painter.drawPixmap(x, y, scaled)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), icon_color)
            painter.end()
            icon = QIcon(pixmap)
            _STEP_NAV_ICON_CACHE[key] = icon
            return icon

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(icon_color)
    pen.setWidthF(2.0)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    s = float(size)

    if name == "user":
        painter.drawEllipse(QRect(int(s * 0.32), int(s * 0.16), int(s * 0.36), int(s * 0.30)))
        path = QPainterPath()
        path.moveTo(s * 0.24, s * 0.86)
        path.cubicTo(s * 0.24, s * 0.66, s * 0.76, s * 0.66, s * 0.76, s * 0.86)
        painter.drawPath(path)
    elif name == "cube":
        path = QPainterPath()
        path.moveTo(s * 0.50, s * 0.12)
        path.lineTo(s * 0.78, s * 0.28)
        path.lineTo(s * 0.78, s * 0.64)
        path.lineTo(s * 0.50, s * 0.82)
        path.lineTo(s * 0.22, s * 0.64)
        path.lineTo(s * 0.22, s * 0.28)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(int(s * 0.50), int(s * 0.12), int(s * 0.50), int(s * 0.48))
        painter.drawLine(int(s * 0.22), int(s * 0.28), int(s * 0.50), int(s * 0.48))
        painter.drawLine(int(s * 0.78), int(s * 0.28), int(s * 0.50), int(s * 0.48))
    elif name == "clock":
        painter.drawEllipse(QRect(int(s * 0.16), int(s * 0.16), int(s * 0.68), int(s * 0.68)))
        painter.drawLine(int(s * 0.50), int(s * 0.50), int(s * 0.50), int(s * 0.30))
        painter.drawLine(int(s * 0.50), int(s * 0.50), int(s * 0.64), int(s * 0.58))
    elif name == "list":
        for y in (0.28, 0.50, 0.72):
            painter.drawLine(int(s * 0.18), int(s * y), int(s * 0.28), int(s * y))
            painter.drawLine(int(s * 0.38), int(s * y), int(s * 0.82), int(s * y))
    elif name == "bolt":
        path = QPainterPath()
        path.moveTo(s * 0.56, s * 0.12)
        path.lineTo(s * 0.28, s * 0.50)
        path.lineTo(s * 0.48, s * 0.50)
        path.lineTo(s * 0.42, s * 0.88)
        path.lineTo(s * 0.72, s * 0.44)
        path.lineTo(s * 0.52, s * 0.44)
        path.closeSubpath()
        painter.drawPath(path)
    else:
        center = QPointF(s / 2.0, s / 2.0)
        painter.drawEllipse(center, s * 0.18, s * 0.18)
        for dx1, dy1, dx2, dy2 in (
            (0, -0.46, 0, -0.29),
            (0.33, -0.33, 0.21, -0.21),
            (0.46, 0, 0.29, 0),
            (0.33, 0.33, 0.21, 0.21),
            (0, 0.46, 0, 0.29),
            (-0.33, 0.33, -0.21, 0.21),
            (-0.46, 0, -0.29, 0),
            (-0.33, -0.33, -0.21, -0.21),
        ):
            painter.drawLine(
                int(center.x() + s * dx1),
                int(center.y() + s * dy1),
                int(center.x() + s * dx2),
                int(center.y() + s * dy2),
            )

    painter.end()
    icon = QIcon(pixmap)
    _STEP_NAV_ICON_CACHE[key] = icon
    return icon


class _HoverExpandFrame(QFrame):
    def __init__(self, on_hover_changed, parent=None) -> None:
        super().__init__(parent)
        self._on_hover_changed = on_hover_changed
        self.setMouseTracking(True)

    def enterEvent(self, event) -> None:  # pragma: no cover - GUI behavior
        self._on_hover_changed(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # pragma: no cover - GUI behavior
        if self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            super().leaveEvent(event)
            return
        self._on_hover_changed(False)
        super().leaveEvent(event)


class _DraggableStepRow(QFrame):
    """Step row frame that delegates drag gestures to the editor controller."""

    def __init__(self, drag_controller, parent=None) -> None:
        super().__init__(parent)
        self._drag_controller = drag_controller
        self.setMouseTracking(True)

    def mousePressEvent(self, event) -> None:  # pragma: no cover - GUI gesture plumbing
        self._drag_controller._on_step_row_mouse_press(self, event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # pragma: no cover - GUI gesture plumbing
        self._drag_controller._on_step_row_mouse_move(self, event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # pragma: no cover - GUI gesture plumbing
        self._drag_controller._on_step_row_mouse_release(self, event)
        super().mouseReleaseEvent(event)


class AdvancedEditorController:
    """Own advanced editor UI, macro persistence, and macro execution."""

    _STEP_DETAIL_MAX_WIDTH = 170

    def __init__(
        self,
        window,
        state,
        advanced_widgets,
        navigation,
        status_controller,
        detection_service,
        macro_execution_service,
        webhook_controller,
        wave_number_detector,
    ) -> None:
        self.window = window
        self.state = state
        self.advanced_widgets = advanced_widgets
        self.navigation = navigation
        self.status_controller = status_controller
        self.detection_service = detection_service
        self.macro_execution_service = macro_execution_service
        self.webhook_controller = webhook_controller
        self.wave_number_detector = wave_number_detector
        self.overlay_controller = None
        self.main_menu_controller = None
        self.run_logger = MacroRunLogger()
        self.legend_card_selector = LegendCardSelector()
        self.dungeon_card_selector = DungeonCardSelector()
        self.odyssey_flow_service = OdysseyFlowService()
        self.match_result_detector = MatchResultDetector()
        self.reward_detector = RewardDetector()
        self.reward_stats_store = RewardStatsStore()
        self._saved_macro_runtime_cache: dict[str, object] | None = None
        self._searchable_unit_inputs_initialized = False
        self._abilities_tab_initialized = False
        self._step_drop_separators = []
        self._step_drag_row = None
        self._step_drag_source_index = None
        self._step_drag_start_global = None
        self._step_drag_active = False
        self._step_drag_target_index = None

        self.window.advancedStepsScrollContent.setStyleSheet("background-color: #0a0a0a;")
        advanced_scroll_layout = QVBoxLayout(self.window.advancedStepsScrollContent)
        advanced_scroll_layout.setAlignment(Qt.AlignTop)
        advanced_scroll_layout.setContentsMargins(8, 8, 8, 8)
        advanced_scroll_layout.setSpacing(6)
        self.state.editor.advanced_scroll_layout = advanced_scroll_layout

        self.window.advRunMacroButton.setStyleSheet(
            "QPushButton { background-color: #10b981; color: #000000; border: none; "
            "border-radius: 0px; font-family: 'Inter', sans-serif; "
            "font-size: 11px; font-weight: bold; letter-spacing: 1; }"
            "QPushButton:hover { background-color: #0ea472; }"
            "QPushButton:pressed { background-color: #0d9668; }"
        )
        self.window.advStopMacroButton.setStyleSheet(
            "QPushButton { background-color: rgba(220, 50, 50, 0.7); color: #000000; border: none; "
            "border-radius: 0px; font-family: 'Inter', sans-serif; "
            "font-size: 11px; font-weight: bold; letter-spacing: 1; }"
            "QPushButton:hover { background-color: rgba(220, 50, 50, 0.85); }"
            "QPushButton:pressed { background-color: rgba(220, 50, 50, 1.0); }"
        )
        self.window.advLogTextArea.setStyleSheet(
            "background-color: #0a0a0a; color: #E0E0E0; border: 1px solid #2a2a2a; "
            "border-radius: 0px; font-size: 12px; font-family: 'SF Mono', 'Menlo', monospace;"
        )

        self.state.editor.adv_log_queue = collections.deque()
        self.state.editor.adv_log_poll_timer = QTimer()
        self.state.editor.adv_log_poll_timer.timeout.connect(self.poll_adv_log)

        self.state.stop_key_timer = QTimer()
        self.state.stop_key_timer.timeout.connect(self.check_stop_key_triggered)
        self.state.stop_key_timer.start(100)
        self._configure_bottom_layout()
        self._init_place_upgrade_scroll_area()
        self._init_other_group()
        self._init_abilities_tab_shell()
        self._apply_advanced_create_step_redesign()
        self._init_step_section_buttons()
        self._style_macro_steps_panel()
        self._style_macro_console_panel()

    @property
    def current_macro(self) -> dict:
        return self.state.editor.current_macro

    @current_macro.setter
    def current_macro(self, value: dict) -> None:
        self.state.editor.current_macro = value

    @property
    def advanced_scroll_layout(self):
        return self.state.editor.advanced_scroll_layout

    def set_overlay_controller(self, overlay_controller) -> None:
        self.overlay_controller = overlay_controller

    def set_main_menu_controller(self, main_menu_controller) -> None:
        self.main_menu_controller = main_menu_controller

    def bind(self) -> None:
        self.window.advRunMacroButton.clicked.connect(self.run_advanced_macro)
        self.window.advStopMacroButton.clicked.connect(self.stop_advanced_macro)
        self.window.addUpgradeStepButton.clicked.connect(self.add_upgrade_step)
        self.window.addAdvancedWaitButton.clicked.connect(self.add_advanced_wait_step)
        self.window.addPlaceStepButton.clicked.connect(self.add_place_step)
        self.window.recordPlaceClickButton.clicked.connect(self.record_place_click)
        self.window.advancedSaveButton.clicked.connect(self.save_advanced_macro)
        self.window.advancedClearButton.clicked.connect(self.clear_advanced_steps)
        self.window.advBackButton.clicked.connect(self.back_from_advanced_create)
        self.window.tabUnitsButton.clicked.connect(lambda: self.switch_advanced_tab("units"))
        self.window.tabPlaceUpgradeButton.clicked.connect(lambda: self.switch_advanced_tab("place_upgrade"))
        self.window.tabWaitButton.clicked.connect(lambda: self.switch_advanced_tab("wait"))
        self.window.tabRawStepsButton.clicked.connect(lambda: self.switch_advanced_tab("raw"))
        self.window.tabAbilitiesButton.clicked.connect(lambda: self.switch_advanced_tab("abilities"))
        self.window.tabSettingsButton.clicked.connect(self.open_settings_dialog)
        self.window.addAdvancedClickButton.clicked.connect(self.add_advanced_click_step)
        self.window.addAdvancedKeyButton.clicked.connect(self.add_advanced_key_step)
        self.window.advRecordClickButton.clicked.connect(self.record_advanced_click)
        self.window.placeUnitCombo.currentIndexChanged.connect(self.update_placement_counter_label)
        self.window.upgradeUnitCombo.currentIndexChanged.connect(self.refresh_upgrade_placement_combo)
        self.window.otherSellAddButton.clicked.connect(self.add_sell_step)
        self.window.otherPriorityAddButton.clicked.connect(self.add_priority_step)
        if hasattr(self.window, "maxUpgradeCheckBox"):
            self.window.autoUpgradeCheckBox.toggled.connect(
                lambda checked: checked and self.window.maxUpgradeCheckBox.setChecked(False)
            )
            self.window.maxUpgradeCheckBox.toggled.connect(
                lambda checked: checked and self.window.autoUpgradeCheckBox.setChecked(False)
            )
            self.window.upgradeNoPlacementsLabel.setText("")

        self._bind_unit_input_save_signals()

        self.refresh_upgrade_unit_combo()
        self.refresh_place_unit_combo()
        self.refresh_other_unit_combos()
        self.refresh_upgrade_placement_combo()
        self.switch_step_section(self.state.editor.step_section, show_status=False)

    def on_enter_advanced_page(self) -> None:
        self._ensure_advanced_editor_runtime_ui_initialized()
        if hasattr(self.window, "statusbar"):
            self.window.statusbar.hide()
        if hasattr(self, "_step_nav_hover_timer"):
            self._step_nav_hover_timer.start()
        self.switch_advanced_tab("units")
        self._apply_initial_step_nav_layout()
        QTimer.singleShot(0, self._apply_initial_step_nav_layout)
        QTimer.singleShot(30, self._apply_initial_step_nav_layout)

    def _bind_unit_input_save_signals(self) -> None:
        for unit_num, input_widget in self.advanced_widgets.unit_inputs.items():
            if getattr(input_widget, "_save_signal_bound", False):
                continue
            if hasattr(input_widget, "lineEdit") and input_widget.lineEdit() is not None:
                input_widget.lineEdit().returnPressed.connect(lambda unit_num=unit_num: self.save_unit_name(unit_num))
                input_widget.activated.connect(lambda _idx, unit_num=unit_num: self.save_unit_name(unit_num))
            elif hasattr(input_widget, "returnPressed"):
                input_widget.returnPressed.connect(lambda unit_num=unit_num: self.save_unit_name(unit_num))
            input_widget._save_signal_bound = True

    def _ensure_advanced_editor_runtime_ui_initialized(self) -> None:
        if not self._searchable_unit_inputs_initialized:
            self._init_searchable_unit_inputs()
            self._searchable_unit_inputs_initialized = True
            self._bind_unit_input_save_signals()
            self._style_units_section()
        if self._abilities_tab_initialized:
            self._style_abilities_section()
            return
        self._init_abilities_tab()
        self._abilities_tab_initialized = True
        self._style_abilities_section()

    def _configure_bottom_layout(self) -> None:
        self.window.tabContentBackground.setGeometry(0, 628, 1090, 242)

        self.window.runStopBackground.setGeometry(1090, 630, 380, 204)
        self.window.advRunMacroButton.setGeometry(1098, 639, 176, 34)
        self.window.advStopMacroButton.setGeometry(1282, 639, 180, 34)
        self.window.advLogTextArea.setGeometry(1098, 679, 364, 151)
        self.window.reservedBottomRight.hide()
        if not hasattr(self.window, "maxUpgradeCheckBox"):
            self.window.maxUpgradeCheckBox = self._create_checkbox("Max Upgrade", self.window.upgradeGroup, 196, 92, 112, 18)
            self.window.maxUpgradeCheckBox.setObjectName("maxUpgradeCheckBox")

    def _style_macro_console_panel(self) -> None:
        if not hasattr(self, "_macro_console_panel"):
            self._macro_console_panel = QFrame(self.window.advancedCreatePage)
            self._macro_console_panel.setObjectName("macroConsolePanel")
            self._macro_console_panel.show()

            self._macro_console_header = QFrame(self._macro_console_panel)
            self._macro_console_header.setObjectName("macroConsoleHeader")
            self._macro_console_header.show()

            old_log_widget = self.window.advLogTextArea
            parent = old_log_widget.parent()
            geometry = old_log_widget.geometry()
            old_log_widget.hide()
            old_log_widget.deleteLater()

            log_widget = QTextEdit(parent)
            log_widget.setObjectName("advLogTextArea")
            log_widget.setReadOnly(True)
            log_widget.setGeometry(geometry)
            log_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            log_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            log_widget.setUndoRedoEnabled(False)
            log_widget.setAcceptRichText(True)
            log_widget.document().setDocumentMargin(0)
            self.window.advLogTextArea = log_widget

        self.window.runStopBackground.hide()
        self._macro_console_panel.setGeometry(1092, 630, 370, 230)
        self._macro_console_panel.setStyleSheet(
            "QFrame#macroConsolePanel {"
            "background-color: #0c0c0c;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 10px;"
            "}"
        )

        self._macro_console_header.setGeometry(0, 0, 370, 52)
        self._macro_console_header.setStyleSheet(
            "QFrame#macroConsoleHeader {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: none;"
            "border-bottom: 1px solid rgba(255, 255, 255, 0.08);"
            "border-top-left-radius: 10px;"
            "border-top-right-radius: 10px;"
            "}"
        )

        self.window.advRunMacroButton.setParent(self._macro_console_header)
        self.window.advStopMacroButton.setParent(self._macro_console_header)
        self.window.advLogTextArea.setParent(self._macro_console_panel)

        self.window.advRunMacroButton.setGeometry(8, 8, 173, 36)
        self.window.advRunMacroButton.setText(START_MACRO_BUTTON_TEXT)
        self.window.advRunMacroButton.setFocusPolicy(Qt.NoFocus)
        self.window.advRunMacroButton.setEnabled(not self.state.macro_is_running)
        self.window.advRunMacroButton.setStyleSheet(
            "QPushButton {"
            "background-color: #10b981;"
            "color: #000000;"
            "border: none;"
            "border-radius: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            "padding: 0px;"
            "}"
            "QPushButton:hover { background-color: #0ea472; }"
            "QPushButton:pressed { background-color: #0d9668; }"
            "QPushButton:disabled { background-color: rgba(16, 185, 129, 0.45); color: rgba(0, 0, 0, 0.70); }"
        )

        self.window.advStopMacroButton.setGeometry(189, 8, 173, 36)
        self.window.advStopMacroButton.setText(STOP_MACRO_BUTTON_TEXT)
        self.window.advStopMacroButton.setFocusPolicy(Qt.NoFocus)
        self.window.advStopMacroButton.setEnabled(self.state.macro_is_running)
        self.window.advStopMacroButton.setStyleSheet(
            "QPushButton {"
            "background-color: #ff2d3d;"
            "color: #ffffff;"
            "border: none;"
            "border-radius: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            "padding: 0px;"
            "}"
            "QPushButton:hover { background-color: #e32635; }"
            "QPushButton:pressed { background-color: #cf1f2c; }"
            "QPushButton:disabled { background-color: rgba(255, 45, 61, 0.35); color: rgba(255, 255, 255, 0.55); }"
        )

        self.window.advLogTextArea.setGeometry(8, 60, 354, 162)
        self.window.advLogTextArea.setStyleSheet(
            "QTextEdit {"
            "background-color: rgba(0, 0, 0, 0.40);"
            "color: #d1d5db;"
            "border: none;"
            "border-radius: 0px;"
            "padding: 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "}"
            "QScrollBar:vertical { background: transparent; width: 0px; margin: 0px; }"
            "QScrollBar::handle:vertical { background: transparent; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )

    @staticmethod
    def _render_adv_log_entry(timestamp: str, message: str) -> str:
        safe_timestamp = html.escape(timestamp)
        safe_message = html.escape(message)
        return (
            '<span style="font-family: \'Space Mono\', \'Menlo\', monospace; '
            'font-size: 9px; font-weight: 500; white-space: pre-wrap;">'
            f'<span style="color: rgba(255,255,255,0.40);">[{safe_timestamp}]</span>'
            '<span style="display:inline-block; width:8px;"></span>'
            f'<span style="color: rgba(52,211,153,0.80);">{safe_message}</span>'
            "</span>"
        )

    def _init_place_upgrade_scroll_area(self) -> None:
        self.window.placeUpgradeScrollArea = QScrollArea(self.window.advancedCreatePage)
        self.window.placeUpgradeScrollArea.setGeometry(202, 630, 870, 190)
        self.window.placeUpgradeScrollArea.setFrameShape(QFrame.NoFrame)
        self.window.placeUpgradeScrollArea.setWidgetResizable(True)
        self.window.placeUpgradeScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.window.placeUpgradeScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.window.placeUpgradeScrollArea.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }"
            "QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.10); border-radius: 4px; min-height: 24px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        self.window.placeUpgradeScrollArea.hide()

        self.window.placeUpgradeScrollContent = QWidget()
        self.window.placeUpgradeScrollContent.resize(870, 334)
        self.window.placeUpgradeScrollContent.setMinimumSize(870, 334)
        self.window.placeUpgradeScrollContent.setStyleSheet("background-color: transparent;")
        self.window.placeUpgradeScrollArea.setWidget(self.window.placeUpgradeScrollContent)

        self.window.upgradeGroup.setParent(self.window.placeUpgradeScrollContent)
        self.window.upgradeGroup.setGeometry(0, 0, 423, 190)
        self.window.upgradeGroup.show()
        self.window.placeGroup.setParent(self.window.placeUpgradeScrollContent)
        self.window.placeGroup.setGeometry(447, 0, 423, 190)
        self.window.placeGroup.show()
        self.window.addUpgradeStepButton = self._replace_primary_step_button(
            self.window.addUpgradeStepButton,
            self.window.upgradeGroup,
            font_size=10,
            letter_spacing=0,
        )
        self.window.addPlaceStepButton = self._replace_primary_step_button(
            self.window.addPlaceStepButton,
            self.window.placeGroup,
            font_size=10,
            letter_spacing=0,
        )

    def _init_other_group(self) -> None:
        self.window.otherGroup = QGroupBox(self.window.placeUpgradeScrollContent)
        self.window.otherGroup.setObjectName("otherGroup")
        self.window.otherGroup.setGeometry(0, 202, 870, 132)
        self.window.otherGroup.setTitle("")
        self.window.otherGroup.setStyleSheet("QGroupBox { background: transparent; border: none; }")

        card_style = (
            "QFrame {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 8px;"
            "}"
        )
        title_style = (
            "background: transparent; color: #ffffff; border: none;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 12px; font-weight: 600;"
        )
        label_style = (
            "background: transparent; color: rgba(255, 255, 255, 0.50); border: none;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px; font-weight: 500;"
        )
        combo_style = (
            "QComboBox {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 6px;"
            "padding: 0px 24px 0px 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QComboBox:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
            "QComboBox::drop-down {"
            "subcontrol-origin: padding;"
            "subcontrol-position: top right;"
            "width: 20px;"
            "border: none;"
            "background: transparent;"
            "}"
            "QComboBox QAbstractItemView {"
            "background-color: #161616;"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "selection-background-color: rgba(255, 255, 255, 0.10);"
            "selection-color: #ffffff;"
            "padding: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "outline: none;"
            "}"
        )
        button_style = (
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 0.08);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "padding: 0px 8px;"
            "}"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); }"
            "QPushButton:pressed { background-color: rgba(255, 255, 255, 0.16); }"
        )

        self.window._otherSellCard = QFrame(self.window.otherGroup)
        self.window._otherSellCard.setGeometry(0, 0, 200, 122)
        self.window._otherSellCard.setStyleSheet(card_style)

        self.window._otherPriorityCard = QFrame(self.window.otherGroup)
        self.window._otherPriorityCard.setGeometry(212, 0, 256, 122)
        self.window._otherPriorityCard.setStyleSheet(card_style)

        sell_title = QLabel("Sell Unit", self.window._otherSellCard)
        sell_title.setGeometry(12, 12, 120, 18)
        sell_title.setStyleSheet(title_style)

        sell_label = QLabel("Unit", self.window._otherSellCard)
        sell_label.setGeometry(12, 48, 40, 16)
        sell_label.setStyleSheet(label_style)

        self.window.otherSellUnitCombo = QComboBox(self.window._otherSellCard)
        self.window.otherSellUnitCombo.setGeometry(60, 42, 128, 28)
        self.window.otherSellUnitCombo.setFocusPolicy(Qt.NoFocus)
        self.window.otherSellUnitCombo.setMaxVisibleItems(8)
        self.window.otherSellUnitCombo.setStyleSheet(combo_style)
        self._configure_searchable_slot_combo(self.window.otherSellUnitCombo, "Select Unit")

        self.window.otherSellAddButton = QPushButton("+  Add Sell Step", self.window._otherSellCard)
        self.window.otherSellAddButton.setGeometry(12, 82, 176, 28)
        self.window.otherSellAddButton.setFocusPolicy(Qt.NoFocus)
        self.window.otherSellAddButton.setStyleSheet(button_style)

        priority_title = QLabel("Priority", self.window._otherPriorityCard)
        priority_title.setGeometry(12, 12, 120, 18)
        priority_title.setStyleSheet(title_style)

        priority_label = QLabel("Unit", self.window._otherPriorityCard)
        priority_label.setGeometry(12, 48, 40, 16)
        priority_label.setStyleSheet(label_style)

        self.window.otherPriorityUnitCombo = QComboBox(self.window._otherPriorityCard)
        self.window.otherPriorityUnitCombo.setGeometry(60, 42, 112, 28)
        self.window.otherPriorityUnitCombo.setFocusPolicy(Qt.NoFocus)
        self.window.otherPriorityUnitCombo.setMaxVisibleItems(8)
        self.window.otherPriorityUnitCombo.setStyleSheet(combo_style)
        self._configure_searchable_slot_combo(self.window.otherPriorityUnitCombo, "Select Unit")

        self.window.otherPriorityChoiceCombo = QComboBox(self.window._otherPriorityCard)
        self.window.otherPriorityChoiceCombo.setGeometry(180, 42, 64, 28)
        self.window.otherPriorityChoiceCombo.setFocusPolicy(Qt.NoFocus)
        self.window.otherPriorityChoiceCombo.setMaxVisibleItems(8)
        self.window.otherPriorityChoiceCombo.setStyleSheet(combo_style)
        self.window.otherPriorityChoiceCombo.addItems(TARGET_PRIORITY_OPTIONS)

        self.window.otherPriorityAddButton = QPushButton("+  Add Priority Step", self.window._otherPriorityCard)
        self.window.otherPriorityAddButton.setGeometry(12, 82, 232, 28)
        self.window.otherPriorityAddButton.setFocusPolicy(Qt.NoFocus)
        self.window.otherPriorityAddButton.setStyleSheet(button_style)

    def _init_abilities_tab_shell(self) -> None:
        self.window.tabAbilitiesButton = QPushButton("ABILITIES", self.window.advancedCreatePage)
        self.window.tabAbilitiesButton.setGeometry(708, 640, 160, 38)

        self.window.advancedAbilitiesGroup = QGroupBox(self.window.advancedCreatePage)
        self.window.advancedAbilitiesGroup.setObjectName("advancedAbilitiesGroup")
        self.window.advancedAbilitiesGroup.setGeometry(10, 668, 1070, 192)
        self.window.advancedAbilitiesGroup.setTitle("")
        self.window.advancedAbilitiesGroup.setVisible(False)
        self.window.advancedAbilitiesGroup.setStyleSheet(
            "background-color: transparent; border: none;"
        )

    def _apply_advanced_create_step_redesign(self) -> None:
        self.window.tabContentBackground.hide()
        self._layout_advanced_tab_header()
        self._style_advanced_tab_header()
        self._style_units_section()
        self._style_place_upgrade_section()
        self._style_wait_section()
        self._style_raw_steps_section()
        if self._abilities_tab_initialized:
            self._style_abilities_section()
        self._apply_initial_step_nav_layout()
        QTimer.singleShot(0, self._apply_initial_step_nav_layout)

    def _layout_advanced_tab_header(self) -> None:
        if not hasattr(self, "_step_nav_frame"):
            self._step_nav_hovered = False
            self._step_nav_frame = _HoverExpandFrame(self._set_step_nav_hovered, self.window.advancedCreatePage)
            self._step_nav_frame.setGeometry(18, 640, 30, 190)
            self._step_nav_frame.setObjectName("advancedStepNavFrame")
            self._step_nav_frame.show()

            self._step_nav_divider = QFrame(self._step_nav_frame)
            self._step_nav_divider.setFrameShape(QFrame.HLine)
            self._step_nav_divider.setFrameShadow(QFrame.Plain)
            self._step_nav_divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); color: rgba(255, 255, 255, 0.08); border: none;")

            self._step_nav_animation = QPropertyAnimation(self._step_nav_frame, b"geometry")
            self._step_nav_animation.setDuration(300)
            self._step_nav_animation.setEasingCurve(QEasingCurve.OutCubic)
            self._step_nav_animation.valueChanged.connect(self._on_step_nav_animation_frame)

            self._step_content_animation = QPropertyAnimation(self.window.placeUpgradeScrollArea, b"geometry")
            self._step_content_animation.setDuration(300)
            self._step_content_animation.setEasingCurve(QEasingCurve.OutCubic)

            self._step_wait_animation = QPropertyAnimation(self.window.advancedWaitGroup, b"geometry")
            self._step_wait_animation.setDuration(300)
            self._step_wait_animation.setEasingCurve(QEasingCurve.OutCubic)
            self._step_wait_animation.valueChanged.connect(lambda _value: self._layout_wait_section_content())

            self._step_units_animation = QPropertyAnimation(self.window.unitSelectionGroup, b"geometry")
            self._step_units_animation.setDuration(300)
            self._step_units_animation.setEasingCurve(QEasingCurve.OutCubic)

            self._step_raw_click_animation = QPropertyAnimation(self.window.advancedClickGroup, b"geometry")
            self._step_raw_click_animation.setDuration(300)
            self._step_raw_click_animation.setEasingCurve(QEasingCurve.OutCubic)

            self._step_raw_key_animation = QPropertyAnimation(self.window.advancedKeyGroup, b"geometry")
            self._step_raw_key_animation.setDuration(300)
            self._step_raw_key_animation.setEasingCurve(QEasingCurve.OutCubic)

            self._step_abilities_animation = QPropertyAnimation(self.window.advancedAbilitiesGroup, b"geometry")
            self._step_abilities_animation.setDuration(300)
            self._step_abilities_animation.setEasingCurve(QEasingCurve.OutCubic)

            self._step_nav_hover_timer = QTimer(self.window)
            self._step_nav_hover_timer.setInterval(80)
            self._step_nav_hover_timer.timeout.connect(self._sync_step_nav_hover_state)

            self._step_nav_buttons = [
                (self.window.tabUnitsButton, "units", "UNITS", "user"),
                (self.window.tabPlaceUpgradeButton, "place_upgrade", "PLACE / UPGRADE", "cube"),
                (self.window.tabWaitButton, "wait", "WAIT", "clock"),
                (self.window.tabRawStepsButton, "raw", "RAW STEPS", "list"),
                (self.window.tabAbilitiesButton, "abilities", "ABILITIES", "bolt"),
            ]

            for button, _tab, _label, _icon_name in self._step_nav_buttons:
                button.setParent(self._step_nav_frame)
                button.show()
                button.raise_()

            self.window.tabSettingsButton.setParent(self._step_nav_frame)
            self.window.tabSettingsButton.show()
            self.window.tabSettingsButton.raise_()
        else:
            self._step_nav_frame.setGeometry(18, 640, self._step_nav_frame.width(), 190)

        self._step_nav_frame.setStyleSheet(
            "QFrame#advancedStepNavFrame {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "}"
        )
        if hasattr(self, "_step_nav_divider"):
            self._step_nav_divider.show()
        self._layout_step_nav_buttons()

    def _layout_step_nav_buttons(self) -> None:
        if not hasattr(self, "_step_nav_frame"):
            return
        nav_width = self._step_nav_frame.width()
        expanded = nav_width > 60
        button_y = 6
        for button, _tab, label, _icon_name in self._step_nav_buttons:
            button.setMinimumHeight(28)
            button.setMaximumHeight(28)
            button.setGeometry(0, button_y, nav_width, 28)
            button.setText(label if expanded else "")
            button_y += 30
        self._step_nav_divider.setGeometry(0, 161, nav_width, 1)
        self.window.tabSettingsButton.setMinimumHeight(28)
        self.window.tabSettingsButton.setMaximumHeight(28)
        self.window.tabSettingsButton.setGeometry(0, 162, nav_width, 28)
        self.window.tabSettingsButton.setText("SETTINGS" if expanded else "")

    def _on_step_nav_animation_frame(self, _value) -> None:
        self._layout_step_nav_buttons()
        self._style_advanced_tab_header()

    def _place_upgrade_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 190 if expanded else 60
        return QRect(x, 640, 870, 190)

    def _units_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 190 if expanded else 60
        return QRect(x, 640, 804, 194)

    def _wait_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 190 if expanded else 60
        width = 540
        return QRect(x, 640, width, 190)

    def _raw_click_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 190 if expanded else 60
        return QRect(x, 640, 390, 190)

    def _raw_key_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 604 if expanded else 474
        return QRect(x, 640, 390, 190)

    def _abilities_geometry_for_nav(self, expanded: bool) -> QRect:
        x = 190 if expanded else 60
        return QRect(x, 640, 914, 208)

    def _set_step_nav_hovered(self, hovered: bool) -> None:
        if not hasattr(self, "_step_nav_frame"):
            return
        self._step_nav_hovered = hovered
        start_rect = self._step_nav_frame.geometry()
        target_rect = QRect(start_rect.x(), start_rect.y(), 160 if hovered else 30, start_rect.height())
        if start_rect != target_rect:
            self._step_nav_animation.stop()
            self._step_nav_animation.setStartValue(start_rect)
            self._step_nav_animation.setEndValue(target_rect)
            self._step_nav_animation.start()
        target_content_rect = self._place_upgrade_geometry_for_nav(hovered)
        current_content_rect = self.window.placeUpgradeScrollArea.geometry()
        if current_content_rect != target_content_rect:
            self._step_content_animation.stop()
            self._step_content_animation.setStartValue(current_content_rect)
            self._step_content_animation.setEndValue(target_content_rect)
            self._step_content_animation.start()
        target_wait_rect = self._wait_geometry_for_nav(hovered)
        current_wait_rect = self.window.advancedWaitGroup.geometry()
        if current_wait_rect != target_wait_rect:
            self._step_wait_animation.stop()
            self._step_wait_animation.setStartValue(current_wait_rect)
            self._step_wait_animation.setEndValue(target_wait_rect)
            self._step_wait_animation.start()
        target_units_rect = self._units_geometry_for_nav(hovered)
        current_units_rect = self.window.unitSelectionGroup.geometry()
        if current_units_rect != target_units_rect:
            self._step_units_animation.stop()
            self._step_units_animation.setStartValue(current_units_rect)
            self._step_units_animation.setEndValue(target_units_rect)
            self._step_units_animation.start()
        target_raw_click_rect = self._raw_click_geometry_for_nav(hovered)
        current_raw_click_rect = self.window.advancedClickGroup.geometry()
        if current_raw_click_rect != target_raw_click_rect:
            self._step_raw_click_animation.stop()
            self._step_raw_click_animation.setStartValue(current_raw_click_rect)
            self._step_raw_click_animation.setEndValue(target_raw_click_rect)
            self._step_raw_click_animation.start()
        target_raw_key_rect = self._raw_key_geometry_for_nav(hovered)
        current_raw_key_rect = self.window.advancedKeyGroup.geometry()
        if current_raw_key_rect != target_raw_key_rect:
            self._step_raw_key_animation.stop()
            self._step_raw_key_animation.setStartValue(current_raw_key_rect)
            self._step_raw_key_animation.setEndValue(target_raw_key_rect)
            self._step_raw_key_animation.start()
        target_abilities_rect = self._abilities_geometry_for_nav(hovered)
        current_abilities_rect = self.window.advancedAbilitiesGroup.geometry()
        if current_abilities_rect != target_abilities_rect:
            self._step_abilities_animation.stop()
            self._step_abilities_animation.setStartValue(current_abilities_rect)
            self._step_abilities_animation.setEndValue(target_abilities_rect)
            self._step_abilities_animation.start()
        self._layout_step_nav_buttons()
        self._style_advanced_tab_header()

    def _sync_step_nav_layout_state(self) -> None:
        if not hasattr(self, "_step_nav_frame"):
            return
        global_pos = QCursor.pos()
        local_pos = self._step_nav_frame.mapFromGlobal(global_pos)
        hovered = self._step_nav_frame.rect().contains(local_pos)
        self._step_nav_hovered = hovered
        self._step_nav_frame.setGeometry(18, 640, 160 if hovered else 30, 190)
        self.window.placeUpgradeScrollArea.setGeometry(self._place_upgrade_geometry_for_nav(hovered))
        self.window.advancedWaitGroup.setGeometry(self._wait_geometry_for_nav(hovered))
        self.window.unitSelectionGroup.setGeometry(self._units_geometry_for_nav(hovered))
        self.window.advancedClickGroup.setGeometry(self._raw_click_geometry_for_nav(hovered))
        self.window.advancedKeyGroup.setGeometry(self._raw_key_geometry_for_nav(hovered))
        self.window.advancedAbilitiesGroup.setGeometry(self._abilities_geometry_for_nav(hovered))
        self._layout_step_nav_buttons()
        self._style_advanced_tab_header()
        self._layout_wait_section_content()

    def _apply_initial_step_nav_layout(self) -> None:
        if not hasattr(self, "_step_nav_frame"):
            return
        self._step_nav_hovered = False
        for animation_name in (
            "_step_nav_animation",
            "_step_content_animation",
            "_step_wait_animation",
            "_step_units_animation",
            "_step_raw_click_animation",
            "_step_raw_key_animation",
            "_step_abilities_animation",
        ):
            animation = getattr(self, animation_name, None)
            if animation is not None:
                animation.stop()
        self._step_nav_frame.setGeometry(18, 640, 30, 190)
        self.window.placeUpgradeScrollArea.setGeometry(self._place_upgrade_geometry_for_nav(False))
        self.window.advancedWaitGroup.setGeometry(self._wait_geometry_for_nav(False))
        self.window.unitSelectionGroup.setGeometry(self._units_geometry_for_nav(False))
        self.window.advancedClickGroup.setGeometry(self._raw_click_geometry_for_nav(False))
        self.window.advancedKeyGroup.setGeometry(self._raw_key_geometry_for_nav(False))
        self.window.advancedAbilitiesGroup.setGeometry(self._abilities_geometry_for_nav(False))
        self._layout_step_nav_buttons()
        self._style_advanced_tab_header()
        self._layout_wait_section_content()

    def _sync_step_nav_hover_state(self) -> None:
        if not hasattr(self, "_step_nav_frame"):
            return
        global_pos = QCursor.pos()
        local_pos = self._step_nav_frame.mapFromGlobal(global_pos)
        inside = self._step_nav_frame.rect().contains(local_pos)
        if inside != getattr(self, "_step_nav_hovered", False):
            self._set_step_nav_hovered(inside)

    def _tab_button_stylesheet(self, *, active: bool) -> str:
        expanded = hasattr(self, "_step_nav_frame") and self._step_nav_frame.width() > 60
        padding = "padding: 0px 8px 0px 8px;" if expanded else "padding: 0px;"
        alignment = "text-align: left;" if expanded else "text-align: center;"
        if active:
            return (
                "QPushButton {"
                "background-color: rgba(255, 255, 255, 0.08);"
                "color: #ffffff;"
                "border: none;"
                "border-radius: 0px;"
                "font-family: 'Space Mono', 'Menlo', monospace;"
                "font-size: 9px;"
                "font-weight: 600;"
                "letter-spacing: 1px;"
                f"{padding}"
                f"{alignment}"
                "}"
            )
        return (
            "QPushButton {"
            "background-color: transparent;"
            "color: rgba(255, 255, 255, 0.30);"
            "border: none;"
            "border-radius: 0px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            f"{padding}"
            f"{alignment}"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 0.03);"
            "color: rgba(255, 255, 255, 0.50);"
            "}"
        )

    def _style_advanced_tab_header(self) -> None:
        expanded = hasattr(self, "_step_nav_frame") and self._step_nav_frame.width() > 60
        tab_button_map = {
            "units": self.window.tabUnitsButton,
            "place_upgrade": self.window.tabPlaceUpgradeButton,
            "wait": self.window.tabWaitButton,
            "raw": self.window.tabRawStepsButton,
            "abilities": self.window.tabAbilitiesButton,
        }
        icon_lookup = {
            "units": "user",
            "place_upgrade": "cube",
            "wait": "clock",
            "raw": "list",
            "abilities": "bolt",
        }
        for button_tab, button in tab_button_map.items():
            active = button_tab == self.state.editor.current_tab
            button.setStyleSheet(self._tab_button_stylesheet(active=active))
            button.setIcon(_step_nav_icon(icon_lookup[button_tab], "#ffffff" if active else "rgba(255, 255, 255, 0.30)", 14))
            button.setIconSize(QSize(14, 14))
            button.setFocusPolicy(Qt.NoFocus)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

        self.window.tabSettingsButton.setFocusPolicy(Qt.NoFocus)
        self.window.tabSettingsButton.setIcon(_step_nav_icon("gear", "rgba(255, 255, 255, 0.30)", 14))
        self.window.tabSettingsButton.setIconSize(QSize(14, 14))
        settings_padding = "padding: 0px 8px 0px 8px;" if expanded else "padding: 0px;"
        settings_alignment = "text-align: left;" if expanded else "text-align: center;"
        self.window.tabSettingsButton.setStyleSheet(
            "QPushButton {"
            "background-color: transparent;"
            "color: rgba(255, 255, 255, 0.30);"
            "border: none;"
            "border-radius: 0px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            f"{settings_padding}"
            f"{settings_alignment}"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 0.03);"
            "color: rgba(255, 255, 255, 0.50);"
            "}"
        )
        self.window.tabSettingsButton.style().unpolish(self.window.tabSettingsButton)
        self.window.tabSettingsButton.style().polish(self.window.tabSettingsButton)
        self.window.tabSettingsButton.update()

    def _card_shell_stylesheet(self) -> str:
        return (
            "QGroupBox {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "}"
            "QLabel {"
            "background-color: transparent;"
            "border: none;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "}"
            "QComboBox, QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QComboBox:hover, QLineEdit:hover {"
            "background-color: rgba(255, 255, 255, 0.06);"
            "}"
            "QComboBox:focus, QLineEdit:focus {"
            "border: 1px solid rgba(255, 255, 255, 0.20);"
            "}"
            "QComboBox::drop-down {"
            "border: none;"
            "width: 24px;"
            "background: transparent;"
            "}"
            "QComboBox QAbstractItemView {"
            "background-color: #1a1a1a;"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "selection-background-color: rgba(255, 255, 255, 0.08);"
            "selection-color: #ffffff;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 12px;"
            "}"
            "QCheckBox {"
            "color: rgba(255, 255, 255, 0.60);"
            "background: transparent;"
            "spacing: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QCheckBox:hover {"
            "color: rgba(255, 255, 255, 0.80);"
            "}"
            "QCheckBox::indicator {"
            "width: 14px;"
            "height: 14px;"
            "border-radius: 4px;"
            "border: 1px solid rgba(255, 255, 255, 0.12);"
            "background: transparent;"
            "}"
            "QCheckBox::indicator:unchecked:hover {"
            "border: 1px solid rgba(255, 255, 255, 0.25);"
            "}"
            "QCheckBox::indicator:checked {"
            "background: #ffffff;"
            "border: 1px solid #ffffff;"
            "}"
        )

    def _style_place_upgrade_section(self) -> None:
        self.window.upgradeGroup.setStyleSheet(self._card_shell_stylesheet())
        self.window.placeGroup.setStyleSheet(self._card_shell_stylesheet())
        self.window.placeUpgradeScrollArea.setGeometry(self._place_upgrade_geometry_for_nav(False))

        self.window.upgradeGroup.setGeometry(0, 0, 423, 190)
        self.window.placeGroup.setGeometry(447, 0, 423, 190)
        self.window.otherGroup.setGeometry(0, 202, 870, 132)

        self.window.upgradeHeaderLabel.setGeometry(24, 18, 260, 18)
        self.window.upgradeHeaderLabel.setText("Unit Upgrade")
        self.window.upgradeHeaderLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.window.upgradeHeaderLabel.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding-left: 0px; padding-right: 0px; "
            "padding-top: 0px; padding-bottom: 0px; margin: 0px; border-bottom: none;"
        )
        self.window.upgradeHeaderLabel.setIndent(0)
        self.window.upgradeHeaderLabel.setMargin(0)
        self.window.upgradeHeaderLabel.setContentsMargins(0, 0, 0, 0)
        self.window.upgradeUnitLabel.setGeometry(24, 58, 56, 16)
        self.window.upgradeUnitLabel.setText("Unit")
        self.window.upgradeUnitLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.upgradeUnitCombo.setGeometry(102, 48, 170, 28)
        self._configure_searchable_slot_combo(self.window.upgradeUnitCombo, "Select Unit")
        self.window.upgradePlacementLabel.setGeometry(284, 57, 10, 14)
        self.window.upgradePlacementLabel.setText("#")
        self.window.upgradePlacementLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.upgradePlacementCombo.setGeometry(302, 48, 64, 28)
        self.window.upgradeCountLabel.setGeometry(24, 96, 56, 16)
        self.window.upgradeCountLabel.setText("Count")
        self.window.upgradeCountLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.upgradeCountInput.setGeometry(102, 86, 170, 28)
        self.window.upgradeCountInput.setPlaceholderText("1")

        self.window.autoUpgradeCheckBox.setGeometry(102, 124, 124, 18)
        self.window.autoUpgradeCheckBox.setText("Auto upgrade")
        if hasattr(self.window, "maxUpgradeCheckBox"):
            self.window.maxUpgradeCheckBox.setGeometry(238, 124, 124, 18)
            self.window.maxUpgradeCheckBox.setText("Max upgrade")
        self.window.upgradeNoPlacementsLabel.setGeometry(280, 90, 110, 16)
        self.window.upgradeNoPlacementsLabel.setStyleSheet(
            "background: transparent; border: none; color: #f87171; font-family: 'Space Mono', 'Menlo', monospace; font-size: 10px; font-weight: 500;"
        )
        options_label = getattr(self.window, "_upgradeOptionsLabel", None)
        if options_label is None:
            options_label = QLabel("Options", self.window.upgradeGroup)
            self.window._upgradeOptionsLabel = options_label
        options_label.setGeometry(24, 124, 56, 16)
        options_label.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        options_label.show()

        self.window.addUpgradeStepButton.setGeometry(24, 156, 342, 28)
        self.window.addUpgradeStepButton.setText("+  Add Upgrade Step")
        self.window.addUpgradeStepButton.setFocusPolicy(Qt.NoFocus)

        self.window.placeHeaderLabel.setGeometry(24, 18, 260, 18)
        self.window.placeHeaderLabel.setText("Unit Place")
        self.window.placeHeaderLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.window.placeHeaderLabel.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding-left: 0px; padding-right: 0px; "
            "padding-top: 0px; padding-bottom: 0px; margin: 0px; border-bottom: none;"
        )
        self.window.placeHeaderLabel.setIndent(0)
        self.window.placeHeaderLabel.setMargin(0)
        self.window.placeHeaderLabel.setContentsMargins(0, 0, 0, 0)
        self.window.placeUnitLabel.setGeometry(24, 58, 56, 16)
        self.window.placeUnitLabel.setText("Unit")
        self.window.placeUnitLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.placeUnitCombo.setGeometry(102, 48, 170, 28)
        self._configure_searchable_slot_combo(self.window.placeUnitCombo, "Select Unit")
        self.window.placementColHeaderLabel.setGeometry(284, 57, 10, 14)
        self.window.placementColHeaderLabel.setText("#")
        self.window.placementColHeaderLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.placementCounterLabel.setGeometry(302, 48, 48, 28)
        self.window.placementCounterLabel.setStyleSheet(
            "QLabel {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "padding: 0 6px;"
            "}"
        )
        self.window.placementCounterLabel.setAlignment(Qt.AlignCenter)
        self.window.placeXLabel.setGeometry(24, 96, 56, 16)
        self.window.placeXLabel.setText("Position")
        self.window.placeXLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        self.window.placeYLabel.hide()
        self.window.placeXInput.setGeometry(102, 86, 64, 28)
        self.window.placeYInput.setGeometry(182, 86, 64, 28)
        self.window.placeXInput.setPlaceholderText("X")
        self.window.placeYInput.setPlaceholderText("Y")

        place_options_label = getattr(self.window, "_placeOptionsLabel", None)
        if place_options_label is None:
            place_options_label = QLabel("Options", self.window.placeGroup)
            self.window._placeOptionsLabel = place_options_label
        place_options_label.setGeometry(24, 124, 56, 16)
        place_options_label.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 500;"
        )
        place_options_label.show()

        self.window.placeUntilEmptyCheckbox.setGeometry(102, 124, 124, 18)
        self.window.placeUntilEmptyCheckbox.setText("Until empty")

        self.window.recordPlaceClickButton.setGeometry(256, 120, 110, 28)
        self.window.recordPlaceClickButton.setText(RECORD_PLACE_CLICK_TEXT)
        self.window.recordPlaceClickButton.setFocusPolicy(Qt.NoFocus)
        self.window.recordPlaceClickButton.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: rgba(255, 255, 255, 0.60);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "padding: 0 8px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 0.08);"
            "color: #ffffff;"
            "}"
            "QPushButton:disabled {"
            "color: rgba(255, 255, 255, 0.35);"
            "}"
        )

        self.window.addPlaceStepButton.setGeometry(24, 156, 342, 28)
        self.window.addPlaceStepButton.setText("+  Add Place Step")
        self.window.addPlaceStepButton.setFocusPolicy(Qt.NoFocus)

    def _style_units_section(self) -> None:
        self.window.unitSelectionGroup.setGeometry(self._units_geometry_for_nav(False))
        self.window.unitSelectionGroup.setTitle("")
        self.window.unitSelectionGroup.setStyleSheet(
            "QGroupBox {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "}"
        )

        self.window.unitSelectionHeaderLabel.hide()
        units_title = getattr(self.window, "_unitsCardTitleLabel", None)
        if units_title is None:
            units_title = QLabel("Units", self.window.unitSelectionGroup)
            self.window._unitsCardTitleLabel = units_title
        units_title.setGeometry(12, 12, 180, 18)
        units_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        units_title.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding: 0px; margin: 0px;"
        )
        units_title.show()
        units_title.raise_()

        card_positions = {
            1: QRect(12, 42, 252, 58),
            2: QRect(272, 42, 252, 58),
            3: QRect(532, 42, 252, 58),
            4: QRect(12, 108, 252, 58),
            5: QRect(272, 108, 252, 58),
            6: QRect(532, 108, 252, 58),
        }
        header_names = {
            1: self.window.unit1HeaderLabel,
            2: self.window.unit2HeaderLabel,
            3: self.window.unit3HeaderLabel,
            4: self.window.unit4HeaderLabel,
            5: self.window.unit5HeaderLabel,
            6: self.window.unit6HeaderLabel,
        }
        coords_labels = {
            1: self.window.unit1CoordsLabel,
            2: self.window.unit2CoordsLabel,
            3: self.window.unit3CoordsLabel,
            4: self.window.unit4CoordsLabel,
            5: self.window.unit5CoordsLabel,
            6: self.window.unit6CoordsLabel,
        }
        group_map = {
            1: self.window.unit1Group,
            2: self.window.unit2Group,
            3: self.window.unit3Group,
            4: self.window.unit4Group,
            5: self.window.unit5Group,
            6: self.window.unit6Group,
        }

        if not hasattr(self.window, "_unit_status_dots"):
            self.window._unit_status_dots = {}

        combo_style = (
            "QComboBox {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QComboBox:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
            "QComboBox::drop-down { border: none; width: 22px; background: transparent; }"
            "QComboBox QAbstractItemView {"
            "background-color: #1a1a1a;"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "selection-background-color: rgba(255, 255, 255, 0.08);"
            "selection-color: #ffffff;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "}"
        )

        for slot in range(1, 7):
            group = group_map[slot]
            group.setGeometry(card_positions[slot])
            group.setTitle("")
            group.setStyleSheet(
                "QGroupBox {"
                "background-color: rgba(255, 255, 255, 0.02);"
                "border: none;"
                "border-radius: 4px;"
                "}"
            )
            group.show()

            header = header_names[slot]
            header.setGeometry(8, 6, 80, 14)
            header.setText(f"UNIT {slot}")
            header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            header.setStyleSheet(
                "background: transparent; border: none; color: rgba(255, 255, 255, 0.40); font-family: 'Space Mono', 'Menlo', monospace; "
                "font-size: 9px; font-weight: 600; letter-spacing: 1px; padding: 0px; margin: 0px;"
            )

            coords_labels[slot].hide()

            input_widget = self.advanced_widgets.unit_inputs[slot]
            input_widget.setParent(group)
            input_widget.setGeometry(8, 24, 192, 28)
            input_widget.setStyleSheet(combo_style)
            input_widget.show()

            saved_label = self.advanced_widgets.unit_saved_labels[slot]
            saved_label.setParent(group)
            saved_label.setGeometry(164, 7, 80, 14)
            saved_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            saved_label.setStyleSheet(
                "background: transparent; border: none; color: #4ade80; font-family: 'Space Mono', 'Menlo', monospace; "
                "font-size: 8px; font-weight: 600; padding: 0px; margin: 0px;"
            )
            saved_label.show()

            dot = self.window._unit_status_dots.get(slot)
            if dot is None:
                dot = QLabel(group)
                self.window._unit_status_dots[slot] = dot
            dot.setGeometry(152, 11, 6, 6)
            dot.setStyleSheet("background-color: #4ade80; border: none; border-radius: 3px;")
            dot.show()

        self._sync_all_unit_saved_displays()

    def _secondary_button_stylesheet(self) -> str:
        return (
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: rgba(255, 255, 255, 0.60);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "padding: 0 8px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 0.08);"
            "color: #ffffff;"
            "}"
        )

    @staticmethod
    def _style_compact_ability_button(button: QPushButton, *, font_size: int) -> None:
        button.setStyleSheet(
            "QPushButton { "
            "background-color: rgba(255, 255, 255, 0.08); "
            "color: #ffffff; "
            "border: 1px solid rgba(255, 255, 255, 0.08); "
            "border-radius: 4px; "
            "font-family: 'Space Mono', 'Menlo', monospace; "
            f"font-size: {font_size}px; "
            "font-weight: 500; "
            "padding: 1px 0px 0px 0px; "
            "} "
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); } "
            "QPushButton:pressed { background-color: rgba(255, 255, 255, 0.16); }"
        )

    def _style_raw_steps_section(self) -> None:
        self.window.advancedClickGroup.setGeometry(self._raw_click_geometry_for_nav(False))
        self.window.advancedKeyGroup.setGeometry(self._raw_key_geometry_for_nav(False))
        for group in (self.window.advancedClickGroup, self.window.advancedKeyGroup):
            group.setTitle("")
            group.setStyleSheet(self._card_shell_stylesheet())

        self.window.clickHeaderLabel.hide()
        self.window.keyHeaderLabel.hide()

        click_title = getattr(self.window, "_clickCardTitleLabel", None)
        if click_title is None:
            click_title = QLabel("Click", self.window.advancedClickGroup)
            self.window._clickCardTitleLabel = click_title
        click_title.setGeometry(24, 18, 180, 18)
        click_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        click_title.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding: 0px; margin: 0px;"
        )
        click_title.show()

        key_title = getattr(self.window, "_keyCardTitleLabel", None)
        if key_title is None:
            key_title = QLabel("Key Press", self.window.advancedKeyGroup)
            self.window._keyCardTitleLabel = key_title
        key_title.setGeometry(24, 18, 180, 18)
        key_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        key_title.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding: 0px; margin: 0px;"
        )
        key_title.show()

        field_label_style = (
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        input_style = (
            "QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QLineEdit:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
        )

        self.window.advClickXLabel.setGeometry(24, 58, 12, 16)
        self.window.advClickXLabel.setText("X")
        self.window.advClickXLabel.setStyleSheet(field_label_style)
        self.window.advClickXInput.setGeometry(44, 52, 64, 28)
        self.window.advClickXInput.setStyleSheet(input_style)
        self.window.advClickXInput.setPlaceholderText("0")

        self.window.advClickYLabel.setGeometry(124, 58, 12, 16)
        self.window.advClickYLabel.setText("Y")
        self.window.advClickYLabel.setStyleSheet(field_label_style)
        self.window.advClickYInput.setGeometry(144, 52, 64, 28)
        self.window.advClickYInput.setStyleSheet(input_style)
        self.window.advClickYInput.setPlaceholderText("0")

        self.window.advRecordClickButton.setGeometry(224, 52, 118, 28)
        self.window.advRecordClickButton.setText("⌖  Record")
        self.window.advRecordClickButton.setFocusPolicy(Qt.NoFocus)
        self.window.advRecordClickButton.setStyleSheet(self._secondary_button_stylesheet())

        if not hasattr(self.window, "_advClickLeftRadio"):
            self.window._advClickLeftRadio = QRadioButton("Left Click", self.window.advancedClickGroup)
            self.window._advClickRightRadio = QRadioButton("Right Click", self.window.advancedClickGroup)
            self.window._advClickLeftRadio.setChecked(True)
        for radio in (self.window._advClickLeftRadio, self.window._advClickRightRadio):
            radio.setStyleSheet(
                "QRadioButton {"
                "color: rgba(255, 255, 255, 0.60);"
                "background: transparent;"
                "spacing: 6px;"
                "font-family: 'Space Mono', 'Menlo', monospace;"
                "font-size: 10px;"
                "font-weight: 500;"
                "}"
                "QRadioButton:hover { color: rgba(255, 255, 255, 0.80); }"
                "QRadioButton::indicator {"
                "width: 14px;"
                "height: 14px;"
                "border-radius: 7px;"
                "border: 1px solid rgba(255, 255, 255, 0.12);"
                "background: transparent;"
                "}"
                "QRadioButton::indicator:unchecked:hover { border: 1px solid rgba(255, 255, 255, 0.25); }"
                "QRadioButton::indicator:checked { background: #ffffff; border: 1px solid #ffffff; }"
            )
            radio.show()
        self.window._advClickLeftRadio.setGeometry(24, 94, 102, 20)
        self.window._advClickRightRadio.setGeometry(150, 94, 110, 20)

        self.window.addAdvancedClickButton.setGeometry(24, 150, 342, 28)
        self.window.addAdvancedClickButton.setText("+  Add Click Step")
        self.window.addAdvancedClickButton.setFocusPolicy(Qt.NoFocus)
        self._style_primary_step_button(self.window.addAdvancedClickButton, font_size=10, letter_spacing=0)

        key_radio_style = (
            "QRadioButton {"
            "color: rgba(255, 255, 255, 0.60);"
            "background: transparent;"
            "spacing: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QRadioButton:hover { color: rgba(255, 255, 255, 0.80); }"
            "QRadioButton::indicator {"
            "width: 14px;"
            "height: 14px;"
            "border-radius: 4px;"
            "border: 1px solid rgba(255, 255, 255, 0.12);"
            "background: transparent;"
            "}"
            "QRadioButton::indicator:unchecked:hover { border: 1px solid rgba(255, 255, 255, 0.25); }"
            "QRadioButton::indicator:checked { background: #ffffff; border: 1px solid #ffffff; }"
        )
        self.window.advKeyPressRadio.setGeometry(24, 52, 116, 20)
        self.window.advKeyPressRadio.setText("Press Key")
        self.window.advKeyPressRadio.setStyleSheet(key_radio_style)
        self.window.advKeyHoldRadio.setGeometry(24, 96, 128, 28)
        self.window.advKeyHoldRadio.setText("Hold Key\nfor:")
        self.window.advKeyHoldRadio.setStyleSheet(key_radio_style)

        self.window.advKeyTimesLabel.setGeometry(184, 58, 24, 16)
        self.window.advKeyTimesLabel.setText("SEC")
        self.window.advKeyTimesLabel.setStyleSheet(field_label_style)
        self.window.advKeyTimesInput.setGeometry(220, 52, 40, 28)
        self.window.advKeyTimesInput.setStyleSheet(input_style)
        self.window.advKeyTimesInput.setPlaceholderText("1")

        self.window.advKeyPressKeyLabel.setGeometry(276, 58, 24, 16)
        self.window.advKeyPressKeyLabel.setText("KEY")
        self.window.advKeyPressKeyLabel.setStyleSheet(field_label_style)
        self.window.advKeyInput.setGeometry(312, 52, 32, 28)
        self.window.advKeyInput.setStyleSheet(input_style)
        self.window.advKeyInput.setAlignment(Qt.AlignCenter)
        self.window.advKeyInput.setMaxLength(1)
        self.window.advKeyInput.setPlaceholderText("t")

        self.window.advKeyHoldSecLabel.setGeometry(184, 102, 24, 16)
        self.window.advKeyHoldSecLabel.setText("SEC")
        self.window.advKeyHoldSecLabel.setStyleSheet(field_label_style)
        self.window.advKeyHoldInput.setGeometry(220, 96, 40, 28)
        self.window.advKeyHoldInput.setStyleSheet(input_style)
        self.window.advKeyHoldInput.setPlaceholderText("1")

        self.window.advKeyHoldKeyLabel.setGeometry(276, 102, 24, 16)
        self.window.advKeyHoldKeyLabel.setText("KEY")
        self.window.advKeyHoldKeyLabel.setStyleSheet(field_label_style)
        self.window.advKeyHoldKeyInput.setGeometry(312, 96, 32, 28)
        self.window.advKeyHoldKeyInput.setStyleSheet(input_style)
        self.window.advKeyHoldKeyInput.setAlignment(Qt.AlignCenter)
        self.window.advKeyHoldKeyInput.setMaxLength(1)
        self.window.advKeyHoldKeyInput.setPlaceholderText("t")

        self.window.addAdvancedKeyButton.setGeometry(24, 150, 342, 28)
        self.window.addAdvancedKeyButton.setText("+  Add Key Step")
        self.window.addAdvancedKeyButton.setFocusPolicy(Qt.NoFocus)
        self._style_primary_step_button(self.window.addAdvancedKeyButton, font_size=10, letter_spacing=0)

    def _sync_unit_saved_display(self, slot: int) -> None:
        label = self.advanced_widgets.unit_saved_labels[slot]
        text = label.text().strip()
        display_name = text.removeprefix("Saved:").strip()
        label.setText(display_name)
        dot = getattr(self.window, "_unit_status_dots", {}).get(slot)
        visible = bool(display_name)
        label.setVisible(visible)
        if dot is not None:
            dot.setVisible(visible)

    def _sync_all_unit_saved_displays(self) -> None:
        for slot in range(1, 7):
            self._sync_unit_saved_display(slot)

    def _wait_indicator_stylesheet(self, *, active: bool) -> str:
        if active:
            return (
                "QPushButton {"
                "background-color: #ffffff;"
                "color: #000000;"
                "border: 1px solid #ffffff;"
                "border-radius: 4px;"
                "font-family: 'Space Mono', 'Menlo', monospace;"
                "font-size: 10px;"
                "font-weight: 700;"
                "padding: 0px;"
                "}"
            )
        return (
            "QPushButton {"
            "background-color: transparent;"
            "color: transparent;"
            "border: 1px solid rgba(255, 255, 255, 0.12);"
            "border-radius: 4px;"
            "padding: 0px;"
            "}"
            "QPushButton:hover {"
            "border: 1px solid rgba(255, 255, 255, 0.25);"
            "}"
        )

    def _wait_text_button_stylesheet(self, *, active: bool) -> str:
        color = "#ffffff" if active else "rgba(255, 255, 255, 0.60)"
        hover = "#ffffff" if active else "rgba(255, 255, 255, 0.80)"
        return (
            "QPushButton {"
            "background: transparent;"
            "border: none;"
            f"color: {color};"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "text-align: left;"
            "padding: 0px;"
            "}"
            "QPushButton:hover {"
            f"color: {hover};"
            "}"
        )

    def _ensure_wait_mode_proxies(self) -> None:
        if hasattr(self.window, "_wait_mode_proxies"):
            return

        radio_map = {
            "seconds": self.window.advancedWaitSecondsRadio,
            "round": self.window.advancedWaitRoundRadio,
            "yen": self.window.advancedWaitYenRadio,
            "game": self.window.advancedWaitGameRadio,
        }
        for radio in radio_map.values():
            radio.hide()

        proxy_specs = {
            "seconds": "Wait for Seconds",
            "round": "Round Completed",
            "yen": "Wait for Yen >=",
            "game": "Wait for Game\nStart",
        }
        proxies = {}
        for mode, text in proxy_specs.items():
            indicator = QPushButton(self.window.advancedWaitGroup)
            indicator.setFocusPolicy(Qt.NoFocus)
            indicator.clicked.connect(lambda _checked=False, selected_mode=mode: self._set_wait_mode(selected_mode))

            label = QPushButton(text, self.window.advancedWaitGroup)
            label.setFocusPolicy(Qt.NoFocus)
            label.clicked.connect(lambda _checked=False, selected_mode=mode: self._set_wait_mode(selected_mode))

            proxies[mode] = {"indicator": indicator, "label": label}

        self.window._wait_mode_proxies = proxies

    def _set_wait_mode(self, mode: str) -> None:
        radio_map = {
            "seconds": self.window.advancedWaitSecondsRadio,
            "round": self.window.advancedWaitRoundRadio,
            "yen": self.window.advancedWaitYenRadio,
            "game": self.window.advancedWaitGameRadio,
        }
        target_radio = radio_map.get(mode)
        if target_radio is None:
            return
        for radio_mode, radio in radio_map.items():
            radio.blockSignals(True)
            radio.setChecked(radio_mode == mode)
            radio.blockSignals(False)
        self._sync_wait_mode_proxies()

    def _sync_wait_mode_proxies(self) -> None:
        proxies = getattr(self.window, "_wait_mode_proxies", None)
        if not proxies:
            return
        checked_map = {
            "seconds": self.window.advancedWaitSecondsRadio.isChecked(),
            "round": self.window.advancedWaitRoundRadio.isChecked(),
            "yen": self.window.advancedWaitYenRadio.isChecked(),
            "game": self.window.advancedWaitGameRadio.isChecked(),
        }
        for mode, widgets in proxies.items():
            active = checked_map.get(mode, False)
            indicator = widgets["indicator"]
            label = widgets["label"]
            indicator.setStyleSheet(self._wait_indicator_stylesheet(active=active))
            indicator.setText("✓" if active else "")
            label.setStyleSheet(self._wait_text_button_stylesheet(active=active))

    def _style_wait_section(self) -> None:
        self.window.advancedWaitGroup.setGeometry(self._wait_geometry_for_nav(False))
        self.window.advancedWaitGroup.setTitle("")
        self.window.advancedWaitGroup.setStyleSheet(self._card_shell_stylesheet())

        self.window.waitHeaderLabel.hide()
        wait_title_label = getattr(self.window, "_waitCardTitleLabel", None)
        if wait_title_label is None:
            wait_title_label = QLabel("Wait", self.window.advancedWaitGroup)
            self.window._waitCardTitleLabel = wait_title_label
        wait_title_label.setGeometry(24, 18, 180, 18)
        wait_title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        wait_title_label.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding: 0px; margin: 0px;"
        )
        wait_title_label.setIndent(0)
        wait_title_label.setMargin(0)
        wait_title_label.setContentsMargins(0, 0, 0, 0)
        wait_title_label.show()
        wait_title_label.raise_()

        self._ensure_wait_mode_proxies()

        seconds_proxy = self.window._wait_mode_proxies["seconds"]
        seconds_proxy["indicator"].setGeometry(24, 81, 14, 14)
        seconds_proxy["label"].setGeometry(40, 76, 128, 24)

        self.window.advancedWaitSecondsInput.setGeometry(278, 74, 64, 28)
        self.window.advancedWaitSecondsInput.setStyleSheet(
            "QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QLineEdit:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
        )
        self.window.advancedWaitSecondsLabel.setGeometry(358, 78, 40, 20)
        self.window.advancedWaitSecondsLabel.setText("SEC")
        self.window.advancedWaitSecondsLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.30); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 600;"
        )

        round_proxy = self.window._wait_mode_proxies["round"]
        round_proxy["indicator"].setGeometry(506, 81, 14, 14)
        round_proxy["label"].setGeometry(522, 76, 128, 24)

        self.window.advancedWaveLabel.setGeometry(772, 78, 40, 20)
        self.window.advancedWaveLabel.setText("Wave")
        self.window.advancedWaveLabel.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.30); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 600;"
        )
        self.window.advancedWaveInput.setGeometry(842, 74, 56, 28)
        self.window.advancedWaveInput.setStyleSheet(
            "QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QLineEdit:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
        )

        yen_proxy = self.window._wait_mode_proxies["yen"]
        yen_proxy["indicator"].setGeometry(24, 120, 14, 14)
        yen_proxy["label"].setGeometry(40, 115, 128, 24)
        self.window.advancedWaitYenInput.setGeometry(278, 113, 64, 28)
        self.window.advancedWaitYenInput.setStyleSheet(
            "QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QLineEdit:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
        )

        placeholder = getattr(self.window, "_waitPlaceholderLabel", None)
        if placeholder is None:
            placeholder = QLabel(self.window.advancedWaitGroup)
            self.window._waitPlaceholderLabel = placeholder
        placeholder.setGeometry(358, 117, 40, 20)
        placeholder.setText("SEC")
        placeholder.setStyleSheet(
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.30); font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 10px; font-weight: 600;"
        )
        placeholder.hide()

        game_proxy = self.window._wait_mode_proxies["game"]
        game_proxy["indicator"].setGeometry(506, 120, 14, 14)
        game_proxy["label"].setGeometry(522, 111, 140, 32)

        self.window.addAdvancedWaitButton.setText("+  Add Wait Step")
        self.window.addAdvancedWaitButton.setFocusPolicy(Qt.NoFocus)
        self._style_primary_step_button(self.window.addAdvancedWaitButton, font_size=10, letter_spacing=0)

        self._layout_wait_section_content()
        self._sync_wait_mode_proxies()

    def _style_abilities_section(self) -> None:
        if not self._abilities_tab_initialized:
            return

        expanded = getattr(self, "_step_nav_hovered", False) or (
            hasattr(self, "_step_nav_frame") and self._step_nav_frame.width() > 60
        )
        self.window.advancedAbilitiesGroup.setGeometry(self._abilities_geometry_for_nav(expanded))
        self.window.advancedAbilitiesGroup.setTitle("")
        self.window.advancedAbilitiesGroup.setStyleSheet("QGroupBox { background-color: transparent; border: none; }")

        legacy_main_group = getattr(self.window, "_legacyAbilityMainGroup", self.window.abilityMainUnitCombo.parentWidget())
        legacy_skele_group = getattr(self.window, "_legacyAbilitySkeleGroup", self.window.abilitySkeleActionButton.parentWidget())
        legacy_ainz_group = getattr(self.window, "_legacyAbilityAinzGroup", self.window.ainzArcaneAddButton.parentWidget())

        card_style = (
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
        )
        field_label_style = (
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50);"
            "font-family: 'Space Mono', 'Menlo', monospace; font-size: 10px; font-weight: 500;"
            "padding: 0px; margin: 0px;"
        )
        combo_style = (
            "QComboBox {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QComboBox:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
            "QComboBox::drop-down { border: none; width: 22px; background: transparent; }"
            "QComboBox QAbstractItemView {"
            "background-color: #1a1a1a;"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "selection-background-color: rgba(255, 255, 255, 0.08);"
            "selection-color: #ffffff;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "}"
        )
        line_edit_style = (
            "QLineEdit {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QLineEdit:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
        )
        small_combo_style = (
            "QComboBox {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "padding: 0 8px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "font-weight: 500;"
            "}"
            "QComboBox:focus { border: 1px solid rgba(255, 255, 255, 0.20); }"
            "QComboBox::drop-down { border: none; width: 20px; background: transparent; }"
            "QComboBox QAbstractItemView {"
            "background-color: #1a1a1a;"
            "color: #ffffff;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "selection-background-color: rgba(255, 255, 255, 0.08);"
            "selection-color: #ffffff;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "}"
        )
        checkbox_style = (
            "QCheckBox {"
            "color: rgba(255, 255, 255, 0.60);"
            "background: transparent;"
            "border: none;"
            "spacing: 6px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "}"
            "QCheckBox::indicator {"
            "width: 14px;"
            "height: 14px;"
            "border-radius: 4px;"
            "border: 1px solid rgba(255, 255, 255, 0.12);"
            "background: transparent;"
            "}"
            "QCheckBox::indicator:unchecked:hover {"
            "border: 1px solid rgba(255, 255, 255, 0.25);"
            "}"
            "QCheckBox::indicator:checked {"
            "background: #ffffff;"
            "border: 1px solid #ffffff;"
            "}"
        )
        title_style = (
            "background: transparent; border: none; color: #ffffff; font-family: 'Space Mono', 'Menlo', monospace; "
            "font-size: 12px; font-weight: 600; padding: 0px; margin: 0px;"
        )

        if not hasattr(self.window, "_generalAbilitiesCard"):
            self.window._generalAbilitiesCard = QFrame(self.window.advancedAbilitiesGroup)
            self.window._otherAbilitiesCard = QFrame(self.window.advancedAbilitiesGroup)
            self.window._ainzSkillsCard = QFrame(self.window.advancedAbilitiesGroup)
            self.window._caloricStoneCard = QFrame(self.window.advancedAbilitiesGroup)

            self.window._generalAbilitiesTitle = QLabel("General Abilities", self.window._generalAbilitiesCard)
            self.window._otherAbilitiesTitle = QLabel("Other Abilities", self.window._otherAbilitiesCard)
            self.window._ainzSkillsTitle = QLabel("Ainz Skills", self.window._ainzSkillsCard)
            self.window._caloricStoneTitle = QLabel("Caloric Stone", self.window._caloricStoneCard)

            self.window._abilityMainUnitLabel = QLabel("Unit", self.window._generalAbilitiesCard)
            self.window._abilityMainAbilityLabel = QLabel("Ability", self.window._generalAbilitiesCard)
            self.window._abilitySkeleLabel = QLabel("Ability", self.window._otherAbilitiesCard)
            self.window._ainzCaloricUnitLabel = QLabel("Unit", self.window._caloricStoneCard)
            self.window._ainzCaloricPositionLabel = QLabel("Position", self.window._caloricStoneCard)

            self.window._abilitySkeleCombo = QComboBox(self.window._otherAbilitiesCard)
            self.window._abilitySkeleCombo.addItem("")
            self.window._abilitySkeleCombo.addItem(SKELE_STRINGS_LABEL)
            self.window._abilitySkeleCombo.setCurrentIndex(0)

        card_geometries = {
            self.window._generalAbilitiesCard: QRect(0, 0, 218, 170),
            self.window._otherAbilitiesCard: QRect(242, 0, 171, 128),
            self.window._ainzSkillsCard: QRect(437, 0, 205, 208),
            self.window._caloricStoneCard: QRect(666, 0, 248, 170),
        }
        for card, rect in card_geometries.items():
            card.setGeometry(rect)
            if isinstance(card, QFrame):
                card.setFrameShape(QFrame.NoFrame)
            elif hasattr(card, "setTitle"):
                card.setTitle("")
            card.setStyleSheet(card_style)
            card.show()
            card.raise_()

        for title_label in (
            self.window._generalAbilitiesTitle,
            self.window._otherAbilitiesTitle,
            self.window._ainzSkillsTitle,
            self.window._caloricStoneTitle,
        ):
            title_label.setGeometry(12, 9, max(0, title_label.parentWidget().width() - 24), 28)
            title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_label.setStyleSheet(title_style)
            title_label.setIndent(0)
            title_label.setMargin(0)
            title_label.setContentsMargins(0, 0, 0, 0)
            title_label.show()
            title_label.raise_()

        self.window._abilityMainUnitLabel.setGeometry(12, 56, 48, 16)
        self.window._abilityMainAbilityLabel.setGeometry(12, 94, 48, 16)
        self.window._abilitySkeleLabel.setGeometry(12, 56, 48, 16)
        self.window._ainzCaloricUnitLabel.setGeometry(12, 56, 48, 16)
        self.window._ainzCaloricPositionLabel.setGeometry(12, 94, 48, 16)
        for label in (
            self.window._abilityMainUnitLabel,
            self.window._abilityMainAbilityLabel,
            self.window._abilitySkeleLabel,
            self.window._ainzCaloricUnitLabel,
            self.window._ainzCaloricPositionLabel,
        ):
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setStyleSheet(field_label_style)
            label.show()

        self.window.abilityMainUnitCombo.setParent(self.window._generalAbilitiesCard)
        self.window.abilityMainUnitCombo.setGeometry(60, 49, 96, 28)
        self.window.abilityMainUnitCombo.setStyleSheet(combo_style)
        self.window.abilityMainUnitCombo.show()

        self.window.abilityMainAbilityCombo.setParent(self.window._generalAbilitiesCard)
        self.window.abilityMainAbilityCombo.setGeometry(60, 87, 96, 28)
        self.window.abilityMainAbilityCombo.setStyleSheet(combo_style)
        self.window.abilityMainAbilityCombo.show()

        self.window.abilityMainAutoCheck.setParent(self.window._generalAbilitiesCard)
        self.window.abilityMainAutoCheck.setGeometry(166, 91, 46, 20)
        self.window.abilityMainAutoCheck.setStyleSheet(checkbox_style)
        self.window.abilityMainAutoCheck.show()

        self.window.abilityMainAddButton.setParent(self.window._generalAbilitiesCard)
        self.window.abilityMainAddButton.setGeometry(12, 125, 194, 28)
        self.window.abilityMainAddButton.setText("+ Add Ability Step")
        self.window.abilityMainAddButton.setFocusPolicy(Qt.NoFocus)
        self._style_compact_ability_button(self.window.abilityMainAddButton, font_size=10)
        self.window.abilityMainAddButton.show()

        self.window._abilitySkeleCombo.setGeometry(60, 49, 99, 28)
        self.window._abilitySkeleCombo.setStyleSheet(combo_style)
        self.window._abilitySkeleCombo.show()

        self.window.abilitySkeleActionButton.hide()
        self.window.abilitySkeleAddButton.setParent(self.window._otherAbilitiesCard)
        self.window.abilitySkeleAddButton.setGeometry(12, 87, 147, 28)
        self.window.abilitySkeleAddButton.setText("+ Add Ability Step")
        self.window.abilitySkeleAddButton.setFocusPolicy(Qt.NoFocus)
        self._style_compact_ability_button(self.window.abilitySkeleAddButton, font_size=10)
        self.window.abilitySkeleAddButton.show()

        ainz_combo_positions = (
            (12, 46),
            (106, 46),
            (12, 76),
            (106, 76),
            (12, 106),
            (106, 106),
            (12, 136),
            (106, 136),
        )
        flat_ainz_combos = [combo for row in self.window.ainzArcaneRows for combo in row]
        for combo, (x, y) in zip(flat_ainz_combos, ainz_combo_positions):
            combo.setParent(self.window._ainzSkillsCard)
            combo.setGeometry(x, y, 89, 24)
            combo.setStyleSheet(small_combo_style)
            combo.show()

        self.window.ainzArcaneAddButton.setParent(self.window._ainzSkillsCard)
        self.window.ainzArcaneAddButton.setGeometry(12, 173, 181, 24)
        self.window.ainzArcaneAddButton.setText("+ Add Skill Selection")
        self.window.ainzArcaneAddButton.setFocusPolicy(Qt.NoFocus)
        self._style_compact_ability_button(self.window.ainzArcaneAddButton, font_size=9)
        self.window.ainzArcaneAddButton.show()

        self.window.ainzCaloricUnitInput.setParent(self.window._caloricStoneCard)
        self.window.ainzCaloricUnitInput.setGeometry(72, 49, 92, 28)
        self.window.ainzCaloricUnitInput.setStyleSheet(combo_style)
        self.window.ainzCaloricUnitInput.show()

        self.window.ainzCaloricLocationInput.setParent(self.window._caloricStoneCard)
        self.window.ainzCaloricLocationInput.setGeometry(72, 87, 92, 28)
        self.window.ainzCaloricLocationInput.setStyleSheet(line_edit_style)
        self.window.ainzCaloricLocationInput.show()

        self.window.ainzCaloricRecordButton.setParent(self.window._caloricStoneCard)
        self.window.ainzCaloricRecordButton.setGeometry(174, 87, 62, 28)
        self.window.ainzCaloricRecordButton.setText("Record")
        self.window.ainzCaloricRecordButton.setFocusPolicy(Qt.NoFocus)
        self.window.ainzCaloricRecordButton.setStyleSheet(self._secondary_button_stylesheet())
        self.window.ainzCaloricRecordButton.show()

        self.window.ainzCaloricAddButton.setParent(self.window._caloricStoneCard)
        self.window.ainzCaloricAddButton.setGeometry(12, 125, 224, 28)
        self.window.ainzCaloricAddButton.setText("+ Add Caloric Step")
        self.window.ainzCaloricAddButton.setFocusPolicy(Qt.NoFocus)
        self._style_compact_ability_button(self.window.ainzCaloricAddButton, font_size=10)
        self.window.ainzCaloricAddButton.show()

        for legacy_group in (legacy_main_group, legacy_skele_group, legacy_ainz_group):
            if legacy_group not in (
                self.window._generalAbilitiesCard,
                self.window._otherAbilitiesCard,
                self.window._ainzSkillsCard,
                self.window._caloricStoneCard,
            ):
                legacy_group.hide()

    def _layout_wait_section_content(self) -> None:
        if not hasattr(self.window, "_wait_mode_proxies"):
            return

        group_width = self.window.advancedWaitGroup.width()
        content_left = 24
        checkbox_size = 14
        checkbox_gap = 6
        base_gap = 8
        section_gap = 24
        checkbox_group_width = 128
        seconds_input_width = 64
        wave_input_width = 56
        sec_label_width = 24
        wave_label_width = 32

        row1_y = 81
        row1_label_y = 76
        row1_input_y = 74
        row2_y = 120
        row2_label_y = 115
        row2_input_y = 113

        seconds_indicator_x = content_left
        seconds_label_x = seconds_indicator_x + checkbox_size + checkbox_gap
        seconds_input_x = content_left + checkbox_group_width + base_gap
        seconds_suffix_x = seconds_input_x + seconds_input_width + base_gap

        round_indicator_x = seconds_suffix_x + sec_label_width + section_gap
        round_label_x = round_indicator_x + checkbox_size + checkbox_gap
        wave_label_x = content_left + checkbox_group_width + base_gap + seconds_input_width + base_gap + sec_label_width + section_gap + checkbox_group_width + base_gap
        wave_input_x = wave_label_x + wave_label_width + base_gap

        yen_indicator_x = content_left
        yen_label_x = yen_indicator_x + checkbox_size + checkbox_gap
        yen_input_x = content_left + checkbox_group_width + base_gap

        game_indicator_x = seconds_suffix_x + sec_label_width + section_gap
        game_label_x = game_indicator_x + checkbox_size + checkbox_gap

        seconds_proxy = self.window._wait_mode_proxies["seconds"]
        seconds_proxy["indicator"].setGeometry(seconds_indicator_x, row1_y, checkbox_size, checkbox_size)
        seconds_proxy["label"].setGeometry(seconds_label_x, row1_label_y, checkbox_group_width - checkbox_size - checkbox_gap, 24)
        self.window.advancedWaitSecondsInput.setGeometry(seconds_input_x, row1_input_y, seconds_input_width, 28)
        self.window.advancedWaitSecondsLabel.setGeometry(seconds_suffix_x, 78, sec_label_width, 20)

        round_proxy = self.window._wait_mode_proxies["round"]
        round_proxy["indicator"].setGeometry(round_indicator_x, row1_y, checkbox_size, checkbox_size)
        round_proxy["label"].setGeometry(round_label_x, row1_label_y, checkbox_group_width - checkbox_size - checkbox_gap, 24)
        self.window.advancedWaveLabel.setGeometry(wave_label_x, 78, wave_label_width, 20)
        self.window.advancedWaveInput.setGeometry(wave_input_x, row1_input_y, wave_input_width, 28)

        yen_proxy = self.window._wait_mode_proxies["yen"]
        yen_proxy["indicator"].setGeometry(yen_indicator_x, row2_y, checkbox_size, checkbox_size)
        yen_proxy["label"].setGeometry(yen_label_x, row2_label_y, checkbox_group_width - checkbox_size - checkbox_gap, 24)
        self.window.advancedWaitYenInput.setGeometry(yen_input_x, row2_input_y, seconds_input_width, 28)

        placeholder = getattr(self.window, "_waitPlaceholderLabel", None)
        if placeholder is not None:
            placeholder.setGeometry(seconds_suffix_x, 117, sec_label_width, 20)

        game_proxy = self.window._wait_mode_proxies["game"]
        game_proxy["indicator"].setGeometry(game_indicator_x, row2_y, checkbox_size, checkbox_size)
        game_proxy["label"].setGeometry(game_label_x, 111, checkbox_group_width - checkbox_size - checkbox_gap, 34)

        self.window.addAdvancedWaitButton.setGeometry(24, 150, max(0, group_width - 48), 28)

    def _init_abilities_tab(self) -> None:
        if self._abilities_tab_initialized:
            return

        def style_shell(group: QGroupBox) -> None:
            group.setStyleSheet(
                "QGroupBox { background-color: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 0px; }"
                "QComboBox, QLineEdit { background-color: #050505; color: #E0E0E0; border: 1px solid #2a2a2a; "
                "border-radius: 0px; padding: 2px 6px; font-family: 'Inter', sans-serif; font-size: 11px; }"
                "QPushButton { background-color: #10b981; color: #000000; border: none; border-radius: 0px; "
                "font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 800; letter-spacing: 1px; }"
                "QPushButton:hover { background-color: #0ea472; }"
                "QCheckBox { color: #E0E0E0; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; }"
                "QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid #555555; background-color: #0a0a0a; }"
                "QCheckBox::indicator:checked { background-color: #10b981; border-color: #10b981; }"
            )

        def add_header(parent: QWidget, text: str, width: int) -> QLabel:
            label = QLabel(text, parent)
            label.setGeometry(0, 0, width, 30)
            label.setStyleSheet(
                "color: #E0E0E0; font-family: 'Inter', sans-serif; font-size: 12px; "
                "font-weight: 800; letter-spacing: 1px; background-color: transparent;"
            )
            return label

        def add_field_label(parent: QWidget, text: str, x: int, y: int, width: int = 120) -> QLabel:
            label = QLabel(text, parent)
            label.setGeometry(x, y, width, 12)
            label.setStyleSheet(
                "color: #555555; font-family: 'Inter', sans-serif; font-size: 9px; "
                "font-weight: 700; letter-spacing: 1px; background-color: transparent;"
            )
            return label

        main_group = QGroupBox(self.window.advancedAbilitiesGroup)
        main_group.setGeometry(0, 0, 252, 182)
        main_group.setTitle("")
        style_shell(main_group)
        self.window._legacyAbilityMainGroup = main_group
        add_header(main_group, "MAIN", 252)
        add_field_label(main_group, "UNIT", 12, 40)
        self.window.abilityMainUnitCombo = self._create_combo(main_group, 12, 54, 148, 22)
        self.window.abilityMainAutoCheck = self._create_checkbox("Auto", main_group, 170, 56, 68, 18)
        add_field_label(main_group, "ABILITY", 12, 84)
        self.window.abilityMainAbilityCombo = self._create_combo(main_group, 12, 98, 226, 22)
        self.window.abilityMainAddButton = self._create_action_button(
            "Add Ability Step",
            main_group,
            12,
            142,
            226,
            28,
        )

        skele_group = QGroupBox(self.window.advancedAbilitiesGroup)
        skele_group.setGeometry(264, 0, 210, 182)
        skele_group.setTitle("")
        style_shell(skele_group)
        self.window._legacyAbilitySkeleGroup = skele_group
        add_header(skele_group, "SKELE KING", 210)
        self.window.abilitySkeleActionButton = QPushButton("Skele: Strings Ability", skele_group)
        self.window.abilitySkeleActionButton.setGeometry(12, 74, 186, 30)
        self.window.abilitySkeleActionButton.setEnabled(False)
        self.window.abilitySkeleActionButton.setStyleSheet(
            "QPushButton { background-color: #050505; color: #E0E0E0; border: 1px solid #2a2a2a; "
            "border-radius: 0px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 700; }"
        )
        self.window.abilitySkeleAddButton = self._create_action_button(
            "Add Ability Step",
            skele_group,
            12,
            142,
            186,
            28,
        )

        ainz_group = QGroupBox(self.window.advancedAbilitiesGroup)
        ainz_group.setGeometry(486, 0, 584, 182)
        ainz_group.setTitle("")
        style_shell(ainz_group)
        self.window._legacyAbilityAinzGroup = ainz_group
        add_header(ainz_group, "AINZ", 584)

        add_field_label(ainz_group, "ARCANE KNOWLEDGE", 12, 40, 180)
        self.window.ainzArcaneRows = []
        row_y = 56
        for idx in range(4):
            element_combo = self._create_combo(ainz_group, 12, row_y, 128, 22)
            skill_combo = self._create_combo(ainz_group, 148, row_y, 176, 22)
            self.window.ainzArcaneRows.append((element_combo, skill_combo))
            row_y += 24

        self.window.ainzArcaneAddButton = self._create_action_button(
            "Add Skill Selection",
            ainz_group,
            12,
            148,
            312,
            24,
        )

        add_field_label(ainz_group, "CALORIC STONE", 344, 40, 160)
        add_field_label(ainz_group, "UNIT", 344, 64, 120)
        self.window.ainzCaloricUnitInput = self._create_searchable_unit_combo(
            ainz_group,
            self._create_rect(344, 78, 228, 22),
            "ainzCaloricUnitInput",
            "",
            "Enter Unit",
        )
        add_field_label(ainz_group, "LOCATION", 344, 104, 120)
        self.window.ainzCaloricLocationInput = self._create_line_edit(ainz_group, 344, 118, 144, 22, "X, Y")
        self.window.ainzCaloricRecordButton = self._create_action_button(
            "Record",
            ainz_group,
            494,
            118,
            78,
            22,
        )
        self.window.ainzCaloricAddButton = self._create_action_button(
            "Add Ability Step",
            ainz_group,
            344,
            148,
            228,
            24,
        )

        self.window.abilityMainUnitCombo.currentIndexChanged.connect(self.populate_main_ability_options)
        self.window.abilityMainAutoCheck.toggled.connect(self._sync_main_ability_auto_state)
        self.window.abilityMainAddButton.clicked.connect(self.add_main_ability_step)
        self.window.abilitySkeleAddButton.clicked.connect(self.add_skele_king_ability_step)
        self.window.ainzArcaneAddButton.clicked.connect(self.add_ainz_arcane_step)
        self.window.ainzCaloricAddButton.clicked.connect(self.add_ainz_caloric_step)
        self.window.ainzCaloricRecordButton.clicked.connect(self.record_ainz_caloric_location)

        for element_combo, skill_combo in self.window.ainzArcaneRows:
            element_combo.addItem("")
            element_combo.addItems(ARCANE_ELEMENTS)
            element_combo.currentTextChanged.connect(
                lambda _text, combo=element_combo, skill=skill_combo: self.populate_ainz_skill_options(combo, skill)
            )
            skill_combo.addItem("")

        self.refresh_ability_unit_combo()
        self._sync_main_ability_auto_state(self.window.abilityMainAutoCheck.isChecked())
        self._abilities_tab_initialized = True

    @staticmethod
    def _create_combo(parent, x: int, y: int, width: int, height: int):
        from PySide6.QtWidgets import QComboBox

        combo = QComboBox(parent)
        combo.setGeometry(x, y, width, height)
        return combo

    @staticmethod
    def _create_line_edit(parent, x: int, y: int, width: int, height: int, placeholder: str):
        from PySide6.QtWidgets import QLineEdit

        line_edit = QLineEdit(parent)
        line_edit.setGeometry(x, y, width, height)
        line_edit.setPlaceholderText(placeholder)
        return line_edit

    @staticmethod
    def _create_rect(x: int, y: int, width: int, height: int):
        from PySide6.QtCore import QRect

        return QRect(x, y, width, height)

    @staticmethod
    def _create_checkbox(text: str, parent, x: int, y: int, width: int, height: int):
        from PySide6.QtWidgets import QCheckBox

        checkbox = QCheckBox(text, parent)
        checkbox.setGeometry(x, y, width, height)
        return checkbox

    @staticmethod
    def _create_action_button(text: str, parent, x: int, y: int, width: int, height: int):
        button = QPushButton(text, parent)
        button.setGeometry(x, y, width, height)
        return button

    @staticmethod
    def _style_primary_step_button(button: QPushButton, *, font_size: int, letter_spacing: int) -> None:
        button.setStyleSheet(
            "QPushButton { "
            "background-color: rgba(255, 255, 255, 0.08); "
            "color: #ffffff; "
            "border: 1px solid rgba(255, 255, 255, 0.08); "
            "border-radius: 4px; "
            "font-family: 'Space Mono', 'Menlo', monospace; "
            f"font-size: {font_size}px; "
            "font-weight: 500; "
            f"letter-spacing: {letter_spacing}px; "
            "padding-top: 1px; "
            "padding-bottom: 0px; "
            "} "
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); } "
            "QPushButton:pressed { background-color: rgba(255, 255, 255, 0.16); }"
        )

    def _replace_primary_step_button(
        self,
        old_button: QPushButton,
        parent,
        *,
        font_size: int,
        letter_spacing: int,
    ) -> QPushButton:
        geometry = old_button.geometry()
        object_name = old_button.objectName()
        text = old_button.text()
        old_button.hide()
        old_button.deleteLater()

        button = QPushButton(text, parent)
        button.setObjectName(object_name)
        button.setGeometry(geometry)
        self._style_primary_step_button(button, font_size=font_size, letter_spacing=letter_spacing)
        button.show()
        button.raise_()
        return button

    def _init_searchable_unit_inputs(self) -> None:
        if self._searchable_unit_inputs_initialized:
            return
        for slot, old_input in list(self.advanced_widgets.unit_inputs.items()):
            parent = old_input.parent()
            combo = self._create_searchable_unit_combo(
                parent,
                old_input.geometry(),
                old_input.objectName(),
                old_input.styleSheet(),
                old_input.placeholderText(),
            )

            old_input.hide()
            self.advanced_widgets.unit_inputs[slot] = combo
        self._searchable_unit_inputs_initialized = True

    def _create_searchable_unit_combo(self, parent, geometry, object_name: str, style_sheet: str, placeholder: str) -> QComboBox:
        combo = QComboBox(parent)
        combo.setGeometry(geometry)
        combo.setObjectName(object_name)
        combo.setStyleSheet(style_sheet)
        combo.setEditable(True)
        combo.setMaxVisibleItems(6)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.addItems(UNIT_NAME_OPTIONS)

        model = QStringListModel(UNIT_NAME_OPTIONS, combo)
        completer = QCompleter(model, combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)

        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(placeholder)
            line_edit.textEdited.connect(
                lambda text, current_combo=combo: self._update_unit_completer(current_combo, text)
            )
        return combo

    def _configure_searchable_slot_combo(self, combo: QComboBox, placeholder: str = "Select Unit") -> None:
        if getattr(combo, "_searchable_slot_combo", False):
            return
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMaxVisibleItems(max(combo.maxVisibleItems(), 8))
        completer = QCompleter(combo.model(), combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)
        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(placeholder)
            line_edit.textEdited.connect(
                lambda text, current_combo=combo: self._update_unit_completer(current_combo, text)
            )
        combo._searchable_slot_combo = True

    @staticmethod
    def _update_unit_completer(combo: QComboBox, text: str) -> None:
        completer = combo.completer()
        if completer is None:
            return
        completer.setCompletionPrefix(text)
        if text.strip():
            completer.complete()

    def populate_main_ability_options(self) -> None:
        if not self._abilities_tab_initialized:
            return
        if not hasattr(self.window, "abilityMainAbilityCombo"):
            return
        selected_slot = self.window.abilityMainUnitCombo.currentData()
        if selected_slot is None:
            self.window.abilityMainAbilityCombo.clear()
            return
        selected_unit = self.current_macro["units"][int(selected_slot)]["name"].strip()
        current_text = self.window.abilityMainAbilityCombo.currentText()
        options = list_main_unit_abilities(selected_unit)
        self.window.abilityMainAbilityCombo.blockSignals(True)
        self.window.abilityMainAbilityCombo.clear()
        for display_name, filename in options:
            self.window.abilityMainAbilityCombo.addItem(display_name, filename)
        self.window.abilityMainAbilityCombo.blockSignals(False)

        if options:
            restored_index = self.window.abilityMainAbilityCombo.findText(current_text)
            self.window.abilityMainAbilityCombo.setCurrentIndex(restored_index if restored_index >= 0 else 0)

    def refresh_ability_unit_combo(self) -> None:
        if not self._abilities_tab_initialized:
            return
        if not hasattr(self.window, "abilityMainUnitCombo"):
            return
        previous_slot = self.window.abilityMainUnitCombo.currentData()
        self.window.abilityMainUnitCombo.blockSignals(True)
        self.window.abilityMainUnitCombo.clear()
        for slot in self._selectable_unit_slots():
            name = self.current_macro["units"][slot].get("name", "")
            if slot <= 6:
                label = f"{name} (Unit {slot})" if name else f"Unit {slot}"
            else:
                label = f"{name} (Caloric)" if name else f"Derived Unit {slot}"
            self.window.abilityMainUnitCombo.addItem(label, slot)
        self.window.abilityMainUnitCombo.blockSignals(False)
        if previous_slot is not None:
            restored_index = self.window.abilityMainUnitCombo.findData(previous_slot)
            if restored_index >= 0:
                self.window.abilityMainUnitCombo.setCurrentIndex(restored_index)
                self.populate_main_ability_options()
                return
        if self.window.abilityMainUnitCombo.count() > 0:
            self.window.abilityMainUnitCombo.setCurrentIndex(0)
        self.populate_main_ability_options()

    def _sync_main_ability_auto_state(self, checked: bool) -> None:
        if hasattr(self.window, "abilityMainAbilityCombo"):
            self.window.abilityMainAbilityCombo.setEnabled(not checked)

    def populate_ainz_skill_options(self, element_combo, skill_combo) -> None:
        if not self._abilities_tab_initialized:
            return
        selected_element = element_combo.currentText().strip()
        current_skill = skill_combo.currentText()
        skill_combo.blockSignals(True)
        skill_combo.clear()
        skill_combo.addItem("")
        for skill in ARCANE_SKILLS.get(selected_element, ()):
            skill_combo.addItem(skill)
        if current_skill:
            restored_index = skill_combo.findText(current_skill)
            if restored_index >= 0:
                skill_combo.setCurrentIndex(restored_index)
        skill_combo.blockSignals(False)

    def _init_step_section_buttons(self) -> None:
        self.window.loopStepsSectionButton = QPushButton("LOOP", self.window.advancedCreatePage)
        self.window.loopStepsSectionButton.setGeometry(1207, 514, 123, 28)
        self.window.loopStepsSectionButton.clicked.connect(lambda: self.switch_step_section("loop"))

        self.window.setupStepsSectionButton = QPushButton("SETUP", self.window.advancedCreatePage)
        self.window.setupStepsSectionButton.setGeometry(1338, 514, 124, 28)
        self.window.setupStepsSectionButton.clicked.connect(lambda: self.switch_step_section("setup"))

        for button in (self.window.loopStepsSectionButton, self.window.setupStepsSectionButton):
            button.show()

        self._apply_step_section_button_styles()

    def _style_macro_steps_panel(self) -> None:
        if not hasattr(self, "_macro_steps_panel"):
            self._macro_steps_panel = QFrame(self.window.advancedCreatePage)
            self._macro_steps_panel.setObjectName("macroStepsPanel")
            self._macro_steps_panel.show()

            self._macro_steps_header = QFrame(self._macro_steps_panel)
            self._macro_steps_header.setObjectName("macroStepsHeader")
            self._macro_steps_header.show()

            self._macro_steps_title = QLabel("MACRO STEPS", self._macro_steps_header)
            self._macro_steps_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._macro_steps_title.show()

            self._macro_steps_footer = QFrame(self._macro_steps_panel)
            self._macro_steps_footer.setObjectName("macroStepsFooter")
            self._macro_steps_footer.show()

            self.window.loopStepsSectionButton.setParent(self._macro_steps_header)
            self.window.setupStepsSectionButton.setParent(self._macro_steps_header)
            self.window.advancedStepsScrollArea.setParent(self._macro_steps_panel)
            self.window.advancedSaveButton.setParent(self._macro_steps_footer)
            self.window.advancedClearButton.setParent(self._macro_steps_footer)
            self.window.advBackButton.setParent(self._macro_steps_footer)

        self._macro_steps_panel.setGeometry(1200, 0, 270, 630)
        self._macro_steps_panel.setStyleSheet(
            "QFrame#macroStepsPanel {"
            "background-color: #0c0c0c;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 10px;"
            "}"
        )

        self._macro_steps_header.setGeometry(0, 0, 270, 72)
        self._macro_steps_header.setStyleSheet(
            "QFrame#macroStepsHeader {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: none;"
            "border-bottom: 1px solid rgba(255, 255, 255, 0.08);"
            "border-top-left-radius: 10px;"
            "border-top-right-radius: 10px;"
            "}"
        )
        self._macro_steps_title.setGeometry(12, 10, 180, 16)
        self._macro_steps_title.setStyleSheet(
            "background: transparent; border: none; color: #ffffff; "
            "font-family: 'Space Mono', 'Menlo', monospace; font-size: 10px; "
            "font-weight: 600; letter-spacing: 1.5px;"
        )

        self.window.loopStepsSectionButton.setGeometry(12, 34, 121, 24)
        self.window.setupStepsSectionButton.setGeometry(137, 34, 121, 24)

        self.window.advancedStepsScrollArea.setGeometry(0, 72, 270, 462)
        self.window.advancedStepsScrollArea.setFrameShape(QFrame.NoFrame)
        self.window.advancedStepsScrollArea.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
            "QScrollBar:vertical { background: transparent; width: 0px; margin: 0px; }"
            "QScrollBar::handle:vertical { background: transparent; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        self.window.advancedStepsScrollContent.setStyleSheet("background: transparent;")
        self.advanced_scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.advanced_scroll_layout.setSpacing(6)

        self._macro_steps_footer.setGeometry(0, 534, 270, 96)
        self._macro_steps_footer.setStyleSheet(
            "QFrame#macroStepsFooter {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: none;"
            "border-top: 1px solid rgba(255, 255, 255, 0.08);"
            "border-bottom-left-radius: 10px;"
            "border-bottom-right-radius: 10px;"
            "}"
        )

        self.window.advancedSaveButton.setGeometry(8, 8, 254, 32)
        self.window.advancedSaveButton.setText("SAVE MACRO")
        self.window.advancedSaveButton.setFocusPolicy(Qt.NoFocus)
        self.window.advancedSaveButton.setStyleSheet(
            "QPushButton {"
            "background-color: #10b981;"
            "color: #000000;"
            "border: none;"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            "padding: 0px;"
            "}"
            "QPushButton:hover { background-color: #0ea472; }"
            "QPushButton:pressed { background-color: #0d9668; }"
        )

        secondary_style = (
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: rgba(255, 255, 255, 0.60);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 9px;"
            "font-weight: 600;"
            "letter-spacing: 1px;"
            "padding: 0px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 0.08);"
            "color: #ffffff;"
            "}"
        )
        self.window.advancedClearButton.setGeometry(8, 46, 124, 28)
        self.window.advancedClearButton.setText("CLEAR")
        self.window.advancedClearButton.setFocusPolicy(Qt.NoFocus)
        self.window.advancedClearButton.setStyleSheet(secondary_style)
        self.window.advBackButton.setGeometry(138, 46, 124, 28)
        self.window.advBackButton.setText("BACK")
        self.window.advBackButton.setFocusPolicy(Qt.NoFocus)
        self.window.advBackButton.setStyleSheet(secondary_style)

    def _apply_step_section_button_styles(self) -> None:
        active_section = self.state.editor.step_section
        button_map = {
            "loop": self.window.loopStepsSectionButton,
            "setup": self.window.setupStepsSectionButton,
        }
        for section, button in button_map.items():
            if section == active_section:
                button.setStyleSheet(
                    "QPushButton { background-color: #10b981; color: #000000; border: none; "
                    "border-radius: 4px; font-family: 'Space Mono', 'Menlo', monospace; font-size: 9px; "
                    "font-weight: 600; letter-spacing: 1px; padding: 0px; }"
                    "QPushButton:hover { background-color: #0ea472; }"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background-color: rgba(255, 255, 255, 0.04); color: rgba(255, 255, 255, 0.60); "
                    "border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 4px; "
                    "font-family: 'Space Mono', 'Menlo', monospace; font-size: 9px; "
                    "font-weight: 600; letter-spacing: 1px; padding: 0px; }"
                    "QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); color: #ffffff; }"
                )

    def _get_order_for_section(self, section: str | None = None) -> list[dict]:
        target_section = section or self.state.editor.step_section
        if target_section == "setup":
            return self.current_macro["setup_order"]
        return self.current_macro["order"]

    def _active_order(self) -> list[dict]:
        return self._get_order_for_section()

    def _active_order_key(self) -> str:
        return "setup_order" if self.state.editor.step_section == "setup" else "order"

    def _section_display_name(self, section: str | None = None) -> str:
        return "Setup" if (section or self.state.editor.step_section) == "setup" else "Loop"

    def _clear_step_drag_state(self) -> None:
        self._step_drag_row = None
        self._step_drag_source_index = None
        self._step_drag_start_global = None
        self._step_drag_active = False
        self._step_drag_target_index = None

    def _step_row_style(self, *, dragging: bool = False) -> str:
        if dragging:
            return (
                "QFrame#stepRow {"
                "background-color: rgba(255, 255, 255, 0.08);"
                "border: 1px solid rgba(16, 185, 129, 0.65);"
                "border-radius: 4px;"
                "}"
            )
        return (
            "QFrame#stepRow {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "}"
            "QFrame#stepRow:hover {"
            "background-color: rgba(255, 255, 255, 0.07);"
            "border-color: rgba(255, 255, 255, 0.18);"
            "}"
        )

    def _drop_separator_style(self, *, active: bool = False) -> str:
        if active:
            return (
                "QFrame#stepDropSeparator {"
                "background-color: #10b981;"
                "border: none;"
                "border-radius: 1px;"
                "}"
            )
        return (
            "QFrame#stepDropSeparator {"
            "background-color: rgba(255, 255, 255, 0.08);"
            "border: none;"
            "border-radius: 1px;"
            "}"
        )

    def _add_step_drop_separator(self, drop_index: int) -> None:
        separator = QFrame()
        separator.setObjectName("stepDropSeparator")
        separator.setProperty("drop_index", drop_index)
        separator.setFixedHeight(2)
        separator.setStyleSheet(self._drop_separator_style(active=False))
        separator.setToolTip("Drop step here")
        self._step_drop_separators.append(separator)
        self.advanced_scroll_layout.addWidget(separator)

    def _set_active_drop_separator(self, drop_index: int | None) -> None:
        self._step_drag_target_index = drop_index
        for separator in self._step_drop_separators:
            active = drop_index is not None and separator.property("drop_index") == drop_index
            separator.setFixedHeight(4 if active else 2)
            separator.setStyleSheet(self._drop_separator_style(active=active))

    def _step_row_widgets(self) -> list[QWidget]:
        rows = []
        for index in range(self.advanced_scroll_layout.count()):
            item = self.advanced_scroll_layout.itemAt(index)
            if not item or not item.widget():
                continue
            widget = item.widget()
            if widget.property("step_data") is not None:
                rows.append(widget)
        return rows

    def _event_global_pos(self, event):
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def _drop_index_for_global_pos(self, global_pos) -> int:
        local_pos = self.window.advancedStepsScrollContent.mapFromGlobal(global_pos)
        rows = self._step_row_widgets()
        for index, row in enumerate(rows):
            if local_pos.y() < row.geometry().center().y():
                return index
        return len(rows)

    def _on_step_row_mouse_press(self, row_widget, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        if self.state.editor.editing.active:
            return

        source_index = self._widget_to_order_index(row_widget)
        if source_index is None:
            return
        if self.state.editor.insert.active:
            self.cancel_advanced_insert_mode()

        self._step_drag_row = row_widget
        self._step_drag_source_index = source_index
        self._step_drag_start_global = self._event_global_pos(event)
        self._step_drag_active = False
        self._step_drag_target_index = None
        row_widget.setCursor(Qt.ClosedHandCursor)

    def _on_step_row_mouse_move(self, row_widget, event) -> None:
        if row_widget is not self._step_drag_row or self._step_drag_start_global is None:
            return
        if not (event.buttons() & Qt.LeftButton):
            return

        global_pos = self._event_global_pos(event)
        if not self._step_drag_active:
            if (global_pos - self._step_drag_start_global).manhattanLength() < 6:
                return
            self._step_drag_active = True
            row_widget.setStyleSheet(self._step_row_style(dragging=True))
            self.window.statusbar.showMessage("Drag step to a separator line to reorder")

        self._set_active_drop_separator(self._drop_index_for_global_pos(global_pos))

    def _on_step_row_mouse_release(self, row_widget, event) -> None:
        if row_widget is not self._step_drag_row:
            return

        source_index = self._step_drag_source_index
        drop_index = self._step_drag_target_index
        was_dragging = self._step_drag_active

        row_widget.setCursor(Qt.OpenHandCursor)
        row_widget.setStyleSheet(self._step_row_style(dragging=False))
        self._set_active_drop_separator(None)
        self._clear_step_drag_state()

        if not was_dragging or source_index is None or drop_index is None:
            return

        active_order = self._active_order()
        if move_instruction_to_drop_index(active_order, source_index, drop_index):
            self._rebuild_derived_units()
            self.rebuild_visible_step_rows()
            self._refresh_unit_dependent_controls()
            self.window.statusbar.showMessage(f"Moved {self._section_display_name()} step")
        else:
            self.window.statusbar.showMessage("Step position unchanged")

    def _clear_step_rows_only(self) -> None:
        self._clear_step_drag_state()
        self._step_drop_separators = []
        while self.advanced_scroll_layout.count():
            item = self.advanced_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh_active_wave_counter(self) -> None:
        active_wave_count = sum(1 for instruction in self._active_order() if instruction.get("cmd") == "wait_wave")
        self.state.editor.advanced_wave_counter = active_wave_count

    def _rebuild_derived_units(self) -> None:
        base_units = {slot: self.current_macro["units"].get(slot, {"name": "", "placements": []}) for slot in range(1, 7)}
        self.current_macro["units"] = dict(base_units)

        self.state.unit_data = {
            slot: {"name": self.current_macro["units"][slot].get("name", ""), "x": coords["x"], "y": coords["y"]}
            for slot, coords in UNIT_COORDINATES.items()
        }

        derived_units: dict[str, tuple[int, int]] = {}
        for order_key in ("setup_order", "order"):
            for instruction in self.current_macro.get(order_key, []):
                if instruction.get("cmd") != "ability_ainz_caloric":
                    continue
                target_name = str(instruction.get("target_unit", "")).strip()
                target_x = instruction.get("target_x")
                target_y = instruction.get("target_y")
                if not target_name or target_x is None or target_y is None:
                    continue
                derived_units[target_name] = (int(target_x), int(target_y))

        next_slot = 7
        for target_name, (target_x, target_y) in derived_units.items():
            self.current_macro["units"][next_slot] = {"name": target_name, "placements": [[target_x, target_y]]}
            self.state.unit_data[next_slot] = {"name": target_name, "x": target_x, "y": target_y}
            next_slot += 1

    def _refresh_unit_dependent_controls(self) -> None:
        self.refresh_upgrade_unit_combo()
        self.refresh_place_unit_combo()
        self.refresh_other_unit_combos()
        self.refresh_ability_unit_combo()
        self.refresh_upgrade_placement_combo()

    def _selectable_unit_slots(self) -> list[int]:
        return sorted(self.current_macro["units"].keys())

    def rebuild_visible_step_rows(self) -> None:
        self._clear_step_rows_only()
        active_order = self._active_order()
        for drop_index, instruction in enumerate(active_order):
            self._add_step_drop_separator(drop_index)
            self.add_advanced_step(instruction, announce=False)
        if active_order:
            self._add_step_drop_separator(len(active_order))
        self.renumber_advanced_steps()
        self.refresh_active_wave_counter()

    def _refresh_visible_rows_after_incremental_change(self) -> None:
        self.renumber_advanced_steps()
        self.refresh_active_wave_counter()
        self.refresh_all_step_displays()

    def switch_step_section(self, section: str, *, show_status: bool = True) -> None:
        if section not in {"loop", "setup"}:
            return
        if self.state.editor.editing.active:
            self.cancel_advanced_edit()
        if self.state.editor.insert.active:
            self.cancel_advanced_insert_mode()
        self.state.editor.step_section = section
        self._apply_step_section_button_styles()
        self.rebuild_visible_step_rows()
        if show_status:
            self.window.statusbar.showMessage(f"Showing {self._section_display_name(section)} steps")

    def go_to_advanced_create_from_main_menu(self) -> None:
        selection = self._prompt_main_menu_mode_and_map()
        if selection is None:
            return
        mode, map_name = selection
        self.state.overlay.mode = mode
        self.state.overlay.map_name = map_name
        self.state.advanced_origin = "main_menu"
        self.state.editing_macro_name = None
        self._ensure_advanced_editor_runtime_ui_initialized()
        self.clear_advanced_steps()
        self.refresh_upgrade_unit_combo()
        self.refresh_place_unit_combo()
        self.refresh_ability_unit_combo()
        self.navigation.go_to_page(PAGE_ADVANCED_CREATE)
        self.window.statusbar.showMessage(f"Creating macro for {mode}/{map_name}")

    def back_from_advanced_create(self) -> None:
        self.state.editing_macro_name = None
        if hasattr(self, "_step_nav_hover_timer"):
            self._step_nav_hover_timer.stop()
        if hasattr(self.window, "statusbar"):
            self.window.statusbar.show()
        self.status_controller.set_running(self.state.macro_is_running)
        if self.state.advanced_origin == "main_menu":
            self.navigation.go_to_page(PAGE_MAIN_MENU)
        else:
            self.navigation.go_to_page(PAGE_OVERLAY)

    def start_new_from_overlay(self, mode: str, map_name: str) -> None:
        self.state.overlay.mode = mode
        self.state.overlay.map_name = map_name
        self.state.advanced_origin = "overlay"
        self.state.editing_macro_name = None
        self._ensure_advanced_editor_runtime_ui_initialized()
        self.clear_advanced_steps()
        self.refresh_upgrade_unit_combo()
        self.refresh_place_unit_combo()
        self.refresh_ability_unit_combo()
        self.navigation.go_to_page(PAGE_ADVANCED_CREATE)

    def load_macro_from_path(
        self,
        macro_path: str,
        *,
        mode: str | None = None,
        map_name: str | None = None,
        macro_name: str | None = None,
        origin: str | None = None,
    ) -> bool:
        self._ensure_advanced_editor_runtime_ui_initialized()
        try:
            loaded = macro_json.load_macro(macro_path)
        except Exception as exc:
            self.window.statusbar.showMessage(f"Error loading macro: {exc}")
            return False

        self.state.last_saved_macro_path = macro_path
        self.state.editing_macro_name = macro_name or os.path.splitext(os.path.basename(macro_path))[0]
        self.state.overlay.mode = mode
        self.state.overlay.map_name = map_name
        self.state.advanced_origin = origin or ("overlay" if mode and map_name else "main_menu")

        self.clear_advanced_steps()
        self.current_macro = loaded

        for slot in range(1, 7):
            name = self.current_macro["units"][slot]["name"]
            self.advanced_widgets.unit_inputs[slot].setCurrentText(name)
            self.state.unit_data[slot]["name"] = name
            self.advanced_widgets.unit_saved_labels[slot].setText(name if name else "")

        default_section = "loop" if self.current_macro["order"] or not self.current_macro["setup_order"] else "setup"
        self.state.editor.step_section = default_section
        self._apply_step_section_button_styles()
        self._rebuild_derived_units()
        self.rebuild_visible_step_rows()
        self.update_placement_counter_label()
        self._refresh_unit_dependent_controls()
        self._sync_all_unit_saved_displays()
        self.navigation.go_to_page(PAGE_ADVANCED_CREATE)
        self.window.statusbar.showMessage(f"Editing macro: {self.state.editing_macro_name}")
        return True

    def _prompt_main_menu_mode_and_map(self) -> tuple[str, str] | None:
        mode_options = [
            ("story", "Story"),
            ("raids", "Raids"),
            ("legend", "Legend"),
            ("bossRush", "Boss Rush"),
            ("events", "Events"),
            ("dungeon", "Dungeon"),
        ]
        mode_labels = [label for _, label in mode_options]
        mode_label, ok = QInputDialog.getItem(
            self.window,
            "Select Game Mode",
            "Choose the macro game mode:",
            mode_labels,
            0,
            False,
        )
        if not ok or not mode_label:
            return None

        selected_mode = next((mode for mode, label in mode_options if label == mode_label), None)
        if selected_mode is None:
            return None

        existing_maps = get_maps_for_mode(selected_mode)
        if existing_maps:
            map_name, ok = QInputDialog.getItem(
                self.window,
                "Select Map",
                "Choose or type the map name:",
                existing_maps,
                0,
                True,
            )
        else:
            map_name, ok = QInputDialog.getText(self.window, "Select Map", "Enter the map name:")
        if not ok or not map_name.strip():
            return None

        return selected_mode, map_name.strip()

    def edit_selected_main_menu_macro(self) -> None:
        selected_items = self.window.macroList.selectedItems()
        if not selected_items:
            self.window.statusbar.showMessage("No macro selected!")
            return

        item_data = selected_items[0].data(Qt.UserRole) or {}
        macro_name = item_data.get("macro_name") or selected_items[0].text()
        macro_path = item_data.get("path")
        mode = item_data.get("mode")
        map_name = item_data.get("map_name")
        if not macro_path or not os.path.exists(macro_path):
            self.window.statusbar.showMessage(f"Macro file not found: {macro_name}")
            return

        self.load_macro_from_path(
            macro_path,
            mode=mode,
            map_name=map_name,
            macro_name=macro_name,
            origin="main_menu",
        )

    def parse_step_display(self, instruction: dict):
        return macro_json.format_step_display(instruction, self.current_macro["units"])

    def _populate_step_row_labels(self, row_widget, instruction: dict) -> None:
        type_str, detail_str = self.parse_step_display(instruction)
        type_label = row_widget.findChild(QLabel, "stepTypeLabel")
        detail_label = row_widget.findChild(QLabel, "stepDetailLabel")
        row_widget.setToolTip(detail_str)
        if type_label:
            type_label.setText(type_str)
        if detail_label:
            elided = detail_label.fontMetrics().elidedText(
                detail_str,
                Qt.ElideRight,
                self._STEP_DETAIL_MAX_WIDTH,
            )
            detail_label.setText(elided)
            detail_label.setToolTip(detail_str)

    def save_unit_name(self, unit_num: int) -> None:
        widget = self.advanced_widgets.unit_inputs[unit_num]
        if hasattr(widget, "currentText"):
            name = widget.currentText().strip()
        else:
            name = widget.text().strip()
        self.current_macro["units"][unit_num]["name"] = name
        self.state.unit_data[unit_num]["name"] = name

        if name:
            coords = self.state.unit_data[unit_num]
            self.advanced_widgets.unit_saved_labels[unit_num].setText(name)
            self.window.statusbar.showMessage(f"Unit {unit_num} saved: {name} at ({coords['x']}, {coords['y']})")
        else:
            self.advanced_widgets.unit_saved_labels[unit_num].setText("")
            self.window.statusbar.showMessage(f"Unit {unit_num} name cleared")

        self._sync_unit_saved_display(unit_num)
        self.refresh_all_step_displays()
        self._refresh_unit_dependent_controls()

    def refresh_all_step_displays(self) -> None:
        for index in range(self.advanced_scroll_layout.count()):
            item = self.advanced_scroll_layout.itemAt(index)
            if not item or not item.widget():
                continue
            widget = item.widget()
            instruction = widget.property("step_data")
            if isinstance(instruction, dict):
                self._populate_step_row_labels(widget, instruction)

    def refresh_upgrade_unit_combo(self) -> None:
        previous_slot = self.window.upgradeUnitCombo.currentData()
        self.window.upgradeUnitCombo.clear()
        for slot in self._selectable_unit_slots():
            name = self.current_macro["units"][slot].get("name", "")
            if slot <= 6:
                label = f"{name} (Unit {slot})" if name else f"Unit {slot}"
            else:
                label = f"{name} (Caloric)" if name else f"Derived Unit {slot}"
            self.window.upgradeUnitCombo.addItem(label, slot)
        if previous_slot is not None:
            restored_index = self.window.upgradeUnitCombo.findData(previous_slot)
            if restored_index >= 0:
                self.window.upgradeUnitCombo.setCurrentIndex(restored_index)

    def refresh_place_unit_combo(self) -> None:
        previous_slot = self.window.placeUnitCombo.currentData()
        self.window.placeUnitCombo.clear()
        for i in range(1, 7):
            name = self.state.unit_data[i]["name"]
            self.window.placeUnitCombo.addItem(f"{name} (Unit {i})" if name else f"Unit {i}", i)
        if previous_slot is not None:
            restored_index = self.window.placeUnitCombo.findData(previous_slot)
            if restored_index >= 0:
                self.window.placeUnitCombo.setCurrentIndex(restored_index)
        self.update_placement_counter_label()

    def refresh_other_unit_combos(self) -> None:
        previous_sell_slot = self.window.otherSellUnitCombo.currentData() if hasattr(self.window, "otherSellUnitCombo") else None
        previous_priority_slot = self.window.otherPriorityUnitCombo.currentData() if hasattr(self.window, "otherPriorityUnitCombo") else None
        self.window.otherSellUnitCombo.clear()
        self.window.otherPriorityUnitCombo.clear()
        for slot in self._selectable_unit_slots():
            name = self.current_macro["units"][slot].get("name", "")
            if slot <= 6:
                label = f"{name} (Unit {slot})" if name else f"Unit {slot}"
            else:
                label = f"{name} (Caloric)" if name else f"Derived Unit {slot}"
            self.window.otherSellUnitCombo.addItem(label, slot)
            self.window.otherPriorityUnitCombo.addItem(label, slot)
        if previous_sell_slot is not None:
            restored_index = self.window.otherSellUnitCombo.findData(previous_sell_slot)
            if restored_index >= 0:
                self.window.otherSellUnitCombo.setCurrentIndex(restored_index)
        if previous_priority_slot is not None:
            restored_index = self.window.otherPriorityUnitCombo.findData(previous_priority_slot)
            if restored_index >= 0:
                self.window.otherPriorityUnitCombo.setCurrentIndex(restored_index)

    def refresh_upgrade_placement_combo(self) -> None:
        unit_index = self.window.upgradeUnitCombo.currentData()
        if unit_index is None:
            unit_index = 1
        self.window.upgradePlacementCombo.clear()

        placements = self.current_macro["units"][unit_index]["placements"]
        if not placements:
            self.window.upgradePlacementCombo.addItem("None")
            self.window.upgradeNoPlacementsLabel.setText("")
            return

        self.window.upgradeNoPlacementsLabel.setText("")
        for index, placement in enumerate(placements):
            self.window.upgradePlacementCombo.addItem(f"#{index} ({placement[0]}, {placement[1]})")

    def update_placement_counter_label(self) -> None:
        current_data = getattr(self.window.placeUnitCombo, "currentData", None)
        unit_index = current_data() if callable(current_data) else None
        if unit_index is None:
            current_index = getattr(self.window.placeUnitCombo, "currentIndex", None)
            unit_index = (current_index() + 1) if callable(current_index) else 1
        if unit_index <= 0 or unit_index not in self.current_macro["units"]:
            self.window.placementCounterLabel.setText("0")
            return
        placements = self.current_macro["units"][unit_index]["placements"]
        self.window.placementCounterLabel.setText(str(len(placements)))

    def _layout_pos_to_order_index(self, layout_pos: int) -> int:
        order_idx = 0
        for i in range(min(layout_pos, self.advanced_scroll_layout.count())):
            item = self.advanced_scroll_layout.itemAt(i)
            if item and item.widget() and item.widget().property("step_data") is not None:
                order_idx += 1
        return order_idx

    def _widget_to_order_index(self, target_widget) -> int | None:
        order_idx = 0
        for i in range(self.advanced_scroll_layout.count()):
            item = self.advanced_scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget is target_widget:
                    return order_idx
                if widget.property("step_data") is not None:
                    order_idx += 1
        return None

    def add_advanced_step(self, instruction: dict, insert_at: int | None = None, *, announce: bool = True) -> None:
        row = _DraggableStepRow(self)
        row.setObjectName("stepRow")
        row.setProperty("step_data", instruction)
        row.setAttribute(Qt.WA_Hover, True)
        row.setCursor(Qt.OpenHandCursor)
        row.setFixedHeight(58)
        row.setStyleSheet(self._step_row_style(dragging=False))

        outer_layout = QHBoxLayout(row)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(8)

        badge = QLabel("0")
        badge.setObjectName("stepNumBadge")
        badge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        badge.setFixedSize(20, 20)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "QLabel {"
            "background-color: rgba(255, 255, 255, 0.04);"
            "color: rgba(255, 255, 255, 0.60);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 600;"
            "}"
        )
        outer_layout.addWidget(badge, 0, Qt.AlignVCenter)

        text_widget = QWidget(row)
        text_widget.setObjectName("stepCard")
        text_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_widget.setAttribute(Qt.WA_StyledBackground, True)
        text_widget.setStyleSheet("background: transparent; border: none;")
        text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        type_label = QLabel("")
        type_label.setObjectName("stepTypeLabel")
        type_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        type_label.setStyleSheet(
            "QLabel {"
            "background: transparent; border: none; color: #ffffff;"
            "font-family: 'Space Mono', 'Menlo', monospace; font-size: 11px; font-weight: 500;"
            "}"
        )
        type_label.setContentsMargins(0, 0, 0, 0)
        type_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        type_label.setFixedHeight(16)

        detail_label = QLabel("")
        detail_label.setObjectName("stepDetailLabel")
        detail_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        detail_label.setWordWrap(False)
        detail_label.setStyleSheet(
            "QLabel {"
            "background: transparent; border: none; color: rgba(255, 255, 255, 0.50);"
            "font-family: 'Space Mono', 'Menlo', monospace; font-size: 9px; font-weight: 500;"
            "}"
        )
        detail_label.setContentsMargins(0, 0, 0, 0)
        detail_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        detail_label.setFixedHeight(14)
        detail_label.setFixedWidth(self._STEP_DETAIL_MAX_WIDTH)

        text_layout.addWidget(type_label)
        text_layout.addWidget(detail_label)
        outer_layout.addWidget(text_widget, 1)

        menu_btn = QPushButton("⋮")
        menu_btn.setObjectName("stepMenuButton")
        menu_btn.setFixedSize(20, 20)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setToolTip("Step actions")
        self.apply_step_menu_button_style(menu_btn)
        menu_btn.clicked.connect(lambda: self.show_step_action_menu(row, menu_btn))
        outer_layout.addWidget(menu_btn, 0, Qt.AlignVCenter)

        self._populate_step_row_labels(row, instruction)

        if insert_at is not None:
            self.advanced_scroll_layout.insertWidget(insert_at, row)
            print(f"Inserted advanced step at position {insert_at}: {instruction.get('cmd', '?')}")
        else:
            self.advanced_scroll_layout.addWidget(row)
            print(f"Advanced step added: {instruction.get('cmd', '?')}")

        if announce:
            self.renumber_advanced_steps()
            self.window.statusbar.showMessage(f"Added {self._section_display_name()} step: {instruction.get('cmd', '?')}")

    @staticmethod
    def apply_step_menu_button_style(button: QPushButton, active: bool = False) -> None:
        background = "rgba(16, 185, 129, 0.16)" if active else "transparent"
        color = "#10b981" if active else "rgba(255, 255, 255, 0.40)"
        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {background};"
            f"color: {color};"
            "border: none;"
            "border-radius: 4px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 14px;"
            "font-weight: 600;"
            "padding: 0px;"
            "margin: 0px;"
            "}"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); color: #ffffff; }"
        )

    def show_step_action_menu(self, row_widget, button_widget: QPushButton) -> None:
        order_index = self._widget_to_order_index(row_widget)
        active_order = self._active_order()
        if order_index is None:
            return
        menu = QMenu(self.window)
        menu.setFixedWidth(128)
        menu.setStyleSheet(
            "QMenu {"
            "background-color: #0c0c0c;"
            "color: rgba(255, 255, 255, 0.70);"
            "border: 1px solid rgba(255, 255, 255, 0.12);"
            "border-radius: 10px;"
            "font-family: 'Space Mono', 'Menlo', monospace;"
            "font-size: 10px;"
            "font-weight: 500;"
            "padding: 2px 0px;"
            "}"
            "QMenu::item { padding: 6px 10px 6px 10px; background-color: transparent; }"
            "QMenu::item:selected { background-color: rgba(255, 255, 255, 0.05); color: #ffffff; }"
            "QMenu::separator { height: 1px; background: rgba(255, 255, 255, 0.08); margin: 2px 0px; }"
        )

        edit_action = QAction("Edit Step", menu)
        move_up_action = QAction("Move Up", menu)
        move_down_action = QAction("Move Down", menu)
        delete_action = QAction("Delete Step", menu)
        menu.addAction(edit_action)
        menu.addAction(move_up_action)
        menu.addAction(move_down_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        move_up_action.setEnabled(order_index > 0)
        move_down_action.setEnabled(order_index < len(active_order) - 1)

        popup_pos = button_widget.mapToGlobal(button_widget.rect().bottomRight())
        popup_pos.setX(popup_pos.x() - menu.sizeHint().width())
        selected_action = menu.exec(popup_pos)
        if selected_action is edit_action:
            if self.state.editor.insert.active:
                self.cancel_advanced_insert_mode()
            self.start_advanced_edit_step(row_widget, row_widget.property("step_data"))
        elif selected_action is move_up_action:
            self.move_advanced_step(row_widget, -1)
        elif selected_action is move_down_action:
            self.move_advanced_step(row_widget, 1)
        elif selected_action is delete_action:
            if self.state.editor.insert.active:
                self.cancel_advanced_insert_mode()
            self.remove_advanced_step(row_widget)

    def move_advanced_step(self, row_widget, offset: int) -> None:
        order_index = self._widget_to_order_index(row_widget)
        active_order = self._active_order()
        if order_index is None:
            return
        target_index = order_index + offset
        if target_index < 0 or target_index >= len(active_order):
            return

        active_order[order_index], active_order[target_index] = active_order[target_index], active_order[order_index]
        self._rebuild_derived_units()
        self.rebuild_visible_step_rows()
        self._refresh_unit_dependent_controls()
        self.window.statusbar.showMessage(f"Moved {self._section_display_name()} step")

    def enter_insert_mode_for_row(self, row_widget, button_widget: QPushButton, *, after: bool) -> None:
        row_position = self.advanced_scroll_layout.indexOf(row_widget)
        if row_position < 0:
            return
        position = row_position + (1 if after else 0)
        self.enter_advanced_insert_mode(position, button_widget)

    def renumber_advanced_steps(self) -> None:
        step_num = 1
        for index in range(self.advanced_scroll_layout.count()):
            item = self.advanced_scroll_layout.itemAt(index)
            if not item or not item.widget():
                continue
            widget = item.widget()
            if widget.property("step_data") is None:
                continue
            badge = widget.findChild(QLabel, "stepNumBadge")
            if badge:
                badge.setText(str(step_num))
                step_num += 1
        self.state.editor.advanced_step_counter = step_num - 1

    def remove_advanced_step(self, row_widget) -> None:
        instruction = row_widget.property("step_data")
        if not instruction:
            return

        cmd = instruction.get("cmd") if isinstance(instruction, dict) else ""
        order_index = self._widget_to_order_index(row_widget)
        active_order = self._active_order()
        if order_index is not None and order_index < len(active_order):
            removed = active_order.pop(order_index)
        else:
            removed = instruction

        if cmd == "place":
            slot = removed["slot"]
            placement_index = removed["placement_index"]
            self._remove_invalid_upgrade_steps(slot, placement_index)
            compact_macro_placement(self.current_macro, slot, placement_index)

        self._rebuild_derived_units()
        self.rebuild_visible_step_rows()
        self.update_placement_counter_label()
        self._refresh_unit_dependent_controls()
        print(f"Removed step: {cmd}")

    def _remove_invalid_upgrade_steps(self, slot: int, placement_index: int) -> None:
        removed_count = 0
        for order_key in ("setup_order", "order"):
            order = self.current_macro.get(order_key, [])
            indices = get_invalid_upgrade_order_indices(order, slot, placement_index)
            for order_idx in reversed(indices):
                order.pop(order_idx)
                removed_count += 1
        if removed_count:
            print(f"Auto-removed {removed_count} upgrades for slot {slot} placement #{placement_index}")

    def _reindex_widget_step_data(self, slot: int, removed_index: int) -> None:
        for i in range(self.advanced_scroll_layout.count()):
            item = self.advanced_scroll_layout.itemAt(i)
            if not item or not item.widget():
                continue
            widget = item.widget()
            step_data = widget.property("step_data")
            if (
                isinstance(step_data, dict)
                and step_data.get("slot") == slot
                and step_data.get("cmd") in ("place", "upgrade")
                and step_data["placement_index"] > removed_index
            ):
                step_data["placement_index"] -= 1
                widget.setProperty("step_data", step_data)

    def enter_advanced_insert_mode(self, position: int, button_widget) -> None:
        if self.state.editor.insert.active:
            self.cancel_advanced_insert_mode()

        self.state.editor.insert.active = True
        self.state.editor.insert.position = position
        self.state.editor.insert.separator = button_widget
        self.apply_step_menu_button_style(button_widget, active=True)
        self.window.statusbar.showMessage(f"Insert mode: add a step at position {position}")
        print(f"Advanced insert mode at position {position}")

    def cancel_advanced_insert_mode(self) -> None:
        if not self.state.editor.insert.active:
            return

        separator = self.state.editor.insert.separator
        if separator:
            self.apply_step_menu_button_style(separator)

        self.state.editor.insert.active = False
        self.state.editor.insert.position = None
        self.state.editor.insert.separator = None
        self.window.statusbar.showMessage("Insert cancelled")
        print("Advanced insert mode cancelled")

    def update_group_style(self, group_widget, highlighted: bool) -> None:
        group_widget.setProperty("highlighted", highlighted)
        group_widget.style().unpolish(group_widget)
        group_widget.style().polish(group_widget)

    def switch_advanced_tab(self, tab_name: str, from_edit: bool = False) -> None:
        if self.state.editor.editing.active and not from_edit:
            self.cancel_advanced_edit()
        if tab_name == "abilities":
            self._ensure_advanced_editor_runtime_ui_initialized()

        self.state.editor.current_tab = tab_name
        tab_widgets = {
            "units": [self.window.unitSelectionGroup],
            "place_upgrade": [self.window.placeUpgradeScrollArea],
            "wait": [self.window.advancedWaitGroup],
            "raw": [self.window.advancedClickGroup, self.window.advancedKeyGroup],
            "abilities": [self.window.advancedAbilitiesGroup],
        }
        self.window.tabContentBackground.setVisible(True)

        for name, widgets in tab_widgets.items():
            visible = name == tab_name
            for widget in widgets:
                widget.setVisible(visible)

        self.state.editor.raw_steps_mode = tab_name == "raw"
        if tab_name == "abilities":
            self._style_abilities_section()
        self._style_advanced_tab_header()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(
            settings=self.current_macro["settings"],
            parent=self.window,
        )
        dialog.exec()
        if dialog.saved:
            self.current_macro["settings"] = dialog.get_settings()

    @staticmethod
    def _configured_force_restart_wave(settings: dict) -> int:
        if not settings.get("force_restart_wave_enabled", False):
            return 0
        try:
            wave = int(settings.get("force_restart_wave", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return wave if wave > 0 else 0

    def _execute_force_restart_click_sequence(self, runtime_pyautogui) -> bool:
        self.adv_macro_log("Force restart sequence started.")
        for index, (x, y) in enumerate(FORCE_RESTART_CLICK_SEQUENCE, start=1):
            if self.state.macro_stop_requested:
                self.adv_macro_log("Force restart cancelled before completion.")
                return False
            self.adv_macro_log(f"Force restart click {index}/{len(FORCE_RESTART_CLICK_SEQUENCE)} at ({x}, {y})")
            runtime_pyautogui.moveTo(x, y)
            time.sleep(0.2)
            runtime_pyautogui.click()
            if index < len(FORCE_RESTART_CLICK_SEQUENCE):
                time.sleep(FORCE_RESTART_CLICK_INTERVAL_SECONDS)
        self.adv_macro_log("Force restart sequence completed.")
        return True

    def highlight_advanced_section(self, section_type: str) -> None:
        self.update_group_style(self.window.upgradeGroup, section_type == "upgrade")
        self.update_group_style(self.window.placeGroup, section_type == "place")
        self.update_group_style(self.window.otherGroup, section_type in {"sell", "priority"})
        self.update_group_style(self.window.advancedWaitGroup, section_type == "wait")
        self.update_group_style(self.window.advancedClickGroup, section_type == "click")
        self.update_group_style(self.window.advancedKeyGroup, section_type == "key")
        self.update_group_style(self.window.advancedAbilitiesGroup, section_type.startswith("ability"))

    def reset_advanced_section_highlights(self) -> None:
        self.update_group_style(self.window.upgradeGroup, False)
        self.update_group_style(self.window.placeGroup, False)
        self.update_group_style(self.window.otherGroup, False)
        self.update_group_style(self.window.advancedWaitGroup, False)
        self.update_group_style(self.window.advancedClickGroup, False)
        self.update_group_style(self.window.advancedKeyGroup, False)
        self.update_group_style(self.window.advancedAbilitiesGroup, False)

    def fill_advanced_section_values(self, parsed_data: dict) -> None:
        if parsed_data["type"] == "place":
            unit_idx = parsed_data.get("unit_index", 1)
            combo_index = self.window.placeUnitCombo.findData(unit_idx)
            if combo_index >= 0:
                self.window.placeUnitCombo.setCurrentIndex(combo_index)
            self.window.placeXInput.setText(parsed_data.get("place_x", "0"))
            self.window.placeYInput.setText(parsed_data.get("place_y", "0"))
            self.window.placeUntilEmptyCheckbox.setChecked(parsed_data.get("until_empty", False))
        elif parsed_data["type"] == "upgrade":
            unit_idx = parsed_data.get("unit_index", 1)
            combo_index = self.window.upgradeUnitCombo.findData(unit_idx)
            if combo_index >= 0:
                self.window.upgradeUnitCombo.setCurrentIndex(combo_index)
            self.refresh_upgrade_placement_combo()
            self.window.autoUpgradeCheckBox.setChecked(parsed_data.get("auto_upgrade", False))
            if hasattr(self.window, "maxUpgradeCheckBox"):
                self.window.maxUpgradeCheckBox.setChecked(parsed_data.get("max_upgrade", False))
            if not parsed_data.get("auto_upgrade") and not parsed_data.get("max_upgrade"):
                self.window.upgradeCountInput.setText(parsed_data.get("count", "1"))
            placement_index = parsed_data.get("placement_index", 0)
            for combo_idx in range(self.window.upgradePlacementCombo.count()):
                if f"#{placement_index}" in self.window.upgradePlacementCombo.itemText(combo_idx):
                    self.window.upgradePlacementCombo.setCurrentIndex(combo_idx)
                    break
        elif parsed_data["type"] == "click":
            self.window.advClickXInput.setText(parsed_data.get("x", "0"))
            self.window.advClickYInput.setText(parsed_data.get("y", "0"))
            if parsed_data.get("button", "left") == "right":
                self.window._advClickRightRadio.setChecked(True)
            else:
                self.window._advClickLeftRadio.setChecked(True)
        elif parsed_data["type"] == "key":
            if parsed_data.get("key_type") == "press":
                self.window.advKeyInput.setText(parsed_data.get("key", "t"))
                self.window.advKeyPressRadio.setChecked(True)
                self.window.advKeyTimesInput.setText(parsed_data.get("times", "1"))
            else:
                self.window.advKeyHoldKeyInput.setText(parsed_data.get("key", "t"))
                self.window.advKeyHoldRadio.setChecked(True)
                self.window.advKeyHoldInput.setText(parsed_data.get("duration", "1.0"))
        elif parsed_data["type"] == "wait":
            wait_type = parsed_data.get("wait_type", "seconds")
            if wait_type == "seconds":
                self.window.advancedWaitSecondsRadio.setChecked(True)
                self.window.advancedWaitSecondsInput.setText(parsed_data.get("seconds", "1.0"))
            elif wait_type == "round":
                self.window.advancedWaitRoundRadio.setChecked(True)
                self.window.advancedWaveInput.setText(parsed_data.get("wave", ""))
            elif wait_type == "game":
                self.window.advancedWaitGameRadio.setChecked(True)
            elif wait_type == "yen":
                self.window.advancedWaitYenRadio.setChecked(True)
                self.window.advancedWaitYenInput.setText(parsed_data.get("yen_amount", "0"))
            self._sync_wait_mode_proxies()
        elif parsed_data["type"] == "ability_main":
            target_slot = parsed_data.get("slot", 1)
            combo_index = self.window.abilityMainUnitCombo.findData(target_slot)
            if combo_index >= 0:
                self.window.abilityMainUnitCombo.setCurrentIndex(combo_index)
            self.populate_main_ability_options()
            self.window.abilityMainAutoCheck.setChecked(parsed_data.get("auto", False))
            if parsed_data.get("ability"):
                self.window.abilityMainAbilityCombo.setCurrentText(parsed_data["ability"])
        elif parsed_data["type"] == "ability_skele_king":
            if hasattr(self.window, "_abilitySkeleCombo"):
                self.window._abilitySkeleCombo.setCurrentText(SKELE_STRINGS_LABEL)
        elif parsed_data["type"] == "ability_ainz_arcane":
            self._reset_ainz_arcane_rows()
            for index, row in enumerate(parsed_data.get("sequence", [])):
                if index >= len(self.window.ainzArcaneRows):
                    break
                element_combo, skill_combo = self.window.ainzArcaneRows[index]
                element_combo.setCurrentText(row.get("element", ""))
                self.populate_ainz_skill_options(element_combo, skill_combo)
                skill_combo.setCurrentText(row.get("skill", ""))
        elif parsed_data["type"] == "ability_ainz_caloric":
            self.window.ainzCaloricUnitInput.setCurrentText(parsed_data.get("target_unit", ""))
            if parsed_data.get("target_x") and parsed_data.get("target_y"):
                self.window.ainzCaloricLocationInput.setText(
                    f"{parsed_data.get('target_x')}, {parsed_data.get('target_y')}"
                )
        elif parsed_data["type"] == "sell":
            combo_index = self.window.otherSellUnitCombo.findData(parsed_data.get("unit_index", 1))
            if combo_index >= 0:
                self.window.otherSellUnitCombo.setCurrentIndex(combo_index)
        elif parsed_data["type"] == "priority":
            combo_index = self.window.otherPriorityUnitCombo.findData(parsed_data.get("unit_index", 1))
            if combo_index >= 0:
                self.window.otherPriorityUnitCombo.setCurrentIndex(combo_index)
            priority_index = self.window.otherPriorityChoiceCombo.findText(parsed_data.get("priority", "First"))
            if priority_index >= 0:
                self.window.otherPriorityChoiceCombo.setCurrentIndex(priority_index)

    def start_advanced_edit_step(self, row_widget, instruction: dict) -> None:
        if self.state.editor.editing.active:
            self.cancel_advanced_edit()

        self.state.editor.editing.active = True
        self.state.editor.editing.row = row_widget
        self.state.editor.editing.original_data = instruction

        parsed = parse_advanced_step_data(instruction, self.current_macro)
        self.state.editor.editing.step_type = parsed["type"]

        if parsed["type"] in ("click", "key"):
            self.switch_advanced_tab("raw", from_edit=True)
        elif parsed["type"] in ("upgrade", "place", "sell", "priority"):
            self.switch_advanced_tab("place_upgrade", from_edit=True)
        elif parsed["type"] == "wait":
            self.switch_advanced_tab("wait", from_edit=True)
        elif parsed["type"].startswith("ability"):
            self.switch_advanced_tab("abilities", from_edit=True)

        self.highlight_advanced_section(parsed["type"])
        self.fill_advanced_section_values(parsed)

        if parsed["type"] == "upgrade":
            self.window.addUpgradeStepButton.setText("Save Changes")
        elif parsed["type"] == "place":
            self.window.addPlaceStepButton.setText("Save Changes")
        elif parsed["type"] == "sell":
            self.window.otherSellAddButton.setText("Save Changes")
        elif parsed["type"] == "priority":
            self.window.otherPriorityAddButton.setText("Save Changes")
        elif parsed["type"] == "wait":
            self.window.addAdvancedWaitButton.setText("Save Changes")
        elif parsed["type"] == "click":
            self.window.addAdvancedClickButton.setText("Save Changes")
        elif parsed["type"] == "key":
            self.window.addAdvancedKeyButton.setText("Save Changes")
        elif parsed["type"] == "ability_main":
            self.window.abilityMainAddButton.setText("Save Changes")
        elif parsed["type"] == "ability_skele_king":
            self.window.abilitySkeleAddButton.setText("Save Changes")
        elif parsed["type"] == "ability_ainz_arcane":
            self.window.ainzArcaneAddButton.setText("Save Changes")
        elif parsed["type"] == "ability_ainz_caloric":
            self.window.ainzCaloricAddButton.setText("Save Changes")

        self.window.statusbar.showMessage("Editing step - modify values and click Save Changes")

    def _reset_action_button_texts(self) -> None:
        self.window.addUpgradeStepButton.setText(self.state.editor.original_button_texts["upgrade"])
        self.window.addPlaceStepButton.setText(self.state.editor.original_button_texts["place"])
        self.window.otherSellAddButton.setText(self.state.editor.original_button_texts["sell"])
        self.window.otherPriorityAddButton.setText(self.state.editor.original_button_texts["priority"])
        self.window.addAdvancedWaitButton.setText(self.state.editor.original_button_texts["wait"])
        self.window.addAdvancedClickButton.setText(self.state.editor.original_button_texts["click"])
        self.window.addAdvancedKeyButton.setText(self.state.editor.original_button_texts["key"])
        if self._abilities_tab_initialized:
            self.window.abilityMainAddButton.setText(self.state.editor.original_button_texts["ability_main"])
            self.window.abilitySkeleAddButton.setText(self.state.editor.original_button_texts["ability_skele_king"])
            self.window.ainzArcaneAddButton.setText(self.state.editor.original_button_texts["ability_ainz_arcane"])
            self.window.ainzCaloricAddButton.setText(self.state.editor.original_button_texts["ability_ainz_caloric"])

    def _reset_ainz_arcane_rows(self) -> None:
        if not self._abilities_tab_initialized:
            return
        for element_combo, skill_combo in self.window.ainzArcaneRows:
            element_combo.setCurrentIndex(0)
            skill_combo.clear()
            skill_combo.addItem("")

    def _reset_ability_inputs(self) -> None:
        if not self._abilities_tab_initialized:
            return
        if self.window.abilityMainUnitCombo.count() > 0:
            self.window.abilityMainUnitCombo.setCurrentIndex(0)
        self.populate_main_ability_options()
        self.window.abilityMainAutoCheck.setChecked(False)
        if hasattr(self.window, "_abilitySkeleCombo"):
            self.window._abilitySkeleCombo.setCurrentIndex(0)
        self.window.ainzCaloricUnitInput.setCurrentText("")
        self.window.ainzCaloricLocationInput.clear()
        self.window.ainzCaloricRecordButton.setText("Record")
        self.window.ainzCaloricRecordButton.setEnabled(True)
        if hasattr(self.window, "maxUpgradeCheckBox"):
            self.window.maxUpgradeCheckBox.setChecked(False)
        self._reset_ainz_arcane_rows()

    def cancel_advanced_edit(self) -> None:
        if not self.state.editor.editing.active:
            return

        self._reset_action_button_texts()

        self.window.upgradeCountInput.clear()
        self.window.placeXInput.clear()
        self.window.placeYInput.clear()
        self.window.placeUntilEmptyCheckbox.setChecked(False)
        if self.window.otherSellUnitCombo.count() > 0:
            self.window.otherSellUnitCombo.setCurrentIndex(0)
        if self.window.otherPriorityUnitCombo.count() > 0:
            self.window.otherPriorityUnitCombo.setCurrentIndex(0)
        self.window.otherPriorityChoiceCombo.setCurrentText("First")
        self.window.advancedWaitSecondsInput.clear()
        self.window.advancedWaitYenInput.clear()
        self.window.advClickXInput.clear()
        self.window.advClickYInput.clear()
        self.window.advKeyInput.clear()
        self.window.advKeyTimesInput.clear()
        self.window.advKeyHoldInput.clear()
        self.window.advKeyHoldKeyInput.clear()
        self._reset_ability_inputs()

        self.reset_advanced_section_highlights()
        self.state.editor.editing.active = False
        self.state.editor.editing.row = None
        self.state.editor.editing.step_type = None
        self.state.editor.editing.original_data = None
        self.window.statusbar.showMessage("Edit cancelled")

    def _finalize_advanced_edit(self, new_instruction: dict, *, rebuild_rows: bool = False) -> bool:
        if not self.state.editor.editing.active or not self.state.editor.editing.row:
            return False

        row_widget = self.state.editor.editing.row
        old_instruction = self.state.editor.editing.original_data
        row_widget.setProperty("step_data", new_instruction)

        row_index = self._widget_to_order_index(row_widget)
        active_order = self._active_order()
        if row_index is not None and row_index < len(active_order):
            active_order[row_index] = new_instruction
        self._rebuild_derived_units()

        old_is_wave = isinstance(old_instruction, dict) and old_instruction.get("cmd") == "wait_wave"
        new_is_wave = new_instruction.get("cmd") == "wait_wave"
        if old_is_wave and not new_is_wave:
            self.update_advanced_wave_counter(-1)
        elif not old_is_wave and new_is_wave:
            self.update_advanced_wave_counter(1)

        print(
            "Updated step: "
            f"{old_instruction.get('cmd') if isinstance(old_instruction, dict) else '?'} -> {new_instruction.get('cmd')}"
        )

        self._reset_action_button_texts()
        self._reset_ability_inputs()
        self.reset_advanced_section_highlights()

        self.state.editor.editing.active = False
        self.state.editor.editing.row = None
        self.state.editor.editing.step_type = None
        self.state.editor.editing.original_data = None
        if rebuild_rows:
            self.rebuild_visible_step_rows()
        else:
            self.refresh_all_step_displays()
            self.refresh_active_wave_counter()
        self._refresh_unit_dependent_controls()
        self.window.statusbar.showMessage("Step updated")
        return True

    def save_advanced_edit(self, new_instruction: dict) -> bool:
        return self._finalize_advanced_edit(new_instruction)

    def clear_advanced_steps(self) -> None:
        if self.state.editor.editing.active:
            self.cancel_advanced_edit()
        if self.state.editor.insert.active:
            self.cancel_advanced_insert_mode()
        self.current_macro = macro_json.create_empty_macro()
        self._rebuild_derived_units()
        self.state.editor.step_section = "loop"
        self._apply_step_section_button_styles()
        self._clear_step_rows_only()
        self.state.editor.advanced_step_counter = 0
        self.state.editor.advanced_wave_counter = 0
        self.update_placement_counter_label()
        self.refresh_upgrade_placement_combo()
        self.window.advancedWaveInput.setText("0")
        self.window.placeUntilEmptyCheckbox.setChecked(False)
        self.window.advancedWaitSecondsRadio.setChecked(True)
        self.window.advancedWaitSecondsInput.clear()
        self.window.advancedWaitYenInput.clear()
        self.window.advancedWaveInput.clear()
        self._sync_wait_mode_proxies()
        self.window.advClickXInput.clear()
        self.window.advClickYInput.clear()
        self.window.advKeyInput.clear()
        self.window.advKeyTimesInput.clear()
        self.window.advKeyHoldInput.clear()
        self.window.advKeyHoldKeyInput.clear()
        self._reset_action_button_texts()
        self._reset_ability_inputs()
        self.switch_advanced_tab("units")
        self.rebuild_visible_step_rows()
        self._refresh_unit_dependent_controls()
        self.window.statusbar.showMessage("Cleared all advanced steps")

    def save_advanced_macro(self) -> None:
        if not self.current_macro["order"] and not self.current_macro["setup_order"]:
            self.window.statusbar.showMessage("No steps to save!")
            return

        for slot, input_widget in self.advanced_widgets.unit_inputs.items():
            if hasattr(input_widget, "currentText"):
                self.current_macro["units"][slot]["name"] = input_widget.currentText().strip()
            else:
                self.current_macro["units"][slot]["name"] = input_widget.text().strip()

        default_name = self.state.editing_macro_name if self.state.editing_macro_name else ""
        name, ok = QInputDialog.getText(self.window, "Save Macro", "Enter macro name:", text=default_name)
        if not ok or not name.strip():
            return

        try:
            macro_path = build_macro_save_path(name.strip(), self.state.overlay.mode, self.state.overlay.map_name)
        except ValueError as exc:
            self.window.statusbar.showMessage(str(exc))
            return
        macro_json.save_macro(self.current_macro, macro_path)
        self.state.last_saved_macro_path = macro_path
        self._invalidate_saved_macro_runtime_cache()

        if self.state.overlay.mode and self.state.overlay.map_name:
            self.window.statusbar.showMessage(
                f"Macro '{name.strip()}' saved to {self.state.overlay.mode}/{self.state.overlay.map_name}!"
            )
            print(f"Saved macro to {macro_path}")
            if self.overlay_controller:
                self.overlay_controller.refresh_overlay_macro_combo(self.state.overlay.mode)
            if self.state.advanced_origin == "main_menu" and self.main_menu_controller:
                self.main_menu_controller.refresh_macro_list()
        else:
            self.window.statusbar.showMessage(f"Saved macro: {name}")
            print(f"Saved macro to {macro_path}")
            if self.main_menu_controller:
                self.main_menu_controller.refresh_macro_list()

    def update_advanced_wave_counter(self, delta: int) -> None:
        self.state.editor.advanced_wave_counter = max(0, self.state.editor.advanced_wave_counter + delta)

    def _append_instruction(self, instruction: dict) -> None:
        if self.state.editor.editing.active:
            self.save_advanced_edit(instruction)
            return

        if self.state.editor.insert.active:
            position = self.state.editor.insert.position
            self.cancel_advanced_insert_mode()
            order_index = self._layout_pos_to_order_index(position)
            self._active_order().insert(order_index, instruction)
            self._rebuild_derived_units()
            self.rebuild_visible_step_rows()
            self._refresh_unit_dependent_controls()
            self.window.statusbar.showMessage(f"Added {self._section_display_name()} step: {instruction.get('cmd', '?')}")
            return

        self._active_order().append(instruction)
        self._rebuild_derived_units()
        self.rebuild_visible_step_rows()
        self._refresh_unit_dependent_controls()
        self.window.statusbar.showMessage(f"Added {self._section_display_name()} step: {instruction.get('cmd', '?')}")

    def add_upgrade_step(self) -> None:
        unit_index = self.window.upgradeUnitCombo.currentData()
        if unit_index is None:
            unit_index = 1
        auto_upgrade = self.window.autoUpgradeCheckBox.isChecked()
        max_upgrade = self.window.maxUpgradeCheckBox.isChecked() if hasattr(self.window, "maxUpgradeCheckBox") else False
        combo_text = self.window.upgradePlacementCombo.currentText()
        if not combo_text or combo_text == "None":
            self.window.statusbar.showMessage("Error: No placements found for this unit")
            return
        idx_match = re.search(r"#(\d+)", combo_text)
        if not idx_match:
            return

        instruction = {
            "cmd": "upgrade",
            "slot": int(unit_index),
            "placement_index": int(idx_match.group(1)),
            "mode": "max" if max_upgrade else ("auto" if auto_upgrade else "manual"),
        }
        if not auto_upgrade and not max_upgrade:
            instruction["count"] = int(self.window.upgradeCountInput.text().strip() or "1")

        if self.state.editor.editing.active and self.state.editor.editing.step_type != "upgrade":
            return
        self._append_instruction(instruction)
        self.window.upgradeNoPlacementsLabel.setText("")

    def add_advanced_wait_step(self) -> None:
        if self.window.advancedWaitSecondsRadio.isChecked():
            instruction = {"cmd": "wait_seconds", "seconds": float(self.window.advancedWaitSecondsInput.text().strip() or "1.0")}
        elif self.window.advancedWaitRoundRadio.isChecked():
            wave_text = self.window.advancedWaveInput.text().strip()
            if not wave_text:
                self.window.statusbar.showMessage("Please enter a round number")
                return
            try:
                wave_val = int(wave_text)
            except ValueError:
                self.window.statusbar.showMessage("Round number must be a whole number")
                return
            if wave_val <= 0:
                self.window.statusbar.showMessage("Round number must be greater than 0")
                return
            instruction = {"cmd": "wait_wave", "wave": wave_val}
        elif self.window.advancedWaitGameRadio.isChecked():
            instruction = {"cmd": "wait_start"}
        elif self.window.advancedWaitYenRadio.isChecked():
            yen_text = self.window.advancedWaitYenInput.text().strip()
            if not yen_text:
                self.window.statusbar.showMessage("Please enter a yen amount")
                return
            try:
                yen_amount = int(yen_text)
            except ValueError:
                self.window.statusbar.showMessage("Yen amount must be a whole number")
                return
            if yen_amount <= 0:
                self.window.statusbar.showMessage("Yen amount must be greater than 0")
                return
            instruction = {"cmd": "wait_yen", "amount": yen_amount}
        else:
            return

        if self.state.editor.editing.active and self.state.editor.editing.step_type != "wait":
            return
        self._append_instruction(instruction)
        self.window.advancedWaitSecondsInput.clear()
        self.window.advancedWaitYenInput.clear()
        if instruction.get("cmd") == "wait_wave":
            self.window.advancedWaveInput.clear()

    def add_place_step(self) -> None:
        current_data = getattr(self.window.placeUnitCombo, "currentData", None)
        unit_index = current_data() if callable(current_data) else None
        if unit_index is None:
            current_index = getattr(self.window.placeUnitCombo, "currentIndex", None)
            unit_index = (current_index() + 1) if callable(current_index) else 1
        place_x = int(self.window.placeXInput.text().strip() or "0")
        place_y = int(self.window.placeYInput.text().strip() or "0")
        until_empty = self.window.placeUntilEmptyCheckbox.isChecked()

        if self.state.editor.editing.active and self.state.editor.editing.step_type == "place":
            row_widget = self.state.editor.editing.row
            order_index = self._widget_to_order_index(row_widget) if row_widget is not None else None
            if order_index is None:
                self.window.statusbar.showMessage("Unable to update place step")
                return
            new_instruction = retarget_place_instruction(
                self.current_macro,
                order_key=self._active_order_key(),
                order_index=order_index,
                new_slot=unit_index,
                new_x=place_x,
                new_y=place_y,
                until_empty=until_empty,
            )
            self._finalize_advanced_edit(new_instruction, rebuild_rows=True)
        else:
            placements = self.current_macro["units"][unit_index]["placements"]
            new_index = len(placements)
            placements.append([place_x, place_y])
            instruction = {"cmd": "place", "slot": unit_index, "placement_index": new_index}
            if until_empty:
                instruction["until_empty"] = True
            self._append_instruction(instruction)
            self.window.placeUntilEmptyCheckbox.setChecked(False)

        self.update_placement_counter_label()
        self.refresh_upgrade_placement_combo()

    def add_sell_step(self) -> None:
        unit_index = self.window.otherSellUnitCombo.currentData()
        if unit_index is None:
            unit_index = 1
        instruction = {"cmd": "sell", "slot": int(unit_index)}
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "sell":
            return
        self._append_instruction(instruction)

    def add_priority_step(self) -> None:
        unit_index = self.window.otherPriorityUnitCombo.currentData()
        if unit_index is None:
            unit_index = 1
        instruction = {
            "cmd": "priority",
            "slot": int(unit_index),
            "priority": self.window.otherPriorityChoiceCombo.currentText().strip() or "First",
        }
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "priority":
            return
        self._append_instruction(instruction)

    def add_advanced_click_step(self) -> None:
        instruction = {
            "cmd": "click",
            "x": int(self.window.advClickXInput.text().strip() or "0"),
            "y": int(self.window.advClickYInput.text().strip() or "0"),
            "button": "right" if self.window._advClickRightRadio.isChecked() else "left",
        }
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "click":
            return
        self._append_instruction(instruction)
        self.window.advClickXInput.clear()
        self.window.advClickYInput.clear()
        self.window._advClickLeftRadio.setChecked(True)

    def add_advanced_key_step(self) -> None:
        if self.window.advKeyPressRadio.isChecked():
            instruction = {
                "cmd": "key_press",
                "key": self.window.advKeyInput.text().strip() or "t",
                "times": int(self.window.advKeyTimesInput.text().strip() or "1"),
            }
        elif self.window.advKeyHoldRadio.isChecked():
            instruction = {
                "cmd": "key_hold",
                "key": self.window.advKeyHoldKeyInput.text().strip() or "t",
                "seconds": float(self.window.advKeyHoldInput.text().strip() or "1.0"),
            }
        else:
            return

        if self.state.editor.editing.active and self.state.editor.editing.step_type != "key":
            return
        self._append_instruction(instruction)
        self.window.advKeyInput.clear()
        self.window.advKeyTimesInput.clear()
        self.window.advKeyHoldInput.clear()
        self.window.advKeyHoldKeyInput.clear()

    def add_main_ability_step(self) -> None:
        unit_slot = self.window.abilityMainUnitCombo.currentData()
        if unit_slot is None:
            self.window.statusbar.showMessage("Save a unit name first")
            return
        unit_slot = int(unit_slot)
        unit_name = self.current_macro["units"][unit_slot]["name"].strip()
        if not unit_name:
            self.window.statusbar.showMessage("Save a unit name first")
            return
        auto_enabled = self.window.abilityMainAutoCheck.isChecked()
        ability_text = self.window.abilityMainAbilityCombo.currentText().strip()
        ability_file = self.window.abilityMainAbilityCombo.currentData()

        if not auto_enabled and (not ability_text or not ability_file):
            self.window.statusbar.showMessage("Select an ability first")
            return

        instruction = {
            "cmd": "ability_main",
            "slot": unit_slot,
            "unit": unit_name,
            "auto": auto_enabled,
        }
        if not auto_enabled:
            instruction["ability"] = ability_text
            instruction["ability_file"] = ability_file

        if self.state.editor.editing.active and self.state.editor.editing.step_type != "ability_main":
            return
        self._append_instruction(instruction)
        self._reset_ability_inputs()

    def add_skele_king_ability_step(self) -> None:
        if hasattr(self.window, "_abilitySkeleCombo") and self.window._abilitySkeleCombo.currentText().strip() != SKELE_STRINGS_LABEL:
            self.window.statusbar.showMessage("Select an ability first")
            return
        instruction = {"cmd": "ability_skele_king"}
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "ability_skele_king":
            return
        self._append_instruction(instruction)

    def add_ainz_arcane_step(self) -> None:
        sequence = []
        for element_combo, skill_combo in self.window.ainzArcaneRows:
            element = element_combo.currentText().strip()
            skill = skill_combo.currentText().strip()
            if not element and not skill:
                continue
            if not element or not skill:
                self.window.statusbar.showMessage("Each Ainz row needs both Element and Skill")
                return
            sequence.append({"element": element, "skill": skill})

        if not sequence:
            self.window.statusbar.showMessage("Add at least one Ainz element/skill row")
            return

        instruction = {"cmd": "ability_ainz_arcane", "sequence": sequence}
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "ability_ainz_arcane":
            return
        self._append_instruction(instruction)
        self._reset_ainz_arcane_rows()

    def add_ainz_caloric_step(self) -> None:
        target_unit = self.window.ainzCaloricUnitInput.currentText().strip()
        if not target_unit:
            self.window.statusbar.showMessage("Enter a unit name for Caloric Stone")
            return

        location_text = self.window.ainzCaloricLocationInput.text().strip()
        if not location_text:
            self.window.statusbar.showMessage("Record or enter a location for Caloric Stone")
            return
        try:
            target_x_str, target_y_str = [part.strip() for part in location_text.split(",", 1)]
            target_x = int(target_x_str)
            target_y = int(target_y_str)
        except (ValueError, IndexError):
            self.window.statusbar.showMessage("Location must be in 'X, Y' format")
            return

        instruction = {"cmd": "ability_ainz_caloric", "target_unit": target_unit, "target_x": target_x, "target_y": target_y}
        if self.state.editor.editing.active and self.state.editor.editing.step_type != "ability_ainz_caloric":
            return
        self._append_instruction(instruction)
        self.window.ainzCaloricUnitInput.setCurrentText("")
        self.window.ainzCaloricLocationInput.clear()
        self.window.ainzCaloricRecordButton.setText("Record")

    def check_for_recorded_place_coords(self) -> None:
        recording = self.state.editor.recording_place_click
        if recording.coords is None:
            return

        x, y = self._recorded_point_to_macro_coordinates(*recording.coords)
        if recording.target == "ainz_caloric":
            self.window.ainzCaloricLocationInput.setText(f"{x}, {y}")
            self.window.ainzCaloricRecordButton.setText("Record")
            self.window.ainzCaloricRecordButton.setEnabled(True)
            self.window.statusbar.showMessage(f"Recorded Caloric Stone location ({x}, {y})")
        else:
            self.window.placeXInput.setText(str(x))
            self.window.placeYInput.setText(str(y))
            self.window.recordPlaceClickButton.setText(RECORD_PLACE_CLICK_TEXT)
            self.window.recordPlaceClickButton.setEnabled(True)
            self.window.statusbar.showMessage(f"Recorded place coordinates ({x}, {y})")
        if not self.state.editor.frameless_active:
            self.window.showNormal()
        self.window.activateWindow()
        recording.coords = None
        recording.target = "place"
        if recording.timer:
            recording.timer.stop()

    def record_place_click(self) -> None:
        from pynput import mouse as pynput_mouse

        recording = self.state.editor.recording_place_click
        if recording.active:
            return
        recording.active = True
        recording.coords = None
        recording.target = "place"
        self.window.recordPlaceClickButton.setText("Click anywhere...")
        self.window.recordPlaceClickButton.setEnabled(False)
        self.window.statusbar.showMessage("Click anywhere on screen to record place coordinates...")
        print("Place recording started - click anywhere...")

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                print(f"Place click detected at ({x}, {y})")
                recording.coords = (int(x), int(y))
                recording.active = False
                return False
            return None

        recording.listener = pynput_mouse.Listener(on_click=on_click)
        recording.listener.start()
        recording.timer = QTimer()
        recording.timer.timeout.connect(self.check_for_recorded_place_coords)
        recording.timer.start(100)

    def record_ainz_caloric_location(self) -> None:
        from pynput import mouse as pynput_mouse

        recording = self.state.editor.recording_place_click
        if recording.active:
            return
        recording.active = True
        recording.coords = None
        recording.target = "ainz_caloric"
        self.window.ainzCaloricRecordButton.setText("Click anywhere...")
        self.window.ainzCaloricRecordButton.setEnabled(False)
        self.window.statusbar.showMessage("Click anywhere on screen to record Caloric Stone location...")
        print("Caloric Stone location recording started - click anywhere...")

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                print(f"Caloric Stone location detected at ({x}, {y})")
                recording.coords = (int(x), int(y))
                recording.active = False
                return False
            return None

        recording.listener = pynput_mouse.Listener(on_click=on_click)
        recording.listener.start()
        recording.timer = QTimer()
        recording.timer.timeout.connect(self.check_for_recorded_place_coords)
        recording.timer.start(100)

    def check_for_recorded_adv_click_coords(self) -> None:
        recording = self.state.editor.recording_adv_click
        if recording.coords is None:
            return

        x, y = self._recorded_point_to_macro_coordinates(*recording.coords)
        self.window.advClickXInput.setText(str(x))
        self.window.advClickYInput.setText(str(y))
        self.window.advRecordClickButton.setText("⌖  Record")
        self.window.advRecordClickButton.setEnabled(True)
        self.window.statusbar.showMessage(f"Recorded click coordinates ({x}, {y})")
        if not self.state.editor.frameless_active:
            self.window.showNormal()
        self.window.activateWindow()
        recording.coords = None
        if recording.timer:
            recording.timer.stop()

    def _recorded_point_to_macro_coordinates(self, x: int, y: int) -> tuple[int, int]:
        settings = self.current_macro.get("settings", {})
        if not settings.get("relative_positioning", False):
            return int(x), int(y)
        try:
            return RelativePositioner(cache_ttl_seconds=0.0).translate_point_back_to_base(
                int(x),
                int(y),
            )
        except RelativePositioningError as exc:
            self.window.statusbar.showMessage(str(exc))
            return int(x), int(y)

    def record_advanced_click(self) -> None:
        from pynput import mouse as pynput_mouse

        recording = self.state.editor.recording_adv_click
        if recording.active:
            return
        recording.active = True
        recording.coords = None
        self.window.advRecordClickButton.setText("Click anywhere...")
        self.window.advRecordClickButton.setEnabled(False)
        self.window.statusbar.showMessage("Click anywhere on screen to record click coordinates...")
        print("Advanced click recording started - click anywhere...")

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                print(f"Advanced click detected at ({x}, {y})")
                recording.coords = (int(x), int(y))
                recording.active = False
                return False
            return None

        recording.listener = pynput_mouse.Listener(on_click=on_click)
        recording.listener.start()
        recording.timer = QTimer()
        recording.timer.timeout.connect(self.check_for_recorded_adv_click_coords)
        recording.timer.start(100)

    def adv_macro_log(self, msg: str) -> None:
        self.state.editor.adv_log_queue.append((time.strftime("%H:%M:%S"), msg))
        self.run_logger.log(msg)

    def _invalidate_saved_macro_runtime_cache(self) -> None:
        self._saved_macro_runtime_cache = None

    def _load_saved_macro_for_run(self, macro_path: str) -> dict:
        stat_result = os.stat(macro_path)
        cache = self._saved_macro_runtime_cache
        if (
            cache is not None
            and cache.get("path") == macro_path
            and cache.get("mtime_ns") == stat_result.st_mtime_ns
            and cache.get("size") == stat_result.st_size
        ):
            return copy.deepcopy(cache["macro"])

        loaded_macro = macro_json.load_macro(macro_path)
        self._saved_macro_runtime_cache = {
            "path": macro_path,
            "mtime_ns": stat_result.st_mtime_ns,
            "size": stat_result.st_size,
            "macro": loaded_macro,
        }
        return copy.deepcopy(loaded_macro)

    @staticmethod
    def _macro_contains_skele_strings_step(macro_data: dict) -> bool:
        for order_key in ("setup_order", "order"):
            for instruction in macro_data.get(order_key, []):
                if instruction.get("cmd") == "ability_skele_king":
                    return True
        return False

    def detect_match_result(self, *, pyautogui_module=None) -> MatchResultDetection:
        self.adv_macro_log("Scanning match result...")
        try:
            result = self.match_result_detector.detect_screen_result(pyautogui_module=pyautogui_module)
        except RelativePositioningError:
            raise
        except Exception as exc:
            self.adv_macro_log(f"Match result scan failed: {exc}")
            return MatchResultDetection("UNKNOWN", 0.0, 0, 0, 0, 0)

        self.adv_macro_log(f"Match Result: {result.label} (conf={result.confidence:.3f})")
        return result

    def parse_and_store_rewards(self, mode: str, map_name: str) -> dict[str, int]:
        self.adv_macro_log("Scanning rewards...")
        try:
            result = self.reward_detector.parse_screen_rewards(mode, map_name)
        except RelativePositioningError:
            raise
        except Exception as exc:
            self.adv_macro_log(f"Reward scan failed: {exc}")
            self.state.session_webhook.last_run_rewards = {}
            return {}

        self.log_reward_parse_result(result)
        if not result.ok:
            self.state.session_webhook.last_run_rewards = {}
            return {}

        self.state.session_webhook.last_run_rewards = dict(result.rewards)
        if result.rewards:
            self.reward_stats_store.add_rewards(result.rewards)
            setattr(self.state, "pending_reward_stats_refresh", True)
        return result.rewards

    def _set_runtime_detection_profiler(
        self,
        runtime_pyautogui,
        runtime_positioner,
        detection_profiler: DetectionProfiler | None,
        screen_capture=None,
    ) -> None:
        self.detection_service.set_runtime_context(
            pyautogui_module=runtime_pyautogui,
            relative_positioner=runtime_positioner,
            detection_profiler=detection_profiler,
            screen_capture=screen_capture,
        )
        self.legend_card_selector.set_runtime_context(
            relative_positioner=runtime_positioner,
            detection_profiler=detection_profiler,
            screen_capture=screen_capture,
        )
        self.dungeon_card_selector.set_runtime_context(
            pyautogui_module=runtime_pyautogui,
            relative_positioner=runtime_positioner,
            detection_profiler=detection_profiler,
            screen_capture=screen_capture,
        )
        self.match_result_detector.set_detection_profiler(detection_profiler)
        self.match_result_detector.set_runtime_context(
            relative_positioner=runtime_positioner,
            screen_capture=screen_capture,
        )
        self.reward_detector.set_detection_profiler(detection_profiler)
        self.reward_detector.set_runtime_context(
            relative_positioner=runtime_positioner,
            screen_capture=screen_capture,
        )
        self.wave_number_detector.set_detection_profiler(detection_profiler)
        self.macro_execution_service.ability_steps.set_screen_capture(screen_capture)
        self.odyssey_flow_service.set_screen_capture(screen_capture)
        self.webhook_controller.webhook_service.set_screen_capture(screen_capture)

    def log_reward_parse_result(self, result: RewardParseResult) -> None:
        if result.warning:
            self.adv_macro_log(f"Reward warning: {result.warning}")
            self.adv_macro_log("Detected reward icons:")
            if result.icons:
                for icon in result.icons:
                    self.adv_macro_log(f"  - {icon.name}: x={icon.x}, conf={icon.confidence:.3f}")
            else:
                self.adv_macro_log("  - none")
            self.adv_macro_log("Detected reward amounts:")
            if result.amounts:
                for amount in result.amounts:
                    self.adv_macro_log(f"  - {amount.value}: text={amount.text!r}, x={amount.x:.0f}, conf={amount.confidence:.3f}")
            else:
                self.adv_macro_log("  - none")
            return

        self.adv_macro_log("Detected rewards:")
        if result.rewards:
            self.adv_macro_log("{")
            for reward_name, amount in result.rewards.items():
                self.adv_macro_log(f'  "{reward_name}": {amount}')
            self.adv_macro_log("}")
        else:
            self.adv_macro_log("{}")

    def poll_adv_log(self) -> None:
        if self.state.pending_overlay_stats_modes and self.overlay_controller is not None:
            for mode in list(self.state.pending_overlay_stats_modes):
                self.overlay_controller.refresh_overlay_stats_for_mode(mode)
            self.state.pending_overlay_stats_modes.clear()

        if getattr(self.state, "pending_reward_stats_refresh", False) and self.overlay_controller is not None:
            self.overlay_controller.refresh_reward_stats_tab()
            self.state.pending_reward_stats_refresh = False

        if not self.state.editor.adv_log_queue:
            return
        scrollbar = self.window.advLogTextArea.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 10
        batched_entries: list[tuple[str, str]] = []
        while self.state.editor.adv_log_queue:
            entry = self.state.editor.adv_log_queue.popleft()
            if entry == "__MACRO_DONE__":
                if batched_entries:
                    cursor = self.window.advLogTextArea.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    for timestamp, message in batched_entries:
                        cursor.insertHtml(self._render_adv_log_entry(timestamp, message))
                        cursor.insertBlock()
                    self.window.advLogTextArea.setTextCursor(cursor)
                    batched_entries.clear()
                self.state.macro_is_running = False
                self.window.advRunMacroButton.setText(START_MACRO_BUTTON_TEXT)
                self.window.advRunMacroButton.setEnabled(True)
                self.window.advStopMacroButton.setEnabled(False)
                self.status_controller.set_running(False)
                self.state.editor.adv_log_poll_timer.stop()
                continue
            if isinstance(entry, tuple) and len(entry) == 2:
                batched_entries.append((entry[0], entry[1]))
            else:
                batched_entries.append((time.strftime("%H:%M:%S"), str(entry)))
        if batched_entries:
            cursor = self.window.advLogTextArea.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            for timestamp, message in batched_entries:
                cursor.insertHtml(self._render_adv_log_entry(timestamp, message))
                cursor.insertBlock()
            self.window.advLogTextArea.setTextCursor(cursor)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def run_advanced_macro(self) -> None:
        import pyautogui
        import supabase_client

        if self.state.macro_thread and self.state.macro_thread.is_alive():
            self.window.statusbar.showMessage("Macro already running!")
            return
        if not self.state.last_saved_macro_path or not os.path.exists(self.state.last_saved_macro_path):
            self.window.statusbar.showMessage("No saved macro found! Save the macro first.")
            return

        try:
            macro_data = self._load_saved_macro_for_run(self.state.last_saved_macro_path)
        except Exception as exc:
            self.window.statusbar.showMessage(f"Error parsing macro: {exc}")
            return

        if self._macro_contains_skele_strings_step(macro_data):
            if not self.macro_execution_service.ability_steps.prepare_skele_strings_runtime(log=self.adv_macro_log):
                self.window.statusbar.showMessage("Skele: Strings setup failed")
                return

        macro_name = os.path.splitext(os.path.basename(self.state.last_saved_macro_path))[0]
        self.state.macro_stop_requested = False
        self.state.stop_triggered_by_key = False

        self.window.advLogTextArea.clear()
        self.state.editor.adv_log_queue.clear()
        self.state.editor.adv_log_poll_timer.start(100)

        relative_positioning_enabled = macro_data["settings"].get("relative_positioning", False)
        runtime_positioner = RelativePositioner() if relative_positioning_enabled else None
        relative_pyautogui = (
            RelativePyAutoGUI(pyautogui, runtime_positioner)
            if runtime_positioner is not None
            else None
        )
        runtime_pyautogui = (
            FocusLeasePyAutoGUI(
                pyautogui,
                relative_pyautogui,
                runtime_positioner,
                debug_log=self.adv_macro_log if self.state.debug_console_mode else None,
            )
            if runtime_positioner is not None
            else pyautogui
        )
        runtime_capture_manager = RuntimeScreenCapture(runtime_positioner)
        try:
            runtime_capture_manager.start()
        except (ScreenCaptureError, RelativePositioningError) as exc:
            self.adv_macro_log(f"Macro start failed: {exc}")
            self.window.statusbar.showMessage(str(exc))
            self.state.editor.adv_log_queue.append("__MACRO_DONE__")
            return
        runtime_screen_capture = (
            runtime_capture_manager
            if runtime_capture_manager.uses_window_capture
            else None
        )

        def runner():
            session_start_time = time.time()
            run_count = 1
            completed_runs = 0
            mode = self.state.overlay.mode or "Custom"
            map_name = self.state.overlay.map_name or macro_name
            self.state.session_webhook.current_macro_name = macro_name
            self.state.session_webhook.gamemode = mode
            self.state.session_webhook.map_name = map_name
            self.state.session_webhook.session_started_at = session_start_time
            self.state.session_webhook.started_runs = 0
            self.state.session_webhook.completed_runs = 0
            self.state.session_webhook.successful_runs = 0
            self.state.session_webhook.failed_runs = 0
            self.state.session_webhook.reward_totals = {}
            self.state.session_webhook.last_run_rewards = {}
            import macro_app.services.detection as detection_module

            original_detection_pyautogui = detection_module.pyautogui
            original_wave_pyautogui = self.wave_number_detector.pyautogui
            self.run_logger.start_session(self._display_mode_name(mode), map_name, macro_name)
            iteration_started_at: float | None = None
            iteration_open = False
            interrupted = False

            def current_win_rate() -> str:
                attempts = self.state.session_webhook.successful_runs + self.state.session_webhook.failed_runs
                if attempts <= 0:
                    return "0%"
                return f"{(self.state.session_webhook.successful_runs / attempts) * 100:.1f}%"

            def current_rewards_per_hour() -> str:
                elapsed = max(0.0, time.time() - session_start_time)
                if elapsed <= 0.0 or not self.state.session_webhook.reward_totals:
                    return ""
                hourly_values = []
                for reward_name, amount in self.state.session_webhook.reward_totals.items():
                    per_hour = int(round((amount / elapsed) * 3600))
                    if per_hour > 0:
                        hourly_values.append((per_hour, reward_name))
                hourly_values.sort(key=lambda item: (-item[0], item[1]))
                return "\n".join(f"{name}: {value}/h" for value, name in hourly_values[:3])

            def handle_runtime_event(event_type: str, payload: dict) -> None:
                if event_type != "stage_complete":
                    return
                self.webhook_controller.send_stage_completed_notification(
                    wave=int(payload.get("wave", 0) or 0),
                    macro_name=macro_name,
                    gamemode=mode or "Unknown",
                    map_name=map_name or "Unknown",
                    session_run_count=max(1, self.state.session_webhook.started_runs),
                )

            try:
                detection_module.pyautogui = runtime_pyautogui
                self.wave_number_detector.pyautogui = runtime_pyautogui
                self._set_runtime_detection_profiler(
                    runtime_pyautogui,
                    runtime_positioner,
                    None,
                    runtime_screen_capture,
                )
                if runtime_positioner is not None:
                    runtime_positioner.current_bounds()
                    self.wave_number_detector.set_region_translator(runtime_positioner.translate_region)
                else:
                    self.wave_number_detector.clear_region_translator()
                if runtime_screen_capture is not None:
                    self.wave_number_detector.set_screen_capture(runtime_screen_capture)
                    self.adv_macro_log("DeskPad Capture: ScreenCaptureKit Roblox window")
                    self.adv_macro_log("DeskPad Focus Lease: On")
                else:
                    self.wave_number_detector.clear_screen_capture()

                legend_card_enabled = macro_data["settings"].get("card_selection_legend", False)
                legend_card_name = macro_data["settings"].get("legend_selected_card", "Immunity")
                dungeon_card_enabled = macro_data["settings"].get("card_selection_dungeon", False)
                dungeon_starter_card = macro_data["settings"].get("dungeon_starter_card", "Money Surge")
                odyssey_macro_enabled = bool(macro_data["settings"].get("odyssey_macro_enabled", False))
                odyssey_auto_card_selection = bool(
                    macro_data["settings"].get(
                        "odyssey_auto_card_selection",
                        macro_data["settings"].get("odyssey_auto_pick_card", True),
                    )
                )
                odyssey_auto_pick_card = odyssey_auto_card_selection
                odyssey_card_priorities = macro_data["settings"].get("odyssey_card_priorities", [])
                odyssey_auto_character_card = bool(macro_data["settings"].get("odyssey_auto_character_card", False))
                odyssey_character = str(macro_data["settings"].get("odyssey_character", "Madara") or "Madara")
                odyssey_character_card_priorities = macro_data["settings"].get("odyssey_character_card_priorities", [])
                odyssey_auto_next_room = bool(macro_data["settings"].get("odyssey_auto_next_room", True))
                odyssey_enabled = bool(
                    odyssey_macro_enabled
                    and (odyssey_auto_card_selection or odyssey_auto_next_room)
                )
                odyssey_room_priorities = macro_data["settings"].get(
                    "odyssey_room_priorities",
                    ["Normal", "Shop", "Boss"],
                )
                odyssey_check_treasure_room = bool(macro_data["settings"].get("odyssey_check_treasure_room", False))
                odyssey_check_unit_reward = bool(macro_data["settings"].get("odyssey_check_unit_reward", False))
                odyssey_auto_shop_room = bool(macro_data["settings"].get("odyssey_auto_shop_room", False))
                odyssey_auto_memoria_selection = bool(
                    macro_data["settings"].get("odyssey_auto_memoria_selection", False)
                )
                odyssey_memoria_priorities = macro_data["settings"].get("odyssey_memoria_priorities", [])
                odyssey_only_buy_when_enough = bool(macro_data["settings"].get("odyssey_only_buy_when_enough", True))
                force_restart_wave = self._configured_force_restart_wave(macro_data["settings"])
                wait_between_clicks = max(0.0, float(macro_data["settings"].get("wait_between_clicks", 0.2) or 0.2))
                wait_between_key_presses = max(
                    0.0,
                    float(macro_data["settings"].get("wait_between_key_presses", 0.2) or 0.2),
                )
                wait_between_steps = max(0.0, float(macro_data["settings"].get("wait_between_steps", 0.0) or 0.0))
                legend_card_summary = "On"
                if legend_card_enabled:
                    legend_card_summary = f"On ({legend_card_name})"
                else:
                    legend_card_summary = "Off"
                dungeon_card_summary = "On"
                if dungeon_card_enabled:
                    dungeon_card_summary = f"On ({dungeon_starter_card})"
                else:
                    dungeon_card_summary = "Off"
                force_restart_summary = "Off"
                if force_restart_wave > 0:
                    force_restart_summary = f"On (Wave {force_restart_wave})"
                odyssey_summary = "Off"
                if odyssey_enabled:
                    odyssey_summary = f"On ({' > '.join(map(str, odyssey_room_priorities))})"
                    odyssey_summary += f", Card Selection: {'On' if odyssey_auto_card_selection else 'Off'}"
                    if odyssey_auto_character_card:
                        odyssey_summary += f", Character Cards: On ({odyssey_character})"
                    odyssey_summary += f", Next Room: {'On' if odyssey_auto_next_room else 'Off'}"
                    if odyssey_check_treasure_room:
                        odyssey_summary += ", Treasure Check"
                    if odyssey_check_unit_reward:
                        odyssey_summary += ", Unit Reward Check"
                    if odyssey_auto_shop_room:
                        odyssey_summary += ", Auto Shop"
                    if odyssey_auto_memoria_selection:
                        odyssey_summary += ", Auto Memoria"

                self.adv_macro_log(f"Starting: {macro_name}")
                self.adv_macro_log(
                    f"Replay: {macro_data['settings']['replay']} | "
                    f"Anti-AFK: {'On' if macro_data['settings'].get('anti_afk', False) else 'Off'} | "
                    f"Check Placed: {'On' if macro_data['settings'].get('check_placed', False) else 'Off'} | "
                    f"Disable Chat: {'On' if macro_data['settings'].get('disable_chat', False) else 'Off'} | "
                    f"Click Wait: {wait_between_clicks:g}s | "
                    f"Key Wait: {wait_between_key_presses:g}s | "
                    f"Step Wait: {wait_between_steps:g}s | "
                    f"Relative Positioning: {'On' if relative_positioning_enabled else 'Off'} | "
                    f"Legend Card: {legend_card_summary} | "
                    f"Dungeon Card: {dungeon_card_summary} | "
                    f"Odyssey: {odyssey_summary} | "
                    f"Force Restart: {force_restart_summary} | "
                    f"Camera Start: {'On' if macro_data['settings'].get('reposition_camera_on_start', False) else 'Off'}"
                )
                self.adv_macro_log(
                    f"Setup Steps: {len(macro_data.get('setup_order', []))} | Loop Steps: {len(macro_data['order'])}"
                )

                def wait_between_runner_steps() -> bool:
                    elapsed = 0.0
                    while elapsed < wait_between_steps:
                        if self.state.macro_stop_requested:
                            return False
                        sleep_time = min(0.05, wait_between_steps - elapsed)
                        time.sleep(sleep_time)
                        elapsed += sleep_time
                    return True

                for _ in range(20):
                    if self.state.macro_stop_requested:
                        self.adv_macro_log("Cancelled during countdown")
                        interrupted = True
                        return
                    time.sleep(0.1)

                runtime_pyautogui.moveTo(*GAME_FOCUS_CLICK)
                time.sleep(0.2)
                runtime_pyautogui.click()
                time.sleep(0.3)
                pre_iteration_settings_ran = True
                if macro_data["settings"].get("disable_chat", False):
                    if not wait_between_runner_steps():
                        self.adv_macro_log("Cancelled during startup wait")
                        interrupted = True
                        return
                    for click_index in range(2):
                        runtime_pyautogui.moveTo(153, 102)
                        time.sleep(0.2)
                        runtime_pyautogui.click()
                        if click_index == 0:
                            time.sleep(0.5)
                    time.sleep(0.3)

                loop_mode = macro_data["settings"]["replay"] == "loop" or odyssey_enabled
                anti_afk_enabled = macro_data["settings"].get("anti_afk", False)
                card_selection_legend = macro_data["settings"].get("card_selection_legend", False)
                legend_selected_card = macro_data["settings"].get("legend_selected_card", "Immunity")
                card_selection_dungeon = macro_data["settings"].get("card_selection_dungeon", False)
                dungeon_starter_card = macro_data["settings"].get("dungeon_starter_card", "Money Surge")
                reposition_camera_on_start = macro_data["settings"].get("reposition_camera_on_start", False)
                setup_order = macro_data.get("setup_order", [])
                force_restart_consumed_for_stop_mode = False
                odyssey_skip_end_check_once = False
                self.odyssey_flow_service.equipped_memoria = None

                while True:
                    if self.state.macro_stop_requested:
                        self.adv_macro_log("Stopped by user")
                        interrupted = True
                        break

                    iteration_started_at = time.time()
                    iteration_open = True
                    self.run_logger.start_iteration()
                    self.state.session_webhook.started_runs += 1
                    self.state.session_webhook.last_run_rewards = {}
                    detection_profiler = DetectionProfiler()
                    self._set_runtime_detection_profiler(
                        runtime_pyautogui,
                        runtime_positioner,
                        detection_profiler,
                        runtime_screen_capture,
                    )
                    dungeon_wave_monitor = None
                    force_restart_requested = threading.Event()
                    force_restart_handled = threading.Event()
                    force_restart_stop = threading.Event()
                    force_restart_thread = None
                    force_restart_trigger = {"wave": None, "confidence": 0.0}
                    runner_step_started = pre_iteration_settings_ran if run_count == 1 else False
                    self.adv_macro_log(f"--- Run #{run_count} ---")
                    self.webhook_controller.send_run_started_notification(
                        macro_name=macro_name,
                        gamemode=mode or "Unknown",
                        map_name=map_name or "Unknown",
                        session_run_count=self.state.session_webhook.started_runs,
                    )

                    def stop_force_restart_watcher() -> None:
                        nonlocal force_restart_thread
                        force_restart_stop.set()
                        if force_restart_thread is not None and force_restart_thread.is_alive():
                            force_restart_thread.join(timeout=0.2)
                        force_restart_thread = None

                    def service_force_restart_request() -> bool:
                        nonlocal dungeon_wave_monitor, force_restart_consumed_for_stop_mode
                        if not force_restart_requested.is_set() or force_restart_handled.is_set():
                            return False
                        trigger_wave = force_restart_trigger["wave"] or force_restart_wave
                        trigger_conf = force_restart_trigger["confidence"]
                        self.adv_macro_log(
                            f"Force restart triggered at wave {trigger_wave} "
                            f"(conf={trigger_conf:.3f}). Running restart sequence..."
                        )
                        if dungeon_wave_monitor is not None:
                            self.adv_macro_log("Stopping dungeon wave-card monitor for force restart.")
                            dungeon_wave_monitor.stop()
                            dungeon_wave_monitor = None
                        if self._execute_force_restart_click_sequence(runtime_pyautogui):
                            force_restart_handled.set()
                            if not loop_mode:
                                force_restart_consumed_for_stop_mode = True
                                self.adv_macro_log(
                                    "Force restart consumed for Stop After Completion. "
                                    "The restarted run will finish normally without arming another force restart."
                                )
                            stop_force_restart_watcher()
                        return True

                    def force_restart_watch_loop() -> None:
                        self.adv_macro_log(
                            f"Force restart watcher active for wave {force_restart_wave} "
                            f"(poll every {FORCE_RESTART_POLL_INTERVAL_SECONDS:g}s)."
                        )
                        while not force_restart_stop.is_set() and not self.state.macro_stop_requested:
                            try:
                                if runtime_positioner is not None:
                                    runtime_positioner.current_bounds()
                                    self.wave_number_detector.set_region_translator(runtime_positioner.translate_region)
                                current_wave, confidence = self.wave_number_detector.detect_current_wave()
                                self.adv_macro_log(
                                    f"Force restart poll: wave={current_wave} "
                                    f"conf={confidence:.3f} target={force_restart_wave}"
                                )
                                if current_wave is not None and current_wave == force_restart_wave:
                                    force_restart_trigger["wave"] = current_wave
                                    force_restart_trigger["confidence"] = confidence
                                    force_restart_requested.set()
                                    return
                            except RelativePositioningError as exc:
                                self.adv_macro_log(f"Force restart watcher error: {exc}")
                            except Exception as exc:
                                self.adv_macro_log(f"Force restart watcher error: {exc}")
                            if force_restart_stop.wait(FORCE_RESTART_POLL_INTERVAL_SECONDS):
                                return

                    force_restart_enabled_for_iteration = force_restart_wave > 0 and (
                        loop_mode or not force_restart_consumed_for_stop_mode
                    )
                    if force_restart_enabled_for_iteration:
                        force_restart_thread = threading.Thread(
                            target=force_restart_watch_loop,
                            daemon=True,
                            name=f"force-restart-wave-{force_restart_wave}",
                        )
                        force_restart_thread.start()

                    if odyssey_enabled and run_count > 1:
                        if runner_step_started and not wait_between_runner_steps():
                            interrupted = True
                            break
                        runner_step_started = True
                        skip_odyssey_end_check = odyssey_skip_end_check_once
                        odyssey_skip_end_check_once = False
                        skip_odyssey_card_selection = (
                            self.odyssey_flow_service.last_selected_node_type == "Elite Boss"
                        )
                        if odyssey_auto_next_room:
                            if skip_odyssey_end_check:
                                self.adv_macro_log(
                                    "Odyssey macro enabled. Shop shortcut completed last loop, "
                                    "so selecting next room without waiting for Odyssey end..."
                                )
                            elif not odyssey_auto_pick_card:
                                self.adv_macro_log(
                                    "Odyssey macro enabled. Auto Card selection is off, "
                                    "so selecting next room without waiting for Odyssey end..."
                                )
                            else:
                                self.adv_macro_log(
                                    "Odyssey macro enabled. Waiting for Odyssey end, then selecting next room..."
                                )
                            odyssey_ready = self.odyssey_flow_service.advance_to_next_room(
                                runtime_pyautogui,
                                relative_positioner=runtime_positioner,
                                wait_for_end=odyssey_auto_pick_card and not skip_odyssey_end_check,
                                skip_end_check=skip_odyssey_end_check or not odyssey_auto_pick_card,
                                card_priorities=odyssey_card_priorities,
                                auto_character_card=odyssey_auto_character_card,
                                character=odyssey_character,
                                character_card_priorities=odyssey_character_card_priorities,
                                skip_card_selection=skip_odyssey_card_selection,
                                room_priorities=odyssey_room_priorities,
                                check_treasure_room=odyssey_check_treasure_room,
                                treasure_room_callback=lambda: self.webhook_controller.send_treasure_room_notification(
                                    macro_name=macro_name,
                                    gamemode=mode or "Unknown",
                                    map_name=map_name or "Unknown",
                                    session_run_count=self.state.session_webhook.started_runs,
                                    relative_positioner=runtime_positioner,
                                ),
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            if not odyssey_ready:
                                self.adv_macro_log("Odyssey next-room flow stopped or failed.")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                            if self.odyssey_flow_service.last_selected_node_type:
                                self.adv_macro_log(
                                    "Odyssey selected stage type recorded: "
                                    f"{self.odyssey_flow_service.last_selected_node_type}"
                                )
                        elif odyssey_auto_pick_card:
                            self.adv_macro_log(
                                "Odyssey macro enabled. Auto next room is off; "
                                "waiting for Odyssey end card only..."
                            )
                            odyssey_ready = self.odyssey_flow_service.wait_for_end_and_continue(
                                runtime_pyautogui,
                                relative_positioner=runtime_positioner,
                                card_priorities=odyssey_card_priorities,
                                auto_character_card=odyssey_auto_character_card,
                                character=odyssey_character,
                                character_card_priorities=odyssey_character_card_priorities,
                                skip_card_selection=skip_odyssey_card_selection,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            if not odyssey_ready:
                                self.adv_macro_log("Odyssey end-card flow stopped or failed.")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                            self.adv_macro_log(
                                "Odyssey end card handled. Auto next room is off, so the macro is ending."
                            )
                            stop_force_restart_watcher()
                            elapsed_seconds = max(0.0, time.time() - iteration_started_at)
                            self.state.session_webhook.completed_runs += 1
                            self.state.session_webhook.successful_runs += 1
                            self.run_logger.finish_iteration(elapsed_seconds, rewards={})
                            iteration_open = False
                            completed_runs += 1
                            break
                    elif odyssey_enabled:
                        self.adv_macro_log(
                            "Odyssey macro enabled. First run starts immediately; "
                            "next-room automation begins after this run ends."
                        )

                    if (
                        odyssey_enabled
                        and (odyssey_auto_shop_room or odyssey_auto_memoria_selection)
                        and run_count > 1
                        and self.odyssey_flow_service.last_selected_node_type == "Shop"
                    ):
                        stop_force_restart_watcher()
                        if odyssey_auto_memoria_selection:
                            if odyssey_auto_shop_room:
                                self.adv_macro_log(
                                    "Odyssey Shop room selected. Auto Memoria is on, "
                                    "so it will run instead of the basic shop shortcut."
                                )
                            shop_handled = self.odyssey_flow_service.run_memoria_shop_selection(
                                runtime_pyautogui,
                                relative_positioner=runtime_positioner,
                                memoria_priorities=odyssey_memoria_priorities,
                                only_buy_when_enough=odyssey_only_buy_when_enough,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            stopped_message = "Odyssey Memoria shop selection stopped."
                            completed_message = (
                                "Odyssey Shop Memoria flow handled without macro steps. "
                                "Next loop will go straight to Odyssey next-room detection."
                            )
                        else:
                            shop_handled = self.odyssey_flow_service.run_shop_stage_shortcut(
                                runtime_pyautogui,
                                relative_positioner=runtime_positioner,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            stopped_message = "Odyssey shop shortcut stopped."
                            completed_message = (
                                "Odyssey Shop room handled without macro steps. "
                                "Next loop will go straight to Odyssey next-room detection."
                            )
                        if not shop_handled:
                            self.adv_macro_log(stopped_message)
                            self.run_logger.interrupt(time.time() - iteration_started_at)
                            iteration_open = False
                            interrupted = True
                            break
                        self.adv_macro_log(completed_message)
                        odyssey_skip_end_check_once = True
                        elapsed_seconds = max(0.0, time.time() - iteration_started_at) if iteration_started_at is not None else 0.0
                        self.state.session_webhook.completed_runs += 1
                        self.state.session_webhook.successful_runs += 1
                        self.run_logger.finish_iteration(elapsed_seconds, rewards={})
                        iteration_open = False
                        completed_runs += 1
                        session_key = (mode, map_name)
                        self.state.session_run_counts[session_key] = self.state.session_run_counts.get(session_key, 0) + 1
                        if self.overlay_controller is not None and mode in self.overlay_controller.overlay_widgets.modes:
                            self.state.pending_overlay_stats_modes.add(mode)
                        run_count += 1
                        continue

                    self.adv_macro_log(
                        f"Dungeon card setting check: enabled={card_selection_dungeon} "
                        f"starter={dungeon_starter_card!r}"
                    )
                    if card_selection_dungeon:
                        if runner_step_started and not wait_between_runner_steps():
                            interrupted = True
                            break
                        runner_step_started = True
                        dungeon_priority_labels = macro_data["settings"].get("dungeon_card_priorities", [])
                        self.adv_macro_log(
                            f"Dungeon card branch entered. Priority count={len(dungeon_priority_labels)}"
                        )
                        runtime_pyautogui.moveTo(*GAME_FOCUS_CLICK)
                        time.sleep(0.2)
                        runtime_pyautogui.click()
                        time.sleep(0.3)
                        starter_selected = self.dungeon_card_selector.select_starter_card(
                            runtime_pyautogui,
                            self.detection_service,
                            dungeon_starter_card,
                            log=self.adv_macro_log,
                            stop_requested=lambda: self.state.macro_stop_requested,
                        )
                        if self.state.macro_stop_requested:
                            self.adv_macro_log("Dungeon starter card selection cancelled")
                            self.run_logger.interrupt(time.time() - iteration_started_at)
                            iteration_open = False
                            interrupted = True
                            break
                        if not starter_selected:
                            self.adv_macro_log(f"Dungeon starter card '{dungeon_starter_card}' not selected.")
                        dungeon_wave_monitor = self.dungeon_card_selector.create_wave_card_monitor(
                            runtime_pyautogui,
                            self.wave_number_detector,
                            macro_data["settings"],
                            log=self.adv_macro_log,
                            stop_requested=lambda: self.state.macro_stop_requested,
                        )
                        self.adv_macro_log("Dungeon wave-card monitor object created.")
                        dungeon_wave_monitor.start()
                        self.adv_macro_log("Dungeon wave-card monitor started for full run iteration.")
                    else:
                        self.adv_macro_log("Dungeon card branch skipped because setting is disabled.")
                    if card_selection_legend:
                        if runner_step_started and not wait_between_runner_steps():
                            interrupted = True
                            break
                        runner_step_started = True
                        runtime_pyautogui.moveTo(*GAME_FOCUS_CLICK)
                        time.sleep(0.2)
                        runtime_pyautogui.click()
                        time.sleep(0.3)
                        if str(mode).lower() == "legend":
                            selected = self.legend_card_selector.select_card(
                                runtime_pyautogui,
                                legend_selected_card,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            if self.state.macro_stop_requested:
                                self.adv_macro_log("Legend card selection cancelled")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                            if not selected:
                                self.adv_macro_log(f"Legend card '{legend_selected_card}' not found, continuing.")
                        else:
                            self.adv_macro_log("Legend card selection skipped: current mode is not Legend.")
                    def handle_runtime_interrupts() -> bool:
                        if self.state.macro_stop_requested:
                            return False
                        if service_force_restart_request():
                            return False
                        if dungeon_wave_monitor is not None:
                            return dungeon_wave_monitor.handle_pending_selection()
                        return True

                    try:
                        if run_count == 1 and reposition_camera_on_start:
                            if runner_step_started and not wait_between_runner_steps():
                                interrupted = True
                                break
                            runner_step_started = True
                            camera_ok = reposition_camera(
                                runtime_pyautogui,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            )
                            if not camera_ok:
                                self.adv_macro_log("Camera repositioning cancelled")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                        if run_count == 1 and setup_order:
                            if runner_step_started and not wait_between_runner_steps():
                                interrupted = True
                                break
                            runner_step_started = True
                            self.adv_macro_log("--- Setup ---")
                            setup_context = MacroExecutionContext(
                                detection=self.detection_service,
                                wave_number_detector=self.wave_number_detector,
                                pyautogui=runtime_pyautogui,
                                stop_requested=lambda: self.state.macro_stop_requested,
                                units=macro_data["units"],
                                interrupt_handler=handle_runtime_interrupts,
                                interrupt_state_getter=(
                                    dungeon_wave_monitor.selection_completed_count
                                    if dungeon_wave_monitor is not None
                                    else None
                                ),
                                status_callback=self.adv_macro_log,
                                log=self.adv_macro_log,
                                check_placed=macro_data["settings"].get("check_placed", False),
                                relative_positioner=runtime_positioner,
                                wait_between_clicks=wait_between_clicks,
                                wait_between_key_presses=wait_between_key_presses,
                                wait_between_steps=wait_between_steps,
                                detection_profiler=detection_profiler,
                                event_callback=handle_runtime_event,
                                debug_console_mode=self.state.debug_console_mode,
                                screen_capture=runtime_screen_capture,
                            )
                            setup_completed = self.macro_execution_service.execute_steps(
                                setup_order,
                                macro_data["units"],
                                setup_context,
                            )
                            if not setup_completed:
                                if force_restart_handled.is_set():
                                    if loop_mode:
                                        self.adv_macro_log(
                                            "Force restart completed during setup. "
                                            "Skipping replay/rewards/webhooks and starting next run."
                                        )
                                    else:
                                        self.adv_macro_log(
                                            "Force restart completed during setup. "
                                            "Stop After Completion is enabled, so the macro is ending now."
                                        )
                                    self.run_logger.interrupt(time.time() - iteration_started_at)
                                    iteration_open = False
                                    if not loop_mode:
                                        break
                                    run_count += 1
                                    continue
                                self.adv_macro_log("Setup stopped")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                            self.adv_macro_log("Setup completed!")
                        previous_macro_action = None
                        apply_initial_macro_step_wait = False
                        if run_count == 1 and setup_order:
                            previous_macro_action = setup_context.last_completed_step_action_type
                            apply_initial_macro_step_wait = True
                        elif runner_step_started and not wait_between_runner_steps():
                            interrupted = True
                            break
                        runner_step_started = True
                        if run_count == 1 and not macro_data["order"]:
                            self.adv_macro_log("No loop steps configured. Macro finished after setup.")
                            stop_force_restart_watcher()
                            self.run_logger.finish_iteration(time.time() - iteration_started_at, rewards={})
                            iteration_open = False
                            completed_runs += 1
                            break
                        completed = self.macro_execution_service.execute_steps(
                            macro_data["order"],
                            macro_data["units"],
                            MacroExecutionContext(
                                detection=self.detection_service,
                                wave_number_detector=self.wave_number_detector,
                                pyautogui=runtime_pyautogui,
                                stop_requested=lambda: self.state.macro_stop_requested,
                                units=macro_data["units"],
                                interrupt_handler=handle_runtime_interrupts,
                                interrupt_state_getter=(
                                    dungeon_wave_monitor.selection_completed_count
                                    if dungeon_wave_monitor is not None
                                    else None
                                ),
                                status_callback=self.adv_macro_log,
                                log=self.adv_macro_log,
                                check_placed=macro_data["settings"].get("check_placed", False),
                                relative_positioner=runtime_positioner,
                                wait_between_clicks=wait_between_clicks,
                                wait_between_key_presses=wait_between_key_presses,
                                wait_between_steps=wait_between_steps,
                                last_completed_step_action_type=previous_macro_action,
                                apply_initial_step_wait=apply_initial_macro_step_wait,
                                detection_profiler=detection_profiler,
                                event_callback=handle_runtime_event,
                                debug_console_mode=self.state.debug_console_mode,
                                screen_capture=runtime_screen_capture,
                            ),
                        )
                        if not completed:
                            if force_restart_handled.is_set():
                                if loop_mode:
                                    self.adv_macro_log(
                                        "Force restart completed during loop steps. "
                                        "Skipping replay/rewards/webhooks and starting next run."
                                    )
                                else:
                                    self.adv_macro_log(
                                        "Force restart completed during loop steps. "
                                        "Stop After Completion is enabled, so the macro is ending now."
                                    )
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                if not loop_mode:
                                    break
                                run_count += 1
                                continue
                            self.adv_macro_log("Macro stopped")
                            self.run_logger.interrupt(time.time() - iteration_started_at)
                            iteration_open = False
                            interrupted = True
                            break
                    finally:
                        pass

                    for line in detection_profiler.summary_lines():
                        self.adv_macro_log(line)
                    self._set_runtime_detection_profiler(
                        runtime_pyautogui,
                        runtime_positioner,
                        None,
                        runtime_screen_capture,
                    )
                    self.adv_macro_log(f"Run #{run_count} completed!")
                    if odyssey_enabled:
                        selected_odyssey_stage = self.odyssey_flow_service.last_selected_node_type
                        if odyssey_check_unit_reward and selected_odyssey_stage == "Boss":
                            self.adv_macro_log("Odyssey Boss stage completed. Checking for unit reward prompt...")
                            if not self.odyssey_flow_service.claim_unit_reward_if_present(
                                runtime_pyautogui,
                                relative_positioner=runtime_positioner,
                                log=self.adv_macro_log,
                                stop_requested=lambda: self.state.macro_stop_requested,
                            ):
                                self.adv_macro_log("Odyssey unit reward check stopped.")
                                self.run_logger.interrupt(time.time() - iteration_started_at)
                                iteration_open = False
                                interrupted = True
                                break
                        elif odyssey_check_unit_reward:
                            self.adv_macro_log(
                                "Odyssey unit reward check skipped: "
                                f"current stage type is {selected_odyssey_stage or 'unknown'}."
                            )
                        self.adv_macro_log(
                            "Odyssey mode: skipping replay/reward scan/webhooks. "
                            f"Next loop will {'wait for Odyssey end and ' if odyssey_auto_pick_card else ''}"
                            f"{'select the next room' if odyssey_auto_next_room else 'handle the Odyssey end card'}."
                        )
                        stop_force_restart_watcher()
                        if dungeon_wave_monitor is not None:
                            self.adv_macro_log("Stopping dungeon wave-card monitor before Odyssey next-room loop.")
                            dungeon_wave_monitor.stop()
                            dungeon_wave_monitor = None
                        elapsed_seconds = max(0.0, time.time() - iteration_started_at) if iteration_started_at is not None else 0.0
                        self.state.session_webhook.completed_runs += 1
                        self.state.session_webhook.successful_runs += 1
                        self.run_logger.finish_iteration(elapsed_seconds, rewards={})
                        iteration_open = False
                        completed_runs += 1
                        session_key = (mode, map_name)
                        self.state.session_run_counts[session_key] = self.state.session_run_counts.get(session_key, 0) + 1
                        if self.overlay_controller is not None and mode in self.overlay_controller.overlay_widgets.modes:
                            self.state.pending_overlay_stats_modes.add(mode)
                        run_count += 1
                        continue
                    self.adv_macro_log("Waiting for replay button...")
                    if dungeon_wave_monitor is not None and dungeon_wave_monitor.is_enabled() and not dungeon_wave_monitor.wave30_completed():
                        self.adv_macro_log(
                            "Dungeon wave-card monitor remains active after steps while waiting for replay/final wave handling."
                        )
                    afk_interval = 300
                    afk_coords = (427, 85)
                    last_afk_time = time.time()
                    replay_found = False
                    replay_center = (0, 0)
                    last_replay_probe_at = 0.0

                    while not self.state.macro_stop_requested:
                        if service_force_restart_request():
                            break
                        if dungeon_wave_monitor is not None and not dungeon_wave_monitor.handle_pending_selection():
                            interrupted = True
                            break
                        current_time = time.time()
                        if anti_afk_enabled and current_time - last_afk_time >= afk_interval:
                            runtime_pyautogui.moveTo(afk_coords[0], afk_coords[1])
                            time.sleep(0.1)
                            runtime_pyautogui.click()
                            last_afk_time = current_time

                        if current_time - last_replay_probe_at >= 2.0:
                            last_replay_probe_at = current_time
                            found, center_x, center_y, _, _, conf, replay_template = self.detection_service.detect_any_image(
                                ("replay", "replay_4", "replay_5"),
                                REPLAY_REGION,
                                REPLAY_CONFIDENCE,
                            )
                            if found:
                                self.adv_macro_log(f"Replay button found ({replay_template}, conf={conf:.3f})")
                                replay_found = True
                                replay_center = (center_x, center_y)
                                break

                        time.sleep(0.1)

                    if force_restart_handled.is_set():
                        if loop_mode:
                            self.adv_macro_log(
                                "Force restart completed while waiting for replay. "
                                "Skipping replay/rewards/webhooks and starting next run."
                            )
                        else:
                            self.adv_macro_log(
                                "Force restart completed while waiting for replay. "
                                "Stop After Completion is enabled, so the macro is ending now."
                            )
                        self.run_logger.interrupt(time.time() - iteration_started_at)
                        iteration_open = False
                        if not loop_mode:
                            break
                        run_count += 1
                        continue

                    if self.state.macro_stop_requested:
                        self.adv_macro_log("Stopped while waiting for replay")
                        stop_force_restart_watcher()
                        interrupted = True
                        break

                    if not replay_found:
                        self.adv_macro_log("Replay button was not found")
                        stop_force_restart_watcher()
                        elapsed_seconds = max(0.0, time.time() - iteration_started_at) if iteration_started_at is not None else 0.0
                        self.state.session_webhook.failed_runs += 1
                        self.webhook_controller.send_event(
                            "run_fail",
                            match_result="FAILED",
                            rewards={},
                            context={
                                "macro_name": macro_name,
                                "gamemode": mode or "Unknown",
                                "map_name": map_name or "Unknown",
                                "elapsed": self.webhook_controller._format_elapsed(elapsed_seconds),
                                "session_run_count": self.state.session_webhook.completed_runs,
                                "win_rate": current_win_rate(),
                                "rewards_per_hour": current_rewards_per_hour(),
                            },
                            relative_positioner=runtime_positioner,
                        )
                        interrupted = True
                        break

                    match_result = self.detect_match_result(pyautogui_module=runtime_pyautogui)
                    rewards = self.parse_and_store_rewards(mode, map_name)
                    rewards_for_webhook = dict(rewards)
                    if not rewards_for_webhook and self.state.session_webhook.last_run_rewards:
                        rewards_for_webhook = dict(self.state.session_webhook.last_run_rewards)
                        self.adv_macro_log("Reward webhook fallback engaged: using last successful parsed rewards.")
                    elapsed_seconds = 0.0
                    if iteration_started_at is not None:
                        elapsed_seconds = max(0.0, time.time() - iteration_started_at)
                    normalized_result = self.webhook_controller._normalized_result(match_result.label)
                    self.state.session_webhook.completed_runs += 1
                    if normalized_result == "DEFEAT":
                        self.state.session_webhook.failed_runs += 1
                    else:
                        self.state.session_webhook.successful_runs += 1
                    for reward_name, amount in rewards_for_webhook.items():
                        self.state.session_webhook.reward_totals[reward_name] = (
                            self.state.session_webhook.reward_totals.get(reward_name, 0) + amount
                        )
                    session_run_count = self.state.session_webhook.completed_runs
                    win_rate = current_win_rate()
                    rewards_per_hour = current_rewards_per_hour()
                    webhook_ready, webhook_reason = self.webhook_controller.event_ready(
                        "run_fail" if normalized_result == "DEFEAT" else "run_finish",
                        rewards=rewards_for_webhook,
                    )
                    webhook_sent = self.webhook_controller.send_runtime_result_notification(
                        normalized_result,
                        rewards_for_webhook,
                        gamemode=mode or "Unknown",
                        map_name=map_name or "Unknown",
                        elapsed_seconds=elapsed_seconds,
                        relative_positioner=runtime_positioner,
                        macro_name=macro_name,
                        session_run_count=session_run_count,
                        win_rate=win_rate,
                        rewards_per_hour=rewards_per_hour,
                    )
                    if webhook_sent:
                        self.adv_macro_log("Webhook sent")
                    else:
                        if webhook_ready:
                            self.adv_macro_log("Webhook not sent (send failed)")
                        else:
                            self.adv_macro_log(f"Webhook not sent ({webhook_reason})")
                    reward_webhook_ready, reward_webhook_reason = self.webhook_controller.event_ready(
                        "reward_collected",
                        rewards=rewards_for_webhook,
                    )
                    reward_webhook_sent = self.webhook_controller.send_reward_collected_notification(
                        rewards_for_webhook,
                        macro_name=macro_name,
                        gamemode=mode or "Unknown",
                        map_name=map_name or "Unknown",
                        elapsed_seconds=elapsed_seconds,
                        session_run_count=session_run_count,
                        win_rate=win_rate,
                        rewards_per_hour=rewards_per_hour,
                        relative_positioner=runtime_positioner,
                    )
                    if reward_webhook_sent:
                        self.adv_macro_log("Reward webhook sent")
                    elif reward_webhook_ready:
                        self.adv_macro_log("Reward webhook not sent (send failed)")
                    elif reward_webhook_reason != "trigger disabled":
                        self.adv_macro_log(f"Reward webhook not sent ({reward_webhook_reason})")
                    persistent_mode = mode or "custom"
                    persistent_map = map_name or macro_name or "custom"
                    supabase_client.record_run(
                        None,
                        macro_name,
                        persistent_mode,
                        persistent_map,
                        completed_runs + 1,
                        elapsed_seconds,
                    )
                    self.run_logger.finish_iteration(time.time() - iteration_started_at, rewards=rewards_for_webhook)
                    iteration_open = False
                    completed_runs += 1
                    session_key = (mode, map_name)
                    self.state.session_run_counts[session_key] = self.state.session_run_counts.get(session_key, 0) + 1
                    if self.overlay_controller is not None and mode in self.overlay_controller.overlay_widgets.modes:
                        self.state.pending_overlay_stats_modes.add(mode)

                    if not loop_mode:
                        self.adv_macro_log("Macro finished (Stop mode)")
                        stop_force_restart_watcher()
                        break

                    if runner_step_started and not wait_between_runner_steps():
                        stop_force_restart_watcher()
                        interrupted = True
                        break
                    runner_step_started = True
                    stop_force_restart_watcher()
                    runtime_pyautogui.moveTo(replay_center[0], replay_center[1])
                    time.sleep(0.5)
                    runtime_pyautogui.click()
                    time.sleep(1)
                    if dungeon_wave_monitor is not None:
                        self.adv_macro_log("Stopping dungeon wave-card monitor before next replay iteration.")
                        dungeon_wave_monitor.stop()
                        dungeon_wave_monitor = None
                    run_count += 1
            except RelativePositioningError as exc:
                self.adv_macro_log(str(exc))
                if iteration_open and iteration_started_at is not None:
                    self.run_logger.interrupt(time.time() - iteration_started_at)
                    iteration_open = False
                interrupted = True
            except Exception as exc:
                self.adv_macro_log(f"Error: {exc}")
                if iteration_open and iteration_started_at is not None:
                    self.run_logger.interrupt(time.time() - iteration_started_at)
                    iteration_open = False
                interrupted = True
            finally:
                if 'stop_force_restart_watcher' in locals():
                    stop_force_restart_watcher()
                if 'dungeon_wave_monitor' in locals() and dungeon_wave_monitor is not None:
                    self.adv_macro_log(
                        "Stopping dungeon wave-card monitor "
                        f"(wave30_done={dungeon_wave_monitor.wave30_completed()}, "
                        f"pending_selection={dungeon_wave_monitor.has_pending_selection()})"
                    )
                    dungeon_wave_monitor.stop()
                total_duration = time.time() - session_start_time
                if interrupted and iteration_open and iteration_started_at is not None:
                    self.run_logger.interrupt(time.time() - iteration_started_at)
                    iteration_open = False
                elif interrupted and completed_runs == 0:
                    self.run_logger.interrupt(total_duration)
                log_path = self.run_logger.finalize()
                if completed_runs > 0:
                    if self.overlay_controller is not None and mode in self.overlay_controller.overlay_widgets.modes:
                        self.state.pending_overlay_stats_modes.add(mode)
                    self.adv_macro_log(f"Total time: {supabase_client.format_duration(total_duration)}")
                if log_path:
                    self.adv_macro_log(f"Saved log: {log_path}")
                self.state.editor.adv_log_queue.append("__MACRO_DONE__")
                self._set_runtime_detection_profiler(pyautogui, None, None, None)
                self.wave_number_detector.clear_region_translator()
                self.wave_number_detector.clear_screen_capture()
                self.wave_number_detector.clear_detection_profiler()
                detection_module.pyautogui = original_detection_pyautogui
                self.wave_number_detector.pyautogui = original_wave_pyautogui
                release_focus_lease = getattr(runtime_pyautogui, "release_focus_lease", None)
                if callable(release_focus_lease):
                    release_focus_lease()
                runtime_capture_manager.stop()

        self.state.macro_thread = threading.Thread(target=runner, daemon=True)
        self.state.macro_thread.start()
        self.window.statusbar.showMessage(f"Running macro: {macro_name}")
        self.window.advRunMacroButton.setText(START_MACRO_BUTTON_TEXT)
        self.window.advRunMacroButton.setEnabled(False)
        self.window.advStopMacroButton.setEnabled(True)
        self.state.macro_is_running = True
        self.status_controller.set_running(True)

    @staticmethod
    def _display_mode_name(mode: str) -> str:
        return {
            "story": "Story",
            "raids": "Raids",
            "legend": "Legend",
            "bossRush": "Boss Rush",
            "events": "Events",
            "dungeon": "Dungeons",
            "Custom": "Custom",
            "custom": "Custom",
        }.get(mode, mode or "Custom")

    def stop_macro(self) -> None:
        self.state.macro_stop_requested = True
        self.state.stop_triggered_by_key = False
        self.state.macro_is_running = False
        self.window.advRunMacroButton.setText(START_MACRO_BUTTON_TEXT)
        self.window.advRunMacroButton.setEnabled(True)
        self.window.advStopMacroButton.setEnabled(False)
        self.window.statusbar.showMessage("Macro stopped")
        if not self.state.editor.frameless_active:
            self.window.showNormal()
            self.window.activateWindow()
        self.status_controller.set_running(False)
        print("Macro stopped")

    def stop_advanced_macro(self) -> None:
        self.stop_macro()
        self.state.editor.adv_log_poll_timer.stop()
        self.adv_macro_log("Macro stopped")
        self.poll_adv_log()
        self.window.advRunMacroButton.setText(START_MACRO_BUTTON_TEXT)

    def check_stop_key_triggered(self) -> None:
        if self.state.start_triggered_by_key:
            self.state.start_triggered_by_key = False
            if self.window.stackedWidget.currentIndex() != PAGE_ADVANCED_CREATE:
                self.window.statusbar.showMessage("Open Config Creator to start a macro with Ctrl+S")
                return
            if self.state.macro_is_running:
                self.window.statusbar.showMessage("Macro already running")
                return
            self.run_advanced_macro()
            return

        if not self.state.stop_triggered_by_key:
            return
        self.state.stop_triggered_by_key = False
        if not self.state.macro_is_running:
            self.window.statusbar.showMessage("Macro is not running")
            return
        self.stop_advanced_macro()

    def handle_escape(self) -> None:
        if self.state.editor.insert.active:
            self.cancel_advanced_insert_mode()
        elif self.state.editor.editing.active:
            self.cancel_advanced_edit()
        else:
            self.stop_macro()
