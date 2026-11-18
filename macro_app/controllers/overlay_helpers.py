"""Pure helpers for overlay map and file routing."""

from __future__ import annotations

import os

from macro_app.constants import MAP_IMAGE_REGISTRY, MODE_FOLDERS, MODE_IMAGE_FOLDERS


def _display_name_from_keyword(keyword: str) -> str:
    return " ".join(part.capitalize() for part in keyword.strip().split())


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _existing_mode_folders(mode: str) -> list[str]:
    folder = MODE_FOLDERS.get(mode)
    if not folder or not os.path.exists(folder):
        return []
    return sorted(
        item
        for item in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, item)) and not item.startswith(".")
    )


def _resolve_existing_folder_name(mode: str, map_name: str, keywords: list[str] | None = None) -> str | None:
    normalized_map = _normalize_name(map_name)
    for folder_name in _existing_mode_folders(mode):
        normalized_folder = _normalize_name(folder_name)
        if normalized_folder == normalized_map:
            return folder_name
    if keywords:
        normalized_keywords = [_normalize_name(keyword) for keyword in keywords if keyword.strip()]
        for folder_name in _existing_mode_folders(mode):
            normalized_folder = _normalize_name(folder_name)
            if any(keyword and keyword in normalized_folder for keyword in normalized_keywords):
                return folder_name
            if any(keyword and normalized_folder in keyword for keyword in normalized_keywords):
                return folder_name
    return None


def built_in_maps_for_mode(mode: str) -> list[str]:
    """Return the built-in map names for a mode from the image registry."""
    registry = MAP_IMAGE_REGISTRY.get(mode, {})
    maps: list[str] = []
    seen: set[str] = set()
    for keywords in registry.values():
        if not keywords:
            continue
        display_name = _resolve_existing_folder_name(mode, keywords[0], keywords) or _display_name_from_keyword(keywords[0])
        normalized = display_name.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        maps.append(display_name)
    return maps


def get_maps_for_mode(mode: str):
    """Get map names for a mode, independent of whether macros exist yet."""
    folder = MODE_FOLDERS.get(mode)
    maps = built_in_maps_for_mode(mode)
    seen = {entry.lower() for entry in maps}
    if not folder:
        return maps
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        return maps
    for item in sorted(os.listdir(folder)):
        item_path = os.path.join(folder, item)
        if os.path.isdir(item_path) and not item.startswith(".") and item.lower() not in seen:
            maps.append(item)
            seen.add(item.lower())
    return maps


def get_macro_folder_for_mode(mode: str, map_name: str):
    """Get the save folder path for a given mode and map."""
    folder = MODE_FOLDERS.get(mode)
    if folder:
        registry = MAP_IMAGE_REGISTRY.get(mode, {})
        matched_keywords: list[str] | None = None
        normalized_map = _normalize_name(map_name)
        for keywords in registry.values():
            if any(_normalize_name(keyword) in normalized_map or normalized_map in _normalize_name(keyword) for keyword in keywords):
                matched_keywords = list(keywords)
                break
        resolved_name = _resolve_existing_folder_name(mode, map_name, matched_keywords) or map_name
        return os.path.join(folder, resolved_name)
    return os.path.join(mode, map_name)


def match_map_image(mode: str, selected_map: str):
    """Return the image path for a selected map or None."""
    selected_map = selected_map.lower()
    registry = MAP_IMAGE_REGISTRY.get(mode, {})
    for filename, keywords in registry.items():
        if any(keyword in selected_map for keyword in keywords):
            folder = MODE_IMAGE_FOLDERS.get(mode, "")
            matched = os.path.join(folder, f"{filename}.png")
            if os.path.exists(matched):
                return matched
    return None
