"""Settings popup dialog for the advanced editor."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from macro_app.constants import resolve_stylesheet_asset_urls
from macro_app.services.dungeon_card_selection import DUNGEON_PRIORITY_GROUPS, STARTER_CARD_SPECS, WAVE_CARD_SPECS


LEGEND_CARD_OPTIONS = ["Immunity", "Champion", "Revitalize", "Thrice", "Quake", "Exploding"]
ODYSSEY_ROOM_OPTIONS = ["Normal", "Shop", "Boss"]
ODYSSEY_CARD_OPTIONS = [
    "Ambush",
    "Precision Optics",
    "Boxing Gloves",
    "Serrated Tips",
    "Military Training",
    "Concussive Blast",
    "Adrenaline Shot",
    "Affinity",
    "Infection",
    "Numbing Agent",
    "The Best Defense",
    "Extended Duration",
    "Slayer Rounds",
    "Treasure Map Fragment",
    "Resource Overflow",
    "Double Tap",
    "Potent Toxins",
]
ODYSSEY_MEMORIA_OPTIONS = [
    "Range",
    "Damage",
    "Speed",
    "All I got",
    "Drops of Serenity",
    "Gambling Fanatic",
    "Water Goddess",
    "Young Entrepreneur",
]
ODYSSEY_CHARACTER_OPTIONS = ["Madara"]
ODYSSEY_CHARACTER_CARD_OPTIONS = {
    "Madara": [
        "Ninjutsu Payout",
        "Stacked Afflictions",
        "Shared Ninjutsu",
        "Layered Slumber",
    ],
}


class SettingsDialog(QDialog):
    """Modal dialog for macro settings."""

    def __init__(self, settings: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setFixedSize(900, 700)
        self.setWindowTitle("")
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.FramelessWindowHint)
        self.setModal(True)
        self._saved = False
        self._settings_tab = "General"

        self._build_ui(settings)
        self._apply_stylesheet()
        self._set_settings_tab("General")

    def resizeEvent(self, event) -> None:  # pragma: no cover - GUI layout hook
        super().resizeEvent(event)
        if hasattr(self, "top_close_button"):
            content_shell = self.top_close_button.parentWidget()
            if content_shell is not None:
                self.top_close_button.setGeometry(content_shell.width() - 40, 24, 16, 16)
                self.top_close_button.raise_()

    @property
    def saved(self) -> bool:
        return self._saved

    def get_settings(self) -> dict:
        """Return the settings dict reflecting current control state."""
        return {
            "replay": "loop" if self.loop_radio.isChecked() else "stop",
            "anti_afk": self.anti_afk_checkbox.isChecked(),
            "check_placed": self.check_placed_checkbox.isChecked(),
            "disable_chat": self.disable_chat_checkbox.isChecked(),
            "force_restart_wave_enabled": self.force_restart_wave_checkbox.isChecked(),
            "force_restart_wave": self._int_from_input(self.force_restart_wave_input),
            "wait_between_clicks": self._float_from_input(self.wait_between_clicks_input, 0.2),
            "wait_between_key_presses": self._float_from_input(self.wait_between_key_input, 0.2),
            "wait_between_steps": self._float_from_input(self.wait_between_steps_input, 0.0),
            "relative_positioning": self.relative_positioning_checkbox.isChecked(),
            "reposition_camera_on_start": self.reposition_camera_checkbox.isChecked(),
            "card_selection_legend": self.legend_card_checkbox.isChecked(),
            "legend_selected_card": self.legend_card_combo.currentText(),
            "card_selection_dungeon": self.dungeon_card_checkbox.isChecked(),
            "dungeon_starter_card": self.dungeon_starter_combo.currentText(),
            "dungeon_card_priorities": [
                self.dungeon_priority_list.item(index).text()
                for index in range(self.dungeon_priority_list.count())
            ],
            "dungeon_max_buff_enabled": self.dungeon_max_buff_checkbox.isChecked(),
            "dungeon_max_buff_percent": self._int_from_input(self.dungeon_max_buff_input),
            "dungeon_max_debuff_enabled": self.dungeon_max_debuff_checkbox.isChecked(),
            "dungeon_max_debuff_percent": self._int_from_input(self.dungeon_max_debuff_input),
            "odyssey_macro_enabled": self.odyssey_macro_checkbox.isChecked(),
            "odyssey_auto_card_selection": self.odyssey_auto_card_checkbox.isChecked(),
            "odyssey_auto_pick_card": self.odyssey_auto_card_checkbox.isChecked(),
            "odyssey_card_priorities": self._priority_list_values(self.odyssey_card_priority_list),
            "odyssey_auto_character_card": self.odyssey_auto_character_card_checkbox.isChecked(),
            "odyssey_character": self.odyssey_character_combo.currentText(),
            "odyssey_character_card_priorities": self._priority_list_values(
                self.odyssey_character_card_priority_list
            ),
            "odyssey_auto_next_room": self.odyssey_auto_next_checkbox.isChecked(),
            "odyssey_room_priorities": [
                self.odyssey_priority_1_combo.currentText(),
                self.odyssey_priority_2_combo.currentText(),
                self.odyssey_priority_3_combo.currentText(),
            ],
            "odyssey_check_treasure_room": self.odyssey_check_treasure_checkbox.isChecked(),
            "odyssey_check_unit_reward": self.odyssey_check_unit_reward_checkbox.isChecked(),
            "odyssey_auto_shop_room": self.odyssey_auto_shop_checkbox.isChecked(),
            "odyssey_auto_memoria_selection": self.odyssey_auto_memoria_checkbox.isChecked(),
            "odyssey_memoria_priorities": self._priority_list_values(self.odyssey_memoria_priority_list),
            "odyssey_only_buy_when_enough": self.odyssey_only_buy_when_enough_checkbox.isChecked(),
        }

    def _build_ui(self, settings: dict) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setFixedWidth(192)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(0)

        sidebar_header = QLabel("SETTINGS")
        sidebar_header.setObjectName("settingsSidebarHeader")
        sidebar_layout.addWidget(sidebar_header)
        sidebar_layout.addSpacing(16)

        self.general_tab_button = self._make_nav_button("General")
        self.card_tab_button = self._make_nav_button("Card")
        self.odyssey_tab_button = self._make_nav_button("Odyssey")
        self.general_tab_button.clicked.connect(lambda: self._set_settings_tab("General"))
        self.card_tab_button.clicked.connect(lambda: self._set_settings_tab("Card"))
        self.odyssey_tab_button.clicked.connect(lambda: self._set_settings_tab("Odyssey"))
        sidebar_layout.addWidget(self.general_tab_button)
        sidebar_layout.addSpacing(4)
        sidebar_layout.addWidget(self.card_tab_button)
        sidebar_layout.addSpacing(4)
        sidebar_layout.addWidget(self.odyssey_tab_button)
        sidebar_layout.addStretch(1)

        root_layout.addWidget(sidebar)

        content_shell = QFrame()
        content_shell.setObjectName("settingsContentShell")
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("settingsContentStack")
        self.content_stack.addWidget(self._build_general_page(settings))
        self.content_stack.addWidget(self._build_card_page(settings))
        self.content_stack.addWidget(self._build_odyssey_page(settings))
        content_layout.addWidget(self.content_stack, 1)

        self.top_close_button = QPushButton("X", content_shell)
        self.top_close_button.setObjectName("settingsTopCloseButton")
        self.top_close_button.setCursor(Qt.PointingHandCursor)
        self.top_close_button.clicked.connect(self.reject)
        self.top_close_button.setGeometry(content_shell.width() - 40, 24, 16, 16)
        self.top_close_button.raise_()

        footer = QFrame()
        footer.setObjectName("settingsFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 16)
        footer_layout.setSpacing(12)
        footer_layout.addStretch(1)

        self.close_button = QPushButton("DISCARD CHANGES")
        self.close_button.setObjectName("settingsDiscardButton")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.reject)
        footer_layout.addWidget(self.close_button)

        self.save_button = QPushButton("SAVE CHANGES")
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self._on_save)
        footer_layout.addWidget(self.save_button)

        content_layout.addWidget(footer)
        root_layout.addWidget(content_shell, 1)

        self.legend_card_checkbox.toggled.connect(self.legend_card_combo.setEnabled)
        self.legend_card_checkbox.toggled.connect(self.legend_card_label.setEnabled)
        self.legend_card_checkbox.toggled.connect(self.legend_select_row.setEnabled)
        self.legend_card_combo.setEnabled(self.legend_card_checkbox.isChecked())
        self.legend_card_label.setEnabled(self.legend_card_checkbox.isChecked())
        self.legend_select_row.setEnabled(self.legend_card_checkbox.isChecked())
        self.force_restart_wave_checkbox.toggled.connect(self.force_restart_wave_input.setEnabled)
        self.force_restart_wave_input.setEnabled(self.force_restart_wave_checkbox.isChecked())
        self.odyssey_macro_checkbox.toggled.connect(self.odyssey_content.setVisible)
        self.odyssey_content.setVisible(self.odyssey_macro_checkbox.isChecked())
        self.odyssey_auto_card_checkbox.toggled.connect(self.odyssey_card_priority_section.setVisible)
        self.odyssey_card_priority_section.setVisible(self.odyssey_auto_card_checkbox.isChecked())
        self.odyssey_auto_character_card_checkbox.toggled.connect(self.odyssey_character_card_section.setVisible)
        self.odyssey_character_card_section.setVisible(self.odyssey_auto_character_card_checkbox.isChecked())
        self.odyssey_auto_memoria_checkbox.toggled.connect(self.odyssey_memoria_section.setVisible)
        self.odyssey_memoria_section.setVisible(self.odyssey_auto_memoria_checkbox.isChecked())

        self.dungeon_card_checkbox.toggled.connect(self._toggle_dungeon_controls)
        self.dungeon_max_buff_checkbox.toggled.connect(self.dungeon_max_buff_input.setEnabled)
        self.dungeon_max_debuff_checkbox.toggled.connect(self.dungeon_max_debuff_input.setEnabled)
        self.dungeon_max_buff_input.setEnabled(self.dungeon_max_buff_checkbox.isChecked())
        self.dungeon_max_debuff_input.setEnabled(self.dungeon_max_debuff_checkbox.isChecked())
        self._toggle_dungeon_controls(self.dungeon_card_checkbox.isChecked())

    def _build_general_page(self, settings: dict) -> QScrollArea:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(24, 24, 24, 24)
        page_layout.setSpacing(0)

        column = QWidget()
        column.setObjectName("settingsPageColumn")
        column.setMaximumWidth(672)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(24)

        primary_section = QWidget()
        primary_layout = QVBoxLayout(primary_section)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.setSpacing(12)

        self.loop_radio = self._make_radio("Loop Endlessly", accent="emerald")
        self.stop_radio = self._make_radio("Stop After Completion", accent="white")
        if settings.get("replay") == "loop":
            self.loop_radio.setChecked(True)
        else:
            self.stop_radio.setChecked(True)
        self.anti_afk_checkbox = self._make_checkbox("Anti-AFK (every 5 min)", accent="emerald")
        self.anti_afk_checkbox.setChecked(settings.get("anti_afk", False))
        self.check_placed_checkbox = self._make_checkbox("Check Placed", accent="white")
        self.check_placed_checkbox.setChecked(settings.get("check_placed", False))
        self.disable_chat_checkbox = self._make_checkbox("Disable Chat", accent="white")
        self.disable_chat_checkbox.setChecked(settings.get("disable_chat", False))

        for widget in (
            self.loop_radio,
            self.stop_radio,
            self.anti_afk_checkbox,
            self.check_placed_checkbox,
            self.disable_chat_checkbox,
        ):
            primary_layout.addWidget(widget)
        column_layout.addWidget(primary_section)

        column_layout.addWidget(self._make_divider())

        force_restart_section = QWidget()
        force_restart_layout = QVBoxLayout(force_restart_section)
        force_restart_layout.setContentsMargins(0, 16, 0, 0)
        force_restart_layout.setSpacing(12)

        force_restart_row = QHBoxLayout()
        force_restart_row.setSpacing(16)
        self.force_restart_wave_checkbox = self._make_checkbox("Force Restart Wave", accent="white")
        self.force_restart_wave_checkbox.setChecked(settings.get("force_restart_wave_enabled", False))
        force_restart_row.addWidget(self.force_restart_wave_checkbox)
        force_restart_row.addStretch(1)
        force_restart_layout.addLayout(force_restart_row)

        force_restart_input_row = QHBoxLayout()
        force_restart_input_row.setContentsMargins(28, 0, 0, 0)
        force_restart_input_row.setSpacing(16)
        force_restart_label = self._make_field_label("Wave Number", 192)
        force_restart_input_row.addWidget(force_restart_label)
        self.force_restart_wave_input = self._make_number_input(str(settings.get("force_restart_wave", 0) or 0))
        self.force_restart_wave_input.setPlaceholderText("Wave")
        force_restart_input_row.addWidget(self.force_restart_wave_input)
        force_restart_input_row.addStretch(1)
        force_restart_layout.addLayout(force_restart_input_row)
        column_layout.addWidget(force_restart_section)

        column_layout.addWidget(self._make_divider())

        wait_section = QWidget()
        wait_layout = QVBoxLayout(wait_section)
        wait_layout.setContentsMargins(0, 16, 0, 0)
        wait_layout.setSpacing(16)

        self.wait_between_clicks_input = self._make_number_input(
            self._format_float(settings.get("wait_between_clicks", 0.2), 0.2)
        )
        self.wait_between_key_input = self._make_number_input(
            self._format_float(settings.get("wait_between_key_presses", 0.2), 0.2)
        )
        self.wait_between_steps_input = self._make_number_input(
            self._format_float(settings.get("wait_between_steps", 0.0), 0.0)
        )

        wait_layout.addLayout(self._make_wait_row("Wait Between Click", self.wait_between_clicks_input))
        wait_layout.addLayout(self._make_wait_row("Wait Between Key Press", self.wait_between_key_input))
        wait_layout.addLayout(self._make_wait_row("Wait Between Steps", self.wait_between_steps_input))
        column_layout.addWidget(wait_section)

        column_layout.addWidget(self._make_divider())

        extra_section = QWidget()
        extra_layout = QVBoxLayout(extra_section)
        extra_layout.setContentsMargins(0, 16, 0, 0)
        extra_layout.setSpacing(12)
        self.relative_positioning_checkbox = self._make_checkbox("Relative positioning", accent="white")
        self.relative_positioning_checkbox.setChecked(settings.get("relative_positioning", False))
        self.reposition_camera_checkbox = self._make_checkbox("Reposition camera on start", accent="white")
        self.reposition_camera_checkbox.setChecked(settings.get("reposition_camera_on_start", False))
        extra_layout.addWidget(self.relative_positioning_checkbox)
        extra_layout.addWidget(self.reposition_camera_checkbox)
        column_layout.addWidget(extra_section)

        column_layout.addStretch(1)
        page_layout.addWidget(column)
        page_layout.addStretch(1)
        return self._wrap_scroll_area(page)

    def _build_card_page(self, settings: dict) -> QScrollArea:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(24, 24, 16, 24)
        page_layout.setSpacing(0)

        column = QWidget()
        column.setObjectName("settingsPageColumn")
        column.setMaximumWidth(768)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(24)

        legend_section = QWidget()
        legend_layout = QVBoxLayout(legend_section)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(16)
        self.legend_card_checkbox = self._make_checkbox("Card Selection (Legend)", accent="white")
        self.legend_card_checkbox.setChecked(settings.get("card_selection_legend", False))
        legend_layout.addWidget(self.legend_card_checkbox)

        self.legend_select_row = QWidget()
        legend_row_layout = QHBoxLayout(self.legend_select_row)
        legend_row_layout.setContentsMargins(28, 0, 0, 0)
        legend_row_layout.setSpacing(16)
        self.legend_card_label = self._make_field_label("Select Card:", 128)
        legend_row_layout.addWidget(self.legend_card_label)
        self.legend_card_combo = self._make_combo_box(LEGEND_CARD_OPTIONS)
        selected_card = str(settings.get("legend_selected_card", "Immunity"))
        selected_index = self.legend_card_combo.findText(selected_card)
        self.legend_card_combo.setCurrentIndex(max(0, selected_index))
        legend_row_layout.addWidget(self.legend_card_combo, 1)
        legend_layout.addWidget(self.legend_select_row)
        column_layout.addWidget(legend_section)

        column_layout.addWidget(self._make_divider())

        dungeon_section = QWidget()
        dungeon_layout = QVBoxLayout(dungeon_section)
        dungeon_layout.setContentsMargins(0, 16, 0, 0)
        dungeon_layout.setSpacing(16)
        self.dungeon_card_checkbox = self._make_checkbox("Card Selection (Dungeon)", accent="emerald")
        self.dungeon_card_checkbox.setChecked(settings.get("card_selection_dungeon", False))
        dungeon_layout.addWidget(self.dungeon_card_checkbox)

        self.dungeon_content = QWidget()
        dungeon_content_layout = QVBoxLayout(self.dungeon_content)
        dungeon_content_layout.setContentsMargins(28, 0, 0, 0)
        dungeon_content_layout.setSpacing(16)

        starter_row = QHBoxLayout()
        starter_row.setSpacing(16)
        self.dungeon_starter_label = self._make_field_label("Starter Card\nSelection:", 192)
        self.dungeon_starter_label.setWordWrap(True)
        starter_row.addWidget(self.dungeon_starter_label)
        self.dungeon_starter_combo = self._make_combo_box(list(STARTER_CARD_SPECS.keys()))
        starter_choice = str(settings.get("dungeon_starter_card", "Money Surge"))
        starter_index = self.dungeon_starter_combo.findText(starter_choice)
        self.dungeon_starter_combo.setCurrentIndex(max(0, starter_index))
        starter_row.addWidget(self.dungeon_starter_combo, 1)
        dungeon_content_layout.addLayout(starter_row)

        priority_label_row = QHBoxLayout()
        priority_label_row.setSpacing(16)
        priority_text = QLabel("Card Selection Priority:")
        priority_text.setObjectName("settingsDungeonPriorityLabel")
        priority_label_row.addWidget(priority_text)
        priority_label_row.addStretch(1)
        self.dungeon_add_card_button = QPushButton("Add Card")
        self.dungeon_add_card_button.setObjectName("settingsListActionButton")
        self.dungeon_add_card_button.setCursor(Qt.PointingHandCursor)
        self.dungeon_add_card_button.clicked.connect(self._show_dungeon_priority_menu)
        priority_label_row.addWidget(self.dungeon_add_card_button)
        dungeon_content_layout.addLayout(priority_label_row)

        self.dungeon_priority_frame = QFrame()
        self.dungeon_priority_frame.setObjectName("settingsPriorityListFrame")
        priority_frame_layout = QVBoxLayout(self.dungeon_priority_frame)
        priority_frame_layout.setContentsMargins(12, 12, 12, 12)
        priority_frame_layout.setSpacing(8)
        self.dungeon_priority_items_container = QWidget()
        self.dungeon_priority_items_layout = QVBoxLayout(self.dungeon_priority_items_container)
        self.dungeon_priority_items_layout.setContentsMargins(0, 0, 0, 0)
        self.dungeon_priority_items_layout.setSpacing(8)
        priority_frame_layout.addWidget(self.dungeon_priority_items_container)
        dungeon_content_layout.addWidget(self.dungeon_priority_frame)

        self.dungeon_priority_list = QListWidget()
        self.dungeon_priority_list.hide()
        for label in settings.get("dungeon_card_priorities", []):
            if label in WAVE_CARD_SPECS:
                self.dungeon_priority_list.addItem(QListWidgetItem(label))
        dungeon_content_layout.addWidget(self.dungeon_priority_list)
        self._render_priority_rows()

        buff_row = QHBoxLayout()
        buff_row.setSpacing(16)
        buff_toggle_row = QHBoxLayout()
        buff_toggle_row.setSpacing(12)
        self.dungeon_max_buff_checkbox = self._make_checkbox("Max Buff", accent="white")
        self.dungeon_max_buff_checkbox.setChecked(settings.get("dungeon_max_buff_enabled", False))
        self.dungeon_max_buff_checkbox.setFixedWidth(140)
        buff_toggle_row.addWidget(self.dungeon_max_buff_checkbox)
        buff_row.addLayout(buff_toggle_row)
        self.dungeon_max_buff_input = self._make_percent_input(str(settings.get("dungeon_max_buff_percent", 0) or 0))
        buff_row.addWidget(self.dungeon_max_buff_input)
        buff_unit = QLabel("%")
        buff_unit.setObjectName("settingsUnitLabel")
        buff_row.addWidget(buff_unit)
        buff_row.addStretch(1)
        dungeon_content_layout.addLayout(buff_row)

        debuff_row = QHBoxLayout()
        debuff_row.setSpacing(16)
        debuff_toggle_row = QHBoxLayout()
        debuff_toggle_row.setSpacing(12)
        self.dungeon_max_debuff_checkbox = self._make_checkbox("Max Debuff", accent="white")
        self.dungeon_max_debuff_checkbox.setChecked(settings.get("dungeon_max_debuff_enabled", False))
        self.dungeon_max_debuff_checkbox.setFixedWidth(140)
        debuff_toggle_row.addWidget(self.dungeon_max_debuff_checkbox)
        debuff_row.addLayout(debuff_toggle_row)
        self.dungeon_max_debuff_input = self._make_percent_input(str(settings.get("dungeon_max_debuff_percent", 0) or 0))
        debuff_row.addWidget(self.dungeon_max_debuff_input)
        debuff_unit = QLabel("%")
        debuff_unit.setObjectName("settingsUnitLabel")
        debuff_row.addWidget(debuff_unit)
        debuff_row.addStretch(1)
        dungeon_content_layout.addLayout(debuff_row)

        dungeon_layout.addWidget(self.dungeon_content)
        column_layout.addWidget(dungeon_section)
        column_layout.addStretch(1)

        page_layout.addWidget(column)
        page_layout.addStretch(1)
        return self._wrap_scroll_area(page)

    def _build_odyssey_page(self, settings: dict) -> QScrollArea:
        page = QWidget()
        page_layout = QHBoxLayout(page)
        page_layout.setContentsMargins(24, 24, 24, 24)
        page_layout.setSpacing(0)

        column = QWidget()
        column.setObjectName("settingsPageColumn")
        column.setMaximumWidth(672)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(24)

        odyssey_section = QWidget()
        odyssey_layout = QVBoxLayout(odyssey_section)
        odyssey_layout.setContentsMargins(0, 0, 0, 0)
        odyssey_layout.setSpacing(16)

        self.odyssey_macro_checkbox = self._make_checkbox("Odyssey Macro", accent="emerald")
        self.odyssey_macro_checkbox.setChecked(settings.get("odyssey_macro_enabled", False))
        odyssey_layout.addWidget(self.odyssey_macro_checkbox)

        self.odyssey_content = QWidget()
        odyssey_content_layout = QVBoxLayout(self.odyssey_content)
        odyssey_content_layout.setContentsMargins(28, 0, 0, 0)
        odyssey_content_layout.setSpacing(12)
        auto_card_default = settings.get("odyssey_auto_card_selection", settings.get("odyssey_auto_pick_card", True))
        self.odyssey_auto_card_checkbox = self._make_checkbox("Auto Card selection", accent="white")
        self.odyssey_auto_card_checkbox.setChecked(auto_card_default)
        self.odyssey_auto_pick_checkbox = self.odyssey_auto_card_checkbox
        odyssey_content_layout.addWidget(self.odyssey_auto_card_checkbox)
        self.odyssey_card_priority_section = self._build_priority_editor(
            "Card Priority",
            ODYSSEY_CARD_OPTIONS,
            settings.get("odyssey_card_priorities", []),
            "Add Card",
            "odyssey_card",
        )
        odyssey_content_layout.addWidget(self.odyssey_card_priority_section)

        self.odyssey_auto_character_card_checkbox = self._make_checkbox("Auto choose character card", accent="white")
        self.odyssey_auto_character_card_checkbox.setChecked(settings.get("odyssey_auto_character_card", False))
        odyssey_content_layout.addWidget(self.odyssey_auto_character_card_checkbox)
        self.odyssey_character_card_section = QWidget()
        character_card_layout = QVBoxLayout(self.odyssey_character_card_section)
        character_card_layout.setContentsMargins(0, 0, 0, 0)
        character_card_layout.setSpacing(12)
        character_row = QHBoxLayout()
        character_row.setSpacing(16)
        character_label = self._make_field_label("Character:", 128)
        character_row.addWidget(character_label)
        self.odyssey_character_combo = self._make_combo_box(ODYSSEY_CHARACTER_OPTIONS)
        self.odyssey_character_combo.setCurrentText(settings.get("odyssey_character", "Madara"))
        character_row.addWidget(self.odyssey_character_combo)
        character_row.addStretch(1)
        character_card_layout.addLayout(character_row)
        character_card_layout.addWidget(
            self._build_priority_editor(
                "Character Card Priority",
                ODYSSEY_CHARACTER_CARD_OPTIONS.get(self.odyssey_character_combo.currentText(), []),
                settings.get("odyssey_character_card_priorities", []),
                "Add Card",
                "odyssey_character_card",
            )
        )
        odyssey_content_layout.addWidget(self.odyssey_character_card_section)

        self.odyssey_auto_next_checkbox = self._make_checkbox("Auto next room", accent="white")
        self.odyssey_auto_next_checkbox.setChecked(settings.get("odyssey_auto_next_room", True))
        odyssey_content_layout.addWidget(self.odyssey_auto_next_checkbox)
        self.odyssey_check_treasure_checkbox = self._make_checkbox("Check Treasure Room", accent="white")
        self.odyssey_check_treasure_checkbox.setChecked(settings.get("odyssey_check_treasure_room", False))
        odyssey_content_layout.addWidget(self.odyssey_check_treasure_checkbox)
        self.odyssey_check_unit_reward_checkbox = self._make_checkbox("Check for unit reward", accent="white")
        self.odyssey_check_unit_reward_checkbox.setChecked(settings.get("odyssey_check_unit_reward", False))
        odyssey_content_layout.addWidget(self.odyssey_check_unit_reward_checkbox)
        self.odyssey_auto_shop_checkbox = self._make_checkbox("Auto shop room", accent="white")
        self.odyssey_auto_shop_checkbox.setChecked(settings.get("odyssey_auto_shop_room", False))
        odyssey_content_layout.addWidget(self.odyssey_auto_shop_checkbox)
        self.odyssey_auto_memoria_checkbox = self._make_checkbox("Auto Memoria Selection", accent="white")
        self.odyssey_auto_memoria_checkbox.setChecked(settings.get("odyssey_auto_memoria_selection", False))
        odyssey_content_layout.addWidget(self.odyssey_auto_memoria_checkbox)
        self.odyssey_memoria_section = QWidget()
        memoria_layout = QVBoxLayout(self.odyssey_memoria_section)
        memoria_layout.setContentsMargins(0, 0, 0, 0)
        memoria_layout.setSpacing(12)
        memoria_layout.addWidget(
            self._build_priority_editor(
                "Memoria Priority",
                ODYSSEY_MEMORIA_OPTIONS,
                settings.get("odyssey_memoria_priorities", []),
                "Add Memoria",
                "odyssey_memoria",
            )
        )
        self.odyssey_only_buy_when_enough_checkbox = self._make_checkbox("Only buy when enough", accent="white")
        self.odyssey_only_buy_when_enough_checkbox.setChecked(settings.get("odyssey_only_buy_when_enough", True))
        memoria_layout.addWidget(self.odyssey_only_buy_when_enough_checkbox)
        odyssey_content_layout.addWidget(self.odyssey_memoria_section)

        priority_section = QWidget()
        priority_layout = QVBoxLayout(priority_section)
        priority_layout.setContentsMargins(0, 8, 0, 0)
        priority_layout.setSpacing(12)
        priority_label = QLabel("Room Priority")
        priority_label.setObjectName("settingsDungeonPriorityLabel")
        priority_layout.addWidget(priority_label)

        raw_priorities = settings.get("odyssey_room_priorities", ["Normal", "Shop", "Boss"])
        priorities = self._normalize_odyssey_priorities(raw_priorities)
        self.odyssey_priority_1_combo = self._make_combo_box(ODYSSEY_ROOM_OPTIONS)
        self.odyssey_priority_2_combo = self._make_combo_box(ODYSSEY_ROOM_OPTIONS)
        self.odyssey_priority_3_combo = self._make_combo_box(ODYSSEY_ROOM_OPTIONS)
        for combo, value in (
            (self.odyssey_priority_1_combo, priorities[0]),
            (self.odyssey_priority_2_combo, priorities[1]),
            (self.odyssey_priority_3_combo, priorities[2]),
        ):
            combo.setCurrentText(value)
        priority_layout.addLayout(self._make_odyssey_priority_row("1st priority:", self.odyssey_priority_1_combo))
        priority_layout.addLayout(self._make_odyssey_priority_row("2nd priority:", self.odyssey_priority_2_combo))
        priority_layout.addLayout(self._make_odyssey_priority_row("3rd priority:", self.odyssey_priority_3_combo))
        odyssey_content_layout.addWidget(priority_section)
        odyssey_layout.addWidget(self.odyssey_content)

        column_layout.addWidget(odyssey_section)
        column_layout.addStretch(1)
        page_layout.addWidget(column)
        page_layout.addStretch(1)
        return self._wrap_scroll_area(page)

    def _make_nav_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("settingsNavButton")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(36)
        return button

    def _make_checkbox(self, text: str, accent: str) -> QCheckBox:
        checkbox = QCheckBox(text)
        checkbox.setProperty("accent", accent)
        checkbox.setCursor(Qt.PointingHandCursor)
        checkbox.setObjectName("settingsCheckbox")
        return checkbox

    def _make_radio(self, text: str, accent: str) -> QRadioButton:
        radio = QRadioButton(text)
        radio.setProperty("accent", accent)
        radio.setCursor(Qt.PointingHandCursor)
        radio.setObjectName("settingsRadio")
        return radio

    def _make_field_label(self, text: str, width: int) -> QLabel:
        label = QLabel(text)
        label.setObjectName("settingsFieldLabel")
        label.setFixedWidth(width)
        return label

    def _make_number_input(self, value: str) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setText(value)
        line_edit.setFixedSize(128, 36)
        line_edit.setObjectName("settingsNumberInput")
        return line_edit

    def _make_percent_input(self, value: str) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setText(value)
        line_edit.setFixedSize(96, 36)
        line_edit.setObjectName("settingsPercentInput")
        return line_edit

    def _make_combo_box(self, options: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("settingsComboBox")
        combo.setFixedHeight(36)
        combo.addItems(options)
        return combo

    def _make_wait_row(self, label_text: str, input_widget: QLineEdit) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        label = self._make_field_label(label_text, 192)
        label.setObjectName("settingsWaitLabel")
        row.addWidget(label)
        row.addWidget(input_widget)
        unit = QLabel("SEC")
        unit.setObjectName("settingsUnitLabel")
        row.addWidget(unit)
        row.addStretch(1)
        return row

    def _make_odyssey_priority_row(self, label_text: str, combo: QComboBox) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        label = self._make_field_label(label_text, 128)
        row.addWidget(label)
        combo.setFixedWidth(180)
        row.addWidget(combo)
        row.addStretch(1)
        return row

    @staticmethod
    def _normalize_odyssey_priorities(raw_priorities) -> list[str]:
        normalized: list[str] = []
        if isinstance(raw_priorities, (list, tuple)):
            for raw_priority in raw_priorities:
                text = str(raw_priority).strip().lower()
                for option in ODYSSEY_ROOM_OPTIONS:
                    if text == option.lower() and option not in normalized:
                        normalized.append(option)
                        break
        for option in ODYSSEY_ROOM_OPTIONS:
            if option not in normalized:
                normalized.append(option)
        return normalized[:3]

    def _build_priority_editor(
        self,
        title: str,
        options: list[str],
        selected_labels,
        add_button_text: str,
        prefix: str,
    ) -> QWidget:
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)

        label_row = QHBoxLayout()
        label_row.setSpacing(16)
        title_label = QLabel(title)
        title_label.setObjectName("settingsDungeonPriorityLabel")
        label_row.addWidget(title_label)
        label_row.addStretch(1)
        add_button = QPushButton(add_button_text)
        add_button.setObjectName("settingsListActionButton")
        add_button.setCursor(Qt.PointingHandCursor)
        label_row.addWidget(add_button)
        section_layout.addLayout(label_row)

        frame = QFrame()
        frame.setObjectName("settingsPriorityListFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(8)
        items_container = QWidget()
        items_layout = QVBoxLayout(items_container)
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(8)
        frame_layout.addWidget(items_container)
        section_layout.addWidget(frame)

        list_widget = QListWidget()
        list_widget.hide()
        valid_options = list(dict.fromkeys(options))
        initial_labels = selected_labels if isinstance(selected_labels, (list, tuple)) else []
        for label in initial_labels:
            if label in valid_options and not self._priority_list_contains(list_widget, label):
                list_widget.addItem(QListWidgetItem(label))
        section_layout.addWidget(list_widget)

        setattr(self, f"{prefix}_priority_list", list_widget)
        setattr(self, f"{prefix}_priority_items_layout", items_layout)
        setattr(self, f"{prefix}_priority_options", valid_options)

        add_button.clicked.connect(
            lambda _checked=False, list_widget=list_widget, items_layout=items_layout, options=valid_options, button=add_button: (
                self._show_generic_priority_menu(list_widget, items_layout, options, button)
            )
        )
        self._render_generic_priority_rows(list_widget, items_layout)
        return section

    @staticmethod
    def _priority_list_values(list_widget: QListWidget) -> list[str]:
        return [list_widget.item(index).text() for index in range(list_widget.count())]

    @staticmethod
    def _priority_list_contains(list_widget: QListWidget, label: str) -> bool:
        return any(list_widget.item(index).text() == label for index in range(list_widget.count()))

    def _show_generic_priority_menu(
        self,
        list_widget: QListWidget,
        items_layout: QVBoxLayout,
        options: list[str],
        button: QPushButton,
    ) -> None:
        menu = QMenu(self)
        menu.setObjectName("settingsPriorityMenu")
        existing_labels = set(self._priority_list_values(list_widget))
        for label in options:
            action = QAction(label, menu)
            action.setEnabled(label not in existing_labels)
            action.triggered.connect(
                lambda _checked=False, value=label: self._add_generic_priority_item(
                    list_widget,
                    items_layout,
                    value,
                )
            )
            menu.addAction(action)
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _add_generic_priority_item(
        self,
        list_widget: QListWidget,
        items_layout: QVBoxLayout,
        label: str,
    ) -> None:
        if self._priority_list_contains(list_widget, label):
            return
        list_widget.addItem(QListWidgetItem(label))
        self._render_generic_priority_rows(list_widget, items_layout)

    def _remove_generic_priority_item(
        self,
        list_widget: QListWidget,
        items_layout: QVBoxLayout,
        row: int,
    ) -> None:
        if row >= 0:
            list_widget.takeItem(row)
            self._render_generic_priority_rows(list_widget, items_layout)

    def _move_generic_priority_item(
        self,
        list_widget: QListWidget,
        items_layout: QVBoxLayout,
        row: int,
        offset: int,
    ) -> None:
        if row < 0:
            return
        target = row + offset
        if target < 0 or target >= list_widget.count():
            return
        item = list_widget.takeItem(row)
        list_widget.insertItem(target, item)
        list_widget.setCurrentRow(target)
        self._render_generic_priority_rows(list_widget, items_layout)

    def _render_generic_priority_rows(
        self,
        list_widget: QListWidget,
        items_layout: QVBoxLayout,
    ) -> None:
        while items_layout.count():
            item = items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index in range(list_widget.count()):
            label = list_widget.item(index).text()
            row = QFrame()
            row.setObjectName("settingsPriorityItem")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 12, 12, 12)
            row_layout.setSpacing(8)

            name = QLabel(label)
            name.setObjectName("settingsPriorityName")
            row_layout.addWidget(name, 1)

            buttons = QHBoxLayout()
            buttons.setSpacing(8)
            up_button = QPushButton("^")
            up_button.setObjectName("settingsPriorityControlButton")
            up_button.setCursor(Qt.PointingHandCursor)
            up_button.setEnabled(index > 0)
            up_button.clicked.connect(
                lambda _checked=False, row_index=index: self._move_generic_priority_item(
                    list_widget,
                    items_layout,
                    row_index,
                    -1,
                )
            )
            buttons.addWidget(up_button)

            down_button = QPushButton("v")
            down_button.setObjectName("settingsPriorityControlButton")
            down_button.setCursor(Qt.PointingHandCursor)
            down_button.setEnabled(index < list_widget.count() - 1)
            down_button.clicked.connect(
                lambda _checked=False, row_index=index: self._move_generic_priority_item(
                    list_widget,
                    items_layout,
                    row_index,
                    1,
                )
            )
            buttons.addWidget(down_button)

            delete_button = QPushButton("x")
            delete_button.setObjectName("settingsPriorityDeleteButton")
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.clicked.connect(
                lambda _checked=False, row_index=index: self._remove_generic_priority_item(
                    list_widget,
                    items_layout,
                    row_index,
                )
            )
            buttons.addWidget(delete_button)
            row_layout.addLayout(buttons)
            items_layout.addWidget(row)
        items_layout.addStretch(1)

    def _make_divider(self) -> QFrame:
        divider = QFrame()
        divider.setObjectName("settingsDivider")
        divider.setFixedHeight(1)
        return divider

    def _wrap_scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("settingsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        return scroll

    def _set_settings_tab(self, tab_name: str) -> None:
        self._settings_tab = tab_name
        general_active = tab_name == "General"
        card_active = tab_name == "Card"
        odyssey_active = tab_name == "Odyssey"
        self.general_tab_button.setChecked(general_active)
        self.card_tab_button.setChecked(card_active)
        self.odyssey_tab_button.setChecked(odyssey_active)
        tab_indices = {"General": 0, "Card": 1, "Odyssey": 2}
        self.content_stack.setCurrentIndex(tab_indices.get(tab_name, 0))
        self._refresh_nav_button_style(self.general_tab_button)
        self._refresh_nav_button_style(self.card_tab_button)
        self._refresh_nav_button_style(self.odyssey_tab_button)

    def _refresh_nav_button_style(self, button: QPushButton) -> None:
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def _show_dungeon_priority_menu(self) -> None:
        menu = QMenu(self)
        menu.setObjectName("settingsPriorityMenu")
        existing_labels = {
            self.dungeon_priority_list.item(index).text()
            for index in range(self.dungeon_priority_list.count())
        }

        for group_name, labels in DUNGEON_PRIORITY_GROUPS:
            section = QAction(group_name, menu)
            section.setEnabled(False)
            menu.addAction(section)
            for label in labels:
                spec = WAVE_CARD_SPECS[label]
                action = QAction(label, menu)
                action.setEnabled(
                    spec.enabled and spec.file_path is not None and spec.file_path.exists() and label not in existing_labels
                )
                action.triggered.connect(lambda _checked=False, value=label: self._add_priority_item(value))
                menu.addAction(action)
            menu.addSeparator()
        if menu.actions():
            menu.actions()[-1].setVisible(False)
        menu.exec(self.dungeon_add_card_button.mapToGlobal(self.dungeon_add_card_button.rect().bottomLeft()))

    def _add_priority_item(self, label: str) -> None:
        if any(self.dungeon_priority_list.item(index).text() == label for index in range(self.dungeon_priority_list.count())):
            return
        self.dungeon_priority_list.addItem(QListWidgetItem(label))
        self._render_priority_rows()

    def _remove_selected_priority_item(self, row: int | None = None) -> None:
        if row is None:
            row = self.dungeon_priority_list.currentRow()
        if row >= 0:
            self.dungeon_priority_list.takeItem(row)
            self._render_priority_rows()

    def _move_priority_item(self, offset: int, row: int | None = None) -> None:
        if row is None:
            row = self.dungeon_priority_list.currentRow()
        if row < 0:
            return
        target = row + offset
        if target < 0 or target >= self.dungeon_priority_list.count():
            return
        item = self.dungeon_priority_list.takeItem(row)
        self.dungeon_priority_list.insertItem(target, item)
        self.dungeon_priority_list.setCurrentRow(target)
        self._render_priority_rows()

    def _render_priority_rows(self) -> None:
        while self.dungeon_priority_items_layout.count():
            item = self.dungeon_priority_items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index in range(self.dungeon_priority_list.count()):
            label = self.dungeon_priority_list.item(index).text()
            row = QFrame()
            row.setObjectName("settingsPriorityItem")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 12, 12, 12)
            row_layout.setSpacing(8)

            name = QLabel(label)
            name.setObjectName("settingsPriorityName")
            row_layout.addWidget(name, 1)

            buttons = QHBoxLayout()
            buttons.setSpacing(8)

            up_button = QPushButton("^")
            up_button.setObjectName("settingsPriorityControlButton")
            up_button.setCursor(Qt.PointingHandCursor)
            up_button.setEnabled(index > 0)
            up_button.clicked.connect(lambda _checked=False, row_index=index: self._move_priority_item(-1, row_index))
            buttons.addWidget(up_button)

            down_button = QPushButton("v")
            down_button.setObjectName("settingsPriorityControlButton")
            down_button.setCursor(Qt.PointingHandCursor)
            down_button.setEnabled(index < self.dungeon_priority_list.count() - 1)
            down_button.clicked.connect(lambda _checked=False, row_index=index: self._move_priority_item(1, row_index))
            buttons.addWidget(down_button)

            delete_button = QPushButton("x")
            delete_button.setObjectName("settingsPriorityDeleteButton")
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.clicked.connect(
                lambda _checked=False, row_index=index: self._remove_selected_priority_item(row_index)
            )
            buttons.addWidget(delete_button)

            row_layout.addLayout(buttons)
            self.dungeon_priority_items_layout.addWidget(row)

        self.dungeon_priority_items_layout.addStretch(1)

    def _toggle_dungeon_controls(self, enabled: bool) -> None:
        self.dungeon_content.setEnabled(enabled)

    @staticmethod
    def _int_from_input(line_edit: QLineEdit) -> int:
        text = line_edit.text().strip()
        if not text:
            return 0
        try:
            return int(text)
        except ValueError:
            return 0

    @staticmethod
    def _float_from_input(line_edit: QLineEdit, default: float) -> float:
        text = line_edit.text().strip()
        if not text:
            return default
        try:
            return max(0.0, float(text))
        except ValueError:
            return default

    @staticmethod
    def _format_float(value, default: float) -> str:
        try:
            parsed = max(0.0, float(value))
        except (TypeError, ValueError):
            parsed = default
        if parsed.is_integer():
            return f"{parsed:.1f}"
        return f"{parsed:g}"

    def _on_save(self) -> None:
        self._saved = True
        self.accept()

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet(
            resolve_stylesheet_asset_urls(
                """
            QDialog#settingsDialog {
                background-color: #0c0c0c;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QFrame#settingsSidebar {
                background-color: rgba(255, 255, 255, 0.02);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
            QLabel#settingsSidebarHeader {
                color: #ffffff;
                font-family: "Space Mono";
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 2px;
            }
            QPushButton#settingsNavButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.5);
                border: none;
                border-radius: 4px;
                text-align: left;
                padding: 8px 12px;
                font-family: "Space Mono";
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#settingsNavButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #ffffff;
            }
            QPushButton#settingsNavButton:checked {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
            }
            QFrame#settingsContentShell {
                background-color: transparent;
            }
            QPushButton#settingsTopCloseButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.4);
                border: none;
                font-family: "Space Mono";
                font-size: 18px;
                font-weight: 600;
                padding: 0px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton#settingsTopCloseButton:hover {
                color: #ffffff;
            }
            QScrollArea#settingsScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea#settingsScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
            }
            QLabel#settingsWaitLabel,
            QLabel#settingsFieldLabel,
            QLabel#settingsDungeonPriorityLabel {
                color: rgba(255, 255, 255, 0.6);
                font-family: "Space Mono";
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#settingsUnitLabel {
                color: rgba(255, 255, 255, 0.4);
                font-family: "Space Mono";
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QRadioButton#settingsRadio,
            QCheckBox#settingsCheckbox {
                color: rgba(255, 255, 255, 0.8);
                font-family: "Space Mono";
                font-size: 14px;
                font-weight: 500;
                spacing: 12px;
            }
            QRadioButton#settingsRadio:hover,
            QCheckBox#settingsCheckbox:hover {
                color: #ffffff;
            }
            QRadioButton#settingsRadio::indicator,
            QCheckBox#settingsCheckbox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: transparent;
            }
            QRadioButton#settingsRadio::indicator:hover,
            QCheckBox#settingsCheckbox::indicator:hover {
                border-color: rgba(255, 255, 255, 0.25);
            }
            QRadioButton#settingsRadio[accent="emerald"]::indicator:checked,
            QCheckBox#settingsCheckbox[accent="emerald"]::indicator:checked {
                background: #10b981;
                border: 1px solid #10b981;
                image: url(references/checkmark.svg);
            }
            QRadioButton#settingsRadio[accent="white"]::indicator:checked,
            QCheckBox#settingsCheckbox[accent="white"]::indicator:checked {
                background: #ffffff;
                border: 1px solid #ffffff;
                image: url(references/checkmark.svg);
            }
            QLineEdit#settingsNumberInput,
            QLineEdit#settingsPercentInput,
            QComboBox#settingsComboBox {
                background-color: rgba(255, 255, 255, 0.04);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 0px 12px;
                font-family: "Space Mono";
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit#settingsNumberInput:focus,
            QLineEdit#settingsPercentInput:focus,
            QComboBox#settingsComboBox:focus {
                border-color: rgba(255, 255, 255, 0.2);
            }
            QComboBox#settingsComboBox {
                min-width: 96px;
            }
            QComboBox#settingsComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox#settingsComboBox QAbstractItemView {
                background-color: #161616;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.08);
                selection-background-color: rgba(255, 255, 255, 0.12);
                selection-color: #ffffff;
                font-family: "Space Mono";
                font-size: 13px;
            }
            QFrame#settingsDivider {
                background-color: rgba(255, 255, 255, 0.08);
            }
            QFrame#settingsFooter {
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }
            QPushButton#settingsDiscardButton,
            QPushButton#settingsSaveButton {
                min-height: 36px;
                border-radius: 4px;
                padding: 0px 24px;
                font-family: "Space Mono";
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#settingsDiscardButton {
                background-color: rgba(255, 255, 255, 0.04);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QPushButton#settingsDiscardButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
            QPushButton#settingsSaveButton {
                background-color: #10b981;
                color: #000000;
                border: none;
            }
            QPushButton#settingsSaveButton:hover {
                background-color: #0ea472;
            }
            QPushButton#settingsListActionButton {
                min-height: 32px;
                border-radius: 4px;
                padding: 0px 16px;
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: #ffffff;
                font-family: "Space Mono";
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#settingsListActionButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
            }
            QFrame#settingsPriorityListFrame {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
            }
            QFrame#settingsPriorityItem {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
            }
            QFrame#settingsPriorityItem:hover {
                border-color: rgba(255, 255, 255, 0.12);
            }
            QLabel#settingsPriorityName {
                color: #ffffff;
                font-family: "Space Mono";
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#settingsPriorityControlButton,
            QPushButton#settingsPriorityDeleteButton {
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 4px;
                padding: 0px;
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.6);
                font-family: "Space Mono";
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#settingsPriorityControlButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
            }
            QPushButton#settingsPriorityControlButton:disabled {
                opacity: 0.3;
            }
            QPushButton#settingsPriorityDeleteButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                border-color: rgba(239, 68, 68, 0.3);
                color: #f87171;
            }
            QMenu#settingsPriorityMenu {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.08);
                font-family: "Space Mono";
                font-size: 12px;
            }
            QMenu#settingsPriorityMenu::item {
                padding: 6px 18px 6px 10px;
            }
            QMenu#settingsPriorityMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.12);
            }
            """
            )
        )
