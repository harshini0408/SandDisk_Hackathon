"""
AURA — Quick Manual
Judge-friendly overview of the entire platform.
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Manual | AURA",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stApp"],
.main .block-container, section[data-testid="stMain"],
section[data-testid="stMain"] > div,
[data-testid="stSidebar"] {
  background-color: #0a0a0f !important;
  color: #e8e8f0 !important;
  font-family: 'Inter', sans-serif !important;
}
p, li, span, label, small, div, td, th { color: #e8e8f0 !important; }
h1,h2,h3,h4,h5 { font-family: 'JetBrains Mono', monospace !important; color: #e8e8f0 !important; }
.stButton button {
  background: linear-gradient(135deg,#1a1a2e,#2a1a3e) !important;
  border: 1px solid #a855f7 !important;
  color: #e8e8f0 !important;
  border-radius: 6px !important;
  font-family: 'JetBrains Mono', monospace !important;
}
[data-baseweb="tab-list"] { background: #12121a !important; border-bottom: 1px solid #2a2a3a !important; }
[data-baseweb="tab"] { color: #8888a0 !important; }
[data-baseweb="tab"][aria-selected="true"] { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }
div.stAlert p { color: #0a0a0f !important; }
</style>
""", unsafe_allow_html=True)

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

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 📖 AURA — Quick Manual")
st.markdown("**Adaptive Unified Resource Architecture** · SSD Firmware Intelligence Platform")
st.markdown("---")

st.info("**How to read this manual:** Each tab below explains one aspect of AURA. Start with *What is AURA?*, then explore the pillars in order. Use the sidebar to jump directly to any pillar.")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔷 What is AURA?",
    "🧠 Pillar 1",
    "🗃️ Pillar 2",
    "🛡️ Pillar 3",
    "⚙️ Pillar 4",
    "🎮 Using the Simulator",
])

# ── Tab 0: Overview ──────────────────────────────────────────────────────────
with tab0:
    st.markdown("## The Problem AURA Solves")
    col_prob, col_sol = st.columns(2)
    with col_prob:
        st.markdown("""<div style="background:#2d0707;border:1px solid #ef4444;border-radius:10px;padding:16px">
<b style="color:#ef4444;font-size:15px">❌ Without AURA</b><br><br>
<span style="color:#e8e8f0;font-size:13px">
• SSD failure is discovered only <b>after data is lost</b><br>
• Error correction is static — same protection for fresh and worn blocks<br>
• Bad block lookup requires <b>scanning the entire block table</b><br>
• Diagnostic data is <b>lost if the host crashes</b><br>
• Firmware decision logic is bloated with redundant gates
</span>
</div>""", unsafe_allow_html=True)
    with col_sol:
        st.markdown("""<div style="background:#072d18;border:1px solid #22c55e;border-radius:10px;padding:16px">
<b style="color:#22c55e;font-size:15px">✅ With AURA</b><br><br>
<span style="color:#e8e8f0;font-size:13px">
• Failure predicted <b>21 days in advance</b> using LSTM<br>
• ECC adapts per-block — worn blocks get more correction power<br>
• O(1) bad block lookup via <b>Bloom filter + Bitmap + Cuckoo hash</b><br>
• Encrypted diagnostics sent via BLE even when host is dead<br>
• Logic minimization reduces firmware size by <b>30–40%</b>
</span>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## The Four-Pillar Architecture")

    st.markdown("""<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">

<div style="background:#1a1a26;border-left:4px solid #3b82f6;border-radius:8px;padding:14px">
  <b style="color:#3b82f6">🧠 PILLAR 1 — Health & Diagnostics</b><br>
  <span style="color:#8888a0;font-size:12px">The central intelligence hub</span><br><br>
  <span style="font-size:13px">Reads 12 SMART attributes every tick, runs an LSTM neural network to compute a <b>health score (0–100)</b>, predicts <b>Remaining Useful Life</b>, and classifies the anomaly type (NONE / SLOW_BURN / WATCH / ACCELERATING / CRITICAL).</span>
</div>

<div style="background:#1a1a26;border-left:4px solid #22c55e;border-radius:8px;padding:14px">
  <b style="color:#22c55e">🗃️ PILLAR 2 — NAND Block Management</b><br>
  <span style="color:#8888a0;font-size:12px">Physical storage layer</span><br><br>
  <span style="font-size:13px">Manages 64 physical NAND blocks. Tracks their wear (P/E cycles), marks failing blocks as bad, and handles data migration. Sends bad-block events up to Pillar 1 and receives retirement commands down.</span>
</div>

<div style="background:#1a1a26;border-left:4px solid #a855f7;border-radius:8px;padding:14px">
  <b style="color:#a855f7">🛡️ PILLAR 3 — ECC & Reliability</b><br>
  <span style="color:#8888a0;font-size:12px">Error correction engine</span><br><br>
  <span style="font-size:13px">A 4-tier error correction pipeline: fast syndrome check → BCH correction → Hard-decision LDPC (up to 20 iterations) → Soft LDPC + ML voltage model → UECC (unrecoverable). Correction power scales with block age.</span>
</div>

<div style="background:#1a1a26;border-left:4px solid #f59e0b;border-radius:8px;padding:14px">
  <b style="color:#f59e0b">⚙️ PILLAR 4 — Logic Optimization</b><br>
  <span style="color:#8888a0;font-size:12px">Build-time firmware optimizer</span><br><br>
  <span style="font-size:13px">Runs at firmware compile time (not runtime). Uses Karnaugh maps + Quine-McCluskey algorithm to simplify boolean decision logic. Verified correct via Binary Decision Diagrams. Reduces gate count by 30–40%.</span>
</div>

</div>""", unsafe_allow_html=True)

# ── Tab 1: Pillar 1 ───────────────────────────────────────────────────────────
with tab1:
    st.markdown("## 🧠 Pillar 1 — Health Monitoring & Diagnostics")
    st.markdown("""<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:10px;padding:18px">
<b style="color:#3b82f6;font-size:14px">What you'll see</b><br>
</div>""", unsafe_allow_html=True)
    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**📊 SMART Metrics Grid**
- 12 metrics displayed as cards with sparklines
- Each metric has a colour-coded status dot (green/amber/red)
- Metrics include: ECC rate, UECC count, bad blocks, P/E average, wear level, RBER, temperature, read latency, retry frequency, reallocated sectors, program fails, erase fails

**📉 14-Day Time-Series**
- All 12 metrics normalised (0–1) and overlaid on one chart
- Shows historical trends as the simulation runs
- Click "Inject Failure Event" to trigger an ECC spike
""")
    with col_b:
        st.markdown("""
**🤖 LSTM Health Engine**
- Displays a health score gauge (0–100)
- Shows failure probability bar and estimated RUL in days
- Attention heatmap shows which metrics drove the prediction
- Two action buttons: retire a block proactively, or raise LDPC cap

**🔐 Security & OOB**
- Generate → encrypt → decrypt a diagnostic report (AES-256-GCM)
- Shamir Secret Sharing: split encryption key into 5 shares, reconstruct with any 3
- Three OOB channels: In-Band (NVMe), BLE beacon, UART emergency dump
""")

    st.success("💡 **Try this:** Set mode to *crash* in the sidebar → go to OOB tab → click 'KILL HOST → Trigger UART Dump' to see the emergency diagnostic channel activate.")

# ── Tab 2: Pillar 2 ───────────────────────────────────────────────────────────
with tab2:
    st.markdown("## 🗃️ Pillar 2 — NAND Block Management")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**🗺️ NAND Block Grid**
- 8×8 grid of 64 blocks, coloured by wear level
- 🟢 Green = fresh  |  🟡 Yellow = aging  |  🔴 Red = bad  |  🟣 Purple = retired
- Enter a block number and click "Inspect Block" for detailed diagnostics
- Shows P/E count, state, BBT lookup trace, Bloom/Cuckoo positions

**🔍 BBT Internals**
- **Bloom Filter** (Tier 1a): 256-bit probabilistic filter — eliminates most lookups instantly
- **Bitmap** (Tier 1b): 64-bit exact lookup using `byte = idx >> 3`, `bit = idx & 7`
- **Cuckoo Hash** (Tier 2): stores full metadata (reason, timestamp, P/E) for confirmed bad blocks
""")
    with col_b:
        st.markdown("""
**✍️ Write Burst Simulation**
- Click "Simulate Write Burst" to fire 10 write requests
- Each request shows the block selection trace, BBT check, and outcome
- Red border = write had to remap (bad block hit)

**⚠️ Wear Retirement Demo**
- Click "Fast-Forward Block 7" to run it to 2700 P/E cycles
- Watch Phase D: data copy → bitmap update → CRC persist → redundant BBT copy
- The CRC-32 hex dump shows the exact bytes written to flash
""")

    st.success("💡 **Try this:** Sidebar → Force Bad Block (any number) → watch that block turn red on the NAND grid and the bad-block count increment in Pillar 1's SMART feed.")

# ── Tab 3: Pillar 3 ───────────────────────────────────────────────────────────
with tab3:
    st.markdown("## 🛡️ Pillar 3 — Data Reliability & Error Correction")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**🔗 AEGIS Pipeline**
- Visual 5-stage diagram showing which tier is active
- Tier 1: Syndrome check — if zero, no error (fastest path)
- Tier 2a: BCH correction — single-burst errors
- Tier 2b: Hard LDPC — iterative bit-flip (8–20 iterations based on wear)
- Tier 3: Soft LDPC + ML voltage model — heavily worn blocks
- UECC: Unrecoverable — triggers CRITICAL anomaly in Pillar 1

**🧪 Syndrome Demo**
- Drag the slider to inject 0–4 errors into a valid codeword
- See the parity-check matrix H and synddrome vector s = H·r
- Zero syndrome = no errors; non-zero = caught
""")
    with col_b:
        st.markdown("""
**⚙️ LDPC Bit-Flip Trace**
- Set a P/E count → AURA auto-selects the LDPC iteration cap
- Step through each iteration with the slider
- Bar chart shows failed-check count per bit position
- Red bars = bits flipped in that iteration

**🔬 Voltage Shift Model (Tier 3)**
- Adjust P/E count, temperature, ECC history
- ML model predicts voltage threshold drift (ΔV in mV)
- Outputs: extra sense passes needed, recovery probability, estimated latency
""")

    st.success("💡 **Try this:** Set P/E count to 2700 (near end-of-life), enable Degraded Mode → observe the LDPC cap increase from 8 to 20 iterations to compensate for higher error rate.")

# ── Tab 4: Pillar 4 ───────────────────────────────────────────────────────────
with tab4:
    st.markdown("## ⚙️ Pillar 4 — Firmware Logic Optimization")
    st.info("Pillar 4 is **standalone** — it runs at firmware build time, not runtime. No simulation data needed here.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**🗂️ K-Map Minimization (4 variables)**
- Variables: A=bad_block, B=wear_limit, C=erase_fail, D=temp_critical
- Purple heatmap shows which input combinations trigger block retirement
- Before: 4 product terms, 11 literals → After: 3 terms, 6 literals
- BDD verification confirms the minimized form is logically identical

**What BDD verification means:**
- A Binary Decision Diagram is a canonical representation of a boolean function
- If two expressions produce the same BDD, they are provably equivalent
- AURA uses this to guarantee the optimized firmware has zero logic regressions
""")
    with col_b:
        st.markdown("""
**🔢 Quine-McCluskey (5+ variables)**
- Handles larger functions than K-maps can visualise
- Groups minterms by popcount, then iteratively combines adjacent groups
- Identifies prime implicants → Petrick's Method selects minimum cover
- Shows the full tabular reduction step by step

**Why does this matter?**
- Fewer gates = faster firmware startup, less ROM usage, lower power
- Every conditional in the block retirement / LDPC escalation logic has been minimized
- The 30–40% reduction is measured from actual gate-count, not estimated
""")

# ── Tab 5: Simulator Guide ────────────────────────────────────────────────────
with tab5:
    st.markdown("## 🎮 Using the Simulation")

    st.markdown("### Sidebar Controls (available on every page)")
    controls_data = [
        ("⚡ Speed slider", "1× / 5× / 20× / 100×", "How many 60-second ticks advance per click or auto-run cycle"),
        ("🎭 Mode", "normal / stress / aging / crash", "stress = high write load | aging = accelerated wear | crash = host dead"),
        ("🆕 Fresh preset", "Resets to new drive", "Very low wear, no bad blocks, high health score"),
        ("📀 Mid-Age preset", "~50% life used", "Some bad blocks, moderate wear — good for demonstrating LSTM"),
        ("🚨 Critical preset", "Near end of life", "High bad block count, LSTM shows CRITICAL anomaly"),
        ("💀 End-Life preset", "Maximum wear", "Most blocks retired, very low health score"),
        ("💥 Force Bad Block", "Block #0–63", "Instantly marks a block as bad — watch Pillar 1's health drop"),
        ("🌡️ Spike", "Thermal event", "Raises temperature metric, triggers anomaly detection"),
        ("⚡ Storm", "Write storm", "Spikes ECC rate and retry frequency"),
        ("💀 Kill Host", "Set crash mode", "Disables in-band channel — demonstrates BLE+UART OOB fallback"),
        ("▶ Auto Run", "Toggle", "Advances simulation continuously — watch metrics evolve live"),
        ("⟳ Tick Once", "Manual advance", "Advance exactly 1 tick (× Speed value) at your own pace"),
    ]
    import pandas as pd
    df = pd.DataFrame(controls_data, columns=["Control", "Values", "Effect"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Recommended Demo Flow")
    st.markdown("""
1. **Homepage** — Read the architecture diagram. Understand Pillar 1 is the brain.
2. **Set Mid-Age preset** (sidebar) — gives interesting live data immediately.
3. **Pillar 1** — See the health score, LSTM gauge, and SMART metrics all live.
4. **Force Bad Block #20** (sidebar) — watch the bad-block count jump and health score drop.
5. **Pillar 2** — See block 20 turn red on the grid. Click "Inspect Block 20" for BBT lookup trace.
6. **Pillar 3** — Inject 2 errors via the syndrome slider. Watch the LDPC trace correct them.
7. **Pillar 1 → LSTM section** — Click "LSTM → Raise LDPC Cap" — Pillar 1 commands Pillar 3.
8. **Pillar 4** — See the K-map heatmap and the 42% logic cost reduction.
9. **Pillar 1 → Security** — Generate a report, encrypt it, split with Shamir, reconstruct.
10. **Set crash mode → OOB tab → UART dump** — demonstrates the tamper-proof fallback.
""")

    st.success("**Total demo time:** ~8–10 minutes following the above flow.")

    st.markdown("---")
    st.markdown("### Glossary")
    gloss = [
        ("SMART", "Self-Monitoring Analysis and Reporting Technology — standardised drive health attributes"),
        ("LSTM", "Long Short-Term Memory — a recurrent neural network for time-series prediction"),
        ("RUL", "Remaining Useful Life — estimated days until the drive becomes unreliable"),
        ("RBER", "Raw Bit Error Rate — proportion of bits read incorrectly before ECC"),
        ("P/E Cycle", "Program/Erase cycle — one write+erase cycle wears NAND flash slightly"),
        ("BBT", "Bad Block Table — data structure tracking which NAND blocks have failed"),
        ("LDPC", "Low-Density Parity-Check code — iterative error correction algorithm"),
        ("BCH", "Bose-Chaudhuri-Hocquenghem code — algebraic error correction for burst errors"),
        ("UECC", "Uncorrectable ECC error — all ECC tiers exhausted, data unrecoverable"),
        ("OOB", "Out-Of-Band — communication channel independent of the main host interface"),
        ("AES-256-GCM", "256-bit AES in Galois/Counter Mode — authenticated encryption"),
        ("Shamir Secret Sharing", "Cryptographic scheme to split a secret into N shares, recoverable with any K"),
        ("K-map", "Karnaugh map — visual grouping method for Boolean function minimization"),
        ("QMC", "Quine-McCluskey — tabular algorithm for minimizing Boolean functions"),
        ("BDD", "Binary Decision Diagram — canonical data structure for proving logical equivalence"),
    ]
    df_gloss = pd.DataFrame(gloss, columns=["Term", "Definition"])
    st.dataframe(df_gloss, use_container_width=True, hide_index=True)
