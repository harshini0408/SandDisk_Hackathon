"""
section_p2_bbt.py — Pillar 2: Bad Block Table Manager Panel
Renders the 8×8 NAND block bitmap, Bloom filter status, FTL relocation log,
and Fast-Reject event log.
"""

import streamlit as st  # type: ignore
from core.event_bus import get_bus, NUM_BLOCKS  # type: ignore


def render_p2_bbt():
    """Render the Pillar 2 BBT Manager panel."""
    bus   = get_bus()
    state = bus.get_state()
    bitmap     = state["bitmap"]
    retire_log = state["retire_log"]
    ftl_log    = state["ftl_log"]
    bloom_set  = state["bloom_set"]

    bad_count  = sum(bitmap)
    good_count = NUM_BLOCKS - bad_count

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0a0a1a,#0d1a14);'
        f'border:1.5px solid #10b981;border-radius:10px;padding:12px 16px;margin-bottom:8px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-family:monospace;font-size:13px;font-weight:700;color:#10b981">🗃️ BBT — Bad Block Table</span>'
        f'<div style="display:flex;gap:10px">'
        f'<span style="background:#052e16;color:#22c55e;border:1px solid #22c55e;border-radius:4px;font-size:10px;font-family:monospace;padding:2px 6px">GOOD: {good_count}</span>'
        f'<span style="background:#200000;color:#ef4444;border:1px solid #ef4444;border-radius:4px;font-size:10px;font-family:monospace;padding:2px 6px">BAD: {bad_count}</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    # ── API badges ────────────────────────────────────────────────────────
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        st.metric("⚡ Fast Reject", f"{state['fast_reject_count']}", help="Blocked read attempts (O(1))")
    with bc2:
        st.metric("🚀 Relocations", f"{state['relocation_count']}", help="FTL data movements")
    with bc3:
        st.metric("🌸 Bloom Filter", f"{len(bloom_set)} blocks", help="Probabilistic has-this-block-been-retired?")

    # ── 8×8 Block Grid ────────────────────────────────────────────────────
    st.markdown('<div style="font-family:monospace;font-size:10px;color:#8888a0;margin:6px 0 2px">NAND Block Map (8×8 = 64 blocks)</div>', unsafe_allow_html=True)
    _render_block_grid(bitmap)

    # ── FTL Relocation table ──────────────────────────────────────────────
    if ftl_log:
        st.markdown('<div style="margin-top:8px;font-family:monospace;font-size:10px;color:#3b82f6">🚀 FTL Relocation Log:</div>', unsafe_allow_html=True)
        for entry in ftl_log[-5:]:
            st.markdown(
                f'<div style="background:#0a0a1e;border-left:3px solid #3b82f6;padding:3px 8px;'
                f'border-radius:3px;margin:1px 0;font-family:monospace;font-size:10px;color:#93c5fd">'
                f'Data moved: {entry}</div>',
                unsafe_allow_html=True,
            )

    # ── Retire log ────────────────────────────────────────────────────────
    if retire_log:
        st.markdown('<div style="margin-top:8px;font-family:monospace;font-size:10px;color:#ef4444">❌ Block Retirement Log:</div>', unsafe_allow_html=True)
        for r in retire_log[-4:]:
            st.markdown(
                f'<div style="background:#1a0000;border-left:3px solid #ef4444;padding:3px 8px;'
                f'border-radius:3px;margin:1px 0;font-family:monospace;font-size:10px;color:#fca5a5">'
                f'[{r["ts"]}] Block {r["block_id"]:02d} → BAD · {r["reason"]}</div>',
                unsafe_allow_html=True,
            )

    # ── Fast reject log ───────────────────────────────────────────────────
    fr_events = bus.get_events("FAST_REJECT")[-3:]
    if fr_events:
        st.markdown('<div style="margin-top:8px;font-family:monospace;font-size:10px;color:#f59e0b">⚡ Fast Reject (O(1)) — ECC pipeline skipped:</div>', unsafe_allow_html=True)
        for e in reversed(fr_events):
            p = e["payload"]
            st.markdown(
                f'<div style="background:#1a1000;border-left:3px solid #f59e0b;padding:3px 8px;'
                f'border-radius:3px;margin:1px 0;font-family:monospace;font-size:10px;color:#fde68a">'
                f'[{e["ts"]}] Block {p.get("block_id","?")} → {p.get("result","REJECTED")} '
                f'· {p.get("latency_us","<1µs")}</div>',
                unsafe_allow_html=True,
            )


def _render_block_grid(bitmap: list):
    """Render an 8×8 grid of NAND blocks, green=good red=bad."""
    cells = []
    for i, bad in enumerate(bitmap):
        if i % 8 == 0 and i > 0:
            cells.append("<br>")
        color   = "#ef4444" if bad else "#22c55e"
        bg      = "#200000" if bad else "#052e16"
        label   = "✗" if bad else "✓"
        tooltip = f"Block {i:02d}: {'BAD' if bad else 'GOOD'}"
        cells.append(
            f'<span title="{tooltip}" style="display:inline-block;width:28px;height:22px;'
            f'background:{bg};border:1px solid {color};border-radius:3px;'
            f'color:{color};font-family:monospace;font-size:9px;text-align:center;'
            f'line-height:22px;margin:1px;cursor:default">{i:02d}</span>'
        )
    st.markdown(
        '<div style="background:#0a0a0f;padding:8px;border-radius:6px;border:1px solid #2a2a3a">'
        + "".join(cells) + "</div>",
        unsafe_allow_html=True,
    )
