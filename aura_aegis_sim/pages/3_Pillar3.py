"""
AURA — Pillar 3: Data Reliability & Error Correction
"""
import streamlit as st
import time
import os
import sys
import pickle
import random
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Pillar 3 — ECC & Reliability | AURA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Dark Theme CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

:root {
  --bg:      #0a0a0f;
  --surface: #12121a;
  --card:    #1a1a26;
  --border:  #2a2a3a;
  --text:    #e8e8f0;
  --muted:   #8888a0;
  --dim:     #4a4a60;
  --green:   #22c55e;
  --amber:   #f59e0b;
  --red:     #ef4444;
  --blue:    #3b82f6;
  --purple:  #a855f7;
  --teal:    #14b8a6;
  --orange:  #f97316;
}

html, body, [data-testid="stApp"] { margin-top: -20px; }

/* Keep global styles consistent with AURA */
h1, h2, h3, h4, h5 { font-family: 'JetBrains Mono', monospace !important; color: var(--text) !important; }

.section-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

div[data-baseweb="tab-list"] { background: var(--surface) !important; border-bottom: 1px solid var(--border); }
div[data-baseweb="tab"] { color: var(--muted) !important; padding: 10px 20px; font-weight: 600; font-family: 'Inter', sans-serif !important;}
div[data-baseweb="tab"][aria-selected="true"] { color: var(--purple) !important; border-bottom: 2px solid var(--purple) !important; }

/* Overrides for specific metrics / elements */
div[data-testid="stMetricValue"] { color: var(--purple) !important; font-size: 1.6rem !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"]  { color: var(--muted) !important; font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── Guard: ensure sim exists ─────────────────────────────────────────────────
if 'sim' not in st.session_state:
    from core.ssd_simulator import SSDSimulator
    st.session_state['sim'] = SSDSimulator(preset='fresh')
    for _ in range(20):
        st.session_state['sim'].tick(60)

if 'voltage_model' not in st.session_state:
    try:
        vpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'voltage_model.pkl')
        if os.path.exists(vpath):
            with open(vpath, 'rb') as f:
                st.session_state['voltage_model'] = pickle.load(f)
        else:
            st.session_state['voltage_model'] = None
    except Exception:
        st.session_state['voltage_model'] = None

if 'auto_run' not in st.session_state:
    st.session_state['auto_run'] = False
if 'last_tick' not in st.session_state:
    st.session_state['last_tick'] = time.time()

sim = st.session_state['sim']
speed = st.session_state.get('speed_val', 1)
model = st.session_state['voltage_model']

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔷 AURA")
    st.page_link("app.py",             label="Home",                            icon="🏠")
    st.page_link("pages/0_Manual.py",  label="📖 Quick Manual",                icon="📖")
    st.page_link("pages/1_Pillar1.py", label="Pillar 1 — Health & Diagnostics", icon="🧠")
    st.page_link("pages/2_Pillar2.py", label="Pillar 2 — NAND Block Mgmt",     icon="🗃️")
    st.page_link("pages/3_Pillar3.py", label="Pillar 3 — ECC & Reliability",   icon="🛡️")
    st.page_link("pages/4_Pillar4.py", label="Pillar 4 — Logic Optimization",  icon="⚙️")
    st.divider()
    st.caption("Pillar 1 commands Pillar 2 & 3.\nPillar 4 is build-time only.")
    st.markdown("---")

    st.markdown("### 🎮 Simulation Controls")
    speed = st.select_slider("Speed", options=[1, 5, 20, 100], value=1, key="speed_sel_p3")
    st.session_state['speed_val'] = speed
    mode = st.selectbox("Mode", ['normal', 'stress', 'aging', 'crash'],
                        index=['normal','stress','aging','crash'].index(sim.mode), key="mode_sel_p3")
    sim.mode = mode

    st.markdown("**Presets:**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🥏 Fresh", key="preset_fresh_p3"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('fresh')
            for _ in range(20):
                st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("🌡️ End-Life", key="preset_eol_p3"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('end_of_life')
            for _ in range(40):
                st.session_state['sim'].tick(60)
            st.rerun()
    with c2:
        if st.button("📀 Mid-Age", key="preset_mid_p3"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('middle_aged')
            for _ in range(30):
                st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("🚨 Critical", key="preset_crit_p3"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('critical')
            for _ in range(50):
                st.session_state['sim'].tick(60)
            st.rerun()

    st.markdown("---")
    auto = st.toggle("▶ Auto Run Simulation", value=st.session_state['auto_run'], key="auto_toggle_p3")
    st.session_state['auto_run'] = auto

    if st.button("⟳ Single Tick", key="tick_btn_p3"):
        for _ in range(speed):
            sim.tick(60.0)
        st.rerun()

    st.markdown("---")
    st.markdown(f"""
<div style="font-family:monospace;font-size:11px;color:#8888a0">
<b style="color:#e8e8f0">Drive:</b> AURA-AEGIS #7<br>
<b style="color:#e8e8f0">NAND:</b> TLC (3000 P/E max)<br>
<b style="color:#e8e8f0">Blocks:</b> 64 total<br>
<b style="color:#e8e8f0">Sim time:</b> {sim.sim_time/3600:.1f}h<br>
<b style="color:#e8e8f0">Mode:</b> {sim.mode.upper()}<br>
<b style="color:#e8e8f0">Speed:</b> {speed}×
</div>
""", unsafe_allow_html=True)

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("# 🛡️ Pillar 3 — AEGIS Pipeline")
st.markdown("### Adaptive ECC & Grade-Intelligent Supervision")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "① Tri-Tier Pipeline",
    "② ECC Allocation",
    "③ FTL Feedback Loop"
])

# ══════════════════════════════════════════════════
# TAB 1 — TRI-TIER PIPELINE
# ══════════════════════════════════════════════════
with tab1:
    st.markdown("#### Tri-Tier Hybrid Decoding Pipeline")
    st.caption("Simulate a NAND read and watch AEGIS route it through the correct ECC tier.")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2], gap="large")
    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("##### Configure Read Request")
        pe_cycles = st.slider("P/E Cycles", 0, 5000, 1200)
        bit_flips = st.slider("Injected Bit Errors", 0, 150, 0)
        temperature = st.slider("Temperature (°C)", 20, 85, 45)
        block_health = st.selectbox("Block Health", ["healthy", "worn", "degraded"])
        retention_days = st.slider("Data Retention (days)", 0, 365, 30)
        wear_level = pe_cycles / 5000 * 100
        ecc_history = pe_cycles * 0.008 + random.uniform(0, 2)
        exec_btn = st.button("▶ Execute NAND Read", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        if exec_btn:
            st.markdown("##### Decoder Output")

            # ── TIER 1 ──────────────────────────
            with st.status("Tier 1 — Syndrome Check...", expanded=True) as s:
                time.sleep(0.4)
                if bit_flips == 0:
                    s.update(label="✅ Tier 1 — Syndrome Zero Bypass", state="complete")
                    st.success("**Syndrome = 0** — No errors detected")
                    st.metric("Read Latency", "0 µs")
                    st.metric("CPU Overhead", "None")
                    st.info("ℹ️ ~40% of all reads on healthy NAND take this path")
                    st.stop()
                else:
                    s.update(label="⚠️ Tier 1 — Errors Detected, Escalating to Tier 2", state="error")
                    st.warning(f"Syndrome ≠ 0 | {bit_flips} bit errors detected")

            # ── TIER 2 ──────────────────────────
            with st.status("Tier 2 — BCH + Hard LDPC...", expanded=True) as s2:
                time.sleep(0.6)
                from utils.ldpc_sim import simulate_bch, simulate_hard_ldpc
                bch = simulate_bch(bit_flips)
                if bch["success"]:
                    s2.update(label="✅ Tier 2 — BCH Correction Successful", state="complete")
                    st.success(f"BCH corrected {bch['bits_corrected']} bits in {bch['latency_us']} µs")
                    st.metric("Tier", "2 — BCH")
                    st.metric("CPU Saved vs Full LDPC", "~30%")
                else:
                    ldpc = simulate_hard_ldpc(bit_flips, block_health)
                    if ldpc["success"]:
                        s2.update(label="✅ Tier 2 — Hard LDPC Corrected", state="complete")
                        prog = st.progress(0)
                        for i in range(ldpc["iterations"]):
                            prog.progress((i + 1) / ldpc["max_iterations"],
                                          text=f"Iteration {i+1}/{ldpc['max_iterations']}")
                            time.sleep(0.08)
                        st.success(f"Hard LDPC corrected in {ldpc['iterations']} iterations")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Iterations Used", ldpc["iterations"])
                        col_b.metric("Max Allowed", ldpc["max_iterations"])
                        col_c.metric("CPU Saved", f"{ldpc['cpu_saved_pct']}%")
                    else:
                        s2.update(label="❌ Tier 2 — LDPC Failed, Escalating to Tier 3", state="error")
                        st.error("Hard LDPC exhausted all iterations")

                        # ── TIER 3 ──────────────────────
                        with st.status("Tier 3 — ML Soft-Decision Recovery...", expanded=True) as s3:
                            time.sleep(0.8)
                            from utils.ldpc_sim import simulate_soft_ldpc_ml
                            if model:
                                result = simulate_soft_ldpc_ml(
                                    pe_cycles, temperature, retention_days,
                                    wear_level, ecc_history, model
                                )
                                s3.update(label="✅ Tier 3 — ML Recovery Successful", state="complete")
                                st.success("Soft-Decision LDPC with ML-predicted voltage shift succeeded")
                                col_a, col_b, col_c = st.columns(3)
                                col_a.metric("Voltage Shift", f"+{result['voltage_shift_mv']} mV")
                                col_b.metric("Re-reads Required", result["reads_required"])
                                col_c.metric("Latency Saved", f"{result['latency_saved_pct']}%")
                                st.caption(f"ML model (<2KB) used {pe_cycles} P/E cycles, "
                                           f"{temperature}°C, {retention_days}d retention "
                                           f"→ predicted optimal voltage vector in <100 CPU cycles")
                            else:
                                s3.update(label="❌ Tier 3 Failed - ML Model Missing", state="error")
                                st.error("The ML Model (voltage_model.pkl) was not found. Please train it first.")

        else:
            st.info("Configure the parameters on the left and click **Execute NAND Read** to begin the simulation.")

# ══════════════════════════════════════════════════
# TAB 2 — ECC ALLOCATION
# ══════════════════════════════════════════════════
with tab2:
    st.markdown("#### Context-Aware ECC Allocation")
    st.caption("Not all data deserves the same protection. AEGIS applies different strategies per block health.")
    st.markdown("<br>", unsafe_allow_html=True)

    blocks = [
        {"id": "Block A", "type": "User Media", "mode": "TLC", "health": "Healthy",
         "ecc": "BCH → Hard LDPC", "max_iter": 8, "color": "green", "pe": 250},
        {"id": "Block B", "type": "OS Files", "mode": "MLC", "health": "Worn",
         "ecc": "BCH + Hard LDPC", "max_iter": 12, "color": "orange", "pe": 2800},
        {"id": "Block C", "type": "App Data", "mode": "SLC", "health": "Degraded",
         "ecc": "BCH + Double LDPC", "max_iter": 20, "color": "red", "pe": 4200},
        {"id": "Block D", "type": "FTL Mapping Table", "mode": "SLC FORCED",
         "health": "Critical Metadata", "ecc": "Double-Enveloped ECC + BCH Verify",
         "max_iter": 20, "color": "red", "pe": 0},
    ]

    cols = st.columns(4)
    for i, blk in enumerate(blocks):
        with cols[i]:
            border_color = {"green": "#2ecc71", "orange": "#f39c12", "red": "#e74c3c"}[blk["color"]]
            st.markdown(f"""
<div style='background: var(--card); border: 2px solid {border_color}; border-radius: 12px; padding: 18px; min-height: 280px'>
<h4 style='margin:0'>{blk['id']}</h4>
<p style='color: var(--muted); font-size: 12px; margin: 4px 0'>{blk['type']}</p>
<hr style='border-color: var(--border)'/>
<b>NAND Mode:</b> <span style='color: var(--blue)'>{blk['mode']}</span><br/>
<b>Health:</b> <span style='color: {border_color}'>{blk['health']}</span><br/>
<div style='margin-top:8px; font-size:12px; color:var(--muted)'>ECC STRATEGY</div>
<code style='color:var(--text); background:var(--surface); padding:4px 6px; border-radius:4px; display:block; margin:4px 0 8px'>
{blk['ecc']}</code>
<b>Max Iterations:</b> <span style='color:var(--purple)'>{blk['max_iter']}</span><br/>
<b>P/E Cycles:</b> {blk['pe']}
</div>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("#### Write Critical Metadata")
    if st.button("📝 Write FTL Mapping Table Entry"):
        with st.container():
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            log = st.empty()
            steps = [
                ("🔍 Classifying data as critical metadata...", 0.3),
                ("🔀 Routing to SLC-mode blocks only...", 0.4),
                ("🛡️ Applying BCH Layer 1 encoding...", 0.5),
                ("🛡️ Applying LDPC Layer 2 encoding (double-envelope)...", 0.5),
                ("🔬 Verifying write with BCH syndrome check...", 0.3),
                ("✅ Written to **Block D** with maximum protection", 0.2),
            ]
            for msg, delay in steps:
                log.info(msg)
                time.sleep(delay)
            log.success("FTL Mapping Table entry written — Double-Enveloped ECC + BCH Verify applied.")
            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TAB 3 — FTL FEEDBACK LOOP
# ══════════════════════════════════════════════════
with tab3:
    st.markdown("#### Health-to-FTL Feedback Loop")
    st.caption("Watch AEGIS detect a dying block and proactively trigger FTL retirement.")
    st.markdown("<br>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 4])
    with colA:
        block_id = st.selectbox("Select Block to Monitor", [f"Block {i}" for i in range(1, 21)])
        sim_age_btn = st.button("▶ Simulate Aging", type="primary", use_container_width=True)
    
    with colB:
        st.info("The decoder continuously monitors its own behavior. If LDPC iterations consistently exceed 15, it flags pre-failure.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        chart_placeholder = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        metric_placeholder = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)
        log_placeholder = st.empty()

    if sim_age_btn:
        iterations = []
        rber_vals = []
        timestamps = []
        retired = False

        for tick in range(40):
            # Simulate LDPC iterations rising with age
            base = 2 + tick * 0.4 + random.gauss(0, 0.5)
            iterations.append(max(1, round(base, 1)))
            rber_vals.append(round(1e-7 * (1.5 ** (tick * 0.3)), 10))
            timestamps.append(f"T+{tick*3}h")

            fig = go.Figure()
            fig.add_hline(y=15, line_dash="dash", line_color="#ef4444",
                          annotation_text=" PRE-FAILURE THRESHOLD (15) ", annotation_position="top left",
                          annotation_font=dict(color="#ef4444", size=11, family="JetBrains Mono"))
            fig.add_trace(go.Scatter(
                x=timestamps, y=iterations, mode='lines+markers',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=7, color='#a855f7'),
                name="LDPC Iterations"
            ))
            fig.update_layout(
                title=dict(text=f"Live LDPC Iteration Tracker — {block_id}", font=dict(family="Inter", size=18, color="#e8e8f0")),
                yaxis_title="LDPC Iterations Required", xaxis_title="Simulation Time",
                height=350, showlegend=False,
                yaxis=dict(range=[0, 22], gridcolor="#2a2a3a"),
                xaxis=dict(gridcolor="#2a2a3a"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#8888a0")
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)

            current = iterations[-1]
            metric_placeholder.metric("Current LDPC Iterations", current,
                                       delta=round(current - iterations[-2], 1) if len(iterations) > 1 else 0,
                                       delta_color="inverse")
            time.sleep(0.15)

            if current >= 15 and not retired:
                retired = True
                # ── RETIREMENT SEQUENCE ──────────
                with log_placeholder.container():
                    st.error(f"⚠️ **PRE-FAILURE DETECTED**: {block_id} hit maximum iteration threshold!")
                    time.sleep(0.3)
                    dest_block = random.randint(200, 599)
                    actions = [
                        f"[{time.strftime('%H:%M:%S')}] AEGIS flag: LDPC iterations > 15",
                        f"[{time.strftime('%H:%M:%S')}] FTL: Initiating proactive data relocation",
                        f"[{time.strftime('%H:%M:%S')}] ✅ Data relocated to safe Block {dest_block}",
                        f"[{time.strftime('%H:%M:%S')}] ✅ {block_id} completely retired from wear-leveling pool",
                        f"[{time.strftime('%H:%M:%S')}] ✅ Bad Block Table (Pillar 2) updated",
                        f"[{time.strftime('%H:%M:%S')}] ✅ SMART attribute exported to Pillar 4 telemetry",
                        f"[{time.strftime('%H:%M:%S')}] STATUS: UECC PREVENTED — No data loss recorded.",
                    ]
                    log_area = st.empty()
                    displayed = []
                    for action in actions:
                        displayed.append(action)
                        if "✅" in action or "STATUS:" in action:
                            log_area.code('\n'.join(displayed), language="bash")
                        else:
                            log_area.code('\n'.join(displayed), language="bash")
                        time.sleep(0.25)
                break

# Auto-advance (copied from main app logic to keep sim clock running)
if st.session_state['auto_run']:
    now = time.time()
    if now - st.session_state['last_tick'] >= 1.0:
        for _ in range(speed):
            sim.tick(60.0)
        st.session_state['last_tick'] = now
    time.sleep(0.5)
    st.rerun()
