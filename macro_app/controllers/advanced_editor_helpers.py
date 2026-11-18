"""Pure helpers for advanced-editor macro data transforms."""

from __future__ import annotations

import os

from macro_app.controllers.overlay_helpers import get_macro_folder_for_mode


def get_invalid_upgrade_order_indices(order: list[dict], slot: int, placement_index: int) -> list[int]:
    """Return indices of upgrades pointing at a removed placement."""
    return [
        idx
        for idx, instruction in enumerate(order)
        if instruction.get("cmd") == "upgrade"
        and instruction.get("slot") == slot
        and instruction.get("placement_index") == placement_index
    ]


def move_instruction_to_drop_index(order: list[dict], source_index: int, drop_index: int) -> bool:
    """Move an instruction to a pre-removal drop index.

    ``drop_index`` represents the line before item ``drop_index`` in the current list,
    or ``len(order)`` for the line after the last item. The helper adjusts the target
    after removing the source item so dragging an item past itself is a no-op.
    """
    if source_index < 0 or source_index >= len(order):
        return False

    drop_index = max(0, min(int(drop_index), len(order)))
    target_index = drop_index
    if target_index > source_index:
        target_index -= 1
    if target_index == source_index:
        return False

    instruction = order.pop(source_index)
    order.insert(target_index, instruction)
    return True


def compact_macro_placement(macro: dict, slot: int, removed_index: int) -> None:
    """Remove a placement and decrement higher references in order."""
    placements = macro["units"][slot]["placements"]
    if removed_index < len(placements):
        placements.pop(removed_index)

    for order_key in ("setup_order", "order"):
        for instruction in macro.get(order_key, []):
            if instruction.get("slot") == slot and instruction.get("cmd") in ("place", "upgrade"):
                if instruction["placement_index"] > removed_index:
                    instruction["placement_index"] -= 1


def retarget_place_instruction(
    macro: dict,
    *,
    order_key: str,
    order_index: int,
    new_slot: int,
    new_x: int,
    new_y: int,
    until_empty: bool,
) -> dict:
    """Update a place instruction, optionally moving it to a different unit slot.

    If the slot changes, the placement is moved to the new unit's placement list and any
    upgrade instructions targeting the edited placement follow that placed instance. Higher
    placement references in the old slot are compacted so indices stay contiguous.
    """
    active_order = macro[order_key]
    old_instruction = active_order[order_index]
    old_slot = int(old_instruction["slot"])
    old_index = int(old_instruction["placement_index"])

    new_instruction = {"cmd": "place", "slot": int(new_slot)}
    if until_empty:
        new_instruction["until_empty"] = True

    if old_slot == new_slot:
        macro["units"][old_slot]["placements"][old_index] = [int(new_x), int(new_y)]
        new_instruction["placement_index"] = old_index
        return new_instruction

    old_placements = macro["units"][old_slot]["placements"]
    if old_index >= len(old_placements):
        raise IndexError(f"Placement #{old_index} is missing for unit slot {old_slot}")
    old_placements.pop(old_index)

    new_placements = macro["units"][new_slot]["placements"]
    new_index = len(new_placements)
    new_placements.append([int(new_x), int(new_y)])
    new_instruction["placement_index"] = new_index

    for target_order_key in ("setup_order", "order"):
        order = macro.get(target_order_key, [])
        for idx, instruction in enumerate(order):
            if instruction.get("cmd") not in ("place", "upgrade"):
                continue
            if instruction.get("slot") != old_slot:
                continue

            placement_index = instruction.get("placement_index")
            if placement_index == old_index:
                if target_order_key == order_key and idx == order_index:
                    continue
                instruction["slot"] = int(new_slot)
                instruction["placement_index"] = new_index
            elif placement_index > old_index:
                instruction["placement_index"] = placement_index - 1

    return new_instruction


def parse_advanced_step_data(instruction: dict, current_macro: dict) -> dict:
    """Convert an instruction dict to the form used to refill editor fields."""
    cmd = instruction["cmd"]
    result = {"type": None}
    if cmd == "place":
        result["type"] = "place"
        result["unit_index"] = instruction["slot"]
        result["placement_index"] = instruction["placement_index"]
        placement = current_macro["units"][instruction["slot"]]["placements"][instruction["placement_index"]]
        result["place_x"] = str(placement[0])
        result["place_y"] = str(placement[1])
        result["until_empty"] = instruction.get("until_empty", False)
    elif cmd == "upgrade":
        result["type"] = "upgrade"
        result["unit_index"] = instruction["slot"]
        result["placement_index"] = instruction["placement_index"]
        result["auto_upgrade"] = instruction["mode"] == "auto"
        result["max_upgrade"] = instruction["mode"] == "max"
        if not result["auto_upgrade"] and not result["max_upgrade"]:
            result["count"] = str(instruction.get("count", 1))
    elif cmd == "sell":
        result["type"] = "sell"
        result["unit_index"] = instruction["slot"]
    elif cmd == "priority":
        result["type"] = "priority"
        result["unit_index"] = instruction["slot"]
        result["priority"] = instruction.get("priority", "First")
    elif cmd == "click":
        result["type"] = "click"
        result["x"] = str(instruction["x"])
        result["y"] = str(instruction["y"])
        result["button"] = instruction.get("button", "left")
    elif cmd == "key_press":
        result["type"] = "key"
        result["key_type"] = "press"
        result["key"] = instruction["key"]
        result["times"] = str(instruction.get("times", 1))
    elif cmd == "key_hold":
        result["type"] = "key"
        result["key_type"] = "hold"
        result["key"] = instruction["key"]
        result["duration"] = str(instruction["seconds"])
    elif cmd == "wait_seconds":
        result["type"] = "wait"
        result["wait_type"] = "seconds"
        result["seconds"] = str(instruction["seconds"])
    elif cmd == "wait_wave":
        result["type"] = "wait"
        result["wait_type"] = "round"
        result["wave"] = str(instruction.get("wave", ""))
    elif cmd == "wait_start":
        result["type"] = "wait"
        result["wait_type"] = "game"
    elif cmd == "wait_yen":
        result["type"] = "wait"
        result["wait_type"] = "yen"
        result["yen_amount"] = str(instruction["amount"])
    elif cmd == "ability_main":
        result["type"] = "ability_main"
        result["unit"] = instruction.get("unit", "")
        result["slot"] = instruction.get("slot", 1)
        result["ability"] = instruction.get("ability", "")
        result["ability_file"] = instruction.get("ability_file", "")
        result["auto"] = instruction.get("auto", False)
    elif cmd == "ability_skele_king":
        result["type"] = "ability_skele_king"
    elif cmd == "ability_ainz_arcane":
        result["type"] = "ability_ainz_arcane"
        result["sequence"] = instruction.get("sequence", [])
    elif cmd == "ability_ainz_caloric":
        result["type"] = "ability_ainz_caloric"
        result["target_unit"] = instruction.get("target_unit", "")
        if "target_x" in instruction:
            result["target_x"] = str(instruction.get("target_x", ""))
        if "target_y" in instruction:
            result["target_y"] = str(instruction.get("target_y", ""))
    return result


def build_macro_save_path(name: str, overlay_mode: str | None, overlay_map: str | None) -> str:
    """Return the target save path for a macro name in the current context."""
    if overlay_mode and overlay_map:
        mode_map_folder = get_macro_folder_for_mode(overlay_mode, overlay_map)
        return os.path.join(mode_map_folder, f"{name}.json")
    raise ValueError("Cannot build macro save path without a mode and map.")
