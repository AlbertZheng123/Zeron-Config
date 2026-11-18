"""File-backed cumulative reward totals."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Mapping

from macro_app.constants import DATA_OUTPUT_DIR

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REWARD_STATS_PATH = Path(DATA_OUTPUT_DIR) / "reward_stats.json"

REWARD_TOTALS = OrderedDict(
    [
        ("Gems", 0),
        ("Gold", 0),
        ("Doggy Bones", 0),
        ("Grenade Pins", 0),
        ("Blood Swords", 0),
        ("Green Essence Stones", 0),
        ("Memoria Rerolls", 0),
        ("Rainbow Essence Stones", 0),
        ("Super Stat Chips", 0),
        ("Trait Rerolls", 0),
    ]
)

REWARD_NAME_ALIASES = {
    "gems": "Gems",
    "gem": "Gems",
    "gold": "Gold",
    "doggy bone": "Doggy Bones",
    "doggy bones": "Doggy Bones",
    "bone": "Doggy Bones",
    "grenade": "Grenade Pins",
    "grenade pin": "Grenade Pins",
    "grenade pins": "Grenade Pins",
    "blood sword": "Blood Swords",
    "blood swords": "Blood Swords",
    "green essence": "Green Essence Stones",
    "green essence stone": "Green Essence Stones",
    "green essence stones": "Green Essence Stones",
    "memoria rr": "Memoria Rerolls",
    "memoria reroll": "Memoria Rerolls",
    "memoria rerolls": "Memoria Rerolls",
    "rainbow essence": "Rainbow Essence Stones",
    "rainbow essence stone": "Rainbow Essence Stones",
    "rainbow essence stones": "Rainbow Essence Stones",
    "super stat": "Super Stat Chips",
    "super stat chip": "Super Stat Chips",
    "super stat chips": "Super Stat Chips",
    "trait rr": "Trait Rerolls",
    "trait reroll": "Trait Rerolls",
    "trait rerolls": "Trait Rerolls",
}


def normalize_reward_name(name: str) -> str | None:
    cleaned = name.strip()
    if not cleaned:
        return None
    return REWARD_NAME_ALIASES.get(cleaned.lower(), cleaned)


class RewardStatsStore:
    """Persist cumulative reward totals in a small JSON file."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_REWARD_STATS_PATH
        self._cache: dict[str, int] | None = None

    def load(self) -> dict[str, int]:
        if self._cache is not None:
            return dict(self._cache)

        totals = dict(REWARD_TOTALS)
        if not self.path.exists():
            self._cache = dict(totals)
            return totals

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._cache = dict(totals)
            return totals

        if not isinstance(raw, dict):
            self._cache = dict(totals)
            return totals

        for reward_name in totals:
            try:
                totals[reward_name] = max(0, int(raw.get(reward_name, 0)))
            except (TypeError, ValueError):
                totals[reward_name] = 0
        for reward_name, amount in raw.items():
            if reward_name in totals:
                continue
            try:
                totals[str(reward_name)] = max(0, int(amount))
            except (TypeError, ValueError):
                continue
        self._cache = dict(totals)
        return totals

    def save(self, totals: Mapping[str, int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized = {}
        for reward_name in REWARD_TOTALS:
            try:
                normalized[reward_name] = max(0, int(totals.get(reward_name, 0)))
            except (TypeError, ValueError):
                normalized[reward_name] = 0
        for reward_name, amount in totals.items():
            if reward_name in normalized:
                continue
            try:
                normalized[str(reward_name)] = max(0, int(amount))
            except (TypeError, ValueError):
                continue

        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(normalized, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        os.replace(tmp_path, self.path)
        self._cache = dict(normalized)

    def add_rewards(self, rewards: Mapping[str, int]) -> dict[str, int]:
        totals = self.load()
        for reward_name, amount in rewards.items():
            normalized_name = normalize_reward_name(reward_name)
            if normalized_name is None:
                continue
            try:
                increment = int(amount)
            except (TypeError, ValueError):
                continue
            if increment <= 0:
                continue
            if normalized_name not in totals:
                totals[normalized_name] = 0
            totals[normalized_name] += increment
        self.save(totals)
        return totals

    def reset(self) -> None:
        self.save(REWARD_TOTALS)
