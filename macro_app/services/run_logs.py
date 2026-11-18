"""File-backed macro run logs."""

from __future__ import annotations

import os
import re
import shutil
import threading
import json
from dataclasses import dataclass
from datetime import datetime

from macro_app.constants import LOGS_FOLDER


@dataclass(frozen=True)
class SavedRunLog:
    path: str
    filename: str
    gamemode: str
    map_name: str
    macro_name: str
    timestamp: str
    status: str
    duration_label: str
    size_label: str
    modified_at: float


class MacroRunLogger:
    """Write the active run to current_macro.log, then archive it on completion."""

    def __init__(self, logs_dir: str = LOGS_FOLDER) -> None:
        self.logs_dir = logs_dir
        self.current_path = os.path.join(logs_dir, "current_macro.log")
        self._lock = threading.Lock()
        self._handle = None
        self._active = False
        self._iteration_open = False
        self._gamemode = "Custom"
        self._map_name = "Macro"
        self._macro_name = ""
        self._session_started_at: datetime | None = None
        self._saved_logs_cache: list[SavedRunLog] | None = None
        self._saved_logs_signature: tuple[int, tuple[str, ...]] | None = None

    @property
    def active(self) -> bool:
        return self._active

    def start_session(
        self,
        gamemode: str,
        map_name: str,
        macro_name: str = "",
        *,
        started_at: datetime | None = None,
    ) -> None:
        os.makedirs(self.logs_dir, exist_ok=True)
        self._invalidate_saved_logs_cache()
        self._gamemode = gamemode or "Custom"
        self._map_name = map_name or "Macro"
        self._macro_name = macro_name.strip()
        self._session_started_at = started_at or datetime.now()
        with self._lock:
            self._close_handle_unlocked()
            self._handle = open(self.current_path, "w", encoding="utf-8", buffering=1)
            self._active = True
            self._iteration_open = False

    def start_iteration(self, *, started_at: datetime | None = None) -> None:
        if not self._active:
            return
        started_at = started_at or datetime.now()
        with self._lock:
            self._write_unlocked("----MACRO START-----")
            self._write_unlocked(started_at.strftime("%m/%d %H:%M:%S"))
            if self._macro_name:
                self._write_unlocked(f"Macro: {self._macro_name}")
            self._iteration_open = True

    def log(self, message: str) -> None:
        if not self._active or not self._iteration_open:
            return
        with self._lock:
            self._write_unlocked(message)

    def finish_iteration(self, duration_seconds: float, rewards: dict | None = None) -> None:
        if not self._active:
            return
        with self._lock:
            self._write_summary_unlocked(duration_seconds, rewards)
            self._write_unlocked("")
            self._write_unlocked("")
            self._write_unlocked("")
            self._iteration_open = False

    def interrupt(self, duration_seconds: float, rewards: dict | None = None) -> None:
        if not self._active:
            return
        with self._lock:
            if not self._iteration_open:
                self._write_unlocked("----MACRO START-----")
                self._write_unlocked(datetime.now().strftime("%m/%d %H:%M:%S"))
            self._write_unlocked("----MACRO INTERRUPTED----")
            self._write_summary_unlocked(duration_seconds, rewards)
            self._write_unlocked("----MACRO ENDED-----")
            self._iteration_open = False

    def finalize(self) -> str | None:
        if not self._active:
            return None
        os.makedirs(self.logs_dir, exist_ok=True)
        with self._lock:
            target_path = self._build_final_path()
            self._close_handle_unlocked()
            if os.path.exists(self.current_path):
                shutil.move(self.current_path, target_path)
            else:
                with open(target_path, "w", encoding="utf-8"):
                    pass
            self._active = False
            self._iteration_open = False
            self._invalidate_saved_logs_cache()
        return target_path

    def list_saved_logs(self) -> list[SavedRunLog]:
        if not os.path.isdir(self.logs_dir):
            return []
        signature = self._saved_logs_dir_signature()
        if self._saved_logs_cache is not None and self._saved_logs_signature == signature:
            return list(self._saved_logs_cache)
        logs: list[SavedRunLog] = []
        for filename in signature[1]:
            path = os.path.join(self.logs_dir, filename)
            if not os.path.isfile(path):
                continue
            stat = os.stat(path)
            gamemode, map_name, timestamp = self._parse_filename(filename)
            macro_name, status, duration_label = self._parse_log_metadata(path, fallback_macro_name=map_name)
            logs.append(
                SavedRunLog(
                    path=path,
                    filename=filename,
                    gamemode=gamemode,
                    map_name=map_name,
                    macro_name=macro_name,
                    timestamp=timestamp,
                    status=status,
                    duration_label=duration_label,
                    size_label=self._format_size(stat.st_size),
                    modified_at=stat.st_mtime,
                )
            )
        saved_logs = sorted(logs, key=lambda item: item.modified_at, reverse=True)
        self._saved_logs_cache = saved_logs
        self._saved_logs_signature = signature
        return list(saved_logs)

    def _build_final_path(self) -> str:
        started_at = self._session_started_at or datetime.now()
        timestamp = started_at.strftime("%m_%d_%H_%M")
        base = (
            f"{self._sanitize_filename_part(self._gamemode)}_"
            f"{self._sanitize_filename_part(self._map_name)}_"
            f"{timestamp}"
        )
        path = os.path.join(self.logs_dir, f"{base}.log")
        if not os.path.exists(path):
            return path
        counter = 2
        while True:
            candidate = os.path.join(self.logs_dir, f"{base}_{counter}.log")
            if not os.path.exists(candidate):
                return candidate
            counter += 1

    def _write_summary_unlocked(self, duration_seconds: float, rewards: dict | None) -> None:
        self._write_unlocked("---- MACRO SUMMARY ---")
        if rewards:
            self._write_unlocked("Rewards:")
            for line in json.dumps(rewards, indent=2, sort_keys=True).splitlines():
                self._write_unlocked(line)
        else:
            self._write_unlocked("Rewards: {}")
        self._write_unlocked(f"Total time: {self._format_duration(duration_seconds)}")

    def _write_unlocked(self, line: str) -> None:
        if self._handle is None or self._handle.closed:
            self._handle = open(self.current_path, "a", encoding="utf-8", buffering=1)
        self._handle.write(f"{line}\n")
        self._handle.flush()

    def _close_handle_unlocked(self) -> None:
        if self._handle is not None and not self._handle.closed:
            self._handle.flush()
            self._handle.close()
        self._handle = None

    def _invalidate_saved_logs_cache(self) -> None:
        self._saved_logs_cache = None
        self._saved_logs_signature = None

    def _saved_logs_dir_signature(self) -> tuple[int, tuple[str, ...]]:
        try:
            dir_stat = os.stat(self.logs_dir)
            dir_mtime_ns = getattr(dir_stat, "st_mtime_ns", int(dir_stat.st_mtime * 1_000_000_000))
        except FileNotFoundError:
            return 0, ()

        filenames = tuple(
            sorted(
                filename
                for filename in os.listdir(self.logs_dir)
                if filename.endswith(".log") and filename != "current_macro.log"
            )
        )
        return dir_mtime_ns, filenames

    @staticmethod
    def _sanitize_filename_part(value: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        return sanitized or "Unknown"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {secs}s"
        if minutes:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    @staticmethod
    def _parse_filename(filename: str) -> tuple[str, str, str]:
        stem = filename[:-4] if filename.endswith(".log") else filename
        parts = stem.split("_")
        if len(parts) >= 6:
            timestamp = "_".join(parts[-4:])
            body = parts[:-4]
            gamemode_parts = 1
            known_modes = {"Boss_Rush", "Legend", "Story", "Raids", "Events", "Dungeons", "Custom"}
            for prefix_size in range(min(3, len(body)), 0, -1):
                prefix = "_".join(body[:prefix_size])
                if prefix in known_modes:
                    gamemode_parts = prefix_size
                    break
            gamemode = "_".join(body[:gamemode_parts]) if body else "Unknown"
            map_name = "_".join(body[gamemode_parts:]) if len(body) > gamemode_parts else "Unknown"
            return gamemode.replace("_", " "), map_name.replace("_", " "), timestamp.replace("_", "/")
        return "Unknown", stem.replace("_", " "), "Unknown"

    @staticmethod
    def _parse_log_metadata(path: str, *, fallback_macro_name: str) -> tuple[str, str, str]:
        macro_name = fallback_macro_name or "Macro"
        status = "SUCCESS"
        duration_label = "Unknown"
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.startswith("Macro: "):
                        parsed_name = line.split(":", 1)[1].strip()
                        if parsed_name:
                            macro_name = parsed_name
                    elif line == "----MACRO INTERRUPTED----":
                        status = "INTERRUPTED"
                    elif line.startswith("Total time: "):
                        duration_label = line.split(":", 1)[1].strip() or duration_label
        except OSError:
            pass
        return macro_name, status, duration_label
