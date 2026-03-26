"""
section_p3_ecc_engine.py — Pillar 3: ECC & Reliability Engine Panel
Renders the AEGIS Tri-Tier ECC Engine status and emits PRE_FAILURE events.
"""

import streamlit as st  # type: ignore
import plotly.graph_objects as go  # type: ignore
from core.event_bus import get_bus  # type: ignore

ECC_TIER1_BYPASS = 0        # syndrome == 0 → instant pass
ECC_TIER2_BCH    = 200      # BCH + soft LDPC range
ECC_TIER2_LDPC   = 350      # hard LDPC range
ECC_TIER3_ML     = 400      # ML soft-decision range
LDPC_SAFE        = 15       # iterations above which Pre-Failure fires
LDPC_MAX         = 20       # max iterations simulated


def _tier(ecc: float) -> tuple:
    """Return (tier_number, tier_name, color)."""
    if ecc <= ECC_TIER1_BYPASS:
        return (1, "Tier 1 — Syndrome Zero Bypass", "#22c55e")
    elif ecc <= ECC_TIER2_BCH:
        return (2, "Tier 2a — BCH Correction", "#f59e0b")
    elif ecc <= ECC_TIER2_LDPC:
        return (2, "Tier 2 — BCH + Hard LDPC", "#f59e0b")
    elif ecc <= ECC_TIER3_ML:
        return (2, "Tier 2 — Hard LDPC (Struggling)", "#f97316")
    else:
        return (3, "Tier 3 — ML Soft-Decision (3.3 KB model)", "#ef4444")


def render_p3_ecc_engine(metrics: dict | None = None, ecc_warn: int = 250, ldpc_thresh: int = LDPC_SAFE):
    """
    Render the Pillar 3 ECC Engine panel.
    metrics: latest SMART dict from SensorMapper (or None for sim-mode).
    """
    bus = get_bus()

    ecc   = 0.0
    ldpc  = 0
    ml_t  = False
    if metrics:
        ecc  = float(metrics.get("ecc_count", 0))
        ldpc = min(LDPC_MAX, int(ecc / 30))
        ml_t = ecc > 380

    tier_num, tier_name, tier_color = _tier(ecc)
    prefail = ldpc > ldpc_thresh or ml_t

    # ── Header ────────────────────────────────────────────────────────────
    # Pre-compute badge HTML — backslashes are illegal inside f-string exprs (Python < 3.12)
    status_badge = (
        '<span style="background:#450000;color:#ef4444;border:1px solid #ef4444;'
        'border-radius:4px;font-size:11px;font-family:monospace;padding:2px 8px">'
        '⚠ PRE-FAILURE</span>'
        if prefail else
        '<span style="background:#052e16;color:#22c55e;border:1px solid #22c55e;'
        'border-radius:4px;font-size:11px;font-family:monospace;padding:2px 8px">'
        '✓ NOMINAL</span>'
    )
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0a0a1a,#1a1228);'
        f'border:1.5px solid {tier_color};border-radius:10px;padding:12px 16px;margin-bottom:8px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<div><span style="font-family:monospace;font-size:13px;font-weight:700;color:{tier_color}">'
        f'🛡️ AEGIS ECC Engine</span>'
        f'<span style="font-family:monospace;font-size:10px;color:#8888a0;margin-left:10px">'
        f'{tier_name}</span></div>'
        f'{status_badge}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── 3 metric cols ─────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🔁 ECC Count", f"{ecc:.0f}", help="Error correction events since monitoring start")
    with c2:
        st.metric("⚙️ LDPC Iterations", f"{ldpc}", delta=f"{'OVER LIMIT' if ldpc > ldpc_thresh else 'SAFE'}",
                  delta_color="inverse" if ldpc > ldpc_thresh else "normal")
    with c3:
        st.metric("🤖 ML Trigger", "🔴 ACTIVE" if ml_t else "⚪ IDLE")

    # ── LDPC iteration gauge ──────────────────────────────────────────────
    bar_col = "#22c55e" if ldpc <= 8 else "#f59e0b" if ldpc <= ldpc_thresh else "#ef4444"
    pct = int(ldpc / LDPC_MAX * 100)
    st.markdown(
        f'<div style="margin:6px 0 2px;font-family:monospace;font-size:10px;color:#8888a0">'
        f'LDPC Iterations ({ldpc}/{LDPC_MAX}) — Tier 2 pipeline</div>'
        f'<div style="background:#1a1a26;border-radius:4px;height:14px;overflow:hidden">'
        f'<div style="background:{bar_col};width:{pct}%;height:100%;border-radius:4px;transition:width 0.3s"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Tri-tier pipeline visual ──────────────────────────────────────────
    _render_tier_pipeline(ecc, ldpc, ml_t, tier_num)

    # ── Last PRE_FAILURE events ───────────────────────────────────────────
    pf_events = bus.get_events("PRE_FAILURE")[-3:]
    if pf_events:
        st.markdown('<div style="margin-top:6px;font-family:monospace;font-size:10px;color:#8888a0">Recent PRE_FAILURE signals:</div>', unsafe_allow_html=True)
        for e in reversed(pf_events):
            p = e["payload"]
            st.markdown(
                f'<div style="background:#200010;border-left:3px solid #ef4444;padding:4px 8px;'
                f'border-radius:3px;margin:2px 0;font-family:monospace;font-size:10px;color:#ffaaaa">'
                f'[{e["ts"]}] Block {p.get("block_id","?")} · ECC={p.get("ecc","?")} · '
                f'LDPC={p.get("ldpc_iterations","?")} · ML={p.get("ml_trigger","?")}</div>',
                unsafe_allow_html=True,
            )


def _render_tier_pipeline(ecc: float, ldpc: int, ml_t: bool, active_tier: int):
    t1_c = "#22c55e" if active_tier >= 1 else "#2a2a3a"
    t2_c = "#f59e0b" if active_tier >= 2 else "#2a2a3a"
    t3_c = "#ef4444" if active_tier >= 3 else "#2a2a3a"

    st.markdown(
        f'<div style="display:flex;gap:4px;margin:8px 0;font-family:monospace;font-size:10px">'
        f'<div style="flex:1;background:#12121a;border:1px solid {t1_c};border-radius:6px;padding:6px;text-align:center">'
        f'<div style="color:{t1_c};font-weight:700">TIER 1</div>'
        f'<div style="color:#8888a0">Syndrome Zero</div>'
        f'<div style="color:{t1_c}">{"✓ PASS" if active_tier == 1 else "→ CONTINUE"}</div>'
        f'</div>'
        f'<div style="display:flex;align-items:center;color:#4a4a60">▶</div>'
        f'<div style="flex:1;background:#12121a;border:1px solid {t2_c};border-radius:6px;padding:6px;text-align:center">'
        f'<div style="color:{t2_c};font-weight:700">TIER 2</div>'
        f'<div style="color:#8888a0">BCH + LDPC</div>'
        f'<div style="color:{t2_c}">{f"{ldpc} iter" if active_tier >= 2 else "IDLE"}</div>'
        f'</div>'
        f'<div style="display:flex;align-items:center;color:#4a4a60">▶</div>'
        f'<div style="flex:1;background:#12121a;border:1px solid {t3_c};border-radius:6px;padding:6px;text-align:center">'
        f'<div style="color:{t3_c};font-weight:700">TIER 3</div>'
        f'<div style="color:#8888a0">ML 3.3KB</div>'
        f'<div style="color:{t3_c}">{"🔴 ACTIVE" if ml_t else "IDLE"}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
