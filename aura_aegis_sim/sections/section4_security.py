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
    _pi_to_term, popcount,
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
    st.markdown("#### ⚙️ Pillar 4 — Logic Optimization Simulator")
    tab_kmap, tab_qmc = st.tabs(["🗂️ 4-Variable K-Map", "🔢 QMC (3–6 Variables)"])

    # ── K-Map Tab ────────────────────────────────────────────────────────────
    with tab_kmap:
        st.markdown("**Custom minterm input** — toggle which of the 16 minterms should output 1, then click **Run Optimization**.")

        # Variable names
        c1, c2, c3, c4 = st.columns(4)
        var_a = c1.text_input("Var A (MSB)", value="bad_block",   key="kmap_va")
        var_b = c2.text_input("Var B",       value="wear_limit",  key="kmap_vb")
        var_c = c3.text_input("Var C",       value="erase_fail",  key="kmap_vc")
        var_d = c4.text_input("Var D (LSB)", value="temp_crit",   key="kmap_vd")

        # 4×4 checkbox grid (Gray-code order same as KMAP layout)
        KMAP_4VAR_LAYOUT = [
            [0,  1,  3,  2],
            [4,  5,  7,  6],
            [12, 13, 15, 14],
            [8,  9,  11, 10],
        ]
        CD_LABELS = ['CD=00', 'CD=01', 'CD=11', 'CD=10']
        AB_LABELS = ['AB=00', 'AB=01', 'AB=11', 'AB=10']

        st.markdown("<div style='font-family:monospace;font-size:12px;margin-bottom:6px'>"
                    "Select cells to mark as <b style='color:#a855f7'>1</b> (minterm present):</div>",
                    unsafe_allow_html=True)

        # Header row
        header_cols = st.columns([1.2] + [1]*4)
        header_cols[0].markdown("<div style='font-size:11px;color:#8888a0'>AB \\ CD</div>", unsafe_allow_html=True)
        for i, cl in enumerate(CD_LABELS):
            header_cols[i+1].markdown(f"<div style='font-size:10px;color:#8888a0;text-align:center'>{cl}</div>", unsafe_allow_html=True)

        custom_minterms: list[int] = []
        for r, row in enumerate(KMAP_4VAR_LAYOUT):
            row_cols = st.columns([1.2] + [1]*4)
            row_cols[0].markdown(f"<div style='font-size:10px;color:#8888a0;padding-top:8px'>{AB_LABELS[r]}</div>", unsafe_allow_html=True)
            for c, minterm_val in enumerate(row):
                checked = row_cols[c+1].checkbox(
                    f"m{minterm_val}", key=f"kmap_m{minterm_val}",
                    value=(minterm_val in RETIREMENT_MINTERMS),
                    label_visibility="visible"
                )
                if checked:
                    custom_minterms.append(minterm_val)

        custom_minterms.sort()

        st.markdown(f"**Selected minterms:** `{custom_minterms}`" if custom_minterms else
                    "**Selected minterms:** _(none selected — function is constant 0)_")

        if st.button("▶ Run K-Map Optimization", key="kmap_run"):
            if not custom_minterms:
                st.warning("No minterms selected — the function is always 0.")
            else:
                result = qmc_minimize(custom_minterms, num_vars=4)

                # Heatmap
                import numpy as np
                grid = kmap_grid(custom_minterms)
                arr = np.array(grid)
                annotations = []
                for r in range(4):
                    for c in range(4):
                        annotations.append(dict(
                            x=c, y=r,
                            text=str(arr[r, c]),
                            font=dict(color='#e8e8f0', size=14, family='JetBrains Mono'),
                            showarrow=False
                        ))
                fig = go.Figure(go.Heatmap(
                    z=arr, colorscale=[[0, '#1a1a26'], [1, '#7c3aed']],
                    showscale=False, hoverinfo='skip',
                ))
                fig.update_layout(
                    height=220, margin=dict(l=60, r=10, t=30, b=50),
                    paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
                    xaxis=dict(tickvals=list(range(4)), ticktext=CD_LABELS,
                               tickfont=dict(color='#8888a0', size=10), showgrid=False),
                    yaxis=dict(tickvals=list(range(4)), ticktext=AB_LABELS,
                               tickfont=dict(color='#8888a0', size=10), showgrid=False,
                               autorange='reversed'),
                    title=dict(text=f'K-Map: {var_a},{var_b},{var_c},{var_d}  (purple = 1)',
                               font=dict(color='#e8e8f0', size=11)),
                    annotations=annotations,
                )
                st.plotly_chart(fig, use_container_width=True, key="kmap_plot_custom")

                # Results
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown("**Minimized SOP expression:**")
                    import re as _re
                    _var_map = {'A': var_a, 'B': var_b, 'C': var_c, 'D': var_d}
                    _raw_terms = [t.strip().strip('()') for t in result['expression'].split(' | ')]
                    _display_terms = []
                    for _term in _raw_terms:
                        if _term in ('0', '1'):
                            _display_terms.append(_term)
                            continue
                        _lits = _re.findall(r'!?[A-E]', _term)
                        _sub = [('!' if l.startswith('!') else '') + _var_map.get(l.lstrip('!'), l.lstrip('!')) for l in _lits]
                        _display_terms.append(' & '.join(_sub))
                    expr_readable = ' | '.join(f'({t})' for t in _display_terms)
                    st.code(expr_readable, language="text")
                with col_r2:
                    n_pi   = len(result['prime_implicants'])
                    n_epi  = len(result['essential_pis'])
                    n_lit  = sum(len(_pi_to_term(pi, 4).replace('!','')) for pi in result['essential_pis'])
                    st.metric("Prime Implicants", n_pi)
                    st.metric("Essential PIs", n_epi)
                    st.metric("Literals in result", n_lit)

                # BDD check against a reference function using the selected minterms
                s = set(custom_minterms)
                all_match = True
                for i in range(16):
                    A = (i >> 3) & 1; B = (i >> 2) & 1; C = (i >> 1) & 1; D = i & 1
                    expected = 1 if i in s else 0
                    # Evaluate the minimized expression
                    actual = 0
                    for pi in result['essential_pis']:
                        def _eval_pi(pi_set, idx):
                            base = min(pi_set)
                            mask = 0
                            for mm in pi_set:
                                mask |= (base ^ mm)
                            A_v=(idx>>3)&1; B_v=(idx>>2)&1; C_v=(idx>>1)&1; D_v=idx&1
                            vals=[A_v,B_v,C_v,D_v]
                            for bit in range(3,-1,-1):
                                if (mask >> bit) & 1:
                                    continue
                                if ((base >> bit) & 1) != vals[3-bit]:
                                    return 0
                            return 1
                        if _eval_pi(pi, i):
                            actual = 1
                            break
                    if expected != actual:
                        all_match = False
                        break

                if all_match:
                    st.success("✅ BDD Verification: minimized expression is **logically identical** to the truth table across all 16 input combinations.")
                else:
                    st.warning("⚠️ Verification found a discrepancy — please check minterms.")

    # ── QMC Tab ──────────────────────────────────────────────────────────────
    with tab_qmc:
        st.markdown("**Quine-McCluskey Minimization** — enter any number of variables and minterms for full tabular reduction.")

        col_qv, col_qm = st.columns([1, 3])
        # ── Preset buttons (update session state for both nvars + minterms) ──
        PRESETS = {
            "qp1": ("LDPC Escalation (5-var)",  "3, 5, 7, 11, 13, 15, 19, 23", 5),
            "qp2": ("Block Retirement (4-var)",  "6, 7, 11, 13, 14, 15",        4),
            "qp3": ("All-even (4-var)",          "0, 2, 4, 6, 8, 10, 12, 14",   4),
            "qp4": ("Half-adder Sum (3-var)",    "1, 2, 4, 7",                   3),
        }
        # Initialise session state defaults on first run
        if "qmc_nvars" not in st.session_state:
            st.session_state["qmc_nvars"] = 5
        if "qmc_minterms" not in st.session_state:
            st.session_state["qmc_minterms"] = "3, 5, 7, 11, 13, 15, 19, 23"

        st.markdown("**Quick presets:**")
        pb1, pb2, pb3, pb4 = st.columns(4)
        for btn_col, (pkey, (plabel, pmints, pnvars)) in zip([pb1, pb2, pb3, pb4], PRESETS.items()):
            if btn_col.button(plabel, key=pkey):
                st.session_state["qmc_nvars"]    = pnvars
                st.session_state["qmc_minterms"] = pmints
                st.rerun()

        num_vars_qmc = col_qv.number_input(
            "Variables (3–6)", min_value=3, max_value=6, step=1, key="qmc_nvars"
        )
        max_m = 2**int(num_vars_qmc) - 1

        minterms_str = col_qm.text_input(
            f"Minterms (comma-separated, 0–{max_m})",
            key="qmc_minterms",
        )

        effective_str = minterms_str
        nvars = int(num_vars_qmc)


        if st.button("▶ Run QMC Minimization", key="qmc_run"):
            try:
                raw = [int(x.strip()) for x in effective_str.split(',') if x.strip()]
                invalid = [m for m in raw if m < 0 or m > max_m]
                if invalid:
                    st.error(f"Minterms out of range for {nvars} variables (must be 0–{max_m}): {invalid}")
                elif not raw:
                    st.warning("No minterms entered.")
                else:
                    result = qmc_minimize(raw, num_vars=nvars)

                    # Popcount grouping table
                    st.markdown("**Step 1 — Group minterms by popcount (number of 1s in binary):**")
                    groups: dict[int, list[int]] = {}
                    for m in raw:
                        pc = popcount(m)
                        groups.setdefault(pc, []).append(m)

                    import pandas as pd
                    rows = []
                    for pc in sorted(groups.keys()):
                        for m in sorted(groups[pc]):
                            rows.append({"Popcount": pc, "Minterm": m, "Binary": format(m, f'0{nvars}b')})
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    # Prime implicant table
                    st.markdown(f"**Step 2 — Prime implicants found: {len(result['prime_implicants'])}**")
                    pi_rows = []
                    for pi in result['prime_implicants']:
                        term = _pi_to_term(pi, nvars)
                        is_essential = pi in result['essential_pis']
                        pi_rows.append({
                            "Minterms covered": sorted(list(pi)),
                            "SOP term": term,
                            "Essential": "✅ Yes" if is_essential else "No",
                        })
                    st.dataframe(pd.DataFrame(pi_rows), use_container_width=True, hide_index=True)

                    # Final result
                    st.markdown("**Step 3 — Minimized expression (Petrick's Method cover):**")
                    st.code(result['expression'], language="text")

                    # Cost metrics
                    var_names = list('ABCDE')[:nvars]
                    n_terms_before = len(raw)
                    n_lit_before   = n_terms_before * nvars
                    n_terms_after  = len(result['essential_pis'])
                    n_lit_after    = sum(len(_pi_to_term(pi, nvars).replace('!', '')) for pi in result['essential_pis'])
                    saved_terms = max(0, n_terms_before - n_terms_after)
                    saved_lits  = max(0, n_lit_before  - n_lit_after)

                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Product terms before", n_terms_before)
                    mc2.metric("Product terms after",  n_terms_after, delta=f"-{saved_terms}" if saved_terms else "0")
                    mc3.metric("Literals before", n_lit_before)
                    mc4.metric("Literals after",  n_lit_after, delta=f"-{saved_lits}" if saved_lits else "0")

                    if n_lit_before > 0:
                        pct = (n_lit_before - n_lit_after) / n_lit_before * 100
                        if pct > 0:
                            st.success(f"⚡ Logic cost reduced by **{pct:.1f}%** — from {n_lit_before} to {n_lit_after} literals.")
                        else:
                            st.info("Expression is already minimal — no further reduction possible.")
            except ValueError:
                st.error("Invalid input — please enter integers separated by commas.")



def render_section4(sim):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔷 SECTION 4 — Security & OOB Channels")
    render_crypto_section(sim)
    st.markdown("---")
    render_shamir_section()
    st.markdown("---")
    render_oob_section(sim)
    st.markdown('</div>', unsafe_allow_html=True)
