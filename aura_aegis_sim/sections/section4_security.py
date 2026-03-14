"""Section 4: Security + OOB Diagnostics + Pillar 3 Logic Optimization"""
import streamlit as st
import json
import time
from datetime import datetime, timezone
from crypto.aes_layer import encrypt_report, decrypt_report
from crypto.shamir_layer import split_secret, reconstruct_secret, format_shares_for_display
from oob.uart_simulator import generate_uart_dump, generate_ble_packet
from core.kmap_qmc_engine import (
    kmap_grid, BEFORE_EXPR, AFTER_EXPR, cost_before, cost_after,
    bdd_verify_equivalent, qmc_ldpc_demo, qmc_minimize,
    RETIREMENT_MINTERMS, LDPC_ESCALATION_MINTERMS,
)
import plotly.graph_objects as go


def _build_report(sim) -> dict:
    snap = sim.get_latest_smart()
    retired = [(i, b.fail_reason, b.pe_count)
               for i, b in enumerate(sim.blocks)
               if b.state == 'RETIRED' and b.fail_reason in ('WEAR_RETIREMENT', 'PREDICTIVE_RETIREMENT')]
    return {
        "drive_id": "AURA-AEGIS-UNIT-7",
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "health_score": round(sim.health_score, 1),
        "failure_probability": round(sim.failure_prob, 3),
        "rul_days": round(sim.rul_days, 1),
        "bad_blocks": int(sum(1 for b in sim.blocks if b.state in ('BAD', 'RETIRED'))),
        "ecc_corrections_24h": sim.ecc_corrections,
        "uecc_count": sim.uecc_count,
        "avg_pe_count": round(sim._avg_pe(), 0),
        "wear_level": round(sim._wear_level() * 100, 1),
        "rber": float(f"{sim._compute_rber():.2e}"),
        "temperature_peak": round(sim.temperature, 1),
        "anomaly_type": sim.anomaly_type,
        "retirement_events": [{"block": i, "reason": r, "pe": pe} for i, r, pe in retired[:5]],
    }


def render_crypto_section(sim):
    st.markdown("#### 🔐 Diagnostic Report + AES-256-GCM Encryption")

    if st.button("📄 Generate Diagnostic Report", key="gen_report_btn"):
        report = _build_report(sim)
        encrypted = encrypt_report(report)
        st.session_state['report'] = report
        st.session_state['encrypted'] = encrypted
        st.session_state['shares'] = split_secret(encrypted['key'], k=3, n=5)

    if 'report' in st.session_state:
        col_plain, col_cipher = st.columns(2)
        with col_plain:
            st.markdown("**🔓 PLAINTEXT** — readable by anyone")
            st.json(st.session_state['report'])
        with col_cipher:
            enc = st.session_state['encrypted']
            st.markdown("**🔒 CIPHERTEXT** — AES-256-GCM")
            st.markdown(f"""
<div style="background:#0a0a0f;border:1px solid #2a2a3a;padding:10px;border-radius:6px;font-family:monospace;font-size:11px">
<span style="color:#8888a0">Key (256-bit):</span><br>
<span style="color:#f59e0b">{enc['key_hex'][:32]}...</span><br><br>
<span style="color:#8888a0">IV (96-bit):</span><br>
<span style="color:#3b82f6">{enc['iv_hex']}</span><br><br>
<span style="color:#8888a0">Ciphertext (first 64 bytes):</span><br>
<span style="color:#ef4444">{enc['ciphertext_preview']}</span><br>
<span style="color:#4a4a60">...random noise to an attacker</span>
</div>
""", unsafe_allow_html=True)

        if st.button("🔓 Decrypt & Verify Integrity", key="decrypt_btn"):
            enc = st.session_state['encrypted']
            plaintext, ok = decrypt_report(enc['ciphertext'], enc['key'], enc['iv'])
            if ok:
                st.success("✅ Authentication tag verified. Data integrity confirmed.")
                st.code(plaintext[:500], language='json')
            else:
                st.error(plaintext)


def render_shamir_section():
    st.markdown("#### 🔑 Shamir Secret Sharing (3-of-5 threshold)")
    if 'shares' not in st.session_state:
        st.info("Generate a report first to create shares.")
        return

    shares = st.session_state['shares']
    share_info = format_shares_for_display(shares)

    cols = st.columns(5)
    for c, info in zip(cols, share_info):
        c.markdown(f"""
<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:8px;padding:8px;text-align:center">
  <div style="color:#a855f7;font-size:20px;font-weight:bold">#{info['index']}</div>
  <div style="color:#8888a0;font-size:9px">{info['destination']}</div>
  <div style="font-family:monospace;font-size:9px;color:#4a4a60;margin-top:4px">{info['preview']}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("**Reconstruct key — select any 3 shares:**")
    selected = st.multiselect("Select shares (need exactly 3):",
                              [f"Share {i+1}" for i in range(5)], key="shamir_sel",
                              max_selections=5)
    selected_indices = [int(s.split()[1]) - 1 for s in selected]

    if st.button("🔓 Reconstruct Key", key="reconstruct_btn"):
        if len(selected_indices) < 3:
            st.error("⚠️ Insufficient shares. Minimum 3 required.")
        else:
            chosen = [shares[i] for i in selected_indices[:3]]
            enc = st.session_state.get('encrypted')
            if enc:
                try:
                    key_len = len(enc['key'])
                    reconstructed = reconstruct_secret(chosen, key_len=key_len)
                    match = reconstructed == enc['key']
                    if match:
                        st.success(f"✅ Key reconstructed: `{reconstructed.hex()[:32]}...`")
                        st.success("🔒 Matches original AES key exactly.")
                    else:
                        st.error("Key mismatch — reconstruction failed.")
                except Exception as e:
                    st.error(f"Reconstruction error: {e}")


def render_oob_section(sim):
    st.markdown("#### 📡 OOB Communication Channels")
    tab_inband, tab_ble, tab_uart = st.tabs(["In-Band (NVMe)", "BLE Beacon", "UART Emergency"])

    with tab_inband:
        is_crash = sim.mode == 'crash'
        status_color = '#ef4444' if is_crash else '#22c55e'
        status_text = '✗ HOST DOWN' if is_crash else '✓ ACTIVE'
        st.markdown(f"""
<div style="background:#1a1a26;border:1px solid #2a2a3a;padding:14px;border-radius:8px;font-family:monospace">
<b style="color:#e8e8f0">In-Band NVMe/PCIe x4</b><br>
Status: <b style="color:{status_color}">{status_text}</b><br>
{"<span style='color:#ef4444'>⚠️ Host unresponsive — falling back to OOB channels</span>" if is_crash else
f"<span style='color:#22c55e'>Alert sent: {{health_score: {sim.health_score:.0f}, action: SCHEDULE_MIGRATION}}</span><br><span style='color:#22c55e'>Dashboard update: ✓</span>"}</div>
""", unsafe_allow_html=True)

    with tab_ble:
        pkt = generate_ble_packet(sim)
        st.markdown(f"""
<div style="background:#1a1a26;border:1px solid #2a2a3a;padding:14px;border-radius:8px;font-family:monospace">
<b style="color:#3b82f6">BLE Beacon</b>
<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;margin-left:6px;animation:pulse 1s infinite"></span><br>
Status: <b style="color:#3b82f6">BROADCASTING (every {pkt['interval_s']}s)</b><br>
Packet ({pkt['length_bytes']} bytes):<br>
<span style="color:#e8e8f0">{pkt['payload']}</span><br>
Recipient: {pkt['device']}<br>
Signal: {pkt['rssi_dbm']} dBm<br>
<span style="color:#4a4a60">Host CPU involvement: ZERO. No PCIe bus required.</span>
</div>
""", unsafe_allow_html=True)

    with tab_uart:
        if st.button("💀 KILL HOST → Trigger UART Dump", key="kill_host_btn"):
            sim.kill_host()
            st.session_state['uart_lines'] = generate_uart_dump(sim)
            st.session_state['uart_idx'] = 0

        if 'uart_lines' in st.session_state:
            visible = st.session_state.get('uart_idx', len(st.session_state['uart_lines']))
            lines_to_show = st.session_state['uart_lines'][:visible + 1]
            term_html = '<br>'.join(
                f'<span style="color:#22c55e">{line}</span>' for line in lines_to_show
            )
            st.markdown(f'<div style="background:#0a0a0f;border:1px solid #22c55e;padding:14px;border-radius:6px;font-family:monospace;font-size:11px;height:280px;overflow-y:auto">{term_html}</div>', unsafe_allow_html=True)

            if st.button("▶ Scroll next line", key="uart_scroll"):
                if st.session_state['uart_idx'] < len(st.session_state['uart_lines']) - 1:
                    st.session_state['uart_idx'] += 1
                    st.rerun()


def render_kmap_section():
    st.markdown("#### 🗂️ Pillar 3 — Logic Optimization Proof (K-map / QMC)")
    tab_kmap, tab_qmc = st.tabs(["4-Variable K-Map", "QMC 5-Variable Demo"])

    with tab_kmap:
        st.markdown(f"""
**Variables:** A=bad_block, B=wear_limit, C=erase_fail, D=temp_critical

| | **BEFORE** | **AFTER** |
|---|---|---|
| Expression | `{BEFORE_EXPR}` | `{AFTER_EXPR}` |
| Product terms | 4 | 3 |
| Literals | 11 | 6 |
| BDD verified | — | ✅ IDENTICAL |
""")
        cb = cost_before()
        ca = cost_after()
        saving_pct = (cb['cost'] - ca['cost']) / cb['cost'] * 100
        st.metric("Logic Cost Reduction", f"{saving_pct:.1f}%", f"Cost {cb['cost']} → {ca['cost']}")

        grid = kmap_grid(RETIREMENT_MINTERMS)
        import numpy as np
        arr = np.array(grid)
        row_labels = ['AB=00','AB=01','AB=11','AB=10']
        col_labels = ['CD=00','CD=01','CD=11','CD=10']
        fig = go.Figure(go.Heatmap(
            z=arr, colorscale=[[0,'#1a1a26'],[1,'#a855f7']],
            showscale=False, hoverinfo='skip',
            text=[[f"{row_labels[r]}\n{col_labels[c]}" for c in range(4)] for r in range(4)],
        ))
        fig.update_layout(
            height=200, margin=dict(l=40,r=10,t=30,b=40),
            paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
            xaxis=dict(tickvals=list(range(4)), ticktext=col_labels,
                       tickfont=dict(color='#8888a0',size=10), showgrid=False),
            yaxis=dict(tickvals=list(range(4)), ticktext=row_labels,
                       tickfont=dict(color='#8888a0',size=10), showgrid=False),
            title=dict(text='K-map (purple=1, retire_block)', font=dict(color='#e8e8f0',size=12)),
        )
        st.plotly_chart(fig, use_container_width=True, key="kmap_plot")

        ok = bdd_verify_equivalent()
        if ok:
            st.success("✅ BDD verification passed — expressions are logically identical across all 16 inputs.")

    with tab_qmc:
        result = qmc_ldpc_demo()
        st.markdown(f"**Minterms:** {LDPC_ESCALATION_MINTERMS}")
        st.markdown("**Popcount groups:**")
        for pc, terms in sorted(result['groups_by_popcount'].items()):
            st.markdown(f"- popcount={pc}: {terms}")
        st.markdown(f"**Prime implicants found:** {len(result['prime_implicants'])}")
        st.markdown(f"**Minimized expression:** `{result['expression']}`")
        st.caption(f"Stages: {result['stages']} | Essential PIs: {len(result['essential_pis'])}")


def render_section4(sim):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔷 SECTION 4 — Security + Minimization Algorithms")
    render_crypto_section(sim)
    st.markdown("---")
    render_shamir_section()
    st.markdown("---")
    render_oob_section(sim)
    st.markdown("---")
    render_kmap_section()
    st.markdown('</div>', unsafe_allow_html=True)
