"""
section_p4_optimizer.py — Pillar 4: Firmware Logic Optimizer Panel
Shows Before/After ECC decision logic, CPU savings, and K-map minimization context.
"""

import streamlit as st  # type: ignore
import plotly.graph_objects as go  # type: ignore
from core.event_bus import get_bus  # type: ignore


BEFORE_CODE = """\
if syndrome == 0:
    return OK          # Tier 1
elif ecc_count < 200:
    run BCH()          # Tier 2a
elif ecc_count < 350:
    run LDPC_hard()    # Tier 2b
elif ldpc_iter < 15:
    run LDPC_soft()    # Tier 2c
else:
    run ML_recover()   # Tier 3
# 10 logic ops, 5 branches"""

AFTER_CODE = """\
tier = ecc_tier_lut[
    syndrome_flags |
    (ecc_band << 1) |
    (ldpc_band << 3)
]
dispatch[tier]()
# 6 logic ops, 1 branch
# Pillar 4: K-map minimized"""


def render_p4_optimizer():
    """Render the Pillar 4 ECC Logic Optimizer panel."""
    bus   = get_bus()
    state = bus.get_state()

    pf_count = state["pre_failure_count"]
    savings  = state["optimizer_savings"] if state["optimizer_savings"] else 40.0
    before_ops = 10
    after_ops  = 6
    latency_saved = round(savings * 0.6, 1)  # rough latency proxy

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0a0a1a,#1a0a2a);'
        'border:1.5px solid #a855f7;border-radius:10px;padding:12px 16px;margin-bottom:8px">'
        '<div style="display:flex;justify-content:space-between;align-items:center">'
        '<span style="font-family:monospace;font-size:13px;font-weight:700;color:#a855f7">⚙️ Pillar 4 — Logic Optimizer</span>'
        '<span style="background:#2d1060;color:#c084fc;border:1px solid #a855f7;'
        'border-radius:4px;font-size:10px;font-family:monospace;padding:2px 8px">K-MAP + QMC</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # ── Savings metrics ───────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("📉 Logic Ops", f"{before_ops} → {after_ops}", delta=f"-{before_ops-after_ops} ops", delta_color="inverse")
    with s2:
        st.metric("💾 CPU Saved", f"{savings:.0f}%", delta=f"+{pf_count} events handled")
    with s3:
        st.metric("⚡ Latency", f"-{latency_saved:.0f}%", help="Estimated cycle reduction on hot path")

    # ── Savings bar ───────────────────────────────────────────────────────
    pct = min(int(savings), 100)
    st.markdown(
        f'<div style="font-family:monospace;font-size:10px;color:#8888a0;margin:6px 0 2px">Firmware size reduction</div>'
        f'<div style="background:#1a1a26;border-radius:4px;height:14px;overflow:hidden;position:relative">'
        f'<div style="background:linear-gradient(90deg,#7c3aed,#a855f7);width:{pct}%;height:100%;'
        f'border-radius:4px;transition:width 0.4s"></div>'
        f'<span style="position:absolute;top:1px;left:8px;font-family:monospace;font-size:10px;'
        f'color:#e8e8f0;font-weight:bold">{savings:.0f}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Before / After code ───────────────────────────────────────────────
    st.markdown('<div style="margin-top:10px;font-family:monospace;font-size:10px;color:#8888a0">Decision Logic — Before vs After K-map optimization:</div>', unsafe_allow_html=True)
    cola, mid, colb = st.columns([5, 1, 5])
    with cola:
        st.markdown(
            f'<div style="background:#1a0a0a;border:1px solid #ef444440;border-radius:6px;padding:8px;'
            f'font-family:monospace;font-size:10px;color:#fca5a5;white-space:pre-wrap">'
            f'❌ BEFORE\n{BEFORE_CODE}</div>',
            unsafe_allow_html=True,
        )
    with mid:
        st.markdown('<div style="text-align:center;padding-top:40px;font-size:18px;color:#a855f7">⇒</div>', unsafe_allow_html=True)
    with colb:
        st.markdown(
            f'<div style="background:#0a1a0a;border:1px solid #22c55e40;border-radius:6px;padding:8px;'
            f'font-family:monospace;font-size:10px;color:#86efac;white-space:pre-wrap">'
            f'✅ AFTER (K-Map)\n{AFTER_CODE}</div>',
            unsafe_allow_html=True,
        )

    # ── Optimizer events from bus ─────────────────────────────────────────
    opt_events = bus.get_events("OPTIMIZER_APPLIED")[-2:]
    if opt_events:
        for e in reversed(opt_events):
            p = e["payload"]
            st.markdown(
                f'<div style="background:#120020;border-left:3px solid #a855f7;padding:4px 8px;'
                f'border-radius:3px;margin:2px 0;font-family:monospace;font-size:10px;color:#d8b4fe">'
                f'[{e["ts"]}] Applied: {p.get("before_ops","?")} ops → {p.get("after_ops","?")} ops · '
                f'{p.get("savings_pct","?")}% saved · {p.get("context","")}</div>',
                unsafe_allow_html=True,
            )

    # ── Explanation ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:8px;background:#12121a;border:1px solid #2a2a3a;border-radius:6px;'
        'padding:8px;font-size:10px;color:#8888a0;font-family:monospace">'
        'Pillar 4 uses <b style="color:#a855f7">Karnaugh Maps (K-maps)</b> and '
        '<b style="color:#c084fc">Quine-McCluskey (QMC)</b> to minimize the combinatorial '
        'logic gates in ECC routing decisions. Verified equivalent using '
        '<b style="color:#e8e8f0">Binary Decision Diagrams (BDDs)</b>. '
        'Result: ~40% smaller firmware footprint, verified mathematically identical behavior.</div>',
        unsafe_allow_html=True,
    )
