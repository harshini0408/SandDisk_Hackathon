"""
hw_predictor.py — Hardware-Driven AI Health Predictor
Rule-based predictor (LSTM-proxy) that analyzes real-time SMART metrics
from the rolling sensor window to output health status and RUL.
"""

from __future__ import annotations
import math


# ── Threshold constants ───────────────────────────────────────────────────────
ECC_WARN     = 250    # ECC count above which status = WARNING
ECC_CRIT     = 400    # ECC count above which status = CRITICAL
BB_CRIT      = 80     # Bad block count above which status = CRITICAL
TEMP_WARN    = 47     # Temperature above which heat warning fires (°C)
WEAR_WARN    = 0.60   # Wear fraction above which warning fires
WEAR_CRIT    = 0.85   # Wear fraction above which critical fires


def predict(history: list[dict], ecc_thresh_warn: int = ECC_WARN,
            ecc_thresh_crit: int = ECC_CRIT,
            bb_thresh_crit: int = BB_CRIT) -> dict:
    """
    Analyze the rolling window of SMART samples and return prediction.

    Parameters
    ----------
    history : list of dicts from SensorMapper.get_history()
    ecc_thresh_warn / ecc_thresh_crit / bb_thresh_crit :
        Optional override thresholds (driven by sidebar sliders).

    Returns
    -------
    dict with keys:
        status      : "HEALTHY" | "WARNING" | "CRITICAL"
        rul         : "Normal" | "45 days" | "21 days"
        color       : hex color string
        icon        : emoji
        description : human-readable reason
        failure_prob: 0.0–1.0
        trend       : "stable" | "rising" | "falling"
        heat_alert  : bool
    """
    if not history:
        return _healthy_result()

    latest = history[-1]
    ecc     = latest.get("ecc_count", 0)
    bb      = latest.get("bad_blocks", 0)
    wear    = latest.get("wear", 0.0)
    temp    = latest.get("temperature", 40)

    # ── Trend analysis over last 20 samples ──────────────────────────────
    window = history[-20:]
    trend = _compute_trend([s.get("ecc_count", 0) for s in window])

    # ── Failure probability (0–1), heuristic ────────────────────────────
    # Normalize each signal to [0,1] and blend
    ecc_norm  = min(ecc / 600.0, 1.0)
    bb_norm   = min(bb / 110.0, 1.0)
    wear_norm = min(wear, 1.0)
    temp_norm = max(0.0, (temp - 40) / 10.0)

    # Weighted blend — ECC is primary driver for NAND health
    fp = min(0.4 * ecc_norm + 0.3 * bb_norm + 0.2 * wear_norm + 0.1 * temp_norm, 1.0)

    # Trend boosts failure prob slightly
    if trend == "rising":
        fp = min(fp * 1.15, 1.0)

    # ── Classification ───────────────────────────────────────────────────
    heat_alert = temp >= TEMP_WARN

    if ecc >= ecc_thresh_crit or bb >= bb_thresh_crit or wear >= WEAR_CRIT:
        status = "CRITICAL"
        rul    = "21 days"
        color  = "#ef4444"
        icon   = "🔴"
        desc   = _critical_desc(ecc, bb, wear, ecc_thresh_crit, bb_thresh_crit)

    elif ecc >= ecc_thresh_warn or wear >= WEAR_WARN or heat_alert:
        status = "WARNING"
        rul    = "45 days"
        color  = "#f59e0b"
        icon   = "🟡"
        desc   = _warning_desc(ecc, wear, temp, heat_alert, ecc_thresh_warn)

    else:
        status = "HEALTHY"
        rul    = "Normal"
        color  = "#22c55e"
        icon   = "🟢"
        desc   = (f"All metrics nominal. "
                  f"ECC={ecc:.0f}, Bad Blocks={bb:.0f}, "
                  f"Wear={wear*100:.1f}%, Temp={temp:.1f}°C")

    return {
        "status":       status,
        "rul":          rul,
        "color":        color,
        "icon":         icon,
        "description":  desc,
        "failure_prob": round(fp, 3),
        "trend":        trend,
        "heat_alert":   heat_alert,
        "ecc":          ecc,
        "bad_blocks":   bb,
        "wear_pct":     wear * 100,
        "temperature":  temp,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _healthy_result() -> dict:
    return {
        "status": "HEALTHY", "rul": "Normal", "color": "#22c55e",
        "icon": "🟢", "description": "No data yet — awaiting sensor input.",
        "failure_prob": 0.0, "trend": "stable", "heat_alert": False,
        "ecc": 0, "bad_blocks": 0, "wear_pct": 0.0, "temperature": 40.0,
    }


def _compute_trend(values: list) -> str:
    if len(values) < 4:
        return "stable"
    mid = len(values) // 2
    first_half  = sum(values[:mid]) / mid
    second_half = sum(values[mid:]) / max(len(values) - mid, 1)
    delta = second_half - first_half
    if delta > first_half * 0.05:
        return "rising"
    elif delta < -first_half * 0.05:
        return "falling"
    return "stable"


def _critical_desc(ecc, bb, wear, ecc_crit, bb_crit) -> str:
    reasons = []
    if ecc >= ecc_crit:
        reasons.append(f"ECC={ecc:.0f} ≥ {ecc_crit}")
    if bb >= bb_crit:
        reasons.append(f"Bad Blocks={bb:.0f} ≥ {bb_crit}")
    if wear >= WEAR_CRIT:
        reasons.append(f"Wear={wear*100:.1f}% ≥ {WEAR_CRIT*100:.0f}%")
    return "⚠️ CRITICAL: " + "; ".join(reasons) + ". Immediate action required."


def _warning_desc(ecc, wear, temp, heat_alert, ecc_warn) -> str:
    reasons = []
    if ecc >= ecc_warn:
        reasons.append(f"ECC={ecc:.0f} ≥ {ecc_warn}")
    if wear >= WEAR_WARN:
        reasons.append(f"Wear={wear*100:.1f}% ≥ {WEAR_WARN*100:.0f}%")
    if heat_alert:
        reasons.append(f"Temp={temp:.1f}°C ≥ {TEMP_WARN}°C")
    return "⚠️ WARNING: " + "; ".join(reasons) + ". Monitor closely."
