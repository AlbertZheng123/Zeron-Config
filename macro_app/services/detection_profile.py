"""Lightweight runtime profiling for macro detection calls."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter


@dataclass
class DetectionTimingStat:
    """Aggregate timing data for one detection category."""

    calls: int = 0
    total_seconds: float = 0.0
    max_seconds: float = 0.0


class DetectionProfiler:
    """Collect per-category timing totals for one macro iteration."""

    def __init__(self) -> None:
        self._stats: dict[str, DetectionTimingStat] = {}

    def record(self, name: str, elapsed_seconds: float) -> None:
        stat = self._stats.setdefault(name, DetectionTimingStat())
        stat.calls += 1
        stat.total_seconds += max(0.0, float(elapsed_seconds))
        stat.max_seconds = max(stat.max_seconds, elapsed_seconds)

    @contextmanager
    def track(self, name: str):
        started_at = perf_counter()
        try:
            yield
        finally:
            self.record(name, perf_counter() - started_at)

    def has_data(self) -> bool:
        return bool(self._stats)

    def summary_lines(self) -> list[str]:
        if not self._stats:
            return ["Detection timing summary: no detections recorded during steps."]

        total_calls = sum(stat.calls for stat in self._stats.values())
        total_seconds = sum(stat.total_seconds for stat in self._stats.values())
        lines = [
            "Detection timing summary:",
            f"  Total: {total_seconds:.3f}s across {total_calls} detection calls",
        ]
        sorted_stats = sorted(
            self._stats.items(),
            key=lambda item: item[1].total_seconds,
            reverse=True,
        )
        for name, stat in sorted_stats:
            avg_ms = (stat.total_seconds / stat.calls) * 1000.0 if stat.calls else 0.0
            max_ms = stat.max_seconds * 1000.0
            lines.append(
                f"  - {name}: total={stat.total_seconds:.3f}s calls={stat.calls} "
                f"avg={avg_ms:.1f}ms max={max_ms:.1f}ms"
            )
        return lines
