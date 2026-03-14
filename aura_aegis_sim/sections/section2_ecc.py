"""Section 2: ECC / LDPC Correction Engine"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from core.ldpc_engine import (
    H_MATRIX, N_BITS, N_CHECKS,
    generate_valid_codeword, inject_errors,
    hard_ldpc_decode, tier1_check, pipeline_read,
    compute_syndrome,
)


def render_pipeline_diagram(last_result: dict):
    tiers = ['Syndrome\nCheck', 'BCH\nAttempt', 'Hard LDPC\n8–20 iter', 'Soft LDPC\n+ML Voltage', 'UECC\nUnrecoverable']
    colors = ['#8888a0'] * 5
    tier_map = {1: 0, '2a-BCH': 1, '2b-LDPC': 2, 3: 3, 'UECC': 4}
    active = tier_map.get(last_result.get('tier', 1), 0)
    colors[active] = '#22c55e' if last_result.get('success') else '#ef4444'

    fig = go.Figure()
    for i, (label, color) in enumerate(zip(tiers, colors)):
        fig.add_trace(go.Scatter(
            x=[i], y=[0], mode='markers+text',
            marker=dict(size=60, color=color, symbol='square',
                        line=dict(color='#2a2a3a', width=2)),
            text=[label], textposition='bottom center',
            textfont=dict(color='#e8e8f0', size=10, family='monospace'),
            showlegend=False,
        ))
        if i < len(tiers) - 1:
            fig.add_annotation(x=i + 0.5, y=0, text='→', showarrow=False,
                               font=dict(size=20, color='#8888a0'))

    fig.update_layout(
        height=130, margin=dict(l=10, r=10, t=30, b=50),
        paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 4.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 0.5]),
        title=dict(text="AEGIS ECC Pipeline", font=dict(color='#e8e8f0', size=13), x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True, key="pipeline_diag")


def render_syndrome_demo():
    st.markdown("#### 🧪 Live Syndrome Demonstration")
    n_errors = st.slider("Inject errors into codeword:", 0, 4, 0, key="syndrome_errs")

    if 'valid_cw' not in st.session_state:
        st.session_state['valid_cw'] = generate_valid_codeword()
    cw = st.session_state['valid_cw']

    if n_errors > 0:
        received, err_pos = inject_errors(cw, n_errors, seed=42)
    else:
        received, err_pos = cw.copy(), []

    syndrome = compute_syndrome(received)
    is_clean = syndrome.sum() == 0

    col_h, col_recv = st.columns(2)
    with col_h:
        st.caption("Parity Check Matrix H (6×16)")
        fig = go.Figure(go.Heatmap(
            z=H_MATRIX.tolist(),
            colorscale=[[0, '#1a1a26'], [1, '#14b8a6']],
            showscale=False, hoverinfo='skip',
        ))
        fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0),
                          paper_bgcolor='#0a0a0f',
                          xaxis=dict(showticklabels=False, showgrid=False),
                          yaxis=dict(showticklabels=False, showgrid=False))
        st.plotly_chart(fig, use_container_width=True, key="h_matrix")

    with col_recv:
        st.caption(f"Received codeword (errors at: {err_pos or 'none'})")
        bits_str = ''.join(str(b) for b in received)
        colored = ""
        for i, b in enumerate(received):
            color = "#ef4444" if i in err_pos else "#22c55e"
            colored += f'<span style="color:{color}">{b}</span>'
        st.markdown(f'<code style="font-size:14px">[{colored}]</code>', unsafe_allow_html=True)

        s_str = ''.join(str(b) for b in syndrome)
        s_color = "#22c55e" if is_clean else "#ef4444"
        st.markdown(f'<b style="color:{s_color}">Syndrome s = [{s_str}] → {"ZERO ✓ No errors" if is_clean else "NON-ZERO ✗ Errors detected"}</b>', unsafe_allow_html=True)


def render_ldpc_trace(sim):
    st.markdown("#### ⚙️ LDPC Bit-Flip Trace")
    col1, col2 = st.columns(2)
    with col1:
        pe_count = st.slider("Block P/E count:", 0, 3000, 1000, 100, key="ldpc_pe")
    with col2:
        degraded = st.checkbox("Degraded mode (P/E > 2500)", key="ldpc_degraded")

    if degraded:
        pe_count = 2700

    if 'ldpc_cw' not in st.session_state or st.button("Generate new codeword", key="new_cw_btn"):
        st.session_state['ldpc_cw'] = generate_valid_codeword()

    cw = st.session_state['ldpc_cw']
    n_err = 3 if not degraded else 5
    received, err_pos = inject_errors(cw, n_err, seed=7)

    wear_pct = pe_count / 3000.0
    ldpc_cap = int(8 + 12 * wear_pct)
    word, success, log = hard_ldpc_decode(received, max_iter=ldpc_cap)

    st.markdown(f'<span style="color:#8888a0">LDPC cap for P/E={pe_count}: **{ldpc_cap}** iterations | Result: <b style="color:{"#22c55e" if success else "#ef4444"}">{"SUCCESS" if success else "FAIL"}</b></span>', unsafe_allow_html=True)

    iter_sel = st.slider("View iteration:", 1, max(len(log), 1), min(len(log), 1), key="ldpc_iter_sel")
    if log:
        entry = log[min(iter_sel - 1, len(log) - 1)]
        fc = entry['failed_checks']
        flipped = entry['flipped']
        threshold = 2

        bar_colors = ['#ef4444' if i in flipped else '#14b8a6' for i in range(N_BITS)]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(range(N_BITS)), y=fc, marker_color=bar_colors,
                             name='Failed checks/bit'))
        fig.add_hline(y=threshold, line_dash='dash', line_color='#f59e0b',
                     annotation_text=f'Threshold={threshold}', annotation_font_color='#f59e0b')
        fig.update_layout(
            height=200, margin=dict(l=10,r=10,t=10,b=30),
            paper_bgcolor='#0a0a0f', plot_bgcolor='#12121a',
            xaxis=dict(title='Bit position', color='#8888a0', showgrid=False),
            yaxis=dict(title='Failed checks', color='#8888a0', showgrid=True, gridcolor='#2a2a3a'),
            font=dict(color='#e8e8f0'),
        )
        st.plotly_chart(fig, use_container_width=True, key="ldpc_bar")
        st.caption(f"Iter {iter_sel}: flipped={flipped}, passing={entry['passing']}/{N_CHECKS}")


def render_voltage_model(sim):
    st.markdown("#### 🔬 Tier 3 — ML Voltage Shift Model")
    c1, c2 = st.columns(2)
    with c1:
        pe_v = st.slider("Block P/E:", 0, 3000, 2000, key="v_pe")
        temp_v = st.slider("Temperature (°C):", 20, 85, 55, key="v_temp")
    with c2:
        ecc_v = st.slider("ECC history:", 0, 100000, 30000, 1000, key="v_ecc")
        wear_v = pe_v / 3000.0

    # Compute via loaded model or formula
    voltage_model = st.session_state.get('voltage_model')
    if voltage_model is not None:
        try:
            delta_v = float(voltage_model.predict([[pe_v, temp_v, ecc_v, wear_v]])[0])
        except Exception:
            delta_v = 0.02 * pe_v + 0.3 * temp_v + 0.001 * ecc_v
    else:
        delta_v = 0.02 * pe_v + 0.3 * temp_v + 0.001 * ecc_v

    extra_passes = max(1, int(delta_v / 40))
    recovery_prob = max(0.5, min(0.99, 1.0 - (pe_v / 3000.0) * 0.4))
    latency_us = 75 + extra_passes * 70

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("ΔV shift", f"+{delta_v:.0f} mV")
    mc2.metric("Extra passes", str(extra_passes))
    mc3.metric("Recovery prob", f"{recovery_prob*100:.1f}%")
    mc4.metric("Est. latency", f"~{latency_us}µs")

    # Scatter plot
    import numpy as np
    pe_range = np.linspace(0, 3000, 50)
    dv_range = 0.02 * pe_range + 0.3 * temp_v + 0.001 * ecc_v
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pe_range, y=dv_range, mode='lines',
                             line=dict(color='#14b8a6', width=2),
                             name='ΔV curve'))
    fig.add_trace(go.Scatter(x=[pe_v], y=[delta_v], mode='markers',
                             marker=dict(size=12, color='#f59e0b', symbol='star'),
                             name='Current point'))
    fig.update_layout(
        height=200, margin=dict(l=10,r=10,t=10,b=30),
        paper_bgcolor='#0a0a0f', plot_bgcolor='#12121a',
        xaxis=dict(title='P/E Count', color='#8888a0', showgrid=False),
        yaxis=dict(title='ΔV (mV)', color='#8888a0', showgrid=True, gridcolor='#2a2a3a'),
        font=dict(color='#e8e8f0'), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="voltage_scatter")


def render_ecc_rate_chart(sim):
    st.markdown("#### 📈 ECC Corrections Over Time (Pillar 2→4 Handoff)")
    import numpy as np
    n = 60
    t = list(range(n))
    wear = sim._wear_level()
    rng = np.random.default_rng(int(sim.sim_time) % 1000)
    tier1_vals = [max(0, int((sim.tier1_bypasses / max(sim._tick_count,1)) * (1 + 0.3*rng.standard_normal()))) for _ in t]
    tier2_vals = [max(0, int((sim.tier2_corrections / max(sim._tick_count,1)) * (1 + 0.5*rng.standard_normal()))) for _ in t]
    tier3_vals = [max(0, int((sim.tier3_escalations / max(sim._tick_count,1)) * (1 + 0.8*rng.standard_normal()))) for _ in t]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=tier1_vals, name='Tier 1 bypasses', mode='lines',
                             line=dict(color='#22c55e', width=2)))
    fig.add_trace(go.Scatter(x=t, y=tier2_vals, name='Tier 2 corrections', mode='lines',
                             line=dict(color='#3b82f6', width=2)))
    fig.add_trace(go.Scatter(x=t, y=tier3_vals, name='Tier 3 escalations', mode='lines',
                             line=dict(color='#ef4444', width=2)))
    fig.update_layout(
        height=200, margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor='#0a0a0f', plot_bgcolor='#12121a',
        xaxis=dict(showgrid=False, color='#8888a0'),
        yaxis=dict(showgrid=True, gridcolor='#2a2a3a', color='#8888a0'),
        legend=dict(bgcolor='#1a1a26', font=dict(color='#e8e8f0', size=10)),
        font=dict(color='#e8e8f0'),
    )
    st.plotly_chart(fig, use_container_width=True, key="ecc_rate_chart")


def render_section2(sim):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔷 SECTION 3 — ECC / LDPC Correction Engine")

    last_result = st.session_state.get('last_ecc_result', {'tier': 1, 'success': True})
    render_pipeline_diagram(last_result)

    st.markdown("---")
    render_syndrome_demo()
    st.markdown("---")
    render_ldpc_trace(sim)
    st.markdown("---")

    # ECC allocation table
    st.markdown("#### 🗂️ Context-Aware ECC Allocation")
    import pandas as pd
    df = pd.DataFrame([
        ["BBT / L2P table",   "SLC-mode", "BCH + LDPC double", 20, "2× overhead"],
        ["Critical metadata", "SLC-mode", "BCH + LDPC double", 20, "2× overhead"],
        ["User data (fresh)", "TLC-mode", "Hard LDPC",          8, "1× baseline"],
        ["User data (worn)",  "TLC-mode", "Hard LDPC adaptive", 20, "1× baseline"],
        ["End-of-life block", "TLC-mode", "Soft LDPC + ML",    40, "3× overhead"],
    ], columns=["Data Type", "Storage Mode", "Protection", "LDPC Cap", "RAM Cost"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    render_voltage_model(sim)
    st.markdown("---")
    render_ecc_rate_chart(sim)
    st.markdown('</div>', unsafe_allow_html=True)
