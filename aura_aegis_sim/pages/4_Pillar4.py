"""
AURA — Pillar 4: Firmware Logic Optimization
Runs at build time. K-map, QMC, BDD verification.
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Pillar 4 — Logic Optimization | AURA",
    page_icon="⚙️",
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
    st.markdown("""
<div style="font-family:monospace;font-size:11px;color:#8888a0">
<b style="color:#e8e8f0">Mode:</b> BUILD-TIME<br>
<b style="color:#e8e8f0">Runtime signals:</b> NONE<br>
<b style="color:#e8e8f0">Purpose:</b> Logic reduction<br>
<b style="color:#e8e8f0">Reduction:</b> 30–40%
</div>
""", unsafe_allow_html=True)

# ─── Page header ──────────────────────────────────────────────────────────────
st.markdown("# ⚙️ Pillar 4 — Firmware Logic Optimization")
st.markdown("---")

st.info("**Pillar 4** operates at firmware **BUILD TIME** — not runtime. "
        "It reduces the logical complexity of firmware decision functions by 30–40%, "
        "making the runtime code faster and more verifiable. "
        "It does **not** send signals to other pillars during operation.")

# ─── Build-time badge ─────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:10px;padding:16px 20px;margin-bottom:20px">
  <div style="display:flex;gap:30px;flex-wrap:wrap;align-items:center">
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#a855f7">30–40%</div>
      <div style="color:#8888a0;font-size:12px">Logic Cost Reduction</div>
    </div>
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#22c55e">✅</div>
      <div style="color:#8888a0;font-size:12px">BDD Verified Identical</div>
    </div>
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:32px;font-weight:700;color:#14b8a6">O(1)</div>
      <div style="color:#8888a0;font-size:12px">Runtime Decision Cost</div>
    </div>
    <div style="flex:1;min-width:200px">
      <div style="color:#8888a0;font-size:12px;margin-bottom:4px">Applied to:</div>
      <div style="font-family:monospace;font-size:11px;color:#e8e8f0">
        • Block retirement decision logic<br>
        • LDPC escalation trigger logic
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── K-map / QMC section ─────────────────────────────────────────────────────
from sections.section4_security import render_kmap_section
render_kmap_section()
