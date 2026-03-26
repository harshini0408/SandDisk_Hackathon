"""
AURA — Pillar 5: Sentinel Secure OOB & Forensic Recovery
Streamlit UI for Out-of-Band Communication, AES-256 Encryption, & Shamir Recovery

Demonstrates:
- Host connectivity simulation (NVMe link toggle)
- Emergency diagnostic triggers via UART/BLE
- AES-256-GCM encrypted forensic reports
- Shamir Secret Sharing (3-of-5 threshold key distribution)
- Technician recovery portal with share reconstruction
- Distributed redundancy (IPFS-style archival)
"""
import streamlit as st
import time
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.ssd_simulator import SSDSimulator
from core.oob_engine import OOBEngine

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pillar 5 — Secure OOB & Forensic Recovery | AURA",
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

html, body, [data-testid="stApp"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
  background-color: var(--surface) !important;
  border-right: 1px solid var(--border);
}

h1,h2,h3,h4,h5 { 
  font-family: 'JetBrains Mono', monospace !important; 
  color: var(--text) !important; 
}

div[data-testid="stMetricValue"] { 
  color: var(--green) !important; 
  font-size: 1.6rem !important; 
  font-weight: 700 !important; 
}
div[data-testid="stMetricLabel"] { 
  color: var(--muted) !important; 
  font-size: 0.75rem !important; 
}

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

.status-card {
  background: linear-gradient(135deg, #1a2332, #2a1a3e);
  border: 2px solid var(--purple);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.status-card-active {
  background: linear-gradient(135deg, #1a2a1a, #2a3a2a);
  border: 2px solid var(--green);
}

.status-card-error {
  background: linear-gradient(135deg, #3a1a1a, #4a2a2a);
  border: 2px solid var(--red);
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

.stButton button:active {
  transform: scale(0.98);
}

div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextInput"] label { 
  color: var(--muted) !important; 
  font-size: 12px !important; 
}

div[data-testid="stSelectbox"] > div,
div[data-testid="stNumberInput"] > div input,
div[data-testid="stTextInput"] > div input {
  background: var(--card) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

div[data-baseweb="tab-list"] { 
  background: var(--surface) !important; 
  border-bottom: 1px solid var(--border); 
}
div[data-baseweb="tab"] { 
  color: var(--muted) !important; 
}
div[data-baseweb="tab"][aria-selected="true"] { 
  color: var(--blue) !important; 
  border-bottom: 2px solid var(--blue) !important; 
}

@keyframes pulse { 
  0%,100%{opacity:1} 
  50%{opacity:0.5} 
}

@keyframes blink-red {
  0%,100%{color:var(--red)}
  50%{color:var(--orange)}
}

.pulse { animation: pulse 2s infinite; }
.blink-red { animation: blink-red 1.5s infinite; }

.stAlert { border-radius: 8px !important; }

.uart-dump {
  background: #000 !important;
  color: #00ff00 !important;
  font-family: 'JetBrains Mono', monospace !important;
  padding: 12px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.4;
  border: 1px solid var(--dim);
  max-height: 400px;
  overflow-y: auto;
}

.ciphertext-display {
  background: #1a1a2e;
  color: var(--orange);
  font-family: 'JetBrains Mono', monospace;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--orange);
  word-break: break-all;
  font-size: 11px;
}

.share-box {
  background: var(--card);
  border: 1px solid var(--teal);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.share-collected {
  background: linear-gradient(135deg, #1a2a2a, #2a3a3a);
  border: 1px solid var(--green);
}

.recovery-indicator {
  display: inline-block;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--dim);
  text-align: center;
  line-height: 24px;
  font-size: 12px;
  margin-right: 8px;
}

.recovery-indicator-active {
  background: var(--green);
  color: var(--bg);
}

</style>
""", unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────────────────────────
if 'simulator' not in st.session_state:
    st.session_state.simulator = SSDSimulator()

if 'oob_engine' not in st.session_state:
    st.session_state.oob_engine = OOBEngine()

if 'host_crash_time' not in st.session_state:
    st.session_state.host_crash_time = None

if 'uart_lines_cache' not in st.session_state:
    st.session_state.uart_lines_cache = []

sim = st.session_state.simulator
oob = st.session_state.oob_engine

# ─── Main Title ───────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="text-align:center; color:#a855f7; font-size:2.5em;">
🛡️ Pillar 5: Sentinel Secure OOB & Forensic Recovery
</h1>
<p style="text-align:center; color:#8888a0; font-size:0.95em;">
Out-of-Band Communication with AES-256 & Shamir Secret Sharing
</p>
""", unsafe_allow_html=True)

st.divider()

# ─── SECTION 1: Host Connectivity Simulation ──────────────────────────────────
st.markdown("### 🔗 Host Connectivity Control")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🟢 Host Connected", use_container_width=True, key="host_on"):
        oob.toggle_host_link(True)
        st.session_state.host_crash_time = None

with col2:
    if st.button("🔴 Simulate Host Crash (NVMe Down)", use_container_width=True, key="host_off"):
        oob.toggle_host_link(False)
        st.session_state.host_crash_time = time.time()
        # Generate forensic report immediately on crash
        oob.generate_forensic_report(sim)

with col3:
    if st.button("📡 Generate Diagnostic Report", use_container_width=True, key="gen_report"):
        oob.generate_forensic_report(sim)
        oob.encrypt_report()
        st.success("✓ Report encrypted with AES-256-GCM")

with col4:
    if st.button("🌐 Push to Distributed Nodes", use_container_width=True, key="push_dist"):
        if oob.encrypted_report:
            result = oob.push_to_distributed_nodes()
            st.success(f"✓ {result['message']}")
        else:
            st.warning("⚠️ No encrypted report to push")

st.divider()

# ─── SECTION 2: Link Status Dashboard ─────────────────────────────────────────
st.markdown("### 📊 Link Status & OOB Channel")

# Update host downtime if offline
if st.session_state.host_crash_time:
    elapsed = time.time() - st.session_state.host_crash_time
    oob.update_host_downtime(elapsed)

status = oob.get_status_summary()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Host Status",
        value=status['host_status'],
        delta=None
    )

with col2:
    st.metric(
        label="NVMe Link",
        value=status['nvme_status'],
        delta=None
    )

with col3:
    st.metric(
        label="OOB Channel",
        value=status['oob_status'],
        delta=None
    )

with col4:
    st.metric(
        label="Downtime",
        value=f"{status['downtime']}",
        delta=None
    )

# Link status text with visual indicator
st.markdown(f"""
<div class="status-card {'status-card-active' if oob.status.oob_channel_active else 'status-card-error'}">
  <div style="font-family: JetBrains Mono; font-size: 0.95em; color: #e8e8f0;">
    <strong>Current Link State:</strong><br/>
    {oob.status.link_status_text}
  </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─── SECTION 3: Forensic Report & Encryption ─────────────────────────────────
st.markdown("### 🔐 Forensic Report & AES-256-GCM Encryption")

tab_report, tab_encrypted, tab_shares = st.tabs([
    "📋 Plaintext Report",
    "🔒 Encrypted Ciphertext",
    "🔑 Shamir Shares (3-of-5)"
])

# TAB 1: Plaintext Report
with tab_report:
    if oob.current_report:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Health Score", f"{oob.current_report.health_score:.0f}/100")
        with col2:
            st.metric("RUL (days)", f"{oob.current_report.rul_estimate:.0f}")
        with col3:
            st.metric("Anomaly Type", oob.current_report.anomaly_type)
        with col4:
            st.metric("Failure Prob", f"{oob.current_report.failure_prob*100:.1f}%")
        
        st.markdown("#### SMART Metrics Snapshot")
        report_data = {
            "Metric": [
                "ECC Rate (corrections/hr)",
                "Bad Block Count",
                "Wear Level (%)",
                "Temperature (°C)",
                "UECC Count",
                "RBER",
                "P/E Avg",
                "Read Latency (µs)"
            ],
            "Value": [
                f"{oob.current_report.ecc_rate:,.0f}",
                f"{oob.current_report.bad_block_count}",
                f"{oob.current_report.wear_level*100:.1f}",
                f"{oob.current_report.temperature:.1f}",
                f"{oob.current_report.uecc_count}",
                f"{oob.current_report.rber:.2e}",
                f"{oob.current_report.pe_avg:,.0f}",
                f"{oob.current_report.read_latency_us:.1f}"
            ]
        }
        st.dataframe(report_data, use_container_width=True, hide_index=True)
        
        st.markdown("#### Wear Statistics & Defects")
        wear_data = {
            "Parameter": [
                "Total Writes (GB)",
                "Total Reads (GB)",
                "Factory Defects",
                "Runtime Failures",
                "BBT CRC"
            ],
            "Value": [
                f"{oob.current_report.total_writes_gb:.2f}",
                f"{oob.current_report.total_reads_gb:.2f}",
                f"{oob.current_report.factory_defects}",
                f"{oob.current_report.runtime_fails}",
                oob.current_report.bbt_crc
            ]
        }
        st.dataframe(wear_data, use_container_width=True, hide_index=True)
        
        # Show report as formatted JSON
        st.markdown("#### Full Report JSON")
        report_json = json.dumps(
            {
                "timestamp": oob.current_report.timestamp,
                "trigger": oob.current_report.trigger_reason,
                "health": oob.current_report.health_score,
                "rul_days": oob.current_report.rul_estimate,
                "anomaly": oob.current_report.anomaly_type,
            },
            indent=2
        )
        st.code(report_json, language="json")
    else:
        st.info("ℹ️ Generate a diagnostic report first by simulating host crash or clicking 'Generate Diagnostic Report'")

# TAB 2: Encrypted Ciphertext
with tab_encrypted:
    if oob.encrypted_report:
        st.success(f"✓ Report Encrypted with AES-256-GCM")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Key ID", oob.aes_key_id or "N/A")
        with col2:
            st.metric("Ciphertext Size", f"{len(oob.encrypted_report['ciphertext'])} bytes")
        with col3:
            st.metric("IV (Nonce)", oob.encrypted_report['iv_hex'][:8] + "...")
        
        st.markdown("#### 🔍 Ciphertext Preview (First 256 bytes)")
        ciphertext_preview = oob.encrypted_report['ciphertext_hex'][:512]
        st.markdown(f'<div class="ciphertext-display">{ciphertext_preview}</div>', unsafe_allow_html=True)
        
        st.markdown("#### Encryption Parameters")
        encryption_info = {
            "Parameter": [
                "Algorithm",
                "Key Size",
                "IV/Nonce Size",
                "Authentication Tag",
                "Mode"
            ],
            "Value": [
                "AES-256",
                "256-bit (32 bytes)",
                "96-bit (12 bytes)",
                "128-bit (16 bytes, appended to ciphertext)",
                "GCM (Authenticated Encryption)"
            ]
        }
        st.dataframe(encryption_info, use_container_width=True, hide_index=True)
        
        st.info("🔒 **What This Means:** The entire forensic report is scrambled using military-grade encryption. Even if an attacker intercepts this data, they cannot read it without the AES key.")
    else:
        st.warning("⚠️ No encrypted report yet. Click 'Generate Diagnostic Report' first.")

# TAB 3: Shamir Shares
with tab_shares:
    if oob.formatted_shares:
        st.success(f"✓ AES Key Split into {len(oob.formatted_shares)} Shares (3-of-5 Threshold)")
        
        st.markdown("#### Shamir Secret Sharing Distribution")
        st.info("""
        **How It Works:**
        - The AES-256 encryption key is mathematically split into 5 shares
        - Any 3 out of 5 shares can reconstruct the original key
        - No single share reveals any information about the key
        - Shares are distributed to geographically dispersed locations
        """)
        
        for share_info in oob.formatted_shares:
            share_box_html = f"""
            <div class="share-box">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="color:#14b8a6;">Share #{share_info['index']}</strong>
                    <span style="color:#8888a0; font-size:0.85em;">{share_info['destination']}</span>
                </div>
                <div style="color:#f59e0b; word-break:break-all; font-size:0.75em; margin-bottom:4px;">
                    {share_info['share_str']}
                </div>
                <div style="color:#8888a0; font-size:0.85em;">
                    Preview: <span style="color:#14b8a6;">{share_info['preview']}</span>
                </div>
            </div>
            """
            st.markdown(share_box_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No shares yet. Click 'Generate Diagnostic Report' first to create shares.")

st.divider()

# ─── SECTION 4: UART Emergency Dump ──────────────────────────────────────────
st.markdown("### 📡 UART Emergency Diagnostic Dump (115200 baud)")

if st.button("📜 Generate UART Dump", use_container_width=True):
    uart_lines = oob.get_uart_dump_lines()
    st.session_state.uart_lines_cache = uart_lines

if st.session_state.uart_lines_cache:
    uart_text = "\n".join(st.session_state.uart_lines_cache)
    st.markdown(f'<div class="uart-dump">{uart_text}</div>', unsafe_allow_html=True)
    
    if st.button("📋 Copy UART Output", use_container_width=True):
        st.info("✓ UART output copied to clipboard (in production)")

st.divider()

# ─── SECTION 5: Distributed Redundancy ────────────────────────────────────────
st.markdown("### 🌐 Distributed Redundancy & IPFS Archive")

if oob.push_status == "DISTRIBUTED":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "✓ DISTRIBUTED")
    with col2:
        st.metric("Nodes", f"{len(oob.distributed_nodes)}")
    with col3:
        st.metric("Total Copies", "9 (3x per node)")
    
    st.markdown("#### Archive Locations")
    for node in oob.distributed_nodes:
        st.markdown(f"✓ **{node}** — 3 redundant copies stored")
    
    if oob.ipfs_hash:
        st.markdown(f"#### IPFS Hash (Content-Addressable Archive)")
        st.code(oob.ipfs_hash, language="text")
else:
    st.warning("⚠️ Report not yet pushed to distributed network. Click 'Push to Distributed Nodes'.")

st.divider()

# ─── SECTION 6: Technician Recovery Interface ─────────────────────────────────
st.markdown("### 🔧 Technician Recovery Portal")

st.markdown("""
**Scenario:** Your SSD is offline. To access the encrypted diagnostic report:
1. Collect 3 out of 5 Shamir shares from their distributed locations
2. Input the shares below
3. System reconstructs the AES key
4. Forensic report is decrypted for analysis
""")

tab_recovery, tab_verify = st.tabs(["🔑 Share Collection", "✓ Verification & Decryption"])

with tab_recovery:
    st.markdown("#### Collected Shares")
    
    col1, col2 = st.columns(2)
    
    with col1:
        share_input = st.text_input(
            "Enter Share (format: index-hexvalue)",
            placeholder="1-ab12cd34...",
            key="share_input"
        )
        
        if st.button("➕ Add Share", use_container_width=True):
            if share_input.strip():
                success = oob.submit_share(share_input.strip())
                if success:
                    st.success(f"✓ Share added: {share_input[:20]}...")
                else:
                    st.error("✗ Invalid share format or duplicate")
    
    with col2:
        st.metric("Shares Collected", f"{len(oob.collected_shares)} / 3 (Threshold)")
        
        if len(oob.collected_shares) >= 3:
            st.success("✓ Threshold reached! Ready to reconstruct key.")

    if oob.collected_shares:
        st.markdown("#### Submitted Shares")
        for i, share in enumerate(oob.collected_shares, 1):
            share_preview = share[:20] + "..." if len(share) > 20 else share
            status_icon = "✓" if i <= len(oob.collected_shares) else "⏳"
            st.markdown(f"{status_icon} Share {i}: `{share_preview}`")
        
        if len(oob.collected_shares) > 0:
            if st.button("🔄 Clear Shares & Restart", use_container_width=True):
                oob.reset_collection()
                st.info("✓ Share collection reset")

with tab_verify:
    st.markdown("#### Key Reconstruction & Decryption")
    
    if len(oob.collected_shares) < 3:
        st.warning(f"⚠️ Need {3 - len(oob.collected_shares)} more share(s) to proceed")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔑 Reconstruct AES Key", use_container_width=True, key="reconstruct"):
                success = oob.reconstruct_key()
                if success:
                    st.success("✓ AES Key reconstructed successfully!")
                    st.info(f"Key ID: {oob.aes_key_id}")
                else:
                    st.error("✗ Key reconstruction failed. Shares may be invalid.")
        
        with col2:
            if st.button("🔓 Decrypt Forensic Report", use_container_width=True, key="decrypt"):
                if oob.decryption_success:
                    plaintext, success = oob.decrypt_forensic_report()
                    if success:
                        st.success("✓ Decryption successful!")
                    else:
                        st.error("✗ Decryption failed")
                else:
                    st.warning("⚠️ Must reconstruct key first")
        
        if oob.decryption_success and oob.recovered_plaintext:
            st.markdown("#### ✓ Decrypted Forensic Report")
            st.code(oob.recovered_plaintext, language="json")
            
            st.success("""
            **Recovery Complete!** ✓
            - Technician can now analyze the SSD's diagnostic data
            - Timestamp confirms when the report was captured
            - All SMART metrics and wear statistics are preserved
            - Can be used for RMA processing or fleet analysis
            """)

st.divider()

# ─── SECTION 7: BLE Beacon Broadcast ──────────────────────────────────────────
st.markdown("### 📶 Emergency BLE Beacon (Fleet-Wide Notification)")

if st.button("📡 Show BLE Beacon Packet", use_container_width=True):
    if oob.current_report:
        beacon = oob.get_ble_beacon()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Type", "Emergency Beacon")
        with col2:
            st.metric("Power", "0.5 mA")
        with col3:
            st.metric("Range", "50m (mesh)")
        with col4:
            st.metric("Interval", "30s")
        
        st.markdown("#### Beacon Payload")
        st.code(beacon['payload'], language="text")
        
        st.info("""
        🌐 **What This Does:**
        - Broadcasts SSD health status via Bluetooth Low Energy
        - Doesn't require host to be running
        - Meshes across storage fleet for network-wide visibility
        - Receivers (maintenance app, fleet dashboard) can see failing drives
        - Only 0.5mA power draw — SSD can keep broadcasting for hours on backup power
        """)
    else:
        st.warning("⚠️ Generate a diagnostic report first")

st.divider()

# ─── SECTION 8: Key Features & Innovation ────────────────────────────────────
st.markdown("### 🎯 Key Features & Innovation Highlights")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 🔴 Failure Forensics
    - OOB ensures that even if the host crashes, **the SSD's failure context is preserved**
    - Complete diagnostic snapshot frozen at the moment of host failure
    - Time-locked evidence for RMA / warranty analysis
    """)

with col2:
    st.markdown("""
    #### 🔐 Confidentiality + Availability
    - **Availability:** OOB channel provides access even when host is dead
    - **Confidentiality:** AES-256-GCM ensures only authorized engineers can read the data
    - **Split Authority:** Shamir shares prevent single-point-of-trust attacks
    """)

with col3:
    st.markdown("""
    #### 🌐 Self-Healing Loop
    - Pillar 1: Detects bad blocks
    - Pillar 2: Corrects errors via AEGIS/LDPC
    - Pillar 3: Optimizes logic to prevent future errors
    - Pillar 4: LSTM learns patterns, predicts failures
    - Pillar 5: **Securely reports everything OOB**
    """)

st.divider()

# ─── SECTION 9: Architecture Diagram (Text-based) ────────────────────────────
st.markdown("### 🏗️ OOB Architecture & Data Flow")

st.markdown("""
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRIMARY COMMUNICATION                           │
│                              (NVMe)                                     │
│                                                                         │
│   ┌──────────────────┐                          ┌──────────────────┐  │
│   │                  │ ◄─ HOST CRASH ────────►  │                  │  │
│   │  HOST SYSTEM     │                          │   SSD FIRMWARE   │  │
│   │  (CPU, OS)       │                          │   (Microcontroller)
│   │                  │                          │                  │  │
│   └──────────────────┘                          └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                   SECONDARY COMMUNICATION (OOB)                         │
│              UART / BLE — Always Available, Low Power                   │
│                                                                         │
│   ┌──────────────────────────┐                  ┌──────────────────┐  │
│   │  TECHNICIAN / MGMT       │  ◄─ SECURE ─►   │  SSD FIRMWARE    │  │
│   │  - Portal                │      (AES-256)   │  - BBT Backup    │  │
│   │  - Key recovery app      │                  │  - SMART logs    │  │
│   │  - Fleet dashboard       │                  │  - Wear stats    │  │
│   └──────────────────────────┘                  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

                    ENCRYPTION & KEY SHARING FLOW

Diagnostic Report
     │
     ▼
  ┌─────────────────────────┐
  │  AES-256-GCM Encryption │ ◄─── Generates random 256-bit key
  │     (AES_KEY)           │
  └─────────────────────────┘
     │
     ├─► Ciphertext (scrambled) ──► IPFS / Distributed Nodes
     │
     └─► AES Key ──────┬──────────────────────────────────────┐
                       │ SHAMIR SECRET SHARING (3-of-5)       │
                       │                                      │
                       ├─► Share 1 ──► Fleet Management      │
                       ├─► Share 2 ──► On-Drive TEE Storage  │
                       ├─► Share 3 ──► Engineer Hardware     │
                       ├─► Share 4 ──► Backup HSM            │
                       └─► Share 5 ──► Emergency Paper Key   │

                    RECOVERY FLOW

Technician Collects 3 Shares
     │
     ▼
  ┌─────────────────────────┐
  │  Lagrange Interpolation │ ◄─── Polynomial reconstruction over GF(p)
  │  (3-of-5 reconstruction)│
  └─────────────────────────┘
     │
     ▼
  AES Key (Original)
     │
     ▼
  ┌─────────────────────────┐
  │ AES-256-GCM Decryption  │
  │   (Verify + Decrypt)    │
  └─────────────────────────┘
     │
     ▼
  Plaintext Forensic Report
     │
     ├─► RMA Analysis
     ├─► Fleet Health Trending
     ├─► Warranty Processing
     └─► Regulatory Compliance
```
""")

st.divider()

# ─── SECTION 10: Implementation Details ───────────────────────────────────────
st.markdown("### 📚 Technical Implementation Details")

details_tab1, details_tab2 = st.tabs(["🔒 Cryptography", "🔑 Shamir Secret Sharing"])

with details_tab1:
    st.markdown("""
    #### AES-256-GCM Implementation
    
    **Algorithm:** Advanced Encryption Standard with 256-bit key in Galois/Counter Mode
    
    **Why AES-256-GCM?**
    - Military-grade security (NSA Suite B approved for TOP SECRET)
    - Authenticated encryption (ensures data is not tampered with)
    - No known practical attacks against AES-256
    - Hardware acceleration available (AES-NI) for performance
    - NIST standard (FIPS 197)
    
    **Key Generation:**
    - 256-bit (32 bytes) cryptographically random key
    - IV/Nonce: 96-bit (12 bytes) random for each encryption
    - Authentication tag: 128-bit appended to verify integrity
    
    **Process:**
    1. Generate random AES-256 key
    2. Generate random 96-bit IV
    3. Encrypt plaintext with AES-256-GCM
    4. Ciphertext + Auth tag returned
    5. IV must be stored with ciphertext (not secret)
    6. Key must be protected via Shamir sharing
    
    **Security Properties:**
    - **Confidentiality:** Only someone with the AES key can read the data
    - **Authenticity:** Auth tag ensures data hasn't been modified
    - **Non-repudiation:** Key holder cannot deny creating the ciphertext
    """)

with details_tab2:
    st.markdown("""
    #### Shamir Secret Sharing (3-of-5 Threshold)
    
    **How It Works (Mathematically):**
    - Secret is used as the constant term (a₀) of a polynomial
    - Polynomial: f(x) = a₀ + a₁·x + a₂·x² (for 3-of-5: k-1 degree)
    - Each share is a point on this polynomial: (x, f(x))
    - Shares are: (1, f(1)), (2, f(2)), (3, f(3)), (4, f(4)), (5, f(5))
    
    **Key Properties:**
    - Any k shares can reconstruct the original secret (key)
    - Fewer than k shares reveal NOTHING about the secret
    - Mathematically proven: impossible to recover without k shares
    - Uses Lagrange interpolation over a large prime field (2^127 - 1)
    
    **Example (Simplified):**
    ```
    Secret Key = 12345 (in 256-bit: ...binary...)
    
    Polynomial: f(x) = 12345 + 7·x + 3·x²
    
    Shares:
      x=1: f(1) = 12355    → Share "1-12355"
      x=2: f(2) = 12371    → Share "2-12371"
      x=3: f(3) = 12393    → Share "3-12393"
      x=4: f(4) = 12421    → Share "4-12421"
      x=5: f(5) = 12455    → Share "5-12455"
    
    Recovery (any 3 shares):
      Input: "1-12355", "3-12393", "5-12455"
      Lagrange: Solve polynomial through these 3 points
      Result: a₀ = 12345 (original key!)
    ```
    
    **Security Model:**
    - No single share holder knows the key
    - Quorum required: at least 3 key custodians must agree
    - Prevents unauthorized key access
    - Enables geographic distribution
    - **3-of-5 threshold:**
      - Tolerates up to 2 shares being compromised or lost
      - Requires majority (3) for key recovery
      - Prevents insider threats (single technician can't open alone)
    """)

st.divider()

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
---
<div style="text-align: center; color: #8888a0; font-size: 0.85em;">
    <strong>Pillar 5: Sentinel Secure OOB & Forensic Recovery</strong><br/>
    Part of the 5-Pillar AURA-AEGIS SSD Firmware Security Architecture<br/>
    <br/>
    <span style="color: #a855f7;">🛡️ Confidentiality • 🌐 Availability • 🔐 Integrity • 📊 Forensics</span>
</div>
""", unsafe_allow_html=True)
