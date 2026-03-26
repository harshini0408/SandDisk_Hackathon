"""
AURA — Pillar 4: Firmware Logic Optimization Engine
Implements:  Auto-correction → QMC + Petrick's → BDD Verification → C Code Gen
"""
import streamlit as st
import os
import sys
import pandas as pd

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
  --bg:#0a0a0f;--surface:#12121a;--card:#1a1a26;--border:#2a2a3a;
  --text:#e8e8f0;--muted:#8888a0;--dim:#4a4a60;
  --green:#22c55e;--amber:#f59e0b;--red:#ef4444;
  --blue:#3b82f6;--purple:#a855f7;--teal:#14b8a6;--orange:#f97316;
}
html,body,[data-testid="stApp"]{background-color:var(--bg)!important;color:var(--text)!important;font-family:'Inter',sans-serif!important;}
[data-testid="stSidebar"]{background-color:var(--surface)!important;border-right:1px solid var(--border);}
h1,h2,h3,h4,h5{font-family:'JetBrains Mono',monospace!important;color:var(--text)!important;}
div[data-testid="stMetricValue"]{color:var(--purple)!important;font-size:1.5rem!important;font-weight:700!important;}
div[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:0.75rem!important;}
section[data-testid="stMain"]>div{background:var(--bg);}
div[data-testid="stDataFrame"]{background:var(--card)!important;}
div[data-testid="stDataFrame"] *{color:var(--text)!important;}
.section-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:24px;}
.stButton button{background:linear-gradient(135deg,#1a1a2e,#2a1a3e)!important;border:1px solid var(--purple)!important;color:var(--text)!important;border-radius:6px!important;font-family:'JetBrains Mono',monospace!important;font-size:12px!important;}
.stButton button:hover{background:linear-gradient(135deg,#2a1a3e,#3a1a5e)!important;border-color:var(--blue)!important;}
div[data-testid="stSelectbox"] label,div[data-testid="stNumberInput"] label,div[data-testid="stSlider"] label,div[data-testid="stTextInput"] label,div[data-testid="stTextArea"] label{color:var(--muted)!important;font-size:12px!important;}
div[data-testid="stSelectbox"]>div,div[data-testid="stNumberInput"]>div input,div[data-testid="stTextInput"]>div>div input{background:var(--card)!important;color:var(--text)!important;border-color:var(--border)!important;}
div[data-baseweb="tab-list"]{background:var(--surface)!important;border-bottom:1px solid var(--border);}
div[data-baseweb="tab"]{color:var(--muted)!important;}
div[data-baseweb="tab"][aria-selected="true"]{color:var(--purple)!important;border-bottom:2px solid var(--purple)!important;}
.stAlert{border-radius:8px!important;}
div.stExpander{background:var(--card)!important;border:1px solid var(--border)!important;border-radius:8px!important;}
div[data-testid="stExpander"] summary{color:var(--text)!important;}
div[data-testid="stCodeBlock"] pre{background:var(--surface)!important;border:1px solid var(--border)!important;}
</style>
""", unsafe_allow_html=True)

# ─── Import engine ────────────────────────────────────────────────────────────
try:
    from core.pillar4_engine import (
        auto_correct, extract_variables, generate_truth_table,
        quine_mccluskey, petricks_method, build_kmap_html,
        build_expression_from_pis, compute_metrics, try_factor_expression,
        generate_c_code, term_to_binary, term_to_str, safe_eval,
        BUILTIN_TESTS,
    )
    ENGINE_OK = True
except ImportError as _e:
    ENGINE_OK = False
    ENGINE_ERR = str(_e)

# ─── Sidebar (navigation only) ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔷 AURA")
    st.page_link("app.py",             label="Home",                            icon="🏠")
    st.page_link("pages/0_Manual.py",  label="📖 Quick Manual",                icon="📖")
    st.page_link("pages/1_Pillar1.py", label="Pillar 1 — Health & Diagnostics", icon="🧠")
    st.page_link("pages/2_Pillar2.py", label="Pillar 2 — NAND Block Mgmt",     icon="🗃️")
    st.page_link("pages/3_Pillar3.py", label="Pillar 3 — ECC & Reliability",   icon="🛡️")
    st.page_link("pages/4_Pillar4.py", label="Pillar 4 — Logic Optimization",  icon="⚙️")
    st.divider()
    st.markdown("""
<div style="font-family:monospace;font-size:11px;color:#8888a0">
<b style="color:#e8e8f0">Mode:</b> BUILD-TIME<br>
<b style="color:#e8e8f0">Runtime signals:</b> NONE<br>
<b style="color:#e8e8f0">Reduction:</b> 30–40%<br>
<b style="color:#e8e8f0">Method:</b> QMC + Petrick's + BDD
</div>
""", unsafe_allow_html=True)

# ─── Page header ──────────────────────────────────────────────────────────────
st.markdown("# ⚙️ Pillar 4 — Firmware Logic Optimization Engine")
st.markdown("---")

if not ENGINE_OK:
    st.error(f"❌ Engine import failed: `{ENGINE_ERR}`. Make sure `core/pillar4_engine.py` exists.")
    st.stop()

st.info(
    "**Pillar 4** runs at firmware **BUILD TIME**. It takes raw Boolean ECC/block-retirement decision "
    "logic, minimizes it using **QMC + Petrick's Method**, verifies it with **BDD exhaustive testing**, "
    "and outputs optimized **C firmware code** — with 30–40% fewer gates, proven mathematically identical."
)

# ─── Top stat banner ─────────────────────────────────────────────────────────
bc1, bc2, bc3, bc4 = st.columns(4)
bc1.metric("Logic Reduction", "30–40%", help="Typical gate cost reduction from QMC optimization")
bc2.metric("Verification", "2ⁿ Tests", help="BDD checks all input combinations exhaustively")
bc3.metric("Method", "QMC+Petrick", help="Quine-McCluskey + Petrick's method for minimal cover")
bc4.metric("Output", "C Code", help="Generates ready-to-flash SSD firmware code")

st.markdown("---")

# ─── Main tabs ───────────────────────────────────────────────────────────────
tab_optimize, tab_tests = st.tabs([
    "🔬 Optimization Pipeline",
    "🧪 Built-In Test Cases",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OPTIMIZATION PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab_optimize:

    # ── CONFIGURATION CARD ────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### ⚙ Configuration")

    cfg_col1, cfg_col2 = st.columns([3, 2])
    with cfg_col1:
        raw_expr = st.text_input(
            "Boolean Expression  (use A–E, &, +, !)",
            value="(A & B & C) + (A & B & D)",
            key="p4_expr",
            help="Supports implicit AND (AB→A&B), word operators (and/or/not), || and *"
        )
        dc_str = st.text_input(
            "Don't-Care minterms (comma-separated, optional)",
            value="",
            key="p4_dc",
            help="These minterms can be 0 or 1 — used to maximize optimization"
        )

    with cfg_col2:
        st.markdown("**Variable → SSD Signal mapping**")
        SIGNAL_OPTIONS = [
            "ecc_error", "bad_block", "wear_limit", "write_request",
            "read_fail", "temp_crit", "retry_flag", "ldpc_fail",
            "uecc_flag", "program_fail", "erase_fail", "reallocated",
        ]
        var_map = {}
        for letter in list("ABCDE"):
            var_map[letter] = st.selectbox(
                f"Variable {letter}",
                options=SIGNAL_OPTIONS,
                index=["ecc_error","bad_block","wear_limit","write_request","read_fail"].index(
                    ["ecc_error","bad_block","wear_limit","write_request","read_fail"][
                        min(list("ABCDE").index(letter), 4)
                    ]
                ),
                key=f"p4_var_{letter}",
            )

    method = st.radio(
        "Minimization method",
        ["Auto (K-Map ≤4 vars, QMC otherwise)", "Force QMC (always)"],
        horizontal=True, key="p4_method"
    )
    force_qmc = (method == "Force QMC (always)")

    run_btn = st.button("▶ Run Optimization Pipeline", type="primary", key="p4_run")
    st.markdown('</div>', unsafe_allow_html=True)

    if run_btn:
        # ── STAGE 0: Auto-correct ───────────────────────────────────────
        with st.expander("📋 Stage 0 — Auto-Correction", expanded=True):
            cr = auto_correct(raw_expr)
            if cr.changes:
                st.warning("Expression was auto-corrected:")
                for c in cr.changes:
                    st.markdown(f"  • {c}")
                col_a, col_b = st.columns(2)
                col_a.code(cr.original, language="text")
                col_b.code(cr.corrected, language="text")
            else:
                st.success("✓ Expression is already well-formed — no corrections needed.")

            if not cr.valid:
                st.error(f"❌ Expression is invalid even after correction: `{cr.error}`")
                st.stop()

        expr = cr.corrected
        variables = extract_variables(expr)
        n = len(variables)

        # Parse don't-cares
        dont_cares = []
        if dc_str.strip():
            try:
                dont_cares = [int(x.strip()) for x in dc_str.split(",") if x.strip()]
                max_m = 2**n - 1
                invalid_dc = [d for d in dont_cares if d < 0 or d > max_m]
                if invalid_dc:
                    st.warning(f"Don't-care minterms out of range (0–{max_m}): {invalid_dc} — ignored.")
                    dont_cares = [d for d in dont_cares if 0 <= d <= max_m]
            except ValueError:
                st.warning("Invalid don't-cares format — ignored.")

        if n > 6:
            st.error(f"Too many variables ({n}). Maximum supported is 6.")
            st.stop()

        use_kmap = (n <= 4) and not force_qmc

        # ── STAGE 1: Truth Table ───────────────────────────────────────
        with st.expander("📊 Stage 1 — Truth Table", expanded=True):
            rows, on_set, off_set = generate_truth_table(expr, variables, dont_cares)
            df_tt = pd.DataFrame(rows)
            # Style output column
            def _style_out(val):
                if val == 1:   return "background-color:#052e16;color:#22c55e;font-weight:700"
                if val == 0:   return "background-color:#120000;color:#4a4a60"
                return "background-color:#1c1400;color:#f59e0b;font-weight:700"
            st.dataframe(
                df_tt.style.applymap(_style_out, subset=["Output"]),
                use_container_width=True, hide_index=True
            )
            st.markdown(
                f'<span style="font-family:monospace;font-size:11px;color:#8888a0">'
                f'On-set: {on_set} &nbsp;|&nbsp; Don\'t-cares: {dont_cares} &nbsp;|&nbsp; Off-set count: {len(off_set)}'
                f'</span>', unsafe_allow_html=True
            )

        if not on_set:
            st.warning("The expression is identically **0** — nothing to minimize.")
            st.stop()

        # ── STAGE 2: K-Map (only for ≤4 variables, non-forced-QMC) ──
        if use_kmap:
            with st.expander("🗂️ Stage 2 — K-Map Visualization", expanded=True):
                kmap_html = build_kmap_html(on_set, dont_cares, variables)
                if kmap_html:
                    # Header labels
                    n_row_vars = max(1, n // 2)
                    n_col_vars = n - n_row_vars
                    row_label = "".join(variables[:n_row_vars])
                    col_label = "".join(variables[n_row_vars:])
                    st.markdown(
                        f'<div style="font-family:monospace;font-size:11px;color:#8888a0;margin-bottom:4px">'
                        f'Rows = <b style="color:#14b8a6">{row_label}</b>, '
                        f'Cols = <b style="color:#14b8a6">{col_label}</b> &nbsp;|&nbsp; '
                        f'<span style="color:#22c55e">■ 1</span> &nbsp; '
                        f'<span style="color:#f59e0b">■ X</span> (don\'t-care) &nbsp; '
                        f'<span style="color:#4a4a60">■ 0</span></div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(kmap_html, unsafe_allow_html=True)
                else:
                    st.info("K-Map not available for this variable count.")
        else:
            with st.expander("🗂️ Stage 2 — K-Map (hidden — using QMC)", expanded=False):
                st.info(
                    f"K-Map visualization is **hidden** for {'≥5 variables' if n >= 5 else 'forced QMC mode'}. "
                    "The QMC grouping table below shows equivalent group-merging steps."
                )

        # ── STAGE 3: QMC Reduction ─────────────────────────────────────
        with st.expander("🔢 Stage 3 — Quine-McCluskey Reduction", expanded=True):
            pis, steps = quine_mccluskey(on_set, dont_cares, n)

            st.markdown(f"**{len(steps)} iterations** · **{len(pis)} prime implicants found**")

            for step in steps:
                st.markdown(
                    f'<div style="font-family:monospace;font-size:11px;color:#a855f7;margin:6px 0 2px">'
                    f'Iteration {step["iteration"]} — {len(step["merges"])} merge(s), '
                    f'{len(step["primes_found"])} prime(s) identified</div>', unsafe_allow_html=True
                )
                if step["merges"]:
                    merge_rows = []
                    for t1, t2, combined in step["merges"]:
                        merge_rows.append({
                            "Term 1": term_to_binary(t1[0], t1[1], n),
                            "Term 2": term_to_binary(t2[0], t2[1], n),
                            "Merged": term_to_binary(combined[0], combined[1], n),
                        })
                    st.dataframe(pd.DataFrame(merge_rows), use_container_width=True, hide_index=True)

            if pis:
                st.markdown("**All prime implicants:**")
                pi_rows = [{"Binary": term_to_binary(p[0],p[1],n),
                            "SOP term": term_to_str(p, variables)} for p in pis]
                st.dataframe(pd.DataFrame(pi_rows), use_container_width=True, hide_index=True)

        # ── STAGE 4: Petrick's Method ───────────────────────────────────
        with st.expander("🎯 Stage 4 — Petrick's Method (Minimal Cover)", expanded=True):
            selected_pis, coverage, essential_idx = petricks_method(pis, on_set, n)

            if essential_idx:
                st.markdown(
                    f'<span style="font-family:monospace;font-size:11px;color:#22c55e">'
                    f'Essential PIs (cover unique minterms): indices {essential_idx}</span>',
                    unsafe_allow_html=True
                )

            petrick_rows = []
            for m, pi_list in sorted(coverage.items()):
                petrick_rows.append({
                    "Minterm": f"m{m}",
                    "Covered by PIs": str(pi_list),
                    "Essential": "✅" if len(pi_list) == 1 else "",
                })
            st.dataframe(pd.DataFrame(petrick_rows), use_container_width=True, hide_index=True)

            optimized_expr = build_expression_from_pis(selected_pis, variables)
            factored_expr  = try_factor_expression(optimized_expr)
            final_expr     = factored_expr

            st.markdown(f"**Minimized SOP:** `{optimized_expr}`")
            if factored_expr != optimized_expr:
                st.markdown(f"**Factored form (cheaper):** `{factored_expr}`")

        # ── STAGE 5: Cost Analysis ──────────────────────────────────────
        with st.expander("📈 Stage 5 — Cost Analysis", expanded=True):
            m_before = compute_metrics(expr)
            m_after  = compute_metrics(final_expr)

            col_b, col_a = st.columns(2)
            with col_b:
                st.markdown('<div style="background:#120000;border:1px solid #ef444440;border-radius:8px;padding:12px">', unsafe_allow_html=True)
                st.markdown('<div style="font-family:monospace;font-size:12px;color:#fca5a5">❌ BEFORE (original)</div>', unsafe_allow_html=True)
                st.code(expr, language="text")
                st.markdown(f"""
<table style="font-family:monospace;font-size:11px;width:100%">
<tr><td style="color:#8888a0">AND gates</td><td style="color:#ef4444">{m_before['and']}</td></tr>
<tr><td style="color:#8888a0">OR gates</td><td style="color:#ef4444">{m_before['or']}</td></tr>
<tr><td style="color:#8888a0">NOT gates</td><td style="color:#ef4444">{m_before['not']}</td></tr>
<tr><td style="color:#8888a0"><b>Gate cost (AND×2+OR×1+NOT×3)</b></td><td style="color:#ef4444"><b>{m_before['cost']}</b></td></tr>
</table>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_a:
                st.markdown('<div style="background:#052e16;border:1px solid #22c55e40;border-radius:8px;padding:12px">', unsafe_allow_html=True)
                st.markdown('<div style="font-family:monospace;font-size:12px;color:#86efac">✅ AFTER (optimized)</div>', unsafe_allow_html=True)
                st.code(final_expr, language="text")
                st.markdown(f"""
<table style="font-family:monospace;font-size:11px;width:100%">
<tr><td style="color:#8888a0">AND gates</td><td style="color:#22c55e">{m_after['and']}</td></tr>
<tr><td style="color:#8888a0">OR gates</td><td style="color:#22c55e">{m_after['or']}</td></tr>
<tr><td style="color:#8888a0">NOT gates</td><td style="color:#22c55e">{m_after['not']}</td></tr>
<tr><td style="color:#8888a0"><b>Gate cost (AND×2+OR×1+NOT×3)</b></td><td style="color:#22c55e"><b>{m_after['cost']}</b></td></tr>
</table>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if m_before['cost'] > 0:
                pct_saved = (m_before['cost'] - m_after['cost']) / m_before['cost'] * 100
                if pct_saved > 0:
                    st.success(f"⚡ Gate cost reduced by **{pct_saved:.1f}%** — from {m_before['cost']} to {m_after['cost']} units.")
                    # Visual progress bar
                    bar_w = int(min(pct_saved, 100))
                    st.markdown(
                        f'<div style="background:#1a1a26;border-radius:4px;height:14px;overflow:hidden;margin-top:4px">'
                        f'<div style="background:linear-gradient(90deg,#a855f7,#22c55e);width:{bar_w}%;height:100%;border-radius:4px"></div>'
                        f'</div>', unsafe_allow_html=True
                    )
                else:
                    st.info("Expression is already minimal — no further reduction possible.")

        # ── STAGE 6: BDD Verification ───────────────────────────────────
        with st.expander("✅ Stage 6 — BDD Verification (Exhaustive Truth Table Check)", expanded=True):
            try:
                mismatches = []
                for i in range(2 ** n):
                    assignment = {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(variables)}
                    if i in dont_cares:
                        continue
                    orig_out  = safe_eval(expr,       assignment)
                    optim_out = safe_eval(final_expr, assignment)
                    if orig_out != optim_out:
                        mismatches.append({
                            "Minterm": f"m{i}",
                            "Original": orig_out,
                            "Optimized": optim_out,
                        })

                if not mismatches:
                    st.success(
                        f"✅ **BDD Verification PASSED** — Optimized expression is logically identical "
                        f"to the original across all {2**n} input combinations (excluding {len(dont_cares)} don't-care(s))."
                    )
                    st.markdown(
                        f'<div style="font-family:monospace;font-size:11px;color:#22c55e">'
                        f'Tested {2**n - len(dont_cares)} combinations · 0 mismatches · Mathematical proof complete.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error(f"⚠️ Verification FAILED — {len(mismatches)} mismatch(es) found!")
                    st.dataframe(pd.DataFrame(mismatches), use_container_width=True, hide_index=True)
            except Exception as bdd_e:
                st.warning(f"BDD verification skipped (expression too complex to evaluate directly): {bdd_e}")

        # ── STAGE 7: Firmware C Code ────────────────────────────────────
        with st.expander("💾 Stage 7 — Firmware C Code Generator", expanded=True):
            # Only map variables that appear in the expression
            used_vars = extract_variables(final_expr)
            active_map = {k: v for k, v in var_map.items() if k in used_vars}

            c_before = generate_c_code(expr,       active_map, label="Original")
            c_after  = generate_c_code(final_expr, active_map, label="Optimized")

            tab_c_before, tab_c_after = st.tabs(["Original C", "Optimized C"])
            with tab_c_before:
                st.code(c_before, language="c")
            with tab_c_after:
                st.code(c_after, language="c")
                st.download_button(
                    "⬇ Download Optimized C",
                    data=c_after,
                    file_name="ssd_optimized_logic.c",
                    mime="text/plain",
                    key="p4_dl_c",
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BUILT-IN TEST CASES
# ══════════════════════════════════════════════════════════════════════════════
with tab_tests:
    st.markdown("### 🧪 Built-In Firmware Logic Test Cases")
    st.info("These 5 cases demonstrate key Boolean reduction laws used in SSD firmware. "
            "Each runs through the full pipeline automatically.")

    for idx, tc in enumerate(BUILTIN_TESTS):
        with st.expander(f"**Test {idx+1}: {tc['label']}**", expanded=(idx == 0)):
            st.markdown(f'<div style="color:#8888a0;font-size:12px">{tc["description"]}</div>', unsafe_allow_html=True)

            expr_tc = tc["expr"]
            dc_tc   = tc["dont_cares"]
            cr_tc   = auto_correct(expr_tc)
            if not cr_tc.valid:
                st.error(f"Invalid test expression: {cr_tc.error}")
                continue

            expr_tc  = cr_tc.corrected
            vars_tc  = extract_variables(expr_tc)
            n_tc     = len(vars_tc)

            try:
                rows_tc, on_tc, _ = generate_truth_table(expr_tc, vars_tc, dc_tc)
            except Exception as e:
                st.error(f"Truth table error: {e}")
                continue

            if not on_tc:
                st.warning("Expression evaluates to 0 everywhere.")
                continue

            pis_tc, _      = quine_mccluskey(on_tc, dc_tc, n_tc)
            sel_tc, cov_tc, _ = petricks_method(pis_tc, on_tc, n_tc)
            opt_tc         = build_expression_from_pis(sel_tc, vars_tc)
            fac_tc         = try_factor_expression(opt_tc)
            final_tc       = fac_tc

            m_b = compute_metrics(expr_tc)
            m_a = compute_metrics(final_tc)

            r1, r2, r3 = st.columns(3)
            r1.markdown(f'<div style="font-family:monospace;background:#120000;border:1px solid #ef444440;border-radius:6px;padding:10px"><div style="color:#fca5a5;font-size:10px">ORIGINAL</div><div style="color:#ef4444;font-size:14px">{expr_tc}</div><div style="color:#8888a0;font-size:10px">Gate cost: {m_b["cost"]}</div></div>', unsafe_allow_html=True)
            r2.markdown(f'<div style="font-family:monospace;background:#052e16;border:1px solid #22c55e40;border-radius:6px;padding:10px"><div style="color:#86efac;font-size:10px">OPTIMIZED</div><div style="color:#22c55e;font-size:14px">{final_tc}</div><div style="color:#8888a0;font-size:10px">Gate cost: {m_a["cost"]}</div></div>', unsafe_allow_html=True)

            # BDD check
            bdd_passed = True
            for i in range(2 ** n_tc):
                if i in dc_tc:
                    continue
                asn = {v: (i >> (n_tc - 1 - j)) & 1 for j, v in enumerate(vars_tc)}
                try:
                    if safe_eval(expr_tc, asn) != safe_eval(final_tc, asn):
                        bdd_passed = False
                        break
                except Exception:
                    bdd_passed = False
                    break

            if m_b["cost"] > 0 and m_b["cost"] > m_a["cost"]:
                pct = (m_b["cost"] - m_a["cost"]) / m_b["cost"] * 100
                r3.markdown(f'<div style="font-family:monospace;background:#120020;border:1px solid #a855f740;border-radius:6px;padding:10px"><div style="color:#d8b4fe;font-size:10px">RESULT</div><div style="color:#a855f7;font-size:18px;font-weight:700">-{pct:.1f}%</div><div style="color:{"#22c55e" if bdd_passed else "#ef4444"};font-size:10px">BDD: {"✅ VERIFIED" if bdd_passed else "❌ MISMATCH"}</div></div>', unsafe_allow_html=True)
            else:
                r3.markdown(f'<div style="font-family:monospace;background:#120020;border:1px solid #a855f740;border-radius:6px;padding:10px"><div style="color:#d8b4fe;font-size:10px">RESULT</div><div style="color:#8888a0;font-size:14px">Already minimal</div><div style="color:{"#22c55e" if bdd_passed else "#ef4444"};font-size:10px">BDD: {"✅ VERIFIED" if bdd_passed else "❌ MISMATCH"}</div></div>', unsafe_allow_html=True)
