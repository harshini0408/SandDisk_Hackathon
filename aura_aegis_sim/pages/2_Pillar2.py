"""
AURA — Pillar 2: NAND Block Management
"""
import streamlit as st
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Pillar 2 — NAND Block Mgmt | AURA",
    page_icon="🗃️",
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

html, body, [data-testid="stApp"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
  background-color: var(--surface) !important;
  border-right: 1px solid var(--border);
}

h1,h2,h3,h4,h5 { font-family: 'JetBrains Mono', monospace !important; color: var(--text) !important; }

div[data-testid="stMetricValue"] { color: var(--green) !important; font-size: 1.6rem !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"]  { color: var(--muted) !important; font-size: 0.75rem !important; }

section[data-testid="stMain"] > div { background: var(--bg); }

div[data-testid="stDataFrame"] { background: var(--card) !important; }
div[data-testid="stDataFrame"] * { color: var(--text) !important; }

.section-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

button[kind="primary"], .stButton button {
  background: linear-gradient(135deg, #1a1a2e, #2a1a3e) !important;
  border: 1px solid var(--purple) !important;
  color: var(--text) !important;
  border-radius: 6px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important;
}
button[kind="primary"]:hover, .stButton button:hover {
  background: linear-gradient(135deg, #2a1a3e, #3a1a5e) !important;
  border-color: var(--blue) !important;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stSlider"] label { color: var(--muted) !important; font-size: 12px !important; }

div[data-testid="stSelectbox"] > div,
div[data-testid="stNumberInput"] > div input {
  background: var(--card) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

div[data-baseweb="tab-list"] { background: var(--surface) !important; border-bottom: 1px solid var(--border); }
div[data-baseweb="tab"] { color: var(--muted) !important; }
div[data-baseweb="tab"][aria-selected="true"] { color: var(--blue) !important; border-bottom: 2px solid var(--blue) !important; }

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Guard: ensure sim exists ─────────────────────────────────────────────────
if 'sim' not in st.session_state:
    from core.ssd_simulator import SSDSimulator
    st.session_state['sim'] = SSDSimulator(preset='fresh')
    for _ in range(20):
        st.session_state['sim'].tick(60)

if 'auto_run' not in st.session_state:
    st.session_state['auto_run'] = False
if 'last_tick' not in st.session_state:
    st.session_state['last_tick'] = time.time()

sim = st.session_state['sim']
speed = st.session_state.get('speed_val', 1)

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
    speed = st.select_slider("Speed", options=[1, 5, 20, 100], value=1, key="speed_sel_p2")
    st.session_state['speed_val'] = speed
    mode = st.selectbox("Mode", ['normal', 'stress', 'aging', 'crash'],
                        index=['normal','stress','aging','crash'].index(sim.mode), key="mode_sel_p2")
    sim.mode = mode

    st.markdown("**Presets:**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🥏 Fresh", key="preset_fresh_p2"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('fresh')
            for _ in range(20):
                st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("🌡️ End-Life", key="preset_eol_p2"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('end_of_life')
            for _ in range(40):
                st.session_state['sim'].tick(60)
            st.rerun()
    with c2:
        if st.button("📀 Mid-Age", key="preset_mid_p2"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('middle_aged')
            for _ in range(30):
                st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("🚨 Critical", key="preset_crit_p2"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('critical')
            for _ in range(50):
                st.session_state['sim'].tick(60)
            st.rerun()

    st.markdown("**Manual Inject:**")
    inj_block = st.number_input("Block #:", 0, 63, 32, key="inj_block_p2")
    if st.button("💥 Force Bad", key="force_bad_btn_p2"):
        sim.force_bad(int(inj_block))
        st.rerun()

    if st.button("🌡️ Thermal Spike", key="thermal_btn_p2"):
        sim.inject_thermal_spike()
        st.rerun()
    if st.button("⚡ Write Storm", key="storm_btn_p2"):
        sim.inject_write_storm()
        st.rerun()
    if st.button("💀 Kill Host", key="kill_btn_p2"):
        sim.kill_host()
        st.rerun()

    st.markdown("---")
    auto = st.toggle("▶ Auto Run Simulation", value=st.session_state['auto_run'], key="auto_toggle_p2")
    st.session_state['auto_run'] = auto

    if st.button("⟳ Single Tick", key="tick_btn_p2"):
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

# ─── Auto-advance ─────────────────────────────────────────────────────────────
if st.session_state['auto_run']:
    now = time.time()
    if now - st.session_state['last_tick'] >= 1.0:
        for _ in range(speed):
            sim.tick(60.0)
        st.session_state['last_tick'] = now
    time.sleep(0.5)
    st.rerun()

# ─── Page header ──────────────────────────────────────────────────────────────
st.markdown("# 🗃️ Pillar 2 — NAND Block Management")
st.markdown("---")

st.info("⚡ **Pillar 2** manages every physical NAND block. "
        "Reports bad block events and wear counts **UP** to Pillar 1, "
        "and receives early retirement commands **DOWN** from Pillar 1's LSTM.")

# ─── NAND section ─────────────────────────────────────────────────────────────
from sections.section1_nand import render_section1
render_section1(sim)

# ─── Signals sent to Pillar 1 ─────────────────────────────────────────────────
st.markdown("### 📡 Signals sent to Pillar 1 (live)")
import pandas as pd
df = pd.DataFrame({
    'Event': ['Block marked bad', 'Block retired (wear)', 'Write remapped'],
    'SMART metric updated': ['③ Bad block count +1', '④ P/E avg, ⑩ Realloc count', '⑨ Retry freq +1'],
    'Effect in Pillar 1': ['LSTM re-runs, health score drops', 'RUL recalculated', 'Anomaly detector checks baseline']
})
st.dataframe(df, hide_index=True, use_container_width=True)
