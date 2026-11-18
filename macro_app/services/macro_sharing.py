"""Supabase-backed shared macro import helpers."""

from __future__ import annotations

import json
import os
import re

import macro_json

from macro_app.constants import MODE_FOLDERS

SUPPORTED_COMMANDS = {
    "place",
    "upgrade",
    "sell",
    "priority",
    "click",
    "wait_seconds",
    "wait_wave",
    "wait_start",
    "wait_yen",
    "key_press",
    "key_hold",
    "ability_main",
    "ability_skele_king",
    "ability_ainz_arcane",
    "ability_ainz_caloric",
}
LEGEND_CARD_OPTIONS = {"Immunity", "Champion", "Revitalize", "Thrice", "Quake", "Exploding"}
DUNGEON_STARTER_CARD_OPTIONS = {"Money Surge", "Fisticuffs", "Kings Burden", "Limit Break"}


class MacroSharingError(ValueError):
    """Raised when a shared macro cannot be imported."""


class MacroSharingService:
    """Fetch, validate, and materialize shared macros."""

    def __init__(self, client_getter=None) -> None:
        self._client_getter = client_getter

    def _get_client(self):
        if self._client_getter is not None:
            return self._client_getter()
        import supabase_client

        return supabase_client.get_supabase_client()

    @staticmethod
    def normalize_share_code(code: str) -> str:
        return code.strip().upper()

    @staticmethod
    def normalize_map_name(name: str) -> str:
        return " ".join(name.strip().lower().split())

    @staticmethod
    def sanitize_macro_filename(name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "", name).strip().replace(" ", "_")
        cleaned = cleaned.strip("._")
        return cleaned or "imported_macro"

    def fetch_shared_macro(self, share_code: str) -> dict:
        code = self.normalize_share_code(share_code)
        if not code:
            raise MacroSharingError("Share code cannot be empty.")

        try:
            result = self._get_client().table("shared_macros").select("*").eq("share_code", code).limit(1).execute()
        except Exception as exc:
            raise MacroSharingError(f"Error fetching shared macro: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            raise MacroSharingError("No shared macro found for that code.")

        record = dict(rows[0])
        record["share_code"] = code
        return self.validate_shared_macro_record(record)

    def validate_shared_macro_record(self, record: dict) -> dict:
        required_fields = {"share_code", "macro_name", "macro_json", "game_mode", "map_name"}
        missing = sorted(field for field in required_fields if field not in record)
        if missing:
            raise MacroSharingError(f"Shared macro is missing required fields: {', '.join(missing)}")

        mode = record["game_mode"]
        if mode not in MODE_FOLDERS:
            raise MacroSharingError("Imported macro uses an unsupported game mode.")

        macro_name = str(record["macro_name"]).strip()
        if not macro_name:
            raise MacroSharingError("Imported macro is missing a valid name.")

        map_name = str(record["map_name"]).strip()
        if not map_name:
            raise MacroSharingError("Imported macro is missing a valid map name.")

        normalized = dict(record)
        normalized["macro_name"] = macro_name
        normalized["map_name"] = map_name
        normalized["macro_json"] = self.normalize_macro_payload(record["macro_json"])
        return normalized

    def validate_import_target(self, record: dict, expected_mode: str, expected_map: str) -> None:
        actual_mode = record["game_mode"]
        actual_map = record["map_name"]
        if actual_mode != expected_mode or self.normalize_map_name(actual_map) != self.normalize_map_name(expected_map):
            raise MacroSharingError(
                f"This code is for {self._display_mode(actual_mode)} / {actual_map}, "
                f"not {self._display_mode(expected_mode)} / {expected_map}."
            )

    def build_import_macro_path(self, target_folder: str, macro_name: str, share_code: str) -> str:
        os.makedirs(target_folder, exist_ok=True)
        sanitized_name = self.sanitize_macro_filename(macro_name)
        base_path = os.path.join(target_folder, f"{sanitized_name}.json")
        if not os.path.exists(base_path):
            return base_path

        code = self.normalize_share_code(share_code)
        candidate = os.path.join(target_folder, f"{sanitized_name}_{code}.json")
        if not os.path.exists(candidate):
            return candidate

        suffix = 2
        while True:
            candidate = os.path.join(target_folder, f"{sanitized_name}_{code}_{suffix}.json")
            if not os.path.exists(candidate):
                return candidate
            suffix += 1

    def normalize_macro_payload(self, payload) -> dict:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise MacroSharingError("Imported macro JSON is invalid.") from exc

        if not isinstance(payload, dict):
            raise MacroSharingError("Imported macro payload must be a JSON object.")

        units_raw = payload.get("units")
        setup_order_raw = payload.get("setup_order", [])
        order_raw = payload.get("order")
        settings_raw = payload.get("settings")
        if (
            not isinstance(units_raw, dict)
            or not isinstance(setup_order_raw, list)
            or not isinstance(order_raw, list)
            or not isinstance(settings_raw, dict)
        ):
            raise MacroSharingError("Imported macro is invalid or unsupported.")

        macro = macro_json.create_empty_macro()

        for raw_slot, raw_unit in units_raw.items():
            slot = self._coerce_slot(raw_slot)
            if slot is None:
                continue
            if not isinstance(raw_unit, dict):
                raise MacroSharingError(f"Unit slot {slot} is invalid.")
            name = str(raw_unit.get("name", "")).strip()
            placements = raw_unit.get("placements", [])
            if not isinstance(placements, list):
                raise MacroSharingError(f"Placements for unit slot {slot} are invalid.")
            macro["units"][slot]["name"] = name
            macro["units"][slot]["placements"] = [self._normalize_placement(item, slot) for item in placements]

        normalized_setup_order = []
        for instruction in setup_order_raw:
            normalized_setup_order.append(self._normalize_instruction(instruction))
        macro["setup_order"] = normalized_setup_order

        normalized_order = []
        for instruction in order_raw:
            normalized_order.append(self._normalize_instruction(instruction))
        macro["order"] = normalized_order

        replay = settings_raw.get("replay", "loop")
        macro["settings"]["replay"] = replay if replay in {"loop", "stop"} else "loop"
        macro["settings"]["anti_afk"] = bool(settings_raw.get("anti_afk", True))
        macro["settings"]["disable_chat"] = bool(settings_raw.get("disable_chat", False))
        macro["settings"]["force_restart_wave_enabled"] = bool(settings_raw.get("force_restart_wave_enabled", False))
        macro["settings"]["force_restart_wave"] = max(0, int(settings_raw.get("force_restart_wave", 0) or 0))
        macro["settings"]["wait_between_clicks"] = max(0.0, float(settings_raw.get("wait_between_clicks", 0.2) or 0.2))
        macro["settings"]["wait_between_key_presses"] = max(
            0.0,
            float(settings_raw.get("wait_between_key_presses", 0.2) or 0.2),
        )
        macro["settings"]["wait_between_steps"] = max(0.0, float(settings_raw.get("wait_between_steps", 0.0) or 0.0))
        macro["settings"]["relative_positioning"] = bool(settings_raw.get("relative_positioning", False))
        macro["settings"]["reposition_camera_on_start"] = bool(settings_raw.get("reposition_camera_on_start", False))
        macro["settings"]["card_selection_legend"] = bool(settings_raw.get("card_selection_legend", False))
        legend_selected_card = str(settings_raw.get("legend_selected_card", "Immunity")).strip()
        macro["settings"]["legend_selected_card"] = (
            legend_selected_card if legend_selected_card in LEGEND_CARD_OPTIONS else "Immunity"
        )
        macro["settings"]["card_selection_dungeon"] = bool(settings_raw.get("card_selection_dungeon", False))
        priorities = settings_raw.get("dungeon_card_priorities", [])
        macro["settings"]["dungeon_card_priorities"] = priorities if isinstance(priorities, list) else []
        macro["settings"]["dungeon_max_buff_enabled"] = bool(settings_raw.get("dungeon_max_buff_enabled", False))
        macro["settings"]["dungeon_max_buff_percent"] = int(settings_raw.get("dungeon_max_buff_percent", 0) or 0)
        macro["settings"]["dungeon_max_debuff_enabled"] = bool(settings_raw.get("dungeon_max_debuff_enabled", False))
        macro["settings"]["dungeon_max_debuff_percent"] = int(settings_raw.get("dungeon_max_debuff_percent", 0) or 0)
        dungeon_starter_card = str(settings_raw.get("dungeon_starter_card", "Money Surge")).strip()
        macro["settings"]["dungeon_starter_card"] = (
            dungeon_starter_card if dungeon_starter_card in DUNGEON_STARTER_CARD_OPTIONS else "Money Surge"
        )

        self._compact_null_placements(macro)
        self._validate_placement_references(macro)
        return macro

    @staticmethod
    def _display_mode(mode: str) -> str:
        display = {
            "story": "Story",
            "raids": "Raids",
            "legend": "Legend",
            "bossRush": "Boss Rush",
            "events": "Events",
            "dungeon": "Dungeon",
        }
        return display.get(mode, mode)

    @staticmethod
    def _coerce_slot(raw_slot) -> int | None:
        try:
            slot = int(raw_slot)
        except (TypeError, ValueError):
            return None
        return slot if 1 <= slot <= 6 else None

    @staticmethod
    def _normalize_placement(item, slot: int):
        if item is None:
            return None
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise MacroSharingError(f"Placement for unit slot {slot} is invalid.")
        try:
            return [int(item[0]), int(item[1])]
        except (TypeError, ValueError) as exc:
            raise MacroSharingError(f"Placement for unit slot {slot} is invalid.") from exc

    def _normalize_instruction(self, instruction: dict) -> dict:
        if not isinstance(instruction, dict):
            raise MacroSharingError("Imported macro has an invalid step entry.")

        cmd = instruction.get("cmd")
        if cmd not in SUPPORTED_COMMANDS:
            raise MacroSharingError(f"Imported macro uses unsupported command: {cmd}")

        if cmd == "click":
            button = str(instruction.get("button", "left")).strip().lower()
            if button not in {"left", "right"}:
                button = "left"
            return {
                "cmd": "click",
                "x": int(instruction["x"]),
                "y": int(instruction["y"]),
                "button": button,
            }
        if cmd == "wait_seconds":
            return {"cmd": "wait_seconds", "seconds": float(instruction["seconds"])}
        if cmd == "wait_wave":
            return {"cmd": "wait_wave", "wave": int(instruction["wave"])}
        if cmd == "wait_start":
            return {"cmd": "wait_start"}
        if cmd == "wait_yen":
            return {"cmd": "wait_yen", "amount": int(instruction["amount"])}
        if cmd == "key_press":
            key = str(instruction["key"]).strip()
            if not key:
                raise MacroSharingError("Imported macro contains an empty key press step.")
            return {"cmd": "key_press", "key": key, "times": int(instruction.get("times", 1))}
        if cmd == "key_hold":
            key = str(instruction["key"]).strip()
            if not key:
                raise MacroSharingError("Imported macro contains an empty key hold step.")
            return {"cmd": "key_hold", "key": key, "seconds": float(instruction["seconds"])}
        if cmd == "sell":
            slot = self._coerce_slot(instruction.get("slot"))
            if slot is None:
                raise MacroSharingError("Imported macro references an invalid unit slot.")
            return {"cmd": "sell", "slot": slot}
        if cmd == "priority":
            slot = self._coerce_slot(instruction.get("slot"))
            if slot is None:
                raise MacroSharingError("Imported macro references an invalid unit slot.")
            priority = str(instruction.get("priority", "First")).strip() or "First"
            return {"cmd": "priority", "slot": slot, "priority": priority}
        if cmd == "ability_main":
            slot = self._coerce_slot(instruction.get("slot"))
            if slot is None:
                raise MacroSharingError("Imported macro references an invalid unit slot.")
            normalized = {
                "cmd": "ability_main",
                "slot": slot,
                "unit": str(instruction.get("unit", "")).strip(),
            }
            if instruction.get("auto"):
                normalized["auto"] = True
                return normalized

            ability = str(instruction.get("ability", "")).strip()
            ability_file = str(instruction.get("ability_file", "")).strip()
            if not ability or not ability_file:
                raise MacroSharingError("Imported macro contains an invalid main ability step.")
            normalized["ability"] = ability
            normalized["ability_file"] = ability_file
            return normalized
        if cmd == "ability_skele_king":
            return {"cmd": "ability_skele_king"}
        if cmd == "ability_ainz_arcane":
            sequence = instruction.get("sequence", [])
            if not isinstance(sequence, list):
                raise MacroSharingError("Imported macro contains an invalid Ainz Arcane sequence.")
            normalized_sequence = []
            for row in sequence:
                if not isinstance(row, dict):
                    raise MacroSharingError("Imported macro contains an invalid Ainz Arcane step.")
                element = str(row.get("element", "")).strip()
                skill = str(row.get("skill", "")).strip()
                if not element or not skill:
                    raise MacroSharingError("Imported macro contains an incomplete Ainz Arcane step.")
                normalized_sequence.append({"element": element, "skill": skill})
            return {"cmd": "ability_ainz_arcane", "sequence": normalized_sequence}
        if cmd == "ability_ainz_caloric":
            target_unit = str(instruction.get("target_unit", "")).strip()
            if not target_unit:
                raise MacroSharingError("Imported macro contains an invalid Ainz Caloric step.")
            normalized = {"cmd": "ability_ainz_caloric", "target_unit": target_unit}
            if "target_x" in instruction:
                normalized["target_x"] = int(instruction["target_x"])
            if "target_y" in instruction:
                normalized["target_y"] = int(instruction["target_y"])
            if ("target_x" in normalized) != ("target_y" in normalized):
                raise MacroSharingError("Imported macro contains an incomplete Ainz Caloric target.")
            return normalized

        slot = self._coerce_slot(instruction.get("slot"))
        if slot is None:
            raise MacroSharingError("Imported macro references an invalid unit slot.")
        placement_index = int(instruction["placement_index"])

        if cmd == "place":
            normalized = {"cmd": "place", "slot": slot, "placement_index": placement_index}
            if instruction.get("until_empty"):
                normalized["until_empty"] = True
            return normalized

        mode = instruction.get("mode", "manual")
        if mode not in {"auto", "manual", "max"}:
            raise MacroSharingError("Imported macro contains an invalid upgrade mode.")
        normalized = {"cmd": "upgrade", "slot": slot, "placement_index": placement_index, "mode": mode}
        if mode == "manual":
            normalized["count"] = int(instruction.get("count", 1))
        return normalized

    @staticmethod
    def _compact_null_placements(macro: dict) -> None:
        instruction_lists = [macro.get("setup_order", []), macro.get("order", [])]
        for slot, unit in macro["units"].items():
            placements = unit.get("placements", [])
            if not any(item is None for item in placements):
                continue
            index_map = {}
            compacted = []
            for old_index, placement in enumerate(placements):
                if placement is not None:
                    index_map[old_index] = len(compacted)
                    compacted.append(placement)
            unit["placements"] = compacted
            for instructions in instruction_lists:
                for instruction in instructions:
                    if instruction.get("slot") == slot and instruction.get("cmd") in {"place", "upgrade"}:
                        old_index = instruction["placement_index"]
                        if old_index in index_map:
                            instruction["placement_index"] = index_map[old_index]

    @staticmethod
    def _validate_placement_references(macro: dict) -> None:
        for instructions in (macro.get("setup_order", []), macro.get("order", [])):
            for instruction in instructions:
                if instruction.get("cmd") not in {"place", "upgrade"}:
                    continue
                slot = instruction["slot"]
                placement_index = instruction["placement_index"]
                placements = macro["units"][slot]["placements"]
                if placement_index < 0 or placement_index >= len(placements):
                    raise MacroSharingError(
                        f"Imported macro references missing placement #{placement_index} for unit slot {slot}."
                    )
