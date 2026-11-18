"""Local run-stats cache for recording macro runs and fetching stats."""

from __future__ import annotations

import json
import os

from macro_app.constants import DATA_OUTPUT_DIR

# Local cache file path under runtime output data.
_CACHE_PATH = os.path.join(DATA_OUTPUT_DIR, "run_stats_cache.json")

# In-memory stats keyed by (mode, map_name).
_stats_cache: dict[tuple[str, str], dict[str, float | int]] = {}


def get_supabase_client():
    """Shared import is temporarily disabled for local-only builds."""
    raise RuntimeError("Shared macro import is temporarily disabled in this build.")


def _cache_key(_user_key, game_mode: str, map_name: str) -> tuple[str, str]:
    return (game_mode, map_name)


def _load_cache() -> None:
    """Load stats from local JSON file into memory."""
    global _stats_cache
    try:
        if not os.path.exists(_CACHE_PATH):
            _stats_cache = {}
            return
        with open(_CACHE_PATH, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        _stats_cache = {}
        for key_str, value in raw.items():
            parts = key_str.split("|", 2)
            if len(parts) == 3:
                _, mode, map_name = parts
            elif len(parts) == 2:
                mode, map_name = parts
            else:
                continue
            cache_key = (mode, map_name)
            entry = _stats_cache.setdefault(cache_key, {"total_runs": 0, "total_time": 0.0})
            entry["total_runs"] += int(value.get("total_runs", 0) or 0)
            entry["total_time"] += float(value.get("total_time", 0.0) or 0.0)
        print(f"[stats] Loaded cache: {len(_stats_cache)} entries")
    except Exception as exc:
        print(f"[stats] Error loading cache: {exc}")
        _stats_cache = {}


def _save_cache() -> None:
    """Save in-memory stats to local JSON file."""
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        raw: dict[str, dict[str, float | int]] = {}
        for (mode, map_name), value in _stats_cache.items():
            raw[f"{mode}|{map_name}"] = value
        with open(_CACHE_PATH, "w", encoding="utf-8") as handle:
            json.dump(raw, handle, indent=2)
    except Exception as exc:
        print(f"[stats] Error saving cache: {exc}")


def init_cache() -> None:
    """Initialize the local stats cache on startup."""
    _load_cache()


def update_local_stats(user_key, game_mode: str, map_name: str, duration_seconds: float) -> None:
    """Update local cache after a completed run."""
    key = _cache_key(user_key, game_mode, map_name)
    if key not in _stats_cache:
        _stats_cache[key] = {"total_runs": 0, "total_time": 0.0}
    _stats_cache[key]["total_runs"] += 1
    _stats_cache[key]["total_time"] += round(duration_seconds, 1)
    _save_cache()


def get_total_runs(user_key, game_mode: str, map_name: str) -> int:
    """Return lifetime run count from local cache."""
    entry = _stats_cache.get(_cache_key(user_key, game_mode, map_name))
    return int(entry["total_runs"]) if entry else 0


def get_total_time(user_key, game_mode: str, map_name: str) -> float:
    """Return total runtime from local cache."""
    entry = _stats_cache.get(_cache_key(user_key, game_mode, map_name))
    return float(entry["total_time"]) if entry else 0.0


def record_run(user_key, macro_name: str, game_mode: str, map_name: str, run_number: int, duration_seconds: float) -> None:
    """Record a completed run in the local cache."""
    del macro_name
    del run_number
    update_local_stats(user_key, game_mode, map_name, duration_seconds)


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        minutes = int(seconds // 60)
        remainder = int(seconds % 60)
        return f"{minutes}m {remainder}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"
