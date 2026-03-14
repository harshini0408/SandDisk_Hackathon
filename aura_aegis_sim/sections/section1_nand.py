"""Section 1: NAND Block Map + BBT Engine"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from core.ssd_simulator import RESERVED_BLOCKS, STATE_BAD, STATE_RETIRED, STATE_RESERVED, MAX_PE
from core.bbt_engine import BBTEngine


def render_nand_grid(sim):
    st.markdown("### 🗺️ NAND Block Map")
    cols_per_row = 8
    blocks = sim.blocks

    # Build grid as plotly heatmap with custom colors
    z = []
    text = []
    colors_list = []
    for row in range(8):
        z_row, t_row, c_row = [], [], []
        for col in range(8):
            idx = row * 8 + col
            blk = blocks[idx]
            color = sim.block_color(idx)
            pe_pct = int(blk.pe_count / MAX_PE * 100)
            t_row.append(f"Block {idx}<br>P/E: {blk.pe_count}/{MAX_PE} ({pe_pct}%)<br>State: {blk.state}")
            z_row.append(pe_pct)
            c_row.append(color)
        z.append(z_row)
        text.append(t_row)
        colors_list.append(c_row)

    # Create figure using scatter squares
    fig = go.Figure()
    for row in range(8):
        for col in range(8):
            idx = row * 8 + col
            blk = blocks[idx]
            color = sim.block_color(idx)
            label = str(idx)
            fig.add_trace(go.Scatter(
                x=[col + 0.5], y=[7 - row + 0.5],
                mode='markers+text',
                marker=dict(size=42, color=color, symbol='square',
                            line=dict(color='#1a1a26', width=2)),
                text=[label], textposition='middle center',
                textfont=dict(color='white', size=10, family='monospace'),
                hovertext=[f"Block {idx}<br>P/E: {blk.pe_count}/{MAX_PE}<br>State: {blk.state}"
                           + (f"<br>Reason: {blk.fail_reason}" if blk.fail_reason else "")],
                hoverinfo='text',
                showlegend=False,
                name=f'blk{idx}',
            ))

    fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor='#0a0a0f', paper_bgcolor='#0a0a0f',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 8]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 8]),
    )
    st.plotly_chart(fig, use_container_width=True, key="nand_grid")

    # Legend row
    legend_items = [
        ("#22c55e", "Good <20%"), ("#84cc16", "Good 20-50%"), ("#eab308", "Aging 50-80%"),
        ("#f97316", "Warning >80%"), ("#ef4444", "BAD"), ("#7f1d1d", "Factory Bad"),
        ("#7c3aed", "Retired"), ("#3b82f6", "Active"), ("#6b7280", "Reserved"),
    ]
    cols = st.columns(len(legend_items))
    for c, (color, label) in zip(cols, legend_items):
        c.markdown(f'<span style="background:{color};padding:2px 8px;border-radius:3px;font-size:10px;color:white">{label}</span>', unsafe_allow_html=True)


def render_block_detail(sim, idx: int):
    blk = sim.blocks[idx]
    bbt = sim.bbt
    is_bad, tier = bbt.check_block(idx)
    meta = bbt.get_metadata(idx)
    pe_pct = blk.pe_count / MAX_PE * 100

    st.markdown(f"#### Block {idx} Detail")
    c1, c2, c3 = st.columns(3)
    c1.metric("P/E Count", f"{blk.pe_count} / {MAX_PE}", f"{pe_pct:.1f}%")
    c2.metric("State", blk.state)
    c3.metric("BBT Tier Used", tier)
    if blk.fail_reason:
        st.error(f"Fail Reason: **{blk.fail_reason}**" + (f" @ T={blk.fail_ts:.0f}s" if blk.fail_ts else ""))

    byte_pos = idx >> 3
    bit_pos = idx & 7
    bitmap_byte = format(bbt.bitmap.data[byte_pos], '08b')[::-1]
    h1, h2, h3 = bbt.bloom.set_positions(idx)
    c_h1, c_h2 = bbt.cuckoo.h1_pos(idx), bbt.cuckoo.h2_pos(idx)

    st.markdown(f"""
```
bitmap[{byte_pos}] = {bitmap_byte}  (bit {bit_pos} = {'1 ← BAD' if is_bad else '0 ← GOOD'})
Bloom hash positions: H1={h1}, H2={h2}, H3={h3}
Cuckoo T1[{c_h1}], T2[{c_h2}]
```
""")
    if meta:
        st.json({"block_idx": meta.block_idx, "reason": meta.reason,
                 "pe_count": meta.pe_count, "timestamp": f"T+{meta.timestamp:.0f}s"})


def render_bbt_internals(sim):
    st.markdown("### 🔍 BBT Internals")
    col_bloom, col_bitmap, col_cuckoo = st.columns(3)

    with col_bloom:
        st.markdown("**Tier 1a — Bloom Filter (256-bit)**")
        grid = sim.bbt.bloom.bit_grid()
        arr = np.array(grid)
        fig = go.Figure(go.Heatmap(z=arr, colorscale=[[0,'#1a1a26'],[1,'#f59e0b']],
                                    showscale=False, hoverinfo='skip'))
        fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0),
                          paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
                          xaxis=dict(showticklabels=False, showgrid=False),
                          yaxis=dict(showticklabels=False, showgrid=False))
        st.plotly_chart(fig, use_container_width=True, key="bloom_grid")
        st.caption("Amber = bit set. All 0 → DEFINITELY GOOD (skip bitmap)")

    with col_bitmap:
        st.markdown("**Tier 1b — Bitmap (64-bit)**")
        rows = sim.bbt.bitmap.grid_rows()
        for byte_i, row_str in enumerate(rows):
            colored = ""
            for bit_i, ch in enumerate(row_str):
                block_idx = byte_i * 8 + bit_i
                if ch == '1':
                    colored += f'<span style="color:#ef4444;font-weight:bold">{ch}</span>'
                else:
                    colored += f'<span style="color:#8888a0">{ch}</span>'
            st.markdown(f'<code>byte[{byte_i}]: {colored}</code>', unsafe_allow_html=True)
        st.caption("byte = X>>3, bit = X&7 — one CPU instruction, O(1)")

    with col_cuckoo:
        st.markdown("**Tier 2 — Cuckoo Hash (2×16 slots)**")
        t1, t2 = sim.bbt.cuckoo.table_snapshot()
        t1_col, t2_col = st.columns(2)
        with t1_col:
            st.caption("Table T1")
            for i, entry in enumerate(t1):
                if entry:
                    st.markdown(f'<small style="color:#22c55e">T1[{i}]: B{entry.block_idx}</small>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<small style="color:#4a4a60">T1[{i}]: —</small>', unsafe_allow_html=True)
        with t2_col:
            st.caption("Table T2")
            for i, entry in enumerate(t2):
                if entry:
                    st.markdown(f'<small style="color:#22c55e">T2[{i}]: B{entry.block_idx}</small>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<small style="color:#4a4a60">T2[{i}]: —</small>', unsafe_allow_html=True)


def render_write_burst(sim):
    st.markdown("### ✍️ Write Burst Simulation")
    if st.button("▶ Simulate Write Burst (10 requests)", key="write_burst_btn"):
        traces = sim.simulate_write_burst(10)
        st.session_state['write_traces'] = traces
    if 'write_traces' in st.session_state:
        for trace in st.session_state['write_traces']:
            block_line = trace[0]
            rest = trace[1:]
            is_bad = any("BAD" in l for l in rest)
            color = "#ef4444" if is_bad else "#22c55e"
            st.markdown(f'<div style="background:#1a1a26;border-left:3px solid {color};padding:8px;margin:4px 0;font-family:monospace;font-size:12px">'
                        + f'<b style="color:{color}">{block_line}</b><br>'
                        + '<br>'.join(rest) + '</div>', unsafe_allow_html=True)


def render_wear_retirement(sim):
    st.markdown("### ⚠️ Wear Retirement Demo")
    if st.button("⏩ Fast-Forward Block 7 to Wear Retirement", key="wear_btn"):
        ok = sim.fast_forward_wear(7, 2700)
        if ok:
            lines = sim.wear_retirement_trace(7)
            st.session_state['wear_lines'] = lines
        else:
            st.warning("Block 7 already retired or reserved.")
    if 'wear_lines' in st.session_state:
        for line in st.session_state['wear_lines']:
            indent = line.startswith("  ")
            color = "#14b8a6" if indent else "#f59e0b"
            st.markdown(f'<span style="font-family:monospace;font-size:12px;color:{color}">{line}</span>', unsafe_allow_html=True)
        # CRC panel
        st.markdown(f"""
<div style="background:#1a1a26;border:1px solid #2a2a3a;padding:10px;border-radius:6px;margin-top:8px">
<span style="font-family:monospace;font-size:12px;color:#8888a0">BBT Written to NAND Block 0:</span><br>
<span style="font-family:monospace;font-size:12px;color:#e8e8f0">Raw bytes: {' '.join(f'{b:02X}' for b in sim.bbt.bitmap.data)}</span><br>
<span style="font-family:monospace;font-size:12px;color:#22c55e">CRC-32: 0x{sim.bbt.crc:08X}</span><br>
<span style="font-family:monospace;font-size:12px;color:#8888a0">Redundant copy → Block 1. Power-safe. Recovers on next boot.</span>
</div>
""", unsafe_allow_html=True)


def render_section1(sim):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔷 SECTION 2 — NAND Block Map + Bad Block Engine")

    selected = st.session_state.get('selected_block', None)

    render_nand_grid(sim)

    block_sel = st.number_input("Click block index for detail:", 0, 63,
                                value=selected or 0, key="block_detail_sel")
    if st.button("Inspect Block", key="inspect_btn"):
        st.session_state['selected_block'] = int(block_sel)

    if st.session_state.get('selected_block') is not None:
        render_block_detail(sim, st.session_state['selected_block'])

    st.markdown("---")
    render_bbt_internals(sim)
    st.markdown("---")
    render_write_burst(sim)
    st.markdown("---")
    render_wear_retirement(sim)
    st.markdown('</div>', unsafe_allow_html=True)
