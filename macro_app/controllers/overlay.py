"""Overlay page controller."""

from __future__ import annotations

import os
import random
import re
import string
import subprocess
import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta

import macro_json
from PySide6.QtCore import QEasingCurve, QPointF, Property, QPropertyAnimation, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from macro_app.constants import MACROS_FOLDER
from macro_app.controllers.overlay_helpers import get_macro_folder_for_mode, get_maps_for_mode, match_map_image
from macro_app.services.macro_sharing import MacroSharingError
from macro_app.services.reward_stats import RewardStatsStore, normalize_reward_name
from macro_app.services.run_logs import MacroRunLogger, SavedRunLog


MODE_TABS = (
    ("story", "Story"),
    ("legend", "Legend"),
    ("raids", "Raid"),
    ("dungeon", "Dungeon"),
    ("bossRush", "Boss Rush"),
    ("events", "Event"),
)

NAV_TABS = (
    ("config", "Config"),
    ("stats", "Stats"),
    ("logs", "Logs"),
    ("integrations", "Integrations"),
    ("settings", "Settings"),
)

FONT_STACK = '"Space Mono"'
SURFACE_BG = "#0c0c0c"
CARD_BG = "#111111"
SUBTLE_BG = "rgba(255, 255, 255, 0.04)"
SUBTLE_BG_HOVER = "rgba(255, 255, 255, 0.06)"
BORDER = "rgba(255, 255, 255, 0.08)"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "rgba(255, 255, 255, 0.30)"
TEXT_TERTIARY = "rgba(255, 255, 255, 0.40)"
TEXT_MUTED = "rgba(255, 255, 255, 0.60)"
ACCENT_GREEN = "#22C55E"
ACCENT_GREEN_TEXT = "#4ADE80"

_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}
_NAV_ICON_PATHS = {
    "sliders": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "main_nav", "config_icon.png")),
    "chart": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "main_nav", "stats_icon.png")),
    "file": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "main_nav", "logs_icon.png")),
    "discord": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "main_nav", "discord_icon.png")),
    "settings": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "main_nav", "settings_icon.png")),
}

_REWARD_ICON_PATHS = {
    "Gems": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "gem_icon.png")),
    "Gold": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "gold_icon.png")),
    "Doggy Bones": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "dog_bone_icon.png")),
    "Grenade Pins": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "grenade_pin_icon.png")),
    "Blood Swords": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "blood_sword_icon.png")),
    "Green Essence Stones": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "green_essence_icon.png")),
    "Rainbow Essence Stones": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "strange_fruit_icon.png")),
    "Green Bean": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "green_bean_icon.png")),
    "Green Beans": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "green_bean_icon.png")),
    "Trait Rerolls": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "brand_icon.png")),
    "Coffee Cup": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "coffee_cup_icon.png")),
    "Coffee Cups": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "coffee_cup_icon.png")),
    "Cup Of Coffee": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "coffee_cup_icon.png")),
    "Auric Coin": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "auric_coin_icon.png")),
    "Blood Armor": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "blood_red_armor_icon.png")),
    "Blue Chakra": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "blue_chakra_icon.png")),
    "Broken Pendant": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "broken_pendant_icon.png")),
    "Broken Sword": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "broken_sword_icon.png")),
    "Bst Familiar 1": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "bst_familiar_1_icon.png")),
    "Bullet": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "bullet_icon.png")),
    "Captain Coat": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "head_captains_coat_icon.png")),
    "Champ Belt": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "champ_belt_icon.png")),
    "Chocolate Bar": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "chocolate_bars_icon.png")),
    "Command Seal": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "command_seal_icon.png")),
    "Crystal": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "crystal_icon.png")),
    "Dragon Token": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "dragon_token_icon.png")),
    "Egg Sword": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "egg_sword_icon.png")),
    "Energy Arrow": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "energy_arrow_icon.png")),
    "Flood Platter": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "food_platter_icon.png")),
    "Fused Spirit Orb": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "fused_spirit_orb_icon.png")),
    "Gear": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "gears_icon.png")),
    "Giant Glasses": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "giants_glasses_icon.png")),
    "Giant Serum": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "giant_serum_icon.png")),
    "Griffith": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "griffith_icon.png")),
    "Hair Ornament": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "hair_ornament_icon.png")),
    "Hardened Blood": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "hardened_blood_icon.png")),
    "Hollow Token": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "hollow_token_icon.png")),
    "Horn Salvation": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "horn_of_salvation_icon.png")),
    "Kuinshi Medallion": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "kuinshi_medallion_icon.png")),
    "Lotg Familiar 1": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "lotg_familiar_1_icon.png")),
    "Lotg Familiar 2": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "lotg_familiar_2_icon.png")),
    "Magic Pendant": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "magic_pendant_icon.png")),
    "Magma Stone": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "magma_stone_icon.png")),
    "Makima": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "makima_icon.png")),
    "Marking": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "brand_icon.png")),
    "Meat": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "meat_icon.png")),
    "Mojon Essence": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "mojon_essence_icon.png")),
    "Monarch Token": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "monarch_token_icon.png")),
    "Perpetual Motion": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "perpetual_motion_icon.png")),
    "Ramen": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "ramen_icon.png")),
    "Red Chakra": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "red_chakra_icon.png")),
    "Red Key": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "red_key_icon.png")),
    "Remote": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "remote_icon.png")),
    "Restricting Headband": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "restricting_headband_icon.png")),
    "Shackled Sight": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "shackled_sight_icon.png")),
    "Shadow Traces": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "shadow_traces_icon.png")),
    "Shinig Familiar 1": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "shinig_familiar_1_icon.png")),
    "Shunpo Spirit": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "shunpo_spirit_icon.png")),
    "Six String": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "six_string_icon.png")),
    "Skin Patch": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "skin_patch_icon.png")),
    "Smith Anvil": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "smiths_anvil_icon.png")),
    "Snake Scale": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "snake_scale_icon.png")),
    "Spirit Javelin": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "spirit_javelin_icon.png")),
    "Spirit Mask": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "spirit_mask_icon.png")),
    "Star Ribbon": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "star_ribbon_icon.png")),
    "Tail Ribbon": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "tail_ribbon_icon.png")),
    "Teddy Bear": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "teddy_bear_icon.png")),
    "Transfigured Soul": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "transfigured_soul_icon.png")),
    "Ulq": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "ulq_icon.png")),
    "Weather Rod": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "weather_rod_icon.png")),
    "Witch Hat": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "witch_hat_icon.png")),
    "Yama": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "yama_icon.png")),
    "Z Blade": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui_references", "stats_icons", "z_blade_icon.png")),
}

STATS_TIMEFRAMES = (
    ("24h", "24 Hours"),
    ("7d", "7 Days"),
    ("30d", "30 Days"),
)

STATS_SORT_OPTIONS = (
    ("latest", "Latest"),
    ("highest", "Highest Amount"),
)

REWARD_VISUALS = OrderedDict(
    [
        ("Gems", ("gem", "#C084FC")),
        ("Gold", ("coins", "#FACC15")),
        ("Green Essence Stones", ("bolt", "#60A5FA")),
        ("Rainbow Essence Stones", ("gem", "#22D3EE")),
        ("Doggy Bones", ("skull", "#FB923C")),
        ("Grenade Pins", ("award", "#FBBF24")),
        ("Blood Swords", ("shield", "#FB7185")),
        ("Coffee Cup", ("star", "#F59E0B")),
        ("Green Bean", ("trending-up", "#34D399")),
        ("Memoria Rerolls", ("star", "#A78BFA")),
        ("Trait Rerolls", ("star", "#F472B6")),
        ("Super Stat Chips", ("trending-up", "#2DD4BF")),
    ]
)


@dataclass(frozen=True)
class StatsRunEntry:
    """Parsed saved-log entry used by the redesigned stats tab."""

    saved_log: SavedRunLog
    rewards: dict[str, int]
    started_at: datetime | None
    display_timestamp: str


def _qt_color(value: str) -> QColor:
    normalized = value.strip()
    match = re.fullmatch(
        r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9]*\.?[0-9]+)\s*\)",
        normalized,
        re.IGNORECASE,
    )
    if match:
        red, green, blue, alpha = match.groups()
        alpha_value = float(alpha)
        if alpha_value <= 1.0:
            alpha_channel = max(0, min(255, round(alpha_value * 255)))
        else:
            alpha_channel = max(0, min(255, round(alpha_value)))
        return QColor(int(red), int(green), int(blue), alpha_channel)
    return QColor(normalized)


def _icon(name: str, color: str, size: int = 16) -> QIcon:
    key = (name, color, size)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached

    icon_color = _qt_color(color)
    icon_path = _NAV_ICON_PATHS.get(name)
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
            _ICON_CACHE[key] = icon
            return icon

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(icon_color)
    pen.setWidthF(2.4 if size >= 14 else 2.0)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    s = float(size)
    if name in {"gear", "settings"}:
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
                QPointF(center.x() + s * dx1, center.y() + s * dy1),
                QPointF(center.x() + s * dx2, center.y() + s * dy2),
            )
    elif name == "chart":
        base_y = s * 0.82
        painter.drawLine(QPointF(s * 0.12, base_y), QPointF(s * 0.88, base_y))
        old_brush = painter.brush()
        painter.setBrush(icon_color)
        for left, top, width, height in (
            (0.18, 0.46, 0.10, 0.36),
            (0.40, 0.24, 0.10, 0.58),
            (0.62, 0.58, 0.10, 0.24),
        ):
            painter.drawRoundedRect(QRectF(s * left, s * top, s * width, s * height), 1.5, 1.5)
        painter.setBrush(old_brush)
    elif name == "sliders":
        for y, knob_x in ((0.26, 0.58), (0.50, 0.34), (0.74, 0.66)):
            painter.drawLine(QPointF(s * 0.16, s * y), QPointF(s * 0.84, s * y))
            painter.drawEllipse(QPointF(s * knob_x, s * y), s * 0.08, s * 0.08)
    elif name == "file":
        rect = QRectF(s * 0.18, s * 0.12, s * 0.58, s * 0.76)
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right() - s * 0.14, rect.top())
        path.lineTo(rect.right(), rect.top() + s * 0.14)
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(rect.right() - s * 0.14, rect.top()), QPointF(rect.right() - s * 0.14, rect.top() + s * 0.14))
        painter.drawLine(QPointF(rect.right() - s * 0.14, rect.top() + s * 0.14), QPointF(rect.right(), rect.top() + s * 0.14))
        painter.drawLine(QPointF(s * 0.30, s * 0.42), QPointF(s * 0.62, s * 0.42))
        painter.drawLine(QPointF(s * 0.30, s * 0.56), QPointF(s * 0.62, s * 0.56))
    elif name == "plug":
        path = QPainterPath()
        path.moveTo(s * 0.36, s * 0.2)
        path.lineTo(s * 0.36, s * 0.42)
        path.lineTo(s * 0.28, s * 0.42)
        path.lineTo(s * 0.28, s * 0.62)
        path.lineTo(s * 0.72, s * 0.62)
        path.lineTo(s * 0.72, s * 0.42)
        path.lineTo(s * 0.64, s * 0.42)
        path.lineTo(s * 0.64, s * 0.2)
        painter.drawPath(path)
        painter.drawLine(QPointF(s * 0.5, s * 0.62), QPointF(s * 0.5, s * 0.86))
    elif name == "upload":
        painter.drawLine(QPointF(s * 0.5, s * 0.2), QPointF(s * 0.5, s * 0.64))
        painter.drawLine(QPointF(s * 0.34, s * 0.36), QPointF(s * 0.5, s * 0.2))
        painter.drawLine(QPointF(s * 0.66, s * 0.36), QPointF(s * 0.5, s * 0.2))
        painter.drawLine(QPointF(s * 0.24, s * 0.76), QPointF(s * 0.76, s * 0.76))
        painter.drawLine(QPointF(s * 0.24, s * 0.76), QPointF(s * 0.24, s * 0.58))
        painter.drawLine(QPointF(s * 0.76, s * 0.76), QPointF(s * 0.76, s * 0.58))
    elif name == "gem":
        diamond = QPolygonF(
            [
                QPointF(s * 0.50, s * 0.10),
                QPointF(s * 0.76, s * 0.34),
                QPointF(s * 0.50, s * 0.82),
                QPointF(s * 0.24, s * 0.34),
            ]
        )
        painter.drawPolygon(diamond)
        painter.drawLine(QPointF(s * 0.37, s * 0.20), QPointF(s * 0.63, s * 0.20))
        painter.drawLine(QPointF(s * 0.37, s * 0.20), QPointF(s * 0.50, s * 0.34))
        painter.drawLine(QPointF(s * 0.63, s * 0.20), QPointF(s * 0.50, s * 0.34))
        painter.drawLine(QPointF(s * 0.24, s * 0.34), QPointF(s * 0.50, s * 0.34))
        painter.drawLine(QPointF(s * 0.50, s * 0.34), QPointF(s * 0.76, s * 0.34))
    elif name == "coins":
        painter.drawEllipse(QRectF(s * 0.20, s * 0.18, s * 0.34, s * 0.34))
        painter.drawEllipse(QRectF(s * 0.46, s * 0.38, s * 0.34, s * 0.34))
        painter.drawLine(QPointF(s * 0.37, s * 0.24), QPointF(s * 0.37, s * 0.46))
        painter.drawLine(QPointF(s * 0.30, s * 0.30), QPointF(s * 0.44, s * 0.30))
    elif name == "bolt":
        bolt = QPolygonF(
            [
                QPointF(s * 0.56, s * 0.12),
                QPointF(s * 0.28, s * 0.52),
                QPointF(s * 0.48, s * 0.52),
                QPointF(s * 0.40, s * 0.88),
                QPointF(s * 0.74, s * 0.42),
                QPointF(s * 0.52, s * 0.42),
            ]
        )
        painter.drawPolyline(bolt)
    elif name == "trending-up":
        painter.drawLine(QPointF(s * 0.16, s * 0.68), QPointF(s * 0.38, s * 0.46))
        painter.drawLine(QPointF(s * 0.38, s * 0.46), QPointF(s * 0.54, s * 0.60))
        painter.drawLine(QPointF(s * 0.54, s * 0.60), QPointF(s * 0.80, s * 0.26))
        painter.drawLine(QPointF(s * 0.62, s * 0.26), QPointF(s * 0.80, s * 0.26))
        painter.drawLine(QPointF(s * 0.80, s * 0.26), QPointF(s * 0.80, s * 0.44))
    elif name == "skull":
        painter.drawEllipse(QRectF(s * 0.24, s * 0.18, s * 0.52, s * 0.42))
        painter.drawEllipse(QRectF(s * 0.36, s * 0.34, s * 0.08, s * 0.10))
        painter.drawEllipse(QRectF(s * 0.56, s * 0.34, s * 0.08, s * 0.10))
        painter.drawLine(QPointF(s * 0.50, s * 0.46), QPointF(s * 0.44, s * 0.56))
        painter.drawLine(QPointF(s * 0.50, s * 0.46), QPointF(s * 0.56, s * 0.56))
        painter.drawLine(QPointF(s * 0.34, s * 0.62), QPointF(s * 0.66, s * 0.62))
        painter.drawLine(QPointF(s * 0.40, s * 0.62), QPointF(s * 0.40, s * 0.78))
        painter.drawLine(QPointF(s * 0.50, s * 0.62), QPointF(s * 0.50, s * 0.80))
        painter.drawLine(QPointF(s * 0.60, s * 0.62), QPointF(s * 0.60, s * 0.78))
    elif name == "star":
        star = QPolygonF(
            [
                QPointF(s * 0.50, s * 0.12),
                QPointF(s * 0.60, s * 0.38),
                QPointF(s * 0.86, s * 0.38),
                QPointF(s * 0.66, s * 0.54),
                QPointF(s * 0.74, s * 0.82),
                QPointF(s * 0.50, s * 0.66),
                QPointF(s * 0.26, s * 0.82),
                QPointF(s * 0.34, s * 0.54),
                QPointF(s * 0.14, s * 0.38),
                QPointF(s * 0.40, s * 0.38),
            ]
        )
        painter.drawPolygon(star)
    elif name == "award":
        painter.drawEllipse(QRectF(s * 0.26, s * 0.16, s * 0.48, s * 0.48))
        painter.drawLine(QPointF(s * 0.38, s * 0.56), QPointF(s * 0.30, s * 0.84))
        painter.drawLine(QPointF(s * 0.62, s * 0.56), QPointF(s * 0.70, s * 0.84))
        painter.drawLine(QPointF(s * 0.30, s * 0.84), QPointF(s * 0.44, s * 0.74))
        painter.drawLine(QPointF(s * 0.70, s * 0.84), QPointF(s * 0.56, s * 0.74))
    elif name == "shield":
        shield = QPainterPath()
        shield.moveTo(s * 0.50, s * 0.12)
        shield.lineTo(s * 0.76, s * 0.24)
        shield.lineTo(s * 0.72, s * 0.58)
        shield.quadTo(s * 0.66, s * 0.82, s * 0.50, s * 0.88)
        shield.quadTo(s * 0.34, s * 0.82, s * 0.28, s * 0.58)
        shield.lineTo(s * 0.24, s * 0.24)
        shield.closeSubpath()
        painter.drawPath(shield)
    elif name == "download":
        painter.drawLine(QPointF(s * 0.5, s * 0.20), QPointF(s * 0.5, s * 0.62))
        painter.drawLine(QPointF(s * 0.34, s * 0.48), QPointF(s * 0.5, s * 0.62))
        painter.drawLine(QPointF(s * 0.66, s * 0.48), QPointF(s * 0.5, s * 0.62))
        painter.drawLine(QPointF(s * 0.24, s * 0.78), QPointF(s * 0.76, s * 0.78))
    elif name == "plus":
        painter.drawLine(QPointF(s * 0.5, s * 0.22), QPointF(s * 0.5, s * 0.78))
        painter.drawLine(QPointF(s * 0.22, s * 0.5), QPointF(s * 0.78, s * 0.5))
    elif name == "play":
        triangle = QPolygonF(
            [
                QPointF(s * 0.34, s * 0.24),
                QPointF(s * 0.72, s * 0.50),
                QPointF(s * 0.34, s * 0.76),
            ]
        )
        painter.drawPolygon(triangle)
    elif name == "x":
        painter.drawLine(QPointF(s * 0.24, s * 0.24), QPointF(s * 0.76, s * 0.76))
        painter.drawLine(QPointF(s * 0.76, s * 0.24), QPointF(s * 0.24, s * 0.76))
    elif name == "check":
        painter.drawLine(QPointF(s * 0.20, s * 0.52), QPointF(s * 0.42, s * 0.74))
        painter.drawLine(QPointF(s * 0.42, s * 0.74), QPointF(s * 0.80, s * 0.24))
    elif name == "chevron-left":
        painter.drawLine(QPointF(s * 0.66, s * 0.20), QPointF(s * 0.38, s * 0.50))
        painter.drawLine(QPointF(s * 0.38, s * 0.50), QPointF(s * 0.66, s * 0.80))
    elif name == "chevron-right":
        painter.drawLine(QPointF(s * 0.34, s * 0.20), QPointF(s * 0.62, s * 0.50))
        painter.drawLine(QPointF(s * 0.62, s * 0.50), QPointF(s * 0.34, s * 0.80))
    elif name == "discord":
        body = QPainterPath()
        body.moveTo(s * 0.20, s * 0.40)
        body.quadTo(s * 0.24, s * 0.22, s * 0.40, s * 0.22)
        body.lineTo(s * 0.60, s * 0.22)
        body.quadTo(s * 0.76, s * 0.22, s * 0.80, s * 0.40)
        body.lineTo(s * 0.76, s * 0.60)
        body.quadTo(s * 0.72, s * 0.76, s * 0.56, s * 0.76)
        body.lineTo(s * 0.48, s * 0.76)
        body.lineTo(s * 0.42, s * 0.84)
        body.lineTo(s * 0.40, s * 0.76)
        body.lineTo(s * 0.40, s * 0.76)
        body.quadTo(s * 0.24, s * 0.76, s * 0.20, s * 0.60)
        body.closeSubpath()
        painter.drawPath(body)
        old_brush = painter.brush()
        painter.setBrush(icon_color)
        painter.drawEllipse(QPointF(s * 0.40, s * 0.48), s * 0.045, s * 0.045)
        painter.drawEllipse(QPointF(s * 0.60, s * 0.48), s * 0.045, s * 0.045)
        painter.setBrush(old_brush)
        painter.drawArc(QRectF(s * 0.36, s * 0.48, s * 0.28, s * 0.18), 205 * 16, 130 * 16)
    elif name == "chevron-down":
        painter.drawLine(QPointF(s * 0.22, s * 0.36), QPointF(s * 0.50, s * 0.64))
        painter.drawLine(QPointF(s * 0.50, s * 0.64), QPointF(s * 0.78, s * 0.36))

    painter.end()
    icon = QIcon(pixmap)
    _ICON_CACHE[key] = icon
    return icon


def _reward_visual(reward_name: str) -> tuple[str, str]:
    normalized = normalize_reward_name(reward_name) or reward_name
    return REWARD_VISUALS.get(normalized, ("award", TEXT_MUTED))


def _reward_stats_pixmap(reward_name: str, size: int = 24) -> QPixmap | None:
    normalized = normalize_reward_name(reward_name) or reward_name
    icon_path = _REWARD_ICON_PATHS.get(normalized)
    if icon_path is None:
        icon_path = _REWARD_ICON_PATHS.get(str(reward_name).strip())
    if not icon_path or not os.path.exists(icon_path):
        return None
    source = QPixmap(icon_path)
    if source.isNull():
        return None
    return source.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class ModeTabButton(QPushButton):
    """Small pill button used for gamemode tabs."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFlat(True)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def _apply_style(self) -> None:
        color = "#000000" if self._active else TEXT_TERTIARY
        hover = TEXT_MUTED if not self._active else "#000000"
        self.setStyleSheet(
            f"""
            QPushButton {{
                color: {color};
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 0 16px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {hover};
            }}
            """
        )


class ModeTabsFrame(QFrame):
    """Tab container that keeps the active highlight synced on first layout."""

    def __init__(self, on_resized, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_resized = on_resized

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._on_resized is not None:
            if self.layout() is not None:
                self.layout().activate()
            self._on_resized()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._on_resized is not None:
            if self.layout() is not None:
                self.layout().activate()
            self._on_resized()


class NavButton(QPushButton):
    """Primary navigation button for the overlay sidebar."""

    def __init__(self, text: str, icon_name: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._active = False
        self._hovered = False
        self._icon_name = icon_name
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self.setIconSize(QSize(14, 14))
        self.setFocusPolicy(Qt.NoFocus)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def _apply_style(self) -> None:
        if self._active:
            color = TEXT_PRIMARY
            background = SUBTLE_BG_HOVER
        elif self._hovered:
            color = TEXT_MUTED
            background = "transparent"
        else:
            color = TEXT_TERTIARY
            background = "transparent"
        self.setIcon(_icon(self._icon_name, color, 14))
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {background};
                color: {color};
                border: none;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {TEXT_MUTED};
                background: {background};
            }}
            """
        )


class ArtworkFrame(QFrame):
    """Rounded image frame that paints the map art directly."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scaled_pixmap: QPixmap | None = None
        self._rendered_pixmap: QPixmap | None = None
        self._scaled_size = QSize()
        self._border_color = QColor("#2a2a2a")
        self._corner_radius = 10.0

    def set_pixmap_path(self, image_path: str | None) -> None:
        self._pixmap = QPixmap(image_path) if image_path and os.path.exists(image_path) else None
        self._scaled_pixmap = None
        self._rendered_pixmap = None
        self._scaled_size = QSize()
        self.update()

    def set_border_color(self, color: str) -> None:
        self._border_color = QColor(color)
        self.update()

    def set_corner_radius(self, radius: float) -> None:
        self._corner_radius = max(0.0, float(radius))
        self._rendered_pixmap = None
        self.update()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._scaled_pixmap = None
        self._rendered_pixmap = None
        self._scaled_size = QSize()
        super().resizeEvent(event)

    def _get_scaled_pixmap(self) -> QPixmap | None:
        if self._pixmap is None or self._pixmap.isNull():
            return None
        if self._scaled_pixmap is not None and self._scaled_size == self.size():
            return self._scaled_pixmap
        self._scaled_size = self.size()
        self._scaled_pixmap = self._pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        return self._scaled_pixmap

    def _get_rendered_pixmap(self) -> QPixmap | None:
        scaled = self._get_scaled_pixmap()
        if scaled is None or scaled.isNull():
            return None
        if self._rendered_pixmap is not None and self._scaled_size == self.size():
            return self._rendered_pixmap

        rendered = QPixmap(self.size())
        rendered.fill(Qt.transparent)
        painter = QPainter(rendered)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        rounded = self.rect().adjusted(0, 0, -1, -1)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rounded, self._corner_radius, self._corner_radius)
        painter.fillPath(clip_path, QColor(CARD_BG))
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.setClipPath(clip_path)
        painter.drawPixmap(x, y, scaled)
        painter.end()
        self._rendered_pixmap = rendered
        return self._rendered_pixmap

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rounded = self.rect().adjusted(0, 0, -1, -1)
        rendered = self._get_rendered_pixmap()
        if rendered is not None and not rendered.isNull():
            painter.drawPixmap(0, 0, rendered)
        else:
            clip_path = QPainterPath()
            clip_path.addRoundedRect(rounded, self._corner_radius, self._corner_radius)
            painter.fillPath(clip_path, QColor(CARD_BG))

        painter.setPen(QPen(self._border_color, 1))
        painter.drawRoundedRect(rounded, self._corner_radius, self._corner_radius)

class OverlayMapCard(QFrame):
    """Clickable map card with background image, actions, and macro selector."""

    create_requested = Signal(str)
    select_requested = Signal(str)
    macro_changed = Signal(str, str)
    activated = Signal(str)

    def __init__(self, map_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_name = map_name
        self._active = False
        self._image_path: str | None = None
        self._suppress_combo_signal = False
        self._normal_rect = QRect()
        self._hover_rect = QRect()
        self._hover_progress = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hoverProgress", self)
        self._hover_anim.setDuration(320)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setObjectName("overlayMapCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(360)
        self.setFixedHeight(246)
        self.setFocusPolicy(Qt.NoFocus)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        self.visual_frame = ArtworkFrame(self)
        self.visual_frame.setObjectName("overlayMapCardVisual")
        self.visual_frame.setFixedHeight(198)
        self.visual_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        root_layout.addWidget(self.visual_frame)

        self.overlay = QFrame(self.visual_frame)
        self.overlay.setStyleSheet(
            """
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(0, 0, 0, 55),
                stop:0.45 rgba(0, 0, 0, 95),
                stop:1 rgba(0, 0, 0, 180)
            );
            border: none;
            """
        )

        self.content = QWidget(self.visual_frame)
        self.content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.addStretch(1)
        content_layout.setSpacing(12)

        self.title_label = QLabel(map_name, self.content)
        self.title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; font-family: {FONT_STACK}; font-size: 14px; font-weight: 700;"
        )
        content_layout.addWidget(self.title_label)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)

        self.create_button = QPushButton("Create", self.content)
        self.create_button.setCursor(Qt.PointingHandCursor)
        self.create_button.setFocusPolicy(Qt.NoFocus)
        self.create_button.setIcon(_icon("plus", "#000000", 12))
        self.create_button.setIconSize(QSize(12, 12))
        self.create_button.setFixedHeight(26)
        self.create_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.92);
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 0 12px;
                font-family: "Space Mono";
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #FFFFFF;
            }
            """
        )
        self.create_button.clicked.connect(lambda: self.create_requested.emit(self.map_name))
        button_row.addWidget(self.create_button)

        self.select_button = QPushButton("Select", self.content)
        self.select_button.setCursor(Qt.PointingHandCursor)
        self.select_button.setFocusPolicy(Qt.NoFocus)
        self.select_button.setIcon(_icon("play", "#FFFFFF", 12))
        self.select_button.setIconSize(QSize(12, 12))
        self.select_button.setFixedHeight(26)
        self.select_button.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.10);
                color: {TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 4px;
                padding: 0 12px;
                font-family: {FONT_STACK};
                font-size: 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.20);
            }}
            """
        )
        self.select_button.clicked.connect(lambda: self.select_requested.emit(self.map_name))
        button_row.addWidget(self.select_button)
        button_row.addStretch(1)
        content_layout.addLayout(button_row)

        self.combo = RefreshingComboBox(lambda: None, self)
        self.combo.setCursor(Qt.PointingHandCursor)
        self.combo.setFocusPolicy(Qt.NoFocus)
        self.combo.setMinimumHeight(32)
        self.combo.setMaximumHeight(32)
        self.combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {SUBTLE_BG};
                color: rgba(255, 255, 255, 0.70);
                border: 1px solid {BORDER};
                border-radius: 4px;
                combobox-popup: 0;
                padding: 0 12px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                background: {SUBTLE_BG_HOVER};
            }}
            QComboBox::drop-down {{
                width: 28px;
                border: none;
                background: transparent;
            }}
            QComboBox QAbstractItemView {{
                background: #1A1A1A;
                color: {TEXT_PRIMARY};
                selection-background-color: rgba(255, 255, 255, 0.10);
                border: 1px solid {BORDER};
                padding: 4px;
                font-family: {FONT_STACK};
            }}
            """
        )
        self.combo.currentTextChanged.connect(self._emit_macro_changed)
        root_layout.addWidget(self.combo)

        self.set_active(False)

    def get_selected_macro(self) -> str:
        value = self.combo.currentText().strip()
        return "" if value == "Choose Macro" else value

    def set_macro_refresh_callback(self, callback) -> None:
        self.combo._on_refresh = callback

    def set_macros(self, macros: list[str], selected_macro: str = "") -> None:
        self._suppress_combo_signal = True
        self.combo.clear()
        self.combo.addItem("Choose Macro")
        for macro_name in macros:
            self.combo.addItem(macro_name)
        if selected_macro and selected_macro in macros:
            self.combo.setCurrentText(selected_macro)
        else:
            self.combo.setCurrentIndex(0)
        self._suppress_combo_signal = False

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_visual_style()

    def set_background(self, image_path: str | None) -> None:
        self._image_path = image_path
        self.visual_frame.set_pixmap_path(image_path)
        self._apply_visual_style()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.activated.emit(self.map_name)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._animate_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._animate_hover(False)
        super().leaveEvent(event)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.sync_internal_geometry()
        super().resizeEvent(event)

    def sync_internal_geometry(self) -> None:
        self.visual_frame.setGeometry(0, 0, self.width(), 198)
        self.combo.setGeometry(0, 214, self.width(), 32)
        rect = self.visual_frame.rect()
        self._normal_rect = rect.adjusted(0, 0, 0, 0)
        self._hover_rect = rect.adjusted(-10, -8, 10, 8)
        self.overlay.setGeometry(rect)
        self.content.setGeometry(rect)

    def _emit_macro_changed(self, value: str) -> None:
        if self._suppress_combo_signal:
            return
        self.activated.emit(self.map_name)
        self.macro_changed.emit(self.map_name, "" if value == "Choose Macro" else value)

    def _animate_hover(self, hovering: bool) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0 if hovering else 0.0)
        self._hover_anim.start()

    def _interpolated_rect(self) -> QRect:
        if self._normal_rect.isNull():
            return QRect()
        t = self._hover_progress
        start = self._normal_rect
        end = self._hover_rect
        return QRect(
            int(start.x() + (end.x() - start.x()) * t),
            int(start.y() + (end.y() - start.y()) * t),
            int(start.width() + (end.width() - start.width()) * t),
            int(start.height() + (end.height() - start.height()) * t),
        )

    def _get_hover_progress(self) -> float:
        return self._hover_progress

    def _set_hover_progress(self, value: float) -> None:
        self._hover_progress = float(value)

    def _apply_visual_style(self) -> None:
        border_color = "rgba(255, 255, 255, 0.14)" if self._active else BORDER
        self.visual_frame.set_border_color(border_color)

    hoverProgress = Property(float, _get_hover_progress, _set_hover_progress)


class RefreshingComboBox(QComboBox):
    """Combo box that refreshes its items right before the popup opens."""

    def __init__(self, on_refresh, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_refresh = on_refresh
        popup_view = QListView(self)
        popup_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        popup_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        popup_view.setTextElideMode(Qt.ElideRight)
        popup_view.setSpacing(0)
        popup_view.setStyleSheet(
            f"""
            QListView {{
                background: #1A1A1A;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                outline: none;
                padding: 0px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QListView::item {{
                min-height: 30px;
                padding: 0 12px;
                border: none;
                margin: 0px;
            }}
            QListView::item:selected {{
                background: rgba(255, 255, 255, 0.10);
                color: {TEXT_PRIMARY};
            }}
            QListView::item:hover {{
                background: rgba(255, 255, 255, 0.06);
            }}
            """
        )
        self.setView(popup_view)
        self.setMaxVisibleItems(10)

    def showPopup(self) -> None:  # type: ignore[override]
        if self._on_refresh is not None:
            self._on_refresh()
        view = self.view()
        if view is not None:
            view.setMinimumWidth(max(self.width(), view.sizeHintForColumn(0) + 28))
        super().showPopup()


class OverlayLogCard(QFrame):
    """Background-image log card matching the redesigned logs layout."""

    download_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._log_path = ""
        self._normal_border = BORDER
        self.setObjectName("overlayLogCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(72)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet("background: transparent;")

        self.artwork = ArtworkFrame(self)
        self.artwork.set_corner_radius(4)
        self.artwork.set_border_color(self._normal_border)

        self.overlay = QFrame(self.artwork)
        self.overlay.setStyleSheet(
            """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(0, 0, 0, 179),
                stop:0.55 rgba(0, 0, 0, 153),
                stop:1 rgba(0, 0, 0, 128)
            );
            border: none;
            """
        )

        self.content = QWidget(self.artwork)
        self.content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(24)

        left_column = QWidget(self.content)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.title_label = QLabel("", left_column)
        self.title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 600; background: transparent;"
        )
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_layout.addWidget(self.title_label)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(12)
        left_layout.addLayout(meta_row)

        self.mode_label = QLabel("", left_column)
        self.mode_label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent;"
        )
        meta_row.addWidget(self.mode_label)

        dot = QLabel("•", left_column)
        dot.setStyleSheet(
            "color: rgba(255, 255, 255, 0.20); font-family: \"Space Mono\"; font-size: 10px; font-weight: 500; background: transparent;"
        )
        meta_row.addWidget(dot)

        self.map_label = QLabel("", left_column)
        self.map_label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent;"
        )
        meta_row.addWidget(self.map_label)
        meta_row.addStretch(1)

        content_layout.addWidget(left_column, 1)

        right_column = QWidget(self.content)
        right_layout = QHBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(24)

        self.timestamp_value = self._build_log_meta_block(right_column, "TIMESTAMP")
        self.timestamp_value.parentWidget().setFixedWidth(150)
        right_layout.addWidget(self.timestamp_value.parentWidget())

        self.duration_value = self._build_log_meta_block(right_column, "DURATION")
        self.duration_value.parentWidget().setFixedWidth(60)
        right_layout.addWidget(self.duration_value.parentWidget())

        self.status_badge = QLabel("", right_column)
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedHeight(24)
        right_layout.addWidget(self.status_badge, 0, Qt.AlignVCenter)

        self.download_button = QPushButton("", right_column)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setFocusPolicy(Qt.NoFocus)
        self.download_button.setIcon(_icon("download", "rgba(255, 255, 255, 0.60)", 14))
        self.download_button.setIconSize(QSize(14, 14))
        self.download_button.setFixedSize(26, 26)
        self.download_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: none;
                border-radius: 4px;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            """
        )
        self.download_button.clicked.connect(self._emit_download)
        right_layout.addWidget(self.download_button, 0, Qt.AlignVCenter)

        content_layout.addWidget(right_column, 0, Qt.AlignRight | Qt.AlignVCenter)

    def _build_log_meta_block(self, parent: QWidget, label_text: str) -> QLabel:
        wrapper = QWidget(parent)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        wrapper.setStyleSheet("background: transparent;")

        label = QLabel(label_text, wrapper)
        label.setAlignment(Qt.AlignRight)
        label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 9px; font-weight: 500; background: transparent;"
        )
        layout.addWidget(label)

        value = QLabel("", wrapper)
        value.setAlignment(Qt.AlignRight)
        value.setStyleSheet(
            f"color: {TEXT_MUTED}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; background: transparent;"
        )
        layout.addWidget(value)
        return value

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.setGeometry(self.rect())
        self.overlay.setGeometry(self.artwork.rect())
        self.content.setGeometry(self.artwork.rect())
        super().resizeEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.set_border_color("rgba(255, 255, 255, 0.15)")
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.set_border_color(self._normal_border)
        super().leaveEvent(event)

    def set_log(self, log: SavedRunLog, image_path: str | None) -> None:
        self._log_path = log.path
        self.artwork.set_pixmap_path(image_path)
        self.title_label.setText(log.macro_name or log.map_name)
        self.mode_label.setText(log.gamemode)
        self.map_label.setText(log.map_name)
        self.timestamp_value.setText(log.timestamp)
        self.duration_value.setText(log.duration_label)
        if log.status == "FAILED":
            self.status_badge.setFixedWidth(65)
            self.status_badge.setStyleSheet(
                """
                color: #F87171;
                background: rgba(239, 68, 68, 0.20);
                border: 1px solid rgba(239, 68, 68, 0.30);
                border-radius: 4px;
                font-family: "Space Mono";
                font-size: 10px;
                font-weight: 700;
                padding: 0 8px;
                """
            )
        else:
            self.status_badge.setFixedWidth(75)
            self.status_badge.setStyleSheet(
                """
                color: #4ADE80;
                background: rgba(34, 197, 94, 0.20);
                border: 1px solid rgba(34, 197, 94, 0.30);
                border-radius: 4px;
                font-family: "Space Mono";
                font-size: 10px;
                font-weight: 700;
                padding: 0 8px;
                """
            )
        self.status_badge.setText(log.status)

    def _emit_download(self) -> None:
        if self._log_path:
            self.download_requested.emit(self._log_path)


class StatsRunCard(QFrame):
    """Compact cinematic run card used on the redesigned stats page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(72)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet("background: transparent;")

        self.artwork = ArtworkFrame(self)
        self.artwork.set_corner_radius(4)
        self.artwork.set_border_color(BORDER)

        self.overlay = QFrame(self.artwork)
        self.overlay.setStyleSheet(
            """
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(0, 0, 0, 179),
                stop:0.55 rgba(0, 0, 0, 153),
                stop:1 rgba(0, 0, 0, 128)
            );
            border: none;
            """
        )

        self.content = QWidget(self.artwork)
        self.content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        left_column = QWidget(self.content)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.title_label = QLabel("", left_column)
        self.title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 600; background: transparent;"
        )
        left_layout.addWidget(self.title_label)

        self.meta_row = QHBoxLayout()
        self.meta_row.setContentsMargins(0, 0, 0, 0)
        self.meta_row.setSpacing(12)
        left_layout.addLayout(self.meta_row)

        self.mode_label = QLabel("", left_column)
        self.mode_label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent;"
        )
        self.meta_row.addWidget(self.mode_label)

        mode_dot = QLabel("•", left_column)
        mode_dot.setStyleSheet(
            "color: rgba(255, 255, 255, 0.20); font-family: \"Space Mono\"; font-size: 10px; font-weight: 500; background: transparent;"
        )
        self.meta_row.addWidget(mode_dot)

        self.map_label = QLabel("", left_column)
        self.map_label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent;"
        )
        self.meta_row.addWidget(self.map_label)

        map_dot = QLabel("•", left_column)
        map_dot.setStyleSheet(
            "color: rgba(255, 255, 255, 0.20); font-family: \"Space Mono\"; font-size: 10px; font-weight: 500; background: transparent;"
        )
        self.meta_row.addWidget(map_dot)

        self.timestamp_label = QLabel("", left_column)
        self.timestamp_label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent;"
        )
        self.meta_row.addWidget(self.timestamp_label)
        self.meta_row.addStretch(1)

        content_layout.addWidget(left_column, 1)

        self.badges_host = QWidget(self.content)
        self.badges_layout = QHBoxLayout(self.badges_host)
        self.badges_layout.setContentsMargins(0, 0, 0, 0)
        self.badges_layout.setSpacing(12)
        content_layout.addWidget(self.badges_host, 0, Qt.AlignRight | Qt.AlignVCenter)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.setGeometry(self.rect())
        self.overlay.setGeometry(self.artwork.rect())
        self.content.setGeometry(self.artwork.rect())
        super().resizeEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.set_border_color("rgba(255, 255, 255, 0.15)")
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self.artwork.set_border_color(BORDER)
        super().leaveEvent(event)

    def set_entry(self, entry: StatsRunEntry, image_path: str | None) -> None:
        self.artwork.set_pixmap_path(image_path)
        self.title_label.setText(entry.saved_log.macro_name or entry.saved_log.map_name)
        self.mode_label.setText(entry.saved_log.gamemode)
        self.map_label.setText(entry.saved_log.map_name)
        self.timestamp_label.setText(entry.display_timestamp)

        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for reward_name, amount in self._ordered_rewards(entry.rewards):
            badge = QFrame(self.badges_host)
            badge.setStyleSheet(
                """
                background: rgba(0, 0, 0, 0.40);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 4px;
                """
            )
            badge_layout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(12, 6, 12, 6)
            badge_layout.setSpacing(6)

            icon_label = QLabel(badge)
            reward_pixmap = _reward_stats_pixmap(reward_name, 14)
            if reward_pixmap is not None:
                icon_label.setPixmap(reward_pixmap)
            else:
                icon_name, color = _reward_visual(reward_name)
                icon_label.setPixmap(_icon(icon_name, color, 14).pixmap(14, 14))
            icon_label.setFixedSize(14, 14)
            icon_label.setStyleSheet("background: transparent; border: none;")
            badge_layout.addWidget(icon_label)

            value_label = QLabel(f"{amount:,}", badge)
            value_label.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 600; background: transparent; border: none;"
            )
            badge_layout.addWidget(value_label)
            self.badges_layout.addWidget(badge)

        self.badges_layout.addStretch(1)

    @staticmethod
    def _ordered_rewards(rewards: dict[str, int]) -> list[tuple[str, int]]:
        known_order = {name: index for index, name in enumerate(REWARD_VISUALS.keys())}
        return sorted(
            rewards.items(),
            key=lambda item: (
                known_order.get(normalize_reward_name(item[0]) or item[0], 10_000),
                -(item[1]),
                item[0],
            ),
        )


class ToggleSwitchButton(QPushButton):
    """Compact toggle switch for the integrations page."""

    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(40, 20)
        self.setStyleSheet("background: transparent; border: none; padding: 0;")

        self._track = QFrame(self)
        self._track.setStyleSheet("background: rgba(255, 255, 255, 0.08); border: none; border-radius: 10px;")
        self._thumb = QFrame(self)
        self._thumb.setFixedSize(16, 16)
        self._thumb.setStyleSheet("background: #FFFFFF; border: none; border-radius: 8px;")
        self._thumb_anim = QPropertyAnimation(self._thumb, b"pos", self)
        self._thumb_anim.setDuration(180)
        self._thumb_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._apply_state)
        self._apply_state(self.isChecked(), animated=False)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._track.setGeometry(0, 0, self.width(), self.height())
        self._apply_state(self.isChecked(), animated=False)
        super().resizeEvent(event)

    def _apply_state(self, checked: bool, *, animated: bool = True) -> None:
        self._track.setStyleSheet(
            f"background: {ACCENT_GREEN if checked else 'rgba(255, 255, 255, 0.08)'}; border: none; border-radius: 10px;"
        )
        target = QPointF(22, 2) if checked else QPointF(2, 2)
        self._thumb_anim.stop()
        if animated:
            self._thumb_anim.setStartValue(self._thumb.pos())
            self._thumb_anim.setEndValue(target.toPoint())
            self._thumb_anim.start()
        else:
            self._thumb.move(target.toPoint())


class IntegrationCheckboxRow(QWidget):
    """Styled checkbox row used throughout the integrations page."""

    toggled = Signal(bool)

    def __init__(self, text: str, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._box = QFrame(self)
        self._box.setFixedSize(16, 16)
        self._box.setStyleSheet("background: transparent; border-radius: 4px;")
        self._check = QLabel(self._box)
        self._check.setGeometry(0, 0, 16, 16)
        self._check.setAlignment(Qt.AlignCenter)
        self._check.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._box, 0, Qt.AlignTop)

        self._label = QLabel(text, self)
        self._label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.60); font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        layout.addWidget(self._label, 1, Qt.AlignVCenter)
        self._apply_style()

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool) -> None:
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        self._apply_style()
        self.toggled.emit(checked)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.set_checked(not self._checked)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def _apply_style(self) -> None:
        if self._checked:
            self._box.setStyleSheet("background: #FFFFFF; border: 1px solid #FFFFFF; border-radius: 4px;")
            self._check.setPixmap(_icon("check", "#000000", 12).pixmap(12, 12))
            label_color = TEXT_MUTED
        else:
            border_color = "rgba(255, 255, 255, 0.25)" if self._hovered else "rgba(255, 255, 255, 0.12)"
            label_color = "rgba(255, 255, 255, 0.80)" if self._hovered else TEXT_MUTED
            self._box.setStyleSheet(
                f"background: transparent; border: 1px solid {border_color}; border-radius: 4px;"
            )
            self._check.clear()
        self._label.setStyleSheet(
            f"color: {label_color}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )

class OverlayController:
    """Handle overlay tabs, cards, stats, logs, and integrations wiring."""

    def __init__(self, window, state, overlay_widgets, navigation, sharing_service) -> None:
        self.window = window
        self.state = state
        self.overlay_widgets = overlay_widgets
        self.navigation = navigation
        self.sharing_service = sharing_service
        self.advanced_editor = None
        self.webhook_controller = None
        self.overlay_instance_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self._overlay_current_tab = "config"
        self._active_mode = MODE_TABS[0][0]
        self._active_map_by_mode: dict[str, str] = {}
        self._selected_macro_by_mode_map: dict[tuple[str, str], str] = {}
        self._log_card_widgets: list[QFrame] = []
        self._empty_log_card: QFrame | None = None
        self._reward_stat_value_labels: dict[str, QLabel] = {}
        self._mode_stat_value_labels: dict[str, dict[str, QLabel]] = {}
        self._stats_timeframe = "24h"
        self._stats_reward_filter = "all"
        self._stats_sort_by = "latest"
        self._mode_cards: dict[str, OverlayMapCard] = {}
        self._card_pool: dict[tuple[str, str], OverlayMapCard] = {}
        self._empty_state_pool: dict[str, QFrame] = {}
        self._logs_page = 0
        self._suppress_rebuild_animation = False
        self.log_service = MacroRunLogger()
        self.reward_stats_store = RewardStatsStore()

        self._shell: QWidget | None = None
        self._nav_buttons: dict[str, NavButton] = {}
        self._mode_buttons: dict[str, ModeTabButton] = {}
        self._nav_stack: QStackedWidget | None = None
        self._config_page: QWidget | None = None
        self._stats_page: QWidget | None = None
        self._logs_page_widget: QWidget | None = None
        self._integrations_page: QWidget | None = None
        self._settings_page: QWidget | None = None
        self._cards_container: QWidget | None = None
        self._cards_scroll_area: QScrollArea | None = None
        self._cards_layout: QGridLayout | None = None
        self._mode_highlight: QFrame | None = None
        self._mode_highlight_animation: QPropertyAnimation | None = None
        self._mode_highlight_animating = False
        self._mode_highlight_sync_pending = False
        self._status_dot_effect: QGraphicsOpacityEffect | None = None
        self._status_dot_animation: QPropertyAnimation | None = None
        self._modal_backdrop: QWidget | None = None
        self._modal_card: QFrame | None = None
        self._import_context_label: QLabel | None = None
        self._import_textarea: QPlainTextEdit | None = None
        self._pending_import_mode: str | None = None
        self._pending_import_map: str | None = None
        self._logs_grid: QWidget | None = None
        self._logs_scroll_area: QScrollArea | None = None
        self._logs_list_layout: QVBoxLayout | None = None
        self._logs_pager_label: QLabel | None = None
        self._logs_prev_button: QPushButton | None = None
        self._logs_next_button: QPushButton | None = None
        self._stats_timeframe_combo: QComboBox | None = None
        self._stats_filter_combo: QComboBox | None = None
        self._stats_sort_combo: QComboBox | None = None
        self._stats_rewards_grid_layout: QGridLayout | None = None
        self._stats_logs_list_layout: QVBoxLayout | None = None
        self._stats_logs_scroll_area: QScrollArea | None = None
        self._integration_webhook_input = None
        self._integration_toggle = None
        self._settings_debug_toggle = None
        self._integration_connection_icon = None
        self._integration_connection_label = None
        self._integration_reward_dropdown_row = None
        self._integration_reward_dropdown_combo = None
        self._integration_ping_dropdown_row = None
        self._integration_ping_dropdown_combo = None
        self._integration_ping_id_input = None
        self._shell_layout: QVBoxLayout | None = None
        self._header_frame: QFrame | None = None
        self._body_widget: QWidget | None = None
        self._sidebar_frame: QFrame | None = None
        self._content_widget: QWidget | None = None

    def set_advanced_editor(self, advanced_editor) -> None:
        self.advanced_editor = advanced_editor

    def set_webhook_controller(self, webhook_controller) -> None:
        self.webhook_controller = webhook_controller

    def bind(self) -> None:
        self._hide_legacy_overlay_widgets()
        self._build_shell()
        for key, button in self._mode_buttons.items():
            button.set_active(key == self._active_mode)
        self.init_overlay_dropdowns()
        self._ensure_valid_active_map(self._active_mode)
        self._rebuild_cards(animated=False)
        self._refresh_mode_summary_cards()
        self.refresh_reward_stats_tab()
        self.refresh_logs_tab()
        self._show_overlay_tab("config")
        self._sync_shell_geometry()

    def _hide_legacy_overlay_widgets(self) -> None:
        self.overlay_widgets.page_title.hide()
        self.overlay_widgets.subtitle.hide()
        for widgets in self.overlay_widgets.modes.values():
            widgets.group.hide()
            widgets.mode_label.hide()
            if widgets.active_label is not None:
                widgets.active_label.hide()
        self.window.overlayWebhookGroup.hide()

    def _build_shell(self) -> None:
        if self._shell is not None:
            self._sync_shell_geometry()
            return

        overlay_parent = getattr(self.window, "overlayContent", self.window.overlayPage)
        scroll_area = getattr(self.window, "overlayScrollArea", None)
        if scroll_area is not None:
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setStyleSheet(
                f"QScrollArea {{ background: {SURFACE_BG}; border: none; }} QWidget#overlayContent {{ background: {SURFACE_BG}; }}"
            )

        self._shell = QWidget(overlay_parent)
        self._shell.setObjectName("overlayShell")
        self._shell.setStyleSheet(f"QWidget#overlayShell {{ background: {SURFACE_BG}; font-family: {FONT_STACK}; }}")

        root_layout = QVBoxLayout(self._shell)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self._shell_layout = root_layout

        header = QFrame(self._shell)
        self._header_frame = header
        header.setFixedHeight(84)
        header.setStyleSheet(f"background: {SURFACE_BG}; border-bottom: 1px solid {BORDER};")
        root_layout.addWidget(header)

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 16, 32, 16)
        header_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        header_layout.addLayout(title_row)

        title_label = QLabel("ZERON", header)
        title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; font-family: {FONT_STACK}; font-size: 20px; font-weight: 800; letter-spacing: -0.02em;"
        )
        title_row.addWidget(title_label)

        subtitle_label = QLabel("CONFIG", header)
        subtitle_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-family: {FONT_STACK}; font-size: 20px; font-weight: 800; letter-spacing: -0.02em;"
        )
        title_row.addWidget(subtitle_label)
        title_row.addStretch(1)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(4)
        header_layout.addLayout(status_row)

        status_prefix = QLabel("STATUS:", header)
        status_prefix.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 700; background: transparent; border: none;"
        )
        status_row.addWidget(status_prefix, 0, Qt.AlignVCenter)

        self.overlay_widgets.status_label.setParent(header)
        self.overlay_widgets.status_label.setText("IDLE")
        self.overlay_widgets.status_label.setStyleSheet(
            f"color: {ACCENT_GREEN_TEXT}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 700; background: transparent; border: none;"
        )
        status_row.addWidget(self.overlay_widgets.status_label, 0, Qt.AlignVCenter)
        status_row.addStretch(1)

        body = QWidget(self._shell)
        self._body_widget = body
        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(body, 1)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame(body)
        self._sidebar_frame = sidebar
        sidebar.setFixedWidth(176)
        sidebar.setStyleSheet(f"background: {SURFACE_BG}; border-right: 1px solid {BORDER};")
        body_layout.addWidget(sidebar)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 24)
        sidebar_layout.setSpacing(2)

        nav_icons = {
            "config": "sliders",
            "stats": "chart",
            "logs": "file",
            "integrations": "discord",
            "settings": "settings",
        }
        for key, label in NAV_TABS:
            button = NavButton(label, nav_icons.get(key, "gear"), sidebar)
            button.clicked.connect(lambda _checked=False, key=key: self._show_overlay_tab(key))
            sidebar_layout.addWidget(button)
            self._nav_buttons[key] = button
        sidebar_layout.addStretch(1)

        content = QWidget(body)
        self._content_widget = content
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_layout.addWidget(content, 1)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._nav_stack = QStackedWidget(content)
        self._nav_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._nav_stack.setStyleSheet(f"background: {SURFACE_BG};")
        content_layout.addWidget(self._nav_stack)

        self._config_page = self._build_config_page()
        self._stats_page = self._build_stats_page()
        self._logs_page_widget = self._build_logs_page()
        self._integrations_page = self._build_integrations_page()
        self._settings_page = self._build_settings_page()

        self._nav_stack.addWidget(self._config_page)
        self._nav_stack.addWidget(self._stats_page)
        self._nav_stack.addWidget(self._logs_page_widget)
        self._nav_stack.addWidget(self._integrations_page)
        self._nav_stack.addWidget(self._settings_page)

        self._build_import_modal()
        self._sync_shell_geometry()
        self._schedule_mode_highlight_sync()

    def _build_config_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(24)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(16)
        layout.addLayout(top_row)

        tab_container = ModeTabsFrame(self._sync_mode_highlight_geometry, page)
        tab_container.setObjectName("overlayModeTabs")
        tab_container.setStyleSheet(
            f"""
            QFrame#overlayModeTabs {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 4px;
            }}
            """
        )
        top_row.addWidget(tab_container, 1)

        tabs_layout = QHBoxLayout(tab_container)
        tabs_layout.setContentsMargins(6, 6, 6, 6)
        tabs_layout.setSpacing(0)

        self._mode_highlight = QFrame(tab_container)
        self._mode_highlight.setObjectName("overlayModeHighlight")
        self._mode_highlight.setStyleSheet("background: #FFFFFF; border-radius: 4px;")
        self._mode_highlight.lower()
        self._mode_highlight_animation = QPropertyAnimation(self._mode_highlight, b"geometry", self._shell)
        self._mode_highlight_animation.setDuration(240)
        self._mode_highlight_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._mode_highlight_animation.finished.connect(self._on_mode_highlight_animation_finished)

        for key, label in MODE_TABS:
            button = ModeTabButton(label, tab_container)
            button.clicked.connect(lambda _checked=False, key=key: self._set_active_mode(key))
            tabs_layout.addWidget(button)
            self._mode_buttons[key] = button

        open_folder_button = QPushButton("Open Folder", page)
        open_folder_button.setCursor(Qt.PointingHandCursor)
        open_folder_button.setFocusPolicy(Qt.NoFocus)
        open_folder_button.setFixedHeight(40)
        open_folder_button.setFixedWidth(116)
        open_folder_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {SUBTLE_BG};
                color: rgba(255, 255, 255, 0.70);
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 0 10px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {SUBTLE_BG_HOVER};
                color: {TEXT_PRIMARY};
            }}
            """
        )
        open_folder_button.setToolTip("Open the macros folder for the selected mode and map.")
        open_folder_button.clicked.connect(self._open_macros_folder_for_active_selection)
        top_row.addWidget(open_folder_button, 0)

        self._cards_scroll_area = QScrollArea(page)
        self._cards_scroll_area.setWidgetResizable(True)
        self._cards_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cards_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cards_scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 0px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: transparent;
                border-radius: 0px;
                min-height: 0px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: transparent;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
                height: 0;
            }}
            """
        )
        layout.addWidget(self._cards_scroll_area, 1)

        self._cards_container = QWidget()
        self._cards_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._cards_layout = QGridLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setHorizontalSpacing(24)
        self._cards_layout.setVerticalSpacing(24)
        self._cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._cards_layout.setColumnStretch(0, 1)
        self._cards_layout.setColumnStretch(1, 1)
        self._cards_scroll_area.setWidget(self._cards_container)
        return page

    def _build_stats_page(self) -> QWidget:
        page = QWidget()
        root_layout = QVBoxLayout(page)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._stats_logs_scroll_area = QScrollArea(page)
        self._stats_logs_scroll_area.setWidgetResizable(True)
        self._stats_logs_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._stats_logs_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._stats_logs_scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 0px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: transparent;
                min-height: 0px;
            }
            """
        )
        root_layout.addWidget(self._stats_logs_scroll_area, 1)

        container = QWidget(page)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)
        self._stats_logs_scroll_area.setWidget(container)

        rewards_section = QWidget(container)
        rewards_section_layout = QVBoxLayout(rewards_section)
        rewards_section_layout.setContentsMargins(0, 0, 0, 0)
        rewards_section_layout.setSpacing(16)

        rewards_header = QHBoxLayout()
        rewards_header.setContentsMargins(0, 0, 0, 0)
        rewards_header.setSpacing(12)

        rewards_title = QLabel("REWARDS ACCUMULATED", rewards_section)
        rewards_title.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; letter-spacing: 0.25em; background: transparent;"
        )
        rewards_header.addWidget(rewards_title)
        rewards_header.addStretch(1)

        timeframe_options = list(STATS_TIMEFRAMES)
        timeframe_wrapper, self._stats_timeframe_combo = self._build_stats_select(
            rewards_section,
            timeframe_options,
            self._stats_timeframe,
            self._on_stats_timeframe_changed,
            minimum_width=164,
        )
        rewards_header.addWidget(timeframe_wrapper, 0, Qt.AlignRight)
        rewards_section_layout.addLayout(rewards_header)

        rewards_card = QFrame(rewards_section)
        rewards_card.setStyleSheet(
            f"background: rgba(255, 255, 255, 0.02); border: 1px solid {BORDER}; border-radius: 4px;"
        )
        rewards_card_layout = QVBoxLayout(rewards_card)
        rewards_card_layout.setContentsMargins(24, 24, 24, 24)
        rewards_card_layout.setSpacing(0)

        rewards_grid = QWidget(rewards_card)
        rewards_grid.setStyleSheet("background: transparent; border: none;")
        self._stats_rewards_grid_layout = QGridLayout(rewards_grid)
        self._stats_rewards_grid_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_rewards_grid_layout.setHorizontalSpacing(32)
        self._stats_rewards_grid_layout.setVerticalSpacing(24)
        rewards_card_layout.addWidget(rewards_grid)
        rewards_section_layout.addWidget(rewards_card)
        layout.addWidget(rewards_section)
        layout.addSpacing(32)

        filters_row = QHBoxLayout()
        filters_row.setContentsMargins(0, 0, 0, 0)
        filters_row.setSpacing(12)

        filter_wrapper, self._stats_filter_combo = self._build_stats_select(
            container,
            [("all", "All Rewards")],
            self._stats_reward_filter,
            self._on_stats_filter_changed,
            minimum_width=240,
        )
        filters_row.addWidget(filter_wrapper, 0, Qt.AlignLeft)

        sort_wrapper, self._stats_sort_combo = self._build_stats_select(
            container,
            list(STATS_SORT_OPTIONS),
            self._stats_sort_by,
            self._on_stats_sort_changed,
            minimum_width=280,
        )
        filters_row.addWidget(sort_wrapper, 0, Qt.AlignLeft)
        filters_row.addStretch(1)
        layout.addLayout(filters_row)
        layout.addSpacing(24)

        logs_host = QWidget(container)
        self._stats_logs_list_layout = QVBoxLayout(logs_host)
        self._stats_logs_list_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_logs_list_layout.setSpacing(12)
        layout.addWidget(logs_host)
        layout.addStretch(1)
        return page

    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)

        wrapper = QWidget(page)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        layout.addWidget(wrapper, 1)

        content = QWidget(wrapper)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)
        wrapper_layout.addWidget(content, 1)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(16)

        left_cluster = QHBoxLayout()
        left_cluster.setContentsMargins(0, 0, 0, 0)
        left_cluster.setSpacing(16)

        logs_label = QLabel("LOGS", page)
        logs_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; letter-spacing: 0.25em; background: transparent;"
        )
        left_cluster.addWidget(logs_label)

        pager_cluster = QHBoxLayout()
        pager_cluster.setContentsMargins(0, 0, 0, 0)
        pager_cluster.setSpacing(8)

        self._logs_prev_button = QPushButton("", page)
        self._logs_prev_button.setCursor(Qt.PointingHandCursor)
        self._logs_prev_button.setFocusPolicy(Qt.NoFocus)
        self._logs_prev_button.setFixedSize(24, 24)
        self._logs_prev_button.setIcon(_icon("chevron-left", "rgba(255, 255, 255, 0.60)", 16))
        self._logs_prev_button.setIconSize(QSize(16, 16))
        self._logs_prev_button.clicked.connect(lambda: self.change_logs_page(-1))
        self._logs_prev_button.setStyleSheet(self._logs_chevron_style())
        pager_cluster.addWidget(self._logs_prev_button)

        self._logs_pager_label = QLabel("0-0 of 0", page)
        self._logs_pager_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        pager_cluster.addWidget(self._logs_pager_label)

        self._logs_next_button = QPushButton("", page)
        self._logs_next_button.setCursor(Qt.PointingHandCursor)
        self._logs_next_button.setFocusPolicy(Qt.NoFocus)
        self._logs_next_button.setFixedSize(24, 24)
        self._logs_next_button.setIcon(_icon("chevron-right", "rgba(255, 255, 255, 0.60)", 16))
        self._logs_next_button.setIconSize(QSize(16, 16))
        self._logs_next_button.clicked.connect(lambda: self.change_logs_page(1))
        self._logs_next_button.setStyleSheet(self._logs_chevron_style())
        pager_cluster.addWidget(self._logs_next_button)

        left_cluster.addLayout(pager_cluster)
        top_row.addLayout(left_cluster)
        top_row.addStretch(1)

        download_all_button = QPushButton("Download All", page)
        download_all_button.setCursor(Qt.PointingHandCursor)
        download_all_button.setFocusPolicy(Qt.NoFocus)
        download_all_button.setIcon(_icon("download", "#FFFFFF", 12))
        download_all_button.setIconSize(QSize(12, 12))
        download_all_button.setFixedHeight(27)
        download_all_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {SUBTLE_BG};
                color: rgba(255, 255, 255, 0.70);
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 0 12px;
                font-family: {FONT_STACK};
                font-size: 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: {TEXT_PRIMARY};
            }}
            """
        )
        download_all_button.clicked.connect(self.download_all_logs)
        top_row.addWidget(download_all_button)
        content_layout.addLayout(top_row)

        self._logs_scroll_area = QScrollArea(content)
        self._logs_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._logs_scroll_area.setWidgetResizable(True)
        self._logs_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._logs_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._logs_scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 0px;
            }
            """
        )
        content_layout.addWidget(self._logs_scroll_area, 1)

        self._logs_grid = QWidget(content)
        self._logs_grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._logs_list_layout = QVBoxLayout(self._logs_grid)
        self._logs_list_layout.setContentsMargins(0, 0, 0, 0)
        self._logs_list_layout.setSpacing(12)
        self._logs_scroll_area.setWidget(self._logs_grid)

        return page

    def _build_stats_select(
        self,
        parent: QWidget,
        options: list[tuple[str, str]],
        current_value: str,
        on_change,
        *,
        minimum_width: int = 0,
    ) -> tuple[QFrame, QComboBox]:
        frame = QFrame(parent)
        frame.setFixedHeight(29)
        if minimum_width:
            frame.setMinimumWidth(minimum_width)
        frame.setStyleSheet(
            f"background: {SUBTLE_BG}; border: 1px solid {BORDER}; border-radius: 4px;"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(0)

        combo = QComboBox(frame)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setFocusPolicy(Qt.NoFocus)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        combo.setStyleSheet(
            f"""
            QComboBox {{
                background: transparent;
                color: rgba(255, 255, 255, 0.70);
                border: none;
                padding: 0 22px 0 12px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                color: rgba(255, 255, 255, 0.70);
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QAbstractItemView {{
                background: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.10);
                selection-background-color: rgba(255, 255, 255, 0.08);
                selection-color: #FFFFFF;
                font-family: {FONT_STACK};
                font-size: 12px;
            }}
            """
        )
        for value, label in options:
            combo.addItem(label, value)
        current_index = max(0, combo.findData(current_value))
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(lambda index, combo=combo: on_change(combo.itemData(index)))
        layout.addWidget(combo, 1)

        chevron = QLabel(frame)
        chevron.setPixmap(_icon("chevron-down", "rgba(255, 255, 255, 0.40)", 14).pixmap(14, 14))
        chevron.setFixedSize(14, 14)
        layout.addWidget(chevron, 0, Qt.AlignCenter)
        return frame, combo

    def _build_integrations_page(self) -> QWidget:
        page = QWidget()
        root_layout = QVBoxLayout(page)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea(page)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 0px;
                margin: 0;
            }
            """
        )
        root_layout.addWidget(scroll_area, 1)

        container = QWidget(page)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        scroll_area.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(0)

        page_label = QLabel("DISCORD INTEGRATION", container)
        page_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; letter-spacing: 0.25em; background: transparent; border: none;"
        )
        layout.addWidget(page_label)
        layout.addSpacing(24)

        webhook_card = self._integration_section_card(container, padding=24)
        webhook_layout = webhook_card.layout()

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        title = self._integration_title_label("Discord Webhooks", webhook_card)
        header_row.addWidget(title, 0, Qt.AlignVCenter)
        header_row.addStretch(1)

        self._integration_connection_icon = QLabel(webhook_card)
        self._integration_connection_icon.setFixedSize(14, 14)
        self._integration_connection_icon.setStyleSheet("background: transparent; border: none;")
        header_row.addWidget(self._integration_connection_icon, 0, Qt.AlignVCenter)

        self._integration_connection_label = QLabel("Not Connected", webhook_card)
        self._integration_connection_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 600; background: transparent; border: none;"
        )
        header_row.addWidget(self._integration_connection_label, 0, Qt.AlignVCenter)
        webhook_layout.addLayout(header_row)
        webhook_layout.addSpacing(20)

        webhook_label = QLabel("Webhook URL", webhook_card)
        webhook_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        webhook_layout.addWidget(webhook_label)
        webhook_layout.addSpacing(8)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(12)

        self._integration_webhook_input = QLineEdit(webhook_card)
        self._integration_webhook_input.setText(self.state.webhook.url)
        self._integration_webhook_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self._integration_webhook_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: {SUBTLE_BG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                min-height: 44px;
                padding: 0 12px;
                color: {TEXT_PRIMARY};
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QLineEdit:placeholder {{
                color: rgba(255, 255, 255, 0.30);
            }}
            """
        )
        self._integration_webhook_input.textChanged.connect(self._on_integration_webhook_changed)
        input_row.addWidget(self._integration_webhook_input, 1)

        test_button = QPushButton("Test", webhook_card)
        test_button.setFocusPolicy(Qt.NoFocus)
        test_button.setCursor(Qt.PointingHandCursor)
        test_button.setFixedSize(82, 44)
        test_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {SUBTLE_BG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
            }}
            """
        )
        test_button.clicked.connect(self._test_integrations_webhook)
        input_row.addWidget(test_button, 0)
        webhook_layout.addLayout(input_row)
        webhook_layout.addSpacing(20)

        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)
        toggle_row.setSpacing(12)
        toggle = ToggleSwitchButton(self.state.webhook.enabled, webhook_card)
        self._integration_toggle = toggle
        toggle.toggled.connect(self._on_integration_toggle_changed)
        toggle_row.addWidget(toggle, 0, Qt.AlignVCenter)
        toggle_label = QLabel("Enable Discord notifications", webhook_card)
        toggle_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.70); font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        toggle_row.addWidget(toggle_label, 0, Qt.AlignVCenter)
        toggle_row.addStretch(1)
        webhook_layout.addLayout(toggle_row)
        layout.addWidget(webhook_card)
        layout.addSpacing(24)

        lower_grid = QGridLayout()
        lower_grid.setContentsMargins(0, 0, 0, 0)
        lower_grid.setHorizontalSpacing(24)
        lower_grid.setVerticalSpacing(24)
        lower_grid.setColumnStretch(0, 1)
        lower_grid.setColumnStretch(1, 1)
        layout.addLayout(lower_grid)

        left_column = QWidget(container)
        left_column.setStyleSheet("background: transparent; border: none;")
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(24)
        lower_grid.addWidget(left_column, 0, 0)

        triggers_card = self._integration_section_card(left_column, padding=20)
        triggers_layout = triggers_card.layout()
        triggers_layout.addWidget(self._integration_title_label("Notification Triggers", triggers_card))
        triggers_layout.addSpacing(16)
        for key, label in (
            ("runStart", "When a run starts"),
            ("runFinish", "When a run finishes"),
            ("runFail", "When a run fails"),
            ("stageComplete", "When a stage is completed"),
        ):
            row = IntegrationCheckboxRow(
                label,
                getattr(self.state.webhook.triggers, self._integration_trigger_attr(key)),
                triggers_card,
            )
            row.toggled.connect(lambda checked, key=key: self._on_integration_trigger_changed(key, checked))
            triggers_layout.addWidget(row)
            triggers_layout.addSpacing(10)

        reward_row = IntegrationCheckboxRow(
            "When a reward is collected",
            self.state.webhook.triggers.reward_collected,
            triggers_card,
        )
        reward_row.toggled.connect(lambda checked: self._on_integration_trigger_changed("rewardCollected", checked))
        triggers_layout.addWidget(reward_row)
        self._integration_reward_dropdown_row, self._integration_reward_dropdown_combo = self._build_stats_select(
            triggers_card,
            [("gems", "Gems"), ("gold", "Gold"), ("essence", "Essence"), ("xp", "XP"), ("tokens", "Tokens"), ("fragments", "Fragments"), ("bones", "Bones")],
            self.state.webhook.triggers.reward_type_filter,
            self._on_integration_reward_type_changed,
        )
        reward_row_wrap = QWidget(triggers_card)
        reward_row_wrap.setStyleSheet("background: transparent; border: none;")
        reward_row_wrap_layout = QHBoxLayout(reward_row_wrap)
        reward_row_wrap_layout.setContentsMargins(24, 8, 0, 0)
        reward_row_wrap_layout.setSpacing(0)
        reward_row_wrap_layout.addWidget(self._integration_reward_dropdown_row, 1)
        triggers_layout.addWidget(reward_row_wrap)
        self._integration_reward_dropdown_row = reward_row_wrap
        left_column_layout.addWidget(triggers_card)

        pings_card = self._integration_section_card(left_column, padding=20)
        pings_layout = pings_card.layout()
        pings_layout.addWidget(self._integration_title_label("Mentions / Pings", pings_card))
        pings_layout.addSpacing(16)

        ping_id_label = QLabel("Discord User ID or Role ID", pings_card)
        ping_id_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        pings_layout.addWidget(ping_id_label)
        pings_layout.addSpacing(8)

        self._integration_ping_id_input = QLineEdit(pings_card)
        self._integration_ping_id_input.setText(self.state.webhook.ping.target_id)
        self._integration_ping_id_input.setPlaceholderText("123456789012345678")
        self._integration_ping_id_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: {SUBTLE_BG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                min-height: 44px;
                padding: 0 12px;
                color: {TEXT_PRIMARY};
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            QLineEdit:placeholder {{
                color: rgba(255, 255, 255, 0.30);
            }}
            """
        )
        self._integration_ping_id_input.textChanged.connect(self._on_integration_ping_id_changed)
        pings_layout.addWidget(self._integration_ping_id_input)
        pings_layout.addSpacing(20)

        ping_on_label = QLabel("Ping on", pings_card)
        ping_on_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        pings_layout.addWidget(ping_on_label)
        pings_layout.addSpacing(10)

        for key, label in (
            ("failuresOnly", "Failures only"),
            ("stageCompletion", "Stage completion"),
        ):
            row = IntegrationCheckboxRow(
                label,
                getattr(self.state.webhook.ping, self._integration_ping_attr(key)),
                pings_card,
            )
            row.toggled.connect(lambda checked, key=key: self._on_integration_ping_option_changed(key, checked))
            pings_layout.addWidget(row)
            pings_layout.addSpacing(10)

        select_reward_row = IntegrationCheckboxRow(
            "Select reward",
            self.state.webhook.ping.select_reward,
            pings_card,
        )
        select_reward_row.toggled.connect(lambda checked: self._on_integration_ping_option_changed("selectReward", checked))
        pings_layout.addWidget(select_reward_row)
        self._integration_ping_dropdown_row, self._integration_ping_dropdown_combo = self._build_stats_select(
            pings_card,
            [("gems", "Gems"), ("gold", "Gold"), ("essence", "Essence"), ("xp", "XP"), ("tokens", "Tokens"), ("fragments", "Fragments"), ("bones", "Bones")],
            self.state.webhook.ping.reward_type,
            self._on_integration_ping_reward_changed,
        )
        ping_row_wrap = QWidget(pings_card)
        ping_row_wrap.setStyleSheet("background: transparent; border: none;")
        ping_row_wrap_layout = QHBoxLayout(ping_row_wrap)
        ping_row_wrap_layout.setContentsMargins(24, 8, 0, 0)
        ping_row_wrap_layout.setSpacing(0)
        ping_row_wrap_layout.addWidget(self._integration_ping_dropdown_row, 1)
        pings_layout.addWidget(ping_row_wrap)
        self._integration_ping_dropdown_row = ping_row_wrap
        left_column_layout.addWidget(pings_card)
        left_column_layout.addStretch(1)

        right_card = self._integration_section_card(container, padding=20)
        right_layout = right_card.layout()
        lower_grid.addWidget(right_card, 0, 1)
        right_layout.addWidget(self._integration_title_label("Message Contents", right_card))
        right_layout.addSpacing(16)

        for key, label in (
            ("macroName", "Macro name"),
            ("gamemode", "Gamemode"),
            ("map", "Map"),
            ("result", "Result"),
            ("runDuration", "Run duration"),
            ("sessionRunCount", "Session run count"),
            ("winRate", "Win rate"),
            ("rewardsThisRun", "Rewards this run"),
            ("rewardsPerHour", "Rewards per hour"),
            ("screenshot", "Screenshot"),
        ):
            row = IntegrationCheckboxRow(
                label,
                getattr(self.state.webhook.contents, self._integration_content_attr(key)),
                right_card,
            )
            row.toggled.connect(lambda checked, key=key: self._on_integration_content_changed(key, checked))
            right_layout.addWidget(row)
            right_layout.addSpacing(10)

        preview_label = QLabel("PREVIEW", right_card)
        preview_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; letter-spacing: 0.08em; background: transparent; border: none;"
        )
        right_layout.addSpacing(18)
        right_layout.addWidget(preview_label)
        right_layout.addSpacing(12)

        preview = QFrame(right_card)
        preview.setStyleSheet("background: #2B2D31; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 4px;")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(16, 16, 16, 16)
        preview_layout.setSpacing(16)
        right_layout.addWidget(preview)

        preview_title = QLabel("Zeron Config", preview)
        preview_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 600; background: transparent; border: none;"
        )
        preview_layout.addWidget(preview_title)

        preview_grid = QGridLayout()
        preview_grid.setContentsMargins(0, 0, 0, 0)
        preview_grid.setHorizontalSpacing(24)
        preview_grid.setVerticalSpacing(12)
        preview_layout.addLayout(preview_grid)

        def preview_block(label: str, value: str, parent: QWidget) -> QWidget:
            block = QWidget(parent)
            block.setStyleSheet("background: transparent; border: none;")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(6)
            top = QLabel(label, block)
            top.setStyleSheet(
                f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; background: transparent; border: none;"
            )
            block_layout.addWidget(top)
            bottom = QLabel(value, block)
            bottom.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
            )
            block_layout.addWidget(bottom)
            return block

        preview_grid.addWidget(preview_block("MATCH RESULTS", "VICTORY", preview), 0, 0)
        preview_grid.addWidget(preview_block("TIME ELAPSED", "18m 42s", preview), 0, 1)
        preview_grid.addWidget(preview_block("TASK", "Dungeon - Underworld", preview), 1, 0)

        rewards_block = QWidget(preview)
        rewards_block.setStyleSheet("background: transparent; border: none;")
        rewards_block_layout = QVBoxLayout(rewards_block)
        rewards_block_layout.setContentsMargins(0, 0, 0, 0)
        rewards_block_layout.setSpacing(6)
        rewards_label = QLabel("REWARDS", rewards_block)
        rewards_label.setStyleSheet(
            f"color: rgba(255, 255, 255, 0.50); font-family: {FONT_STACK}; font-size: 10px; font-weight: 600; background: transparent; border: none;"
        )
        rewards_block_layout.addWidget(rewards_label)
        rewards_values = QLabel("+3 Doggy Bones\n+75 Gold\n+30 Gems", rewards_block)
        rewards_values.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        rewards_values.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        rewards_block_layout.addWidget(rewards_values)
        preview_grid.addWidget(rewards_block, 1, 1)

        footer_line = QFrame(preview)
        footer_line.setFixedHeight(1)
        footer_line.setStyleSheet("background: rgba(255, 255, 255, 0.08); border: none;")
        preview_layout.addWidget(footer_line)

        footer = QLabel("Zeron Config Result Webhook Test", preview)
        footer.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 9px; font-weight: 500; background: transparent; border: none;"
        )
        preview_layout.addWidget(footer)

        layout.addStretch(1)
        self._refresh_integrations_controls()
        return page

    def _integration_section_card(self, parent: QWidget, *, padding: int = 20) -> QFrame:
        card = QFrame(parent)
        card.setStyleSheet(
            f"background: rgba(255, 255, 255, 0.02); border: 1px solid {BORDER}; border-radius: 4px;"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(0)
        return card

    def _integration_title_label(self, text: str, parent: QWidget) -> QLabel:
        label = QLabel(text, parent)
        label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 600; background: transparent; border: none;"
        )
        return label

    @staticmethod
    def _integration_trigger_attr(key: str) -> str:
        return {
            "runStart": "run_start",
            "runFinish": "run_finish",
            "runFail": "run_fail",
            "rewardCollected": "reward_collected",
            "stageComplete": "stage_complete",
        }[key]

    @staticmethod
    def _integration_ping_attr(key: str) -> str:
        return {
            "failuresOnly": "failures_only",
            "stageCompletion": "stage_completion",
            "selectReward": "select_reward",
        }[key]

    @staticmethod
    def _integration_content_attr(key: str) -> str:
        return {
            "macroName": "macro_name",
            "gamemode": "gamemode",
            "map": "map",
            "result": "result",
            "runDuration": "run_duration",
            "sessionRunCount": "session_run_count",
            "winRate": "win_rate",
            "rewardsThisRun": "rewards_this_run",
            "rewardsPerHour": "rewards_per_hour",
            "screenshot": "screenshot",
        }[key]

    def _on_integration_webhook_changed(self, text: str) -> None:
        self.state.webhook.url = text
        if self.webhook_controller is not None:
            self.webhook_controller.sync_ui()
        self._refresh_integrations_controls()

    def _on_integration_toggle_changed(self, checked: bool) -> None:
        checked = bool(checked)
        if checked == self.state.webhook.enabled:
            return
        if checked and self.webhook_controller is not None:
            success = self.webhook_controller.enable_from_url(self.state.webhook.url)
            if not success and self._integration_toggle is not None:
                self._integration_toggle.blockSignals(True)
                self._integration_toggle.setChecked(False)
                self._integration_toggle._apply_state(False, animated=False)
                self._integration_toggle.blockSignals(False)
        elif checked:
            self.state.webhook.enabled = True
        else:
            if self.webhook_controller is not None:
                self.webhook_controller.disable()
            else:
                self.state.webhook.enabled = False
        self._refresh_integrations_controls()

    def _on_integration_trigger_changed(self, key: str, checked: bool) -> None:
        setattr(self.state.webhook.triggers, self._integration_trigger_attr(key), bool(checked))
        self._refresh_integrations_controls()

    def _on_integration_reward_type_changed(self, value: str) -> None:
        if value:
            self.state.webhook.triggers.reward_type_filter = value

    def _on_integration_ping_id_changed(self, value: str) -> None:
        self.state.webhook.ping.target_id = value

    def _on_integration_ping_option_changed(self, key: str, checked: bool) -> None:
        setattr(self.state.webhook.ping, self._integration_ping_attr(key), bool(checked))
        self._refresh_integrations_controls()

    def _on_integration_ping_reward_changed(self, value: str) -> None:
        if value:
            self.state.webhook.ping.reward_type = value

    def _on_integration_content_changed(self, key: str, checked: bool) -> None:
        setattr(self.state.webhook.contents, self._integration_content_attr(key), bool(checked))

    def _test_integrations_webhook(self) -> None:
        if self.webhook_controller is None:
            return
        self.webhook_controller.test_url(self.state.webhook.url)
        self._refresh_integrations_controls()

    def _refresh_integrations_controls(self) -> None:
        is_connected = bool(self.state.webhook.url.strip())
        if self._integration_webhook_input is not None and self._integration_webhook_input.text() != self.state.webhook.url:
            self._integration_webhook_input.blockSignals(True)
            self._integration_webhook_input.setText(self.state.webhook.url)
            self._integration_webhook_input.blockSignals(False)
        if self._integration_webhook_input is not None:
            self._integration_webhook_input.setEnabled(not self.state.webhook.enabled)
        if self._integration_toggle is not None and self._integration_toggle.isChecked() != self.state.webhook.enabled:
            self._integration_toggle.blockSignals(True)
            self._integration_toggle.setChecked(self.state.webhook.enabled)
            self._integration_toggle._apply_state(self.state.webhook.enabled, animated=False)
            self._integration_toggle.blockSignals(False)
        if self._integration_connection_icon is not None:
            icon_name = "check" if is_connected else "x"
            icon_color = ACCENT_GREEN_TEXT if is_connected else TEXT_SECONDARY
            self._integration_connection_icon.setPixmap(_icon(icon_name, icon_color, 14).pixmap(14, 14))
        if self._integration_connection_label is not None:
            self._integration_connection_label.setText("Connected" if is_connected else "Not Connected")
            self._integration_connection_label.setStyleSheet(
                f"color: {ACCENT_GREEN_TEXT if is_connected else TEXT_SECONDARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 600; background: transparent; border: none;"
            )
        if self._integration_reward_dropdown_row is not None:
            self._integration_reward_dropdown_row.setVisible(self.state.webhook.triggers.reward_collected)
        if self._integration_ping_dropdown_row is not None:
            self._integration_ping_dropdown_row.setVisible(self.state.webhook.ping.select_reward)

    def sync_integrations_ui(self) -> None:
        self._refresh_integrations_controls()

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(20)
        layout.addWidget(self._build_section_header("SETTINGS", ""))

        panel = QFrame(page)
        panel.setStyleSheet(
            f"background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 10px;"
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(0)
        layout.addWidget(panel)

        debug_row = QWidget(panel)
        debug_row.setStyleSheet("background: transparent; border: none;")
        debug_layout = QHBoxLayout(debug_row)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setSpacing(16)

        debug_label = QLabel("Debug Console Mode", debug_row)
        debug_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
        )
        debug_layout.addWidget(debug_label)
        debug_layout.addStretch(1)

        toggle = ToggleSwitchButton(self.state.debug_console_mode, debug_row)
        toggle.toggled.connect(self._on_settings_debug_console_changed)
        self._settings_debug_toggle = toggle
        debug_layout.addWidget(toggle, 0, Qt.AlignVCenter)
        panel_layout.addWidget(debug_row)

        layout.addStretch(1)
        return page

    def _on_settings_debug_console_changed(self, checked: bool) -> None:
        self.state.debug_console_mode = bool(checked)

    def _build_import_modal(self) -> None:
        if self._modal_backdrop is not None:
            return
        page = self.window.overlayPage
        self._modal_backdrop = QWidget(page)
        self._modal_backdrop.setStyleSheet("background: rgba(0, 0, 0, 0.60);")
        self._modal_backdrop.hide()
        self._modal_backdrop.mousePressEvent = lambda event: self._close_import_modal()  # type: ignore[assignment]

        backdrop_effect = QGraphicsOpacityEffect(self._modal_backdrop)
        backdrop_effect.setOpacity(0.0)
        self._modal_backdrop.setGraphicsEffect(backdrop_effect)
        self._modal_backdrop_effect = backdrop_effect
        self._modal_backdrop_anim = QPropertyAnimation(backdrop_effect, b"opacity", self._shell)
        self._modal_backdrop_anim.setDuration(180)

        self._modal_card = QFrame(page)
        self._modal_card.setFixedWidth(448)
        self._modal_card.setStyleSheet(
            f"background: #1A1A1A; border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 4px;"
        )
        self._modal_card.hide()

        modal_effect = QGraphicsOpacityEffect(self._modal_card)
        modal_effect.setOpacity(0.0)
        self._modal_card.setGraphicsEffect(modal_effect)
        self._modal_card_effect = modal_effect
        self._modal_card_anim = QPropertyAnimation(modal_effect, b"opacity", self._shell)
        self._modal_card_anim.setDuration(180)

        modal_layout = QVBoxLayout(self._modal_card)
        modal_layout.setContentsMargins(24, 24, 24, 24)
        modal_layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        title = QLabel("Import Macro", self._modal_card)
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 600; background: transparent;"
        )
        header_row.addWidget(title)
        header_row.addStretch(1)

        close_button = QPushButton("", self._modal_card)
        close_button.setFocusPolicy(Qt.NoFocus)
        close_button.setIcon(_icon("x", "rgba(255, 255, 255, 0.40)", 16))
        close_button.setIconSize(QSize(16, 16))
        close_button.setFixedSize(16, 16)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                background: transparent;
            }}
            """
        )
        close_button.clicked.connect(self._close_import_modal)
        header_row.addWidget(close_button)
        modal_layout.addLayout(header_row)

        self._import_context_label = QLabel("", self._modal_card)
        self._import_context_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-family: {FONT_STACK}; font-size: 11px; font-weight: 500; background: transparent;"
        )
        modal_layout.addWidget(self._import_context_label)

        self._import_textarea = QPlainTextEdit(self._modal_card)
        self._import_textarea.setPlaceholderText("Paste your macro code here...")
        self._import_textarea.setFixedHeight(132)
        self._import_textarea.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {SUBTLE_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 10px 12px;
                font-family: {FONT_STACK};
                font-size: 12px;
                font-weight: 500;
            }}
            """
        )
        modal_layout.addWidget(self._import_textarea)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        cancel_button = QPushButton("Cancel", self._modal_card)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setFocusPolicy(Qt.NoFocus)
        cancel_button.setMinimumHeight(32)
        cancel_button.setStyleSheet(self._secondary_button_style())
        cancel_button.clicked.connect(self._close_import_modal)
        action_row.addWidget(cancel_button)

        import_button = QPushButton("Import", self._modal_card)
        import_button.setCursor(Qt.PointingHandCursor)
        import_button.setFocusPolicy(Qt.NoFocus)
        import_button.setMinimumHeight(32)
        import_button.setStyleSheet(self._primary_button_style())
        import_button.clicked.connect(self._submit_import_modal)
        action_row.addWidget(import_button)
        modal_layout.addLayout(action_row)

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 20px; font-weight: 800; background: transparent;"
        )
        return label

    def _section_subtitle(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 700; background: transparent;"
        )
        return label

    def _build_section_header(self, title: str, subtitle: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._section_title(title))
        layout.addWidget(self._section_subtitle(subtitle))
        return widget

    def _pager_button_style(self) -> str:
        return (
            f"QPushButton {{ background: {SUBTLE_BG}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; "
            f"border-radius: 8px; font-family: {FONT_STACK}; font-size: 14px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {SUBTLE_BG_HOVER}; }}"
            "QPushButton:disabled { color: rgba(255,255,255,0.18); border-color: rgba(255,255,255,0.04); }"
        )

    def _logs_chevron_style(self) -> str:
        return (
            "QPushButton { background: transparent; border: none; padding: 0; border-radius: 4px; }"
            "QPushButton:hover { background: transparent; }"
            "QPushButton:disabled { background: transparent; }"
        )

    def _primary_button_style(self) -> str:
        return (
            f"QPushButton {{ background: #FFFFFF; color: #000000; border: none; border-radius: 4px; "
            f"padding: 0 16px; font-family: {FONT_STACK}; font-size: 12px; font-weight: 600; }}"
            "QPushButton:hover { background: rgba(255,255,255,0.90); }"
        )

    def _secondary_button_style(self) -> str:
        return (
            f"QPushButton {{ background: {SUBTLE_BG}; color: {TEXT_MUTED}; border: none; border-radius: 4px; "
            f"padding: 0 16px; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {SUBTLE_BG_HOVER}; color: {TEXT_PRIMARY}; }}"
        )

    def _show_overlay_tab(self, tab_key: str) -> None:
        self._overlay_current_tab = tab_key
        if self._nav_stack is None:
            return
        page_index = {key: index for index, (key, _label) in enumerate(NAV_TABS)}[tab_key]
        self._nav_stack.setCurrentIndex(page_index)
        for key, button in self._nav_buttons.items():
            button.set_active(key == tab_key)
        if tab_key == "stats":
            self._refresh_mode_summary_cards()
            self.refresh_reward_stats_tab()
        elif tab_key == "logs":
            self.refresh_logs_tab()
        self._sync_shell_geometry()

    def _set_active_mode(self, mode: str) -> None:
        if mode == self._active_mode and self._mode_highlight is not None:
            self._animate_mode_highlight()
            self._schedule_mode_highlight_sync()
            return
        self._active_mode = mode
        self._ensure_valid_active_map(mode)
        for key, button in self._mode_buttons.items():
            button.set_active(key == mode)
        self._animate_mode_highlight()
        self._rebuild_cards(animated=True)
        self._schedule_mode_highlight_sync()

    def _animate_mode_highlight(self) -> None:
        if self._mode_highlight is None or self._mode_highlight_animation is None:
            return
        button = self._mode_buttons.get(self._active_mode)
        if button is None:
            return
        target = button.geometry().adjusted(0, 0, 0, 0)
        if self._mode_highlight.geometry().isNull():
            self._mode_highlight.setGeometry(target)
            self._mode_highlight.show()
            self._mode_highlight.lower()
            button.raise_()
            return
        self._mode_highlight.show()
        self._mode_highlight.lower()
        for mode_button in self._mode_buttons.values():
            mode_button.raise_()
        self._mode_highlight_animating = True
        self._mode_highlight_animation.stop()
        self._mode_highlight_animation.setStartValue(self._mode_highlight.geometry())
        self._mode_highlight_animation.setEndValue(target)
        self._mode_highlight_animation.start()

    def _on_mode_highlight_animation_finished(self) -> None:
        self._mode_highlight_animating = False

    def _sync_mode_highlight_geometry(self) -> None:
        if self._mode_highlight is None:
            return
        if self._mode_highlight_animating:
            return
        button = self._mode_buttons.get(self._active_mode)
        if button is None:
            return
        self._mode_highlight.setGeometry(button.geometry())
        self._mode_highlight.lower()
        button.raise_()

    def _schedule_mode_highlight_sync(self) -> None:
        if self._mode_highlight_sync_pending:
            return
        self._mode_highlight_sync_pending = True
        QTimer.singleShot(0, self._sync_mode_highlight_after_layout)

    def _sync_mode_highlight_after_layout(self) -> None:
        self._mode_highlight_sync_pending = False
        if self._mode_highlight is None:
            return
        tab_container = self._mode_highlight.parentWidget()
        if tab_container is not None and tab_container.layout() is not None:
            tab_container.layout().activate()
        self._sync_mode_highlight_geometry()

    def _sync_shell_geometry(self) -> None:
        if self._shell is None:
            return
        overlay_parent = getattr(self.window, "overlayContent", self.window.overlayPage)
        scroll_area = getattr(self.window, "overlayScrollArea", None)
        page_width = max(700, self.window.width())
        page_height = max(580, self.window.height())
        self.window.overlayPage.resize(page_width, page_height)
        page_rect = QRect(0, 0, page_width, page_height)
        width = page_width
        height = page_height

        if scroll_area is not None:
            scroll_area.setGeometry(page_rect)

        if self._modal_backdrop is not None:
            self._modal_backdrop.setGeometry(page_rect)
        if self._modal_card is not None:
            modal_height = self._modal_card.sizeHint().height()
            modal_x = (page_rect.width() - self._modal_card.width()) // 2
            modal_y = max(24, (page_rect.height() - modal_height) // 2)
            self._modal_card.setGeometry(modal_x, modal_y, self._modal_card.width(), modal_height)

        self._shell.setGeometry(0, 0, width, height)
        self._shell.resize(width, height)
        overlay_parent.resize(width, height)
        overlay_parent.setFixedSize(width, height)
        if self._shell_layout is not None:
            self._shell_layout.activate()
        self._apply_explicit_shell_geometry(width, height)

    def _apply_explicit_shell_geometry(self, width: int, height: int) -> None:
        if (
            self._header_frame is None
            or self._body_widget is None
            or self._sidebar_frame is None
            or self._content_widget is None
            or self._nav_stack is None
        ):
            return
        header_height = 84
        sidebar_width = 176
        body_height = max(0, height - header_height)
        content_width = max(0, width - sidebar_width)

        self._header_frame.setGeometry(0, 0, width, header_height)
        self._body_widget.setGeometry(0, header_height, width, body_height)
        self._sidebar_frame.setGeometry(0, 0, sidebar_width, body_height)
        self._content_widget.setGeometry(sidebar_width, 0, content_width, body_height)
        self._nav_stack.setGeometry(0, 0, content_width, body_height)

        for page in (self._config_page, self._stats_page, self._logs_page_widget, self._integrations_page, self._settings_page):
            if page is not None:
                page.resize(content_width, body_height)
                if page.layout() is not None:
                    page.layout().activate()
        self._sync_mode_highlight_geometry()
        self._schedule_mode_highlight_sync()
        for card in self._mode_cards.values():
            card.sync_internal_geometry()

    def init_overlay_dropdowns(self) -> None:
        for mode, _label in MODE_TABS:
            widgets = self.overlay_widgets.modes[mode]
            maps = get_maps_for_mode(mode)
            widgets.map_combo.blockSignals(True)
            widgets.map_combo.clear()
            if maps:
                widgets.map_combo.addItems(maps)
            else:
                widgets.map_combo.addItem("(No maps found)")
            widgets.map_combo.blockSignals(False)

            existing_active_map = self._active_map_by_mode.get(mode)
            if existing_active_map in maps:
                widgets.map_combo.setCurrentText(existing_active_map)
            elif maps:
                self._active_map_by_mode[mode] = maps[0]
                widgets.map_combo.setCurrentText(maps[0])
            else:
                self._active_map_by_mode.pop(mode, None)

            for map_name in maps:
                self._sync_hidden_macro_combo(mode, map_name)

    def _sync_hidden_macro_combo(self, mode: str, map_name: str) -> list[str]:
        widgets = self.overlay_widgets.modes[mode]
        folder = get_macro_folder_for_mode(mode, map_name)
        macros = []
        if os.path.exists(folder):
            macros = sorted(filename[:-5] for filename in os.listdir(folder) if filename.endswith(".json"))

        selected_macro = self._selected_macro_by_mode_map.get((mode, map_name), "")
        if selected_macro not in macros:
            selected_macro = macros[0] if macros else ""
            self._selected_macro_by_mode_map[(mode, map_name)] = selected_macro

        if widgets.map_combo.currentText() == map_name:
            widgets.macro_combo.blockSignals(True)
            widgets.macro_combo.clear()
            for macro_name in macros:
                widgets.macro_combo.addItem(macro_name)
            if selected_macro:
                widgets.macro_combo.setCurrentText(selected_macro)
            widgets.macro_combo.blockSignals(False)
        return macros

    def _ensure_valid_active_map(self, mode: str) -> str | None:
        maps = get_maps_for_mode(mode)
        active_map = self._active_map_by_mode.get(mode)
        if active_map in maps:
            return active_map
        if maps:
            self._active_map_by_mode[mode] = maps[0]
            return maps[0]
        self._active_map_by_mode.pop(mode, None)
        return None

    def _rebuild_cards(self, *, animated: bool) -> None:
        if self._cards_layout is None or self._cards_container is None:
            return

        self._cards_container.setUpdatesEnabled(False)
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
        self._mode_cards.clear()

        maps = get_maps_for_mode(self._active_mode)
        active_map = self._ensure_valid_active_map(self._active_mode)

        if not maps:
            empty_state = self._empty_state_pool.get(self._active_mode)
            if empty_state is None:
                empty_state = QFrame(self._cards_container)
                empty_state.setStyleSheet(
                    f"background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 10px;"
                )
                empty_layout = QVBoxLayout(empty_state)
                empty_layout.setContentsMargins(24, 24, 24, 24)
                empty_layout.setSpacing(10)
                title = QLabel("No maps found for this mode yet.", empty_state)
                title.setStyleSheet(
                    f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 14px; font-weight: 700; background: transparent;"
                )
                body = QLabel(
                    "Create the map folder inside the unified macros directory and it will appear here automatically.",
                    empty_state,
                )
                body.setWordWrap(True)
                body.setStyleSheet(
                    f"color: {TEXT_MUTED}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent;"
                )
                empty_layout.addWidget(title)
                empty_layout.addWidget(body)
                empty_layout.addStretch(1)
                self._empty_state_pool[self._active_mode] = empty_state
            empty_state.show()
            self._cards_layout.addWidget(empty_state, 0, 0, 1, 2)
            self._cards_container.setMinimumHeight(180)
        else:
            for index, map_name in enumerate(maps):
                card_key = (self._active_mode, map_name)
                card = self._card_pool.get(card_key)
                if card is None:
                    card = OverlayMapCard(map_name, self._cards_container)
                    card.set_macro_refresh_callback(
                        lambda mode=self._active_mode, map_name=map_name: self._refresh_card_macro_options(mode, map_name)
                    )
                    card.activated.connect(
                        lambda map_name, mode=self._active_mode: self._activate_map(mode, map_name)
                    )
                    card.create_requested.connect(
                        lambda map_name, mode=self._active_mode: self.create_macro_from_overlay(mode, map_name)
                    )
                    card.select_requested.connect(
                        lambda map_name, mode=self._active_mode: self.edit_macro_from_overlay(mode, map_name=map_name)
                    )
                    card.macro_changed.connect(
                        lambda map_name, macro_name, mode=self._active_mode: self._on_card_macro_changed(
                            mode,
                            map_name,
                            macro_name,
                        )
                    )
                    self._card_pool[card_key] = card
                macros = self._sync_hidden_macro_combo(self._active_mode, map_name)
                selected_macro = self._selected_macro_by_mode_map.get((self._active_mode, map_name), "")
                card.set_macros(macros, selected_macro)
                matched_image = match_map_image(self._active_mode, map_name)
                if matched_image is not None:
                    matched_image = os.path.abspath(matched_image)
                card.set_background(matched_image)
                card.set_active(map_name == active_map)
                card.show()
                self._mode_cards[map_name] = card
                self._cards_layout.addWidget(card, index // 2, index % 2)
            row_count = max(1, (len(maps) + 1) // 2)
            self._cards_container.setMinimumHeight(row_count * 246 + max(0, row_count - 1) * 24)

        self._cards_layout.setRowStretch(max(0, len(maps) // 2 + 1), 1)
        self._cards_container.setUpdatesEnabled(True)
        if self._cards_scroll_area is not None:
            self._cards_scroll_area.verticalScrollBar().setValue(0)

    def _activate_map(self, mode: str, map_name: str) -> None:
        self._active_map_by_mode[mode] = map_name
        widgets = self.overlay_widgets.modes[mode]
        if widgets.map_combo.findText(map_name) >= 0:
            widgets.map_combo.setCurrentText(map_name)
        for card_map, card in self._mode_cards.items():
            card.set_active(card_map == map_name)
        self._refresh_mode_summary_cards()

    def _on_card_macro_changed(self, mode: str, map_name: str, macro_name: str) -> None:
        self._selected_macro_by_mode_map[(mode, map_name)] = macro_name
        self._activate_map(mode, map_name)
        widgets = self.overlay_widgets.modes[mode]
        if widgets.map_combo.findText(map_name) >= 0:
            widgets.map_combo.setCurrentText(map_name)
            if widgets.macro_combo.findText(macro_name) >= 0:
                widgets.macro_combo.setCurrentText(macro_name)

    def _resolve_target_map(self, mode: str, explicit_map: str | None = None) -> str | None:
        if explicit_map:
            return explicit_map
        active_map = self._active_map_by_mode.get(mode)
        if active_map:
            return active_map
        maps = get_maps_for_mode(mode)
        return maps[0] if maps else None

    def _refresh_card_macro_options(self, mode: str, map_name: str) -> None:
        card = self._card_pool.get((mode, map_name))
        if card is None:
            return
        macros = self._sync_hidden_macro_combo(mode, map_name)
        selected_macro = self._selected_macro_by_mode_map.get((mode, map_name), "")
        card.set_macros(macros, selected_macro)

    def _resolve_selected_macro(self, mode: str, map_name: str, explicit_macro: str | None = None) -> str:
        if explicit_macro:
            return explicit_macro
        remembered = self._selected_macro_by_mode_map.get((mode, map_name), "")
        if remembered:
            return remembered
        widgets = self.overlay_widgets.modes[mode]
        if widgets.map_combo.currentText() == map_name:
            return widgets.macro_combo.currentText().strip()
        return ""

    def create_macro_from_overlay(self, mode: str, map_name: str | None = None) -> None:
        target_map = self._resolve_target_map(mode, map_name)
        if not target_map:
            self.window.statusbar.showMessage("Please select a map before creating a macro.")
            return

        self._activate_map(mode, target_map)
        self.state.overlay.mode = mode
        self.state.overlay.map_name = target_map
        self.state.editing_macro_name = None
        self.advanced_editor.start_new_from_overlay(mode, target_map)
        self.window.statusbar.showMessage(f"Creating macro for {mode} - {target_map}")

    def _open_macros_folder_for_active_selection(self) -> None:
        os.makedirs(MACROS_FOLDER, exist_ok=True)
        subprocess.run(["open", MACROS_FOLDER], check=False)
        self.window.statusbar.showMessage("Opened the macros folder.")

    def import_macro_from_code(self, mode: str, map_name: str | None = None) -> None:
        target_map = self._resolve_target_map(mode, map_name)
        if not target_map:
            self.window.statusbar.showMessage("Please select a map before importing a macro.")
            return
        self._pending_import_mode = mode
        self._pending_import_map = target_map
        self._activate_map(mode, target_map)
        if self._import_context_label is not None:
            mode_label = dict(MODE_TABS).get(mode, mode.title())
            self._import_context_label.setText(f"Target: {mode_label} / {target_map}")
        if self._import_textarea is not None:
            self._import_textarea.clear()
        self._show_import_modal()

    def _show_import_modal(self) -> None:
        if self._modal_backdrop is None or self._modal_card is None:
            return
        self._sync_shell_geometry()
        self._modal_backdrop.show()
        self._modal_card.show()
        self._modal_backdrop.raise_()
        self._modal_card.raise_()
        self._modal_backdrop_anim.stop()
        self._modal_backdrop_anim.setStartValue(0.0)
        self._modal_backdrop_anim.setEndValue(1.0)
        self._modal_backdrop_anim.start()
        self._modal_card_anim.stop()
        self._modal_card_anim.setStartValue(0.0)
        self._modal_card_anim.setEndValue(1.0)
        self._modal_card_anim.start()
        if self._import_textarea is not None:
            self._import_textarea.setFocus()

    def _close_import_modal(self) -> None:
        if self._modal_backdrop is None or self._modal_card is None:
            return
        self._modal_backdrop.hide()
        self._modal_card.hide()
        self._pending_import_mode = None
        self._pending_import_map = None

    def _submit_import_modal(self) -> None:
        if self._pending_import_mode is None or self._pending_import_map is None or self._import_textarea is None:
            return

        share_code = self._import_textarea.toPlainText().strip()
        normalized_code = self.sharing_service.normalize_share_code(share_code)
        if not normalized_code:
            self.window.statusbar.showMessage("Share code cannot be empty.")
            return

        mode = self._pending_import_mode
        map_name = self._pending_import_map

        try:
            record = self.sharing_service.fetch_shared_macro(normalized_code)
            self.sharing_service.validate_import_target(record, mode, map_name)
            target_folder = get_macro_folder_for_mode(mode, map_name)
            target_path = self.sharing_service.build_import_macro_path(
                target_folder,
                record["macro_name"],
                record["share_code"],
            )
            macro_json.save_macro(record["macro_json"], target_path)
        except MacroSharingError as exc:
            self.window.statusbar.showMessage(str(exc))
            return
        except Exception as exc:
            self.window.statusbar.showMessage(f"Failed to import macro: {exc}")
            return

        imported_name = os.path.splitext(os.path.basename(target_path))[0]
        self._selected_macro_by_mode_map[(mode, map_name)] = imported_name
        self.refresh_overlay_macro_combo(mode, map_name=map_name)
        self._close_import_modal()
        self.window.statusbar.showMessage(f"Imported macro '{imported_name}' into {dict(MODE_TABS).get(mode, mode)} / {map_name}")

    def refresh_overlay_macro_combo(self, mode: str, map_name: str | None = None) -> None:
        target_map = self._resolve_target_map(mode, map_name)
        self.init_overlay_dropdowns()
        if target_map is not None:
            macros = self._sync_hidden_macro_combo(mode, target_map)
            remembered = self._selected_macro_by_mode_map.get((mode, target_map), "")
            if remembered not in macros:
                remembered = macros[0] if macros else ""
                self._selected_macro_by_mode_map[(mode, target_map)] = remembered

            if mode == self._active_mode:
                card = self._mode_cards.get(target_map)
                if card is not None:
                    card.set_macros(macros, remembered)
                    matched_image = match_map_image(mode, target_map)
                    card.set_background(os.path.abspath(matched_image) if matched_image else None)
        if mode == self._active_mode:
            self._rebuild_cards(animated=False)
        self._refresh_mode_summary_cards()

    def edit_macro_from_overlay(
        self,
        mode: str,
        map_name: str | None = None,
        macro_name: str | None = None,
    ) -> None:
        target_map = self._resolve_target_map(mode, map_name)
        if not target_map:
            self.window.statusbar.showMessage("Please select a map before selecting a macro.")
            return
        selected_macro = self._resolve_selected_macro(mode, target_map, macro_name)
        if not selected_macro:
            self.window.statusbar.showMessage("No macro file selected!")
            return

        mode_map_folder = get_macro_folder_for_mode(mode, target_map)
        macro_path = os.path.join(mode_map_folder, f"{selected_macro}.json")
        if not os.path.exists(macro_path):
            self.window.statusbar.showMessage(f"Macro file not found: {selected_macro}")
            self.refresh_overlay_macro_combo(mode, map_name=target_map)
            return

        self._activate_map(mode, target_map)
        loaded = self.advanced_editor.load_macro_from_path(
            macro_path,
            mode=mode,
            map_name=target_map,
            macro_name=selected_macro,
            origin="overlay",
        )
        if loaded:
            self.window.statusbar.showMessage(f"Editing macro: {selected_macro} ({mode}/{target_map})")

    def refresh_overlay_stats_for_mode(self, mode: str) -> None:
        import supabase_client

        active_map = self._resolve_target_map(mode)
        label_set = self._mode_stat_value_labels.get(mode)
        if label_set is None:
            return

        if not active_map:
            label_set["map"].setText("No map selected")
            label_set["runs"].setText("Runs: 0")
            label_set["total"].setText("Total: 0")
            label_set["time"].setText("Time: 0s")
            return

        session_key = (mode, active_map)
        session_runs = self.state.session_run_counts.get(session_key, 0)
        total_runs = supabase_client.get_total_runs(None, mode, active_map)
        total_time = supabase_client.get_total_time(None, mode, active_map)

        label_set["map"].setText(active_map)
        label_set["runs"].setText(f"Runs: {session_runs}")
        label_set["total"].setText(f"Total: {total_runs}")
        label_set["time"].setText(f"Time: {supabase_client.format_duration(total_time)}")

    def _refresh_mode_summary_cards(self) -> None:
        for mode, _label in MODE_TABS:
            self.refresh_overlay_stats_for_mode(mode)

    def refresh_all_overlay_stats(self) -> None:
        self.init_overlay_dropdowns()
        self._ensure_valid_active_map(self._active_mode)
        self._rebuild_cards(animated=False)
        self._refresh_mode_summary_cards()
        self.refresh_reward_stats_tab()
        if self._overlay_current_tab == "logs":
            self.refresh_logs_tab()
        self._sync_shell_geometry()
        self._schedule_mode_highlight_sync()
        QTimer.singleShot(30, self._sync_mode_highlight_after_layout)

    def _on_stats_timeframe_changed(self, value: str) -> None:
        if not value or value == self._stats_timeframe:
            return
        self._stats_timeframe = value
        self.refresh_reward_stats_tab()

    def _on_stats_filter_changed(self, value: str) -> None:
        if not value:
            value = "all"
        if value == self._stats_reward_filter:
            return
        self._stats_reward_filter = value
        self.refresh_reward_stats_tab()

    def _on_stats_sort_changed(self, value: str) -> None:
        if not value:
            value = "latest"
        if value == self._stats_sort_by:
            return
        self._stats_sort_by = value
        self.refresh_reward_stats_tab()

    def _load_stats_run_entries(self) -> list[StatsRunEntry]:
        entries: list[StatsRunEntry] = []
        for saved_log in self.log_service.list_saved_logs():
            entries.append(self._parse_stats_run_entry(saved_log))
        return entries

    def _parse_stats_run_entry(self, saved_log: SavedRunLog) -> StatsRunEntry:
        rewards: dict[str, int] = {}
        started_at: datetime | None = None
        try:
            with open(saved_log.path, "r", encoding="utf-8") as handle:
                lines = [line.rstrip("\n") for line in handle]
        except OSError:
            lines = []

        timestamp_pattern = re.compile(r"^\d{2}/\d{2} \d{2}:\d{2}:\d{2}$")
        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if started_at is None and timestamp_pattern.fullmatch(line):
                started_at = self._resolve_stats_timestamp(line, saved_log.modified_at)
            if line == "Rewards:":
                json_lines: list[str] = []
                for reward_line in lines[index + 1 :]:
                    stripped = reward_line.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("Total time:"):
                        break
                    json_lines.append(stripped)
                if json_lines:
                    try:
                        parsed_rewards = json.loads("\n".join(json_lines))
                    except json.JSONDecodeError:
                        parsed_rewards = {}
                    if isinstance(parsed_rewards, dict):
                        rewards = self._normalize_stats_rewards(parsed_rewards)
                break
            if line.startswith("Rewards: "):
                payload = line.split(":", 1)[1].strip()
                if payload == "{}":
                    rewards = {}
                else:
                    try:
                        parsed_rewards = json.loads(payload)
                    except json.JSONDecodeError:
                        parsed_rewards = {}
                    if isinstance(parsed_rewards, dict):
                        rewards = self._normalize_stats_rewards(parsed_rewards)
                break

        display_timestamp = (
            started_at.strftime("%Y-%m-%d %H:%M:%S")
            if started_at is not None
            else datetime.fromtimestamp(saved_log.modified_at).strftime("%Y-%m-%d %H:%M:%S")
        )
        return StatsRunEntry(saved_log=saved_log, rewards=rewards, started_at=started_at, display_timestamp=display_timestamp)

    @staticmethod
    def _normalize_stats_rewards(rewards: dict) -> dict[str, int]:
        normalized: dict[str, int] = {}
        for reward_name, amount in rewards.items():
            canonical = normalize_reward_name(str(reward_name)) or str(reward_name)
            try:
                parsed_amount = int(amount)
            except (TypeError, ValueError):
                continue
            if parsed_amount <= 0:
                continue
            normalized[canonical] = normalized.get(canonical, 0) + parsed_amount
        return normalized

    @staticmethod
    def _resolve_stats_timestamp(raw_timestamp: str, fallback_modified_at: float) -> datetime | None:
        try:
            parsed = datetime.strptime(raw_timestamp, "%m/%d %H:%M:%S")
        except ValueError:
            return None
        now = datetime.now()
        resolved = parsed.replace(year=now.year)
        if resolved > now + timedelta(days=1):
            resolved = resolved.replace(year=now.year - 1)
        if resolved.timestamp() <= 0:
            return datetime.fromtimestamp(fallback_modified_at)
        return resolved

    def _timeframe_cutoff(self) -> datetime:
        now = datetime.now()
        if self._stats_timeframe == "7d":
            return now - timedelta(days=7)
        if self._stats_timeframe == "30d":
            return now - timedelta(days=30)
        return now - timedelta(hours=24)

    def _stats_reward_totals(self, entries: list[StatsRunEntry]) -> list[tuple[str, int]]:
        totals: dict[str, int] = {}
        cutoff = self._timeframe_cutoff()
        for entry in entries:
            reference_time = entry.started_at or datetime.fromtimestamp(entry.saved_log.modified_at)
            if reference_time < cutoff:
                continue
            for reward_name, amount in entry.rewards.items():
                totals[reward_name] = totals.get(reward_name, 0) + amount

        ordered_names = list(REWARD_VISUALS.keys()) + sorted(name for name in totals if name not in REWARD_VISUALS)
        return [(name, totals[name]) for name in ordered_names if totals.get(name, 0) > 0]

    def _refresh_stats_filter_options(self, entries: list[StatsRunEntry]) -> None:
        if self._stats_filter_combo is None:
            return
        reward_names = set()
        for entry in entries:
            if not entry.rewards:
                continue
            reward_names.update(entry.rewards.keys())
        ordered_names = [name for name in REWARD_VISUALS if name in reward_names] + sorted(
            name for name in reward_names if name not in REWARD_VISUALS
        )
        options = [("all", "All Rewards")] + [(name, name) for name in ordered_names]

        self._stats_filter_combo.blockSignals(True)
        self._stats_filter_combo.clear()
        for value, label in options:
            self._stats_filter_combo.addItem(label, value)
        current_index = self._stats_filter_combo.findData(self._stats_reward_filter)
        if current_index < 0:
            self._stats_reward_filter = "all"
            current_index = 0
        self._stats_filter_combo.setCurrentIndex(current_index)
        self._stats_filter_combo.blockSignals(False)

    def _filtered_stats_entries(self, entries: list[StatsRunEntry]) -> list[StatsRunEntry]:
        filtered = [entry for entry in entries if entry.rewards]
        if self._stats_reward_filter != "all":
            filtered = [entry for entry in filtered if entry.rewards.get(self._stats_reward_filter, 0) > 0]

        if self._stats_sort_by == "highest" and self._stats_reward_filter != "all":
            filtered = sorted(
                filtered,
                key=lambda entry: (
                    -(entry.rewards.get(self._stats_reward_filter, 0)),
                    -(entry.started_at.timestamp() if entry.started_at is not None else entry.saved_log.modified_at),
                ),
            )
        else:
            filtered = sorted(
                filtered,
                key=lambda entry: -(entry.started_at.timestamp() if entry.started_at is not None else entry.saved_log.modified_at),
            )
        return filtered

    def refresh_reward_stats_tab(self) -> None:
        if self._stats_rewards_grid_layout is None or self._stats_logs_list_layout is None:
            return
        entries = self._load_stats_run_entries()
        totals = self._stats_reward_totals(entries)
        self._refresh_stats_filter_options(entries)

        while self._stats_rewards_grid_layout.count():
            item = self._stats_rewards_grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not totals:
            empty = QLabel("No rewards recorded in this timeframe yet.", self._stats_page)
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent; border: none;"
            )
            self._stats_rewards_grid_layout.addWidget(empty, 0, 0, 1, 6)
        else:
            for index, (reward_name, amount) in enumerate(totals):
                reward_item = QWidget(self._stats_page)
                reward_item.setStyleSheet("background: transparent; border: none;")
                item_layout = QVBoxLayout(reward_item)
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(12)
                item_layout.setAlignment(Qt.AlignCenter)

                icon_label = QLabel(reward_item)
                reward_pixmap = _reward_stats_pixmap(reward_name, 24)
                if reward_pixmap is not None:
                    icon_label.setPixmap(reward_pixmap)
                else:
                    icon_name, color = _reward_visual(reward_name)
                    icon_label.setPixmap(_icon(icon_name, color, 24).pixmap(24, 24))
                icon_label.setFixedSize(24, 24)
                icon_label.setStyleSheet("background: transparent; border: none;")
                item_layout.addWidget(icon_label, 0, Qt.AlignHCenter)

                text_block = QWidget(reward_item)
                text_block.setStyleSheet("background: transparent; border: none;")
                text_layout = QVBoxLayout(text_block)
                text_layout.setContentsMargins(0, 0, 0, 0)
                text_layout.setSpacing(0)

                value_label = QLabel(f"{amount:,}", text_block)
                value_label.setAlignment(Qt.AlignCenter)
                value_label.setStyleSheet(
                    f"color: {TEXT_PRIMARY}; font-family: {FONT_STACK}; font-size: 18px; font-weight: 700; background: transparent; border: none;"
                )
                text_layout.addWidget(value_label)

                name_label = QLabel(reward_name, text_block)
                name_label.setAlignment(Qt.AlignCenter)
                name_label.setStyleSheet(
                    f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 10px; font-weight: 500; background: transparent; border: none; margin-top: 4px;"
                )
                text_layout.addWidget(name_label)
                item_layout.addWidget(text_block, 0, Qt.AlignHCenter)

                self._stats_rewards_grid_layout.addWidget(reward_item, index // 6, index % 6)

        while self._stats_logs_list_layout.count():
            item = self._stats_logs_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        filtered_entries = self._filtered_stats_entries(entries)
        if not filtered_entries:
            empty = QFrame(self._stats_page)
            empty.setStyleSheet(
                f"background: rgba(255, 255, 255, 0.02); border: 1px solid {BORDER}; border-radius: 4px;"
            )
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            label = QLabel("No runs match the current stats filters.", empty)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 12px; font-weight: 500; background: transparent;"
            )
            empty_layout.addWidget(label)
            self._stats_logs_list_layout.addWidget(empty)
            return

        for entry in filtered_entries:
            card = StatsRunCard(self._stats_page)
            card.set_entry(entry, self._resolve_log_image_path(entry.saved_log))
            self._stats_logs_list_layout.addWidget(card)
        self._stats_logs_list_layout.addStretch(1)

    def refresh_logs_tab(self) -> None:
        if self._logs_grid is None or self._logs_pager_label is None or self._logs_list_layout is None:
            return
        logs = self.log_service.list_saved_logs()
        page_size = 10
        total = len(logs)
        max_page = max(0, (total - 1) // page_size)
        self._logs_page = max(0, min(self._logs_page, max_page))
        start = self._logs_page * page_size
        page_logs = logs[start : start + page_size]

        self._logs_pager_label.setText("0-0 of 0" if total == 0 else f"{start + 1}-{start + len(page_logs)} of {total}")
        if self._logs_prev_button is not None:
            self._logs_prev_button.setEnabled(self._logs_page > 0)
            self._logs_prev_button.setIcon(
                _icon(
                    "chevron-left",
                    "rgba(255, 255, 255, 0.60)" if self._logs_page > 0 else "rgba(255, 255, 255, 0.20)",
                    16,
                )
            )
        if self._logs_next_button is not None:
            self._logs_next_button.setEnabled(self._logs_page < max_page)
            self._logs_next_button.setIcon(
                _icon(
                    "chevron-right",
                    "rgba(255, 255, 255, 0.60)" if self._logs_page < max_page else "rgba(255, 255, 255, 0.20)",
                    16,
                )
            )

        if self._empty_log_card is not None:
            self._empty_log_card.hide()

        while self._logs_list_layout.count():
            item = self._logs_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not page_logs:
            self._empty_log_card = QFrame(self._logs_grid)
            self._empty_log_card.setStyleSheet(
                f"background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 10px;"
            )
            layout = QVBoxLayout(self._empty_log_card)
            layout.setContentsMargins(24, 24, 24, 24)
            label = QLabel("No completed macro logs yet.", self._empty_log_card)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                f"color: {TEXT_TERTIARY}; font-family: {FONT_STACK}; font-size: 13px; font-weight: 700; background: transparent;"
            )
            layout.addWidget(label)
            self._logs_list_layout.addWidget(self._empty_log_card)
            return

        for log in page_logs:
            card = OverlayLogCard(self._logs_grid)
            card.set_log(log, self._resolve_log_image_path(log))
            card.download_requested.connect(self.download_log_file)
            self._logs_list_layout.addWidget(card)
        self._logs_list_layout.addStretch(1)

    def change_logs_page(self, delta: int) -> None:
        self._logs_page = max(0, self._logs_page + delta)
        self.refresh_logs_tab()

    def _resolve_log_image_path(self, log: SavedRunLog) -> str | None:
        mode_key = self._mode_key_from_log(log.gamemode)
        if mode_key is None:
            return None
        matched = match_map_image(mode_key, log.map_name)
        return os.path.abspath(matched) if matched else None

    @staticmethod
    def _mode_key_from_log(gamemode_label: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9]+", "", gamemode_label.lower())
        mapping = {
            "story": "story",
            "storymode": "story",
            "legend": "legend",
            "legendmode": "legend",
            "raid": "raids",
            "raidmode": "raids",
            "raids": "raids",
            "dungeon": "dungeon",
            "dungeonmode": "dungeon",
            "bossrush": "bossRush",
            "bossrushmode": "bossRush",
            "event": "events",
            "eventmode": "events",
            "events": "events",
        }
        return mapping.get(normalized)

    def _animate_log_card(self, card: QWidget, index: int) -> None:
        del card, index

    def download_log_file(self, path: str) -> None:
        if not os.path.exists(path):
            self.window.statusbar.showMessage("Log file no longer exists.")
            self.refresh_logs_tab()
            return
        suggested = os.path.basename(path)
        target_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save Log",
            os.path.join(os.path.expanduser("~/Downloads"), suggested),
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
        )
        if not target_path:
            return
        try:
            with open(path, "r", encoding="utf-8") as source, open(target_path, "w", encoding="utf-8") as target:
                target.write(source.read())
            self.window.statusbar.showMessage(f"Saved log to {os.path.basename(target_path)}")
        except OSError as exc:
            self.window.statusbar.showMessage(f"Could not save log: {exc}")

    def download_all_logs(self) -> None:
        logs = self.log_service.list_saved_logs()
        if not logs:
            self.window.statusbar.showMessage("No logs available to export.")
            return
        target_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save All Logs",
            os.path.join(os.path.expanduser("~/Downloads"), "all-logs.txt"),
            "Text Files (*.txt);;All Files (*)",
        )
        if not target_path:
            return
        try:
            with open(target_path, "w", encoding="utf-8") as target:
                for log in logs:
                    target.write(f"{log.macro_name} - {log.timestamp}\n")
                    target.write(f"{log.gamemode} | {log.map_name}\n")
                    target.write(f"Status: {log.status} | Duration: {log.duration_label}\n")
                    target.write("=" * 60 + "\n")
                    with open(log.path, "r", encoding="utf-8") as source:
                        target.write(source.read().strip() + "\n\n")
            self.window.statusbar.showMessage(f"Saved combined logs to {os.path.basename(target_path)}")
        except OSError as exc:
            self.window.statusbar.showMessage(f"Could not save logs: {exc}")

    def open_log_in_finder(self, path: str) -> None:
        if not os.path.exists(path):
            self.window.statusbar.showMessage("Log file no longer exists.")
            self.refresh_logs_tab()
            return
        try:
            subprocess.run(["open", "-R", path], check=False)
            self.window.statusbar.showMessage(f"Opened log location: {os.path.basename(path)}")
        except Exception as exc:
            self.window.statusbar.showMessage(f"Could not open log location: {exc}")
