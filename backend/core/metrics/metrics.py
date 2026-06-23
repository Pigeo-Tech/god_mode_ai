"""In-memory metrics registry with Prometheus exposition format.

Phase 2. Implements the IMetrics port. Counters, gauges, and histograms are kept in memory and
rendered for the `/metrics` endpoint. Swap for prometheus_client in production without changing
callers.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any

_DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)


def _key(name: str, labels: dict[str, str]) -> tuple:
    return (name, tuple(sorted(labels.items())))


class _Timer:
    def __init__(self, registry: "MetricsRegistry", name: str, labels: dict[str, str]) -> None:
        self._registry, self._name, self._labels = registry, name, labels
        self._start = 0.0

    def __enter__(self) -> "_Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        self._registry.observe(self._name, time.perf_counter() - self._start, **self._labels)


class MetricsRegistry:
    """Implements the IMetrics port."""

    def __init__(self) -> None:
        self._counters: dict[tuple, float] = defaultdict(float)
        self._gauges: dict[tuple, float] = {}
        self._hist_sum: dict[tuple, float] = defaultdict(float)
        self._hist_count: dict[tuple, int] = defaultdict(int)
        self._hist_buckets: dict[tuple, dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in _DEFAULT_BUCKETS})
        self._lock = Lock()

    def counter(self, name: str, value: float = 1.0, **labels: str) -> None:
        with self._lock:
            self._counters[_key(name, labels)] += value

    def gauge(self, name: str, value: float, **labels: str) -> None:
        with self._lock:
            self._gauges[_key(name, labels)] = value

    def observe(self, name: str, value: float, **labels: str) -> None:
        k = _key(name, labels)
        with self._lock:
            self._hist_sum[k] += value
            self._hist_count[k] += 1
            for b in _DEFAULT_BUCKETS:
                if value <= b:
                    self._hist_buckets[k][b] += 1

    def timer(self, name: str, **labels: str) -> _Timer:
        return _Timer(self, name, labels)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counters": {repr(k): v for k, v in self._counters.items()},
                "gauges": {repr(k): v for k, v in self._gauges.items()},
                "histogram_counts": {repr(k): v for k, v in self._hist_count.items()},
            }

    def render(self) -> str:
        """Render Prometheus text exposition format."""
        lines: list[str] = []

        def fmt_labels(label_tuple: tuple) -> str:
            if not label_tuple:
                return ""
            inner = ",".join(f'{k}="{v}"' for k, v in label_tuple)
            return "{" + inner + "}"

        with self._lock:
            for (name, labels), val in self._counters.items():
                lines.append(f"{name}_total{fmt_labels(labels)} {val}")
            for (name, labels), val in self._gauges.items():
                lines.append(f"{name}{fmt_labels(labels)} {val}")
            for (name, labels), cnt in self._hist_count.items():
                base = fmt_labels(labels)
                lines.append(f"{name}_count{base} {cnt}")
                lines.append(f"{name}_sum{base} {self._hist_sum[(name, labels)]}")
        return "\n".join(lines) + "\n"
