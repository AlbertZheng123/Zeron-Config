"""JSON macro file format: create, save, load, display helpers."""

import json
import os


def create_empty_macro():
    """Return a fresh empty macro dict with 6 unit slots."""
    return {
        "units": {
            i: {"name": "", "placements": []}
            for i in range(1, 7)
        },
        "setup_order": [],
        "order": [],
        "settings": {
            "replay": "loop",
            "anti_afk": True,
            "check_placed": False,
            "disable_chat": False,
            "force_restart_wave_enabled": False,
            "force_restart_wave": 0,
            "wait_between_clicks": 0.2,
            "wait_between_key_presses": 0.2,
            "wait_between_steps": 0.0,
            "relative_positioning": False,
            "reposition_camera_on_start": False,
            "card_selection_legend": False,
            "legend_selected_card": "Immunity",
            "card_selection_dungeon": False,
            "dungeon_card_priorities": [],
            "dungeon_max_buff_enabled": False,
            "dungeon_max_buff_percent": 0,
            "dungeon_max_debuff_enabled": False,
            "dungeon_max_debuff_percent": 0,
            "dungeon_starter_card": "Money Surge",
            "odyssey_macro_enabled": False,
            "odyssey_auto_card_selection": True,
            "odyssey_auto_pick_card": True,
            "odyssey_card_priorities": [],
            "odyssey_auto_character_card": False,
            "odyssey_character": "Madara",
            "odyssey_character_card_priorities": [],
            "odyssey_auto_next_room": True,
            "odyssey_room_priorities": ["Normal", "Shop", "Boss"],
            "odyssey_check_treasure_room": False,
            "odyssey_check_unit_reward": False,
            "odyssey_auto_shop_room": False,
            "odyssey_auto_memoria_selection": False,
            "odyssey_memoria_priorities": [],
            "odyssey_only_buy_when_enough": True,
        },
    }


def save_macro(macro, filepath):
    """Save macro dict to a JSON file.

    Converts int unit keys to strings for JSON compatibility.
    """
    serializable = {
        "units": {
            str(k): v for k, v in macro["units"].items()
        },
        "setup_order": macro.get("setup_order", []),
        "order": macro["order"],
        "settings": macro["settings"],
    }
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(serializable, f, indent=2)


def load_macro(filepath):
    """Load macro dict from a JSON file.

    Converts string unit keys back to ints. Compacts any null tombstones
    left by the old deletion system, reindexing order instructions.
    """
    with open(filepath, "r") as f:
        raw = json.load(f)

    units = {}
    for k, v in raw["units"].items():
        units[int(k)] = v

    setup_order = raw.get("setup_order", [])
    order = raw["order"]

    # Compact null tombstones from old format
    for slot, unit in units.items():
        placements = unit.get("placements", [])
        if any(p is None for p in placements):
            index_map = {}
            new_placements = []
            for old_idx, p in enumerate(placements):
                if p is not None:
                    index_map[old_idx] = len(new_placements)
                    new_placements.append(p)
            unit["placements"] = new_placements
            for instruction_list in (setup_order, order):
                for instr in instruction_list:
                    if instr.get("slot") == slot and instr["cmd"] in ("place", "upgrade"):
                        old_pi = instr["placement_index"]
                        if old_pi in index_map:
                            instr["placement_index"] = index_map[old_pi]

    return {
        "units": units,
        "setup_order": setup_order,
        "order": order,
        "settings": {
            **create_empty_macro()["settings"],
            **raw.get("settings", {}),
        },
    }


def format_step_display(instruction, units=None):
    """Format an instruction dict into (type_str, detail_str) for step card display."""
    cmd = instruction["cmd"]

    if cmd == "click":
        return ("CLICK", f"X: {instruction['x']}   Y: {instruction['y']}")

    elif cmd == "place":
        slot = instruction["slot"]
        pi = instruction["placement_index"]
        name = _unit_display_name(units, slot)
        coords = _placement_coords_str(units, slot, pi)
        until = "  \u221e" if instruction.get("until_empty") else ""
        return ("PLACE", f"{name} #{pi}  \u2192 {coords}{until}")

    elif cmd == "upgrade":
        slot = instruction["slot"]
        pi = instruction["placement_index"]
        name = _unit_display_name(units, slot)
        mode = instruction["mode"]
        if mode == "auto":
            detail = f"{name} #{pi}  Auto"
        elif mode == "max":
            detail = f"{name} #{pi}  Max Upgrade"
        else:
            count = instruction.get("count", 1)
            detail = f"{name} #{pi}  {count}x"
        return ("UPGRADE", detail)

    elif cmd == "sell":
        slot = instruction["slot"]
        name = _unit_display_name(units, slot)
        return ("SELL", name)

    elif cmd == "priority":
        slot = instruction["slot"]
        name = _unit_display_name(units, slot)
        priority = instruction.get("priority", "First")
        return ("PRIORITY", f"{name}  {priority}")

    elif cmd == "wait_seconds":
        return ("WAIT", f"{instruction['seconds']} seconds")

    elif cmd == "wait_wave":
        return ("WAIT", f"Round Completed  Wave {instruction['wave']}")

    elif cmd == "wait_start":
        return ("WAIT", "Game Start")

    elif cmd == "wait_yen":
        return ("WAIT", f"Yen \u2265 {instruction['amount']}")

    elif cmd == "key_press":
        times = instruction.get("times", 1)
        if times > 1:
            return ("KEY PRESS", f"{instruction['key']}  \u00d7{times}")
        return ("KEY PRESS", instruction["key"])

    elif cmd == "key_hold":
        return ("KEY HOLD", f"{instruction['key']}  {instruction['seconds']}s")

    elif cmd == "ability_main":
        slot = instruction.get("slot")
        unit_name = _unit_display_name(units, slot) if slot is not None else instruction.get("unit", "Unit")
        if instruction.get("auto"):
            return ("ABILITY", f"{unit_name}  Auto")
        return ("ABILITY", f"{unit_name}  {instruction.get('ability', 'Ability')}")

    elif cmd == "ability_skele_king":
        return ("ABILITY", "Skele: Strings")

    elif cmd == "ability_ainz_arcane":
        sequence = instruction.get("sequence", [])
        if not sequence:
            return ("ABILITY", "Ainz  Arcane")
        detail = " | ".join(f"{row.get('element', '?')} / {row.get('skill', '?')}" for row in sequence)
        return ("ABILITY", f"Ainz  {detail}")

    elif cmd == "ability_ainz_caloric":
        target = instruction.get("target_unit", "").strip() or "(no target)"
        if "target_x" in instruction and "target_y" in instruction:
            return ("ABILITY", f"Ainz  Caloric Stone  {target}  ({instruction['target_x']}, {instruction['target_y']})")
        return ("ABILITY", f"Ainz  Caloric Stone  {target}")

    else:
        return (cmd.upper(), str(instruction))


def _unit_display_name(units, slot):
    """Get display name for a unit slot."""
    if units and slot in units:
        name = units[slot].get("name", "")
        if name:
            return name
    return f"Unit {slot}"


def _placement_coords_str(units, slot, placement_index):
    """Get formatted coordinate string for a placement."""
    if units and slot in units:
        placements = units[slot].get("placements", [])
        if placement_index < len(placements):
            x, y = placements[placement_index]
            return f"({x}, {y})"
    return "(?)"
