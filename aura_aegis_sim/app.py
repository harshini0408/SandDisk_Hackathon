"""
AURA — Adaptive Unified Resource Architecture
SSD Firmware Intelligence Platform
Homepage
"""
import streamlit as st
import time
import os
import sys
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(__file__))

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AURA | SSD Firmware Intelligence",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS — Dark Theme, forced regardless of system mode ──────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stApp"],
.main .block-container, section[data-testid="stMain"],
section[data-testid="stMain"] > div,
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background-color: #0a0a0f !important;
  color: #e8e8f0 !important;
  font-family: 'Inter', sans-serif !important;
}

/* Force text visible in both light and dark OS modes */
p, li, span, label, small, div, td, th, a {
  color: #e8e8f0 !important;
}

[data-testid="stSidebar"] {
  border-right: 1px solid #2a2a3a !important;
}

h1, h2, h3, h4, h5 {
  font-family: 'JetBrains Mono', monospace !important;
  color: #e8e8f0 !important;
}

[data-testid="stMetricValue"] { color: #22c55e !important; font-size: 1.5rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #8888a0 !important; font-size: 0.75rem !important; }

[data-testid="stDataFrame"] { background: #1a1a26 !important; }
[data-testid="stDataFrame"] * { color: #e8e8f0 !important; }

.stButton button {
  background: linear-gradient(135deg, #1a1a2e, #2a1a3e) !important;
  border: 1px solid #a855f7 !important;
  color: #e8e8f0 !important;
  border-radius: 6px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important;
  transition: all 0.2s ease !important;
}
.stButton button:hover {
  background: linear-gradient(135deg, #2a1a3e, #3a1a5e) !important;
  border-color: #3b82f6 !important;
  transform: translateY(-1px) !important;
}

[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSlider"] label { color: #8888a0 !important; font-size: 12px !important; }

[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
  background: #1a1a26 !important;
  color: #e8e8f0 !important;
  border-color: #2a2a3a !important;
}

[data-baseweb="tab-list"] { background: #12121a !important; border-bottom: 1px solid #2a2a3a !important; }
[data-baseweb="tab"] { color: #8888a0 !important; }
[data-baseweb="tab"][aria-selected="true"] { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }

.stAlert { border-radius: 8px !important; }
div.stAlert p { color: #0a0a0f !important; }

.section-card {
  background: #1a1a26;
  border: 1px solid #2a2a3a;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.ticker-wrap {
  background: #12121a;
  border: 1px solid #2a2a3a;
  border-radius: 6px;
  padding: 8px 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #22c55e;
  overflow: hidden;
  white-space: nowrap;
}

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
if 'sim' not in st.session_state:
    from core.ssd_simulator import SSDSimulator
    st.session_state['sim'] = SSDSimulator(preset='middle_aged')
    for _ in range(20):
        st.session_state['sim'].tick(60)

if 'voltage_model' not in st.session_state:
    try:
        import joblib
        vpath = os.path.join(os.path.dirname(__file__), 'models', 'voltage_model.pkl')
        st.session_state['voltage_model'] = joblib.load(vpath) if os.path.exists(vpath) else None
    except Exception:
        st.session_state['voltage_model'] = None

for key in ('auto_run', ):
    if key not in st.session_state:
        st.session_state[key] = False
if 'last_tick' not in st.session_state:
    st.session_state['last_tick'] = time.time()

sim = st.session_state['sim']

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔷 AURA")
    st.page_link("app.py",             label="Home",                           icon="🏠")
    st.page_link("pages/0_Manual.py",  label="📖 Quick Manual",               icon="📖")
    st.page_link("pages/1_Pillar1.py", label="Pillar 1 — Health & Diagnostics", icon="🧠")
    st.page_link("pages/2_Pillar2.py", label="Pillar 2 — NAND Block Mgmt",     icon="🗃️")
    st.page_link("pages/3_Pillar3.py", label="Pillar 3 — ECC & Reliability",   icon="🛡️")
    st.page_link("pages/4_Pillar4.py", label="Pillar 4 — Logic Optimization",  icon="⚙️")
    st.divider()
    st.caption("Pillar 1 commands Pillar 2 & 3.\nPillar 4 is build-time only.")
    st.markdown("---")

    st.markdown("### 🎮 Simulation Controls")
    speed = st.select_slider("Speed", options=[1, 5, 20, 100], value=1, key="speed_sel")
    st.session_state['speed_val'] = speed
    mode = st.selectbox("Mode", ['normal', 'stress', 'aging', 'crash'],
                        index=['normal','stress','aging','crash'].index(sim.mode), key="mode_sel")
    sim.mode = mode

    st.markdown("**Presets:**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🆕 Fresh", key="preset_fresh"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('fresh')
            for _ in range(20): st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("💀 End-Life", key="preset_eol"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('end_of_life')
            for _ in range(40): st.session_state['sim'].tick(60)
            st.rerun()
    with c2:
        if st.button("📀 Mid-Age", key="preset_mid"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('middle_aged')
            for _ in range(30): st.session_state['sim'].tick(60)
            st.rerun()
        if st.button("🚨 Critical", key="preset_crit"):
            from core.ssd_simulator import SSDSimulator
            st.session_state['sim'] = SSDSimulator('critical')
            for _ in range(50): st.session_state['sim'].tick(60)
            st.rerun()

    st.markdown("**Inject:**")
    inj_block = st.number_input("Block #:", 0, 63, 32, key="inj_block")
    if st.button("💥 Force Bad Block", key="force_bad_btn"):
        sim.force_bad(int(inj_block)); st.rerun()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🌡️ Spike", key="thermal_btn"):
            sim.inject_thermal_spike(); st.rerun()
    with col_b:
        if st.button("⚡ Storm", key="storm_btn"):
            sim.inject_write_storm(); st.rerun()
    if st.button("💀 Kill Host", key="kill_btn"):
        sim.kill_host(); st.rerun()

    st.markdown("---")
    auto = st.toggle("▶ Auto Run", value=st.session_state['auto_run'], key="auto_toggle")
    st.session_state['auto_run'] = auto
    if st.button("⟳ Tick Once", key="tick_btn"):
        for _ in range(speed): sim.tick(60.0)
        st.rerun()

    st.markdown("---")
    st.markdown(f"""<div style="font-family:monospace;font-size:11px;color:#8888a0">
<b style="color:#e8e8f0">Drive:</b> AURA #7 · TLC<br>
<b style="color:#e8e8f0">Sim time:</b> {sim.sim_time/3600:.1f}h<br>
<b style="color:#e8e8f0">Mode:</b> {sim.mode.upper()} · {speed}×</div>""",
    unsafe_allow_html=True)

# ─── Auto-advance ─────────────────────────────────────────────────────────────
if st.session_state['auto_run']:
    now = time.time()
    if now - st.session_state['last_tick'] >= 1.0:
        speed_v = st.session_state.get('speed_val', 1)
        for _ in range(speed_v): sim.tick(60.0)
        st.session_state['last_tick'] = now
    time.sleep(0.5)
    st.rerun()

# ─── HERO ────────────────────────────────────────────────────────────────────
health = sim.health_score
rul = sim.rul_days
health_color = '#22c55e' if health > 70 else '#f59e0b' if health > 40 else '#ef4444'
bad_count = sum(1 for b in sim.blocks if b.state in ('BAD', 'RETIRED'))

st.markdown(f"""
<div style="background:linear-gradient(135deg,#12121a,#1a1a2e);border:1px solid #2a2a3a;border-radius:14px;padding:24px 28px;margin-bottom:20px">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
    <div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#e8e8f0">🔷 AURA</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#a855f7;margin-top:2px">Adaptive Unified Resource Architecture</div>
      <div style="font-size:13px;color:#8888a0;margin-top:6px;max-width:480px">
        Predicts SSD failure <b style="color:#3b82f6">21 days early</b>, corrects bit errors in real-time,<br>
        and leaves a tamper-proof diagnostic trail — even through a total crash.
      </div>
    </div>
    <div style="display:flex;gap:24px;flex-wrap:wrap">
      <div style="text-align:center;background:#0a0a0f44;padding:12px 20px;border-radius:10px;border:1px solid #2a2a3a">
        <div style="font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:700;color:{health_color};line-height:1">{health:.0f}</div>
        <div style="color:#8888a0;font-size:10px;letter-spacing:1px">HEALTH SCORE</div>
        <div style="color:#3b82f6;font-size:13px;font-weight:600">~{rul:.0f} days left</div>
      </div>
      <div style="text-align:left;background:#0a0a0f44;padding:12px 18px;border-radius:10px;border:1px solid #2a2a3a;font-family:monospace;font-size:12px">
        <div style="color:#8888a0">Bad blocks: <b style="color:#ef4444">{bad_count}</b></div>
        <div style="color:#8888a0">ECC fixed: <b style="color:#22c55e">{sim.ecc_corrections:,}</b></div>
        <div style="color:#8888a0">Wear: <b style="color:#f59e0b">{sim._wear_level()*100:.1f}%</b></div>
        <div style="color:#8888a0">Mode: <b style="color:#a855f7">{sim.mode.upper()}</b></div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Action buttons row ───────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
with btn_col1:
    if st.button("📖 Open Manual", key="open_manual_hero"):
        st.switch_page("pages/0_Manual.py")
with btn_col2:
    if st.button("🧠 Start with Pillar 1", key="start_p1"):
        st.switch_page("pages/1_Pillar1.py")

st.markdown("---")
st.markdown("## The Four Pillars")

# ─── PILLAR CARDS ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 🧠 Pillar 1 — Health & Diagnostics")
        st.caption("The brain. Predicts failure, commands all other pillars.")
        st.markdown("""
- **Live SMART feed** — 12 metrics, sparklines
- **LSTM predictor** — health score, RUL, failure probability
- **Anomaly detection** — per-drive personal baseline
- **AES-256 + Shamir** — encrypted tamper-proof reports
- **OOB channels** — BLE beacon + UART (survives host crash)
""")
        if st.button("Open Pillar 1 →", key="p1"):
            st.switch_page("pages/1_Pillar1.py")

with col2:
    with st.container(border=True):
        st.markdown("### 🗃️ Pillar 2 — NAND Block Management")
        st.caption("The body. Manages every physical block on the chip.")
        st.markdown("""
- **Live 8×8 block grid** — 64 blocks, colour-coded by wear
- **Bad Block Table** — Bloom filter + Bitmap + Cuckoo hash
- **O(1) lookup** — bit-arithmetic trace, no scan needed
- **Wear retirement** — Phase D demo with CRC persistence
""")
        if st.button("Open Pillar 2 →", key="p2"):
            st.switch_page("pages/2_Pillar2.py")

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.markdown("### 🛡️ Pillar 3 — ECC & Reliability")
        st.caption("The immune system. Corrects bit errors before they become data loss.")
        st.markdown("""
- **AEGIS pipeline** — Tier 1 → BCH → Hard LDPC → Soft+ML → UECC
- **Live syndrome demo** — H·r matrix calculation
- **LDPC bit-flip trace** — step through each iteration
- **Voltage shift model** — ML-based Tier 3 correction
""")
        if st.button("Open Pillar 3 →", key="p3"):
            st.switch_page("pages/3_Pillar3.py")

with col4:
    with st.container(border=True):
        st.markdown("### ⚙️ Pillar 4 — Logic Optimization")
        st.caption("The optimizer. Shrinks firmware decision logic by 30–40% at build time.")
        st.markdown("""
- **K-map** — 4-variable visual heatmap minimization
- **Quine-McCluskey** — tabular reduction for 5+ variables
- **BDD verification** — proves zero logic errors introduced
- **30–40% cost reduction** — measured, not estimated
""")
        if st.button("Open Pillar 4 →", key="p4"):
            st.switch_page("pages/4_Pillar4.py")

# ─── ARCHITECTURE DIAGRAM ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## How the Pillars Connect")

def _rgba(hex_color: str, alpha: float = 0.2) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'

nodes = {
    "Pillar 1\n(Health Brain)": (2, 2),
    "Pillar 2\n(NAND Grid)":   (0, 2),
    "Pillar 3\n(ECC Engine)":  (4, 2),
    "Pillar 4\n(Logic Opt)":   (2, 0),
}
node_colors = {
    "Pillar 1\n(Health Brain)": "#3b82f6",
    "Pillar 2\n(NAND Grid)":   "#22c55e",
    "Pillar 3\n(ECC Engine)":  "#a855f7",
    "Pillar 4\n(Logic Opt)":   "#f59e0b",
}

arrow_specs = [
    dict(x=2.0,  y=2.05, ax=0.45, ay=2.05, arrowcolor='#22c55e',
         text="↑ bad block / wear data", showarrow=True),
    dict(x=0.45, y=1.85, ax=1.95, ay=1.85, arrowcolor='#3b82f6',
         text="↓ retire block cmd", showarrow=True),
    dict(x=2.0,  y=2.15, ax=3.55, ay=2.15, arrowcolor='#a855f7',
         text="↑ ECC correction rate", showarrow=True),
    dict(x=3.55, y=1.95, ax=2.05, ay=1.95, arrowcolor='#3b82f6',
         text="↓ LDPC ceiling cmd", showarrow=True),
    dict(x=2.0,  y=0.45, ax=2.0,  ay=1.6,  arrowcolor='#f59e0b',
         text="BUILD-TIME", showarrow=True),
]

fig = go.Figure()

for spec in arrow_specs:
    fig.add_annotation(
        x=spec['x'], y=spec['y'], ax=spec['ax'], ay=spec['ay'],
        xref='x', yref='y', axref='x', ayref='y',
        showarrow=spec['showarrow'],
        arrowhead=2, arrowsize=1.2, arrowwidth=2,
        arrowcolor=spec['arrowcolor'],
        text=spec.get('text', ''),
        font=dict(color=spec['arrowcolor'], size=9, family='JetBrains Mono'),
    )

for label, (x, y) in nodes.items():
    color = node_colors[label]
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode='markers+text',
        marker=dict(
            size=90,
            color=_rgba(color, 0.15),
            symbol='square',
            line=dict(color=color, width=3),
        ),
        text=[label],
        textposition='middle center',
        textfont=dict(color='#e8e8f0', size=10, family='JetBrains Mono'),
        showlegend=False,
        hoverinfo='skip',
    ))

fig.update_layout(
    height=330,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor='#0a0a0f',
    plot_bgcolor='#0a0a0f',
    xaxis=dict(range=[-0.9, 4.9], showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(range=[-0.6, 3.1], showgrid=False, zeroline=False, showticklabels=False),
)
st.plotly_chart(fig, use_container_width=True, key="arch_diagram")

st.markdown("""<div style="background:#12121a;border:1px solid #2a2a3a;border-radius:8px;
padding:12px 20px;font-family:monospace;font-size:12px">
<span style="color:#22c55e">Pillar 2 → Pillar 1:</span> bad block events & wear counts<br>
<span style="color:#a855f7">Pillar 3 → Pillar 1:</span> ECC rates & RBER metrics<br>
<span style="color:#3b82f6">Pillar 1 → Pillar 2:</span> proactive block retirement commands<br>
<span style="color:#3b82f6">Pillar 1 → Pillar 3:</span> LDPC ceiling raise commands<br>
<span style="color:#f59e0b">Pillar 4:</span> standalone — operates at firmware build time only
</div>""", unsafe_allow_html=True)
