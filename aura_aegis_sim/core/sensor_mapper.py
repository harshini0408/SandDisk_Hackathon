"""
sensor_mapper.py — Raw Sensor → SMART Metrics Converter
Maps ESP32 potentiometer values (0–4095) to SSD SMART telemetry.
"""

import math
import time


class SensorMapper:
    """
    Converts raw ADC potentiometer readings into SSD SMART-like metrics.

    Mapping equations:
        wear        = raw / 4095                       (0.0 – 1.0)
        bad_blocks  = 10 + wear * 100                  (10 – 110)
        ecc_count   = 100 + wear * 500                 (100 – 600)
        temperature = 40 + wear * 10                   (40 – 50 °C)
    """

    ADC_MAX = 4095
    MAX_HISTORY = 200  # rolling window size

    def __init__(self):
        self._history: list[dict] = []

    # ── Core mapping ──────────────────────────────────────────────────────

    def map(self, raw: int) -> dict:
        """
        Convert raw sensor value to SMART metrics dict.
        Returns a snapshot dict with timestamp.
        """
        raw = max(0, min(self.ADC_MAX, int(raw)))
        wear = raw / self.ADC_MAX

        metrics = {
            "timestamp": time.time(),
            "sensor_raw": raw,
            "wear": round(wear, 4),
            "wear_pct": round(wear * 100, 1),
            "bad_blocks": round(10 + wear * 100, 1),
            "ecc_count": round(100 + wear * 500, 0),
            "temperature": round(40 + wear * 10, 1),
        }
        return metrics

    # ── History management ────────────────────────────────────────────────

    def add_sample(self, raw: int) -> dict:
        """Map raw value, append to rolling history, return metrics dict."""
        metrics = self.map(raw)
        self._history.append(metrics)
        # Keep only last MAX_HISTORY samples
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY:]
        return metrics

    def get_history(self) -> list[dict]:
        """Return a copy of the rolling history."""
        return list(self._history)

    def clear_history(self):
        """Reset the rolling buffer."""
        self._history = []

    # ── Convenience series extraction ─────────────────────────────────────

    def series(self, field: str) -> list:
        """Extract a named field across all history entries."""
        return [s[field] for s in self._history if field in s]

    def get_latest(self) -> dict | None:
        """Return the most recent sample, or None."""
        return self._history[-1] if self._history else None
