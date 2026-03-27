"""
AURA — Pillar 4: Firmware Logic Optimization Engine
Streamlit multi-stage interactive simulation.
"""
import streamlit as st
import re, time
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sections.section_p4_optimizer import (
    auto_correct, extract_variables, generate_truth_table,
    quine_mccluskey, build_kmap_html, petricks_method,
    build_expression_from_pis, try_factor_expression,
    compute_metrics, generate_c_code, safe_eval, safe_parse,
    term_to_str, term_to_binary, get_covered_minterms,
    BUILTIN_TESTS,
)

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pillar 4 — Logic Optimizer | AURA",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── DARK THEME CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600;700&display=swap');

html,body,[data-testid="stApp"]{
  background:#0a0a0f!important;color:#e8e8f0!important;
  font-family:'Inter',sans-serif!important;}

[data-testid="stSidebar"]{
  background:#12121a!important;border-right:1px solid #2a2a3a;}
[data-testid="stSidebar"] *{color:#e8e8f0!important;}

h1,h2,h3,h4,h5{
  font-family:'JetBrains Mono',monospace!important;
  color:#e8e8f0!important;}

div[data-testid="stExpander"]{
  background:#12121a!important;
  border:1px solid #2a2a3a!important;
  border-left:4px solid #7c3aed!important;
  border-radius:8px!important;margin-bottom:10px;}
div[data-testid="stExpander"] summary{
  color:#e8e8f0!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;}
div[data-testid="stExpander"] summary:hover{color:#a855f7!important;}

div[data-baseweb="tab-list"]{background:#12121a!important;border-bottom:1px solid #2a2a3a!important;}
div[data-baseweb="tab"]{color:#8888a0!important;}
div[data-baseweb="tab"][aria-selected="true"]{
  color:#3b82f6!important;border-bottom:2px solid #3b82f6!important;}

div[data-testid="stMetricValue"]{color:#22c55e!important;font-size:1.4rem!important;font-weight:700!important;}
div[data-testid="stMetricLabel"]{color:#8888a0!important;font-size:0.72rem!important;}
[data-testid="stMetricDelta"]{font-size:0.82rem!important;}

div[data-testid="stDataFrame"]{background:#12121a!important;}
div[data-testid="stDataFrame"] *{color:#e8e8f0!important;}
div[data-testid="stDataFrame"] th{background:#1a1a26!important;}

div[data-testid="stCode"],.stCode{
  background:#0d1117!important;border:1px solid #2a2a3a!important;border-radius:6px!important;}
div[data-testid="stCode"] pre,.stCode pre{color:#79c0ff!important;}

div[data-testid="stAlert"]{border-radius:8px!important;}

.stButton button{
  background:linear-gradient(135deg,#1a1a2e,#2a1a3e)!important;
  border:1px solid #7c3aed!important;color:#e8e8f0!important;
  font-family:'JetBrains Mono',monospace!important;
  border-radius:6px!important;font-weight:600!important;}
.stButton button:hover{border-color:#3b82f6!important;background:linear-gradient(135deg,#1e1e3a,#2e1e4a)!important;}

div[data-testid="stSelectbox"]>div,
div[data-testid="stTextInput"]>div>input,
div[data-testid="stTextArea"]>div>textarea{
  background:#1a1a26!important;color:#e8e8f0!important;
  border-color:#2a2a3a!important;border-radius:6px!important;}

div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label{
  color:#a0a0b8!important;font-size:12px!important;font-weight:600!important;
  text-transform:uppercase!important;letter-spacing:0.5px!important;}

.chip-green{display:inline-block;background:#052e16;color:#22c55e;
  border:1px solid #16a34a;border-radius:20px;padding:2px 12px;
  font-family:'JetBrains Mono',monospace;font-size:11px;margin:2px}
.chip-red{display:inline-block;background:#2d0a0a;color:#ef4444;
  border:1px solid #991b1b;border-radius:20px;padding:2px 12px;
  font-family:'JetBrains Mono',monospace;font-size:11px;margin:2px}
.chip-blue{display:inline-block;background:#0c1e3a;color:#60a5fa;
  border:1px solid #1e40af;border-radius:20px;padding:2px 12px;
  font-family:'JetBrains Mono',monospace;font-size:11px;margin:2px}
.chip-amber{display:inline-block;background:#1c1400;color:#f59e0b;
  border:1px solid #92400e;border-radius:20px;padding:2px 12px;
  font-family:'JetBrains Mono',monospace;font-size:11px;margin:2px}

hr{border-color:#2a2a3a!important;}
div[data-testid="stProgressBar"]>div{background:#7c3aed!important;}

/* input card */
.input-card{
  background:#12121a;border:1px solid #2a2a3a;border-left:4px solid #3b82f6;
  border-radius:10px;padding:24px 24px 16px;margin-bottom:24px;}
.input-card-title{
  font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;
  color:#60a5fa;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;}

/* status pill */
.status-pill{
  display:inline-flex;align-items:center;gap:6px;
  background:#0c1e3a;color:#60a5fa;border:1px solid #1e40af;
  border-radius:6px;padding:6px 14px;font-family:'JetBrains Mono',monospace;
  font-size:12px;font-weight:600;margin:4px 4px 4px 0;}

/* stage label */
.stage-badge{
  display:inline-block;background:#1a0a3a;color:#a855f7;
  border:1px solid #7c3aed;border-radius:4px;
  padding:2px 10px;font-family:'JetBrains Mono',monospace;
  font-size:11px;font-weight:700;margin-right:8px;}
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR — NAVIGATION ONLY ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔷 AURA")
    st.page_link("app.py",             label="Home",                             icon="🏠")
    st.page_link("pages/0_Manual.py",  label="Quick Manual",                    icon="📖")
    st.page_link("pages/1_Pillar1.py", label="Pillar 1 — Health & Diagnostics", icon="🧠")
    st.page_link("pages/2_Pillar2.py", label="Pillar 2 — NAND Block Mgmt",      icon="🗃️")
    st.page_link("pages/3_Pillar3.py", label="Pillar 3 — ECC & Reliability",    icon="🛡️")
    st.page_link("pages/4_Pillar4.py", label="Pillar 4 — Logic Optimization",   icon="⚙️")
    st.divider()
    st.markdown("""
<div style='font-family:monospace;font-size:11px;color:#8888a0;line-height:1.7'>
<b style='color:#e8e8f0'>Mode:</b> BUILD-TIME<br>
<b style='color:#e8e8f0'>Purpose:</b> Logic reduction<br>
<b style='color:#e8e8f0'>BDD:</b> Formally verified<br>
<b style='color:#e8e8f0'>Engine:</b> QMC + Petrick's
</div>""", unsafe_allow_html=True)


# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:14px;margin-bottom:4px'>
  <div style='font-size:2rem'>⚡</div>
  <div>
    <div style='font-family:JetBrains Mono,monospace;font-size:1.5rem;
      font-weight:700;color:#e8e8f0;line-height:1.2'>
      Pillar 4 — Firmware Logic Optimization Engine
    </div>
    <div style='color:#8888a0;font-size:13px;margin-top:3px'>
      Hybrid K-Map / Quine-McCluskey &nbsp;·&nbsp; Petrick's Cover &nbsp;·&nbsp;
      BDD Verification &nbsp;·&nbsp; C Firmware Code
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


# ═════════════════════════════════════════════════════════════════════════════
# INPUTS — MAIN PANEL
# ═════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="input-card">', unsafe_allow_html=True)
st.markdown('<div class="input-card-title">⚙ Configuration</div>', unsafe_allow_html=True)

inp_c1, inp_c2, inp_c3 = st.columns([5, 4, 3])

with inp_c1:
    expr_input = st.text_input(
        "Boolean Expression",
        value="(A & B & C) + (A & B & D)",
        help="Uppercase variables. Operators: & (AND), + (OR), ! (NOT). Autocorrect handles typos.",
        placeholder="e.g. (A & B & C) + (A & B & D)",
    )
    var_mapping_raw = st.text_area(
        "Variable Mapping  (for generated firmware code)",
        value="A = block_valid\nB = write_request\nC = read_request\nD = ecc_error",
        height=110,
        help="One per line: VAR = signal_name",
    )

with inp_c2:
    dc_raw = st.text_input(
        "Don't-Care Minterms  (optional)",
        value="",
        placeholder="e.g. 15, 7",
        help="Comma-separated minterm indices for impossible SSD states.",
    )
    method_choice = st.selectbox(
        "Minimization Method",
        ["Hybrid (Auto)", "Force K-Map", "Force QMC"],
        help="Hybrid selects K-Map for ≤4 variables, QMC otherwise.",
    )
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(
        "▶  Run Full Optimization Pipeline",
        type="primary",
        use_container_width=True,
    )

with inp_c3:
    st.markdown("""
<div style='background:#0a0a14;border:1px solid #2a2a3a;border-radius:8px;
  padding:14px 16px;font-family:JetBrains Mono,monospace;font-size:11px;
  color:#8888a0;line-height:2'>
  <div style='color:#60a5fa;font-weight:700;margin-bottom:8px;font-size:10px;
    text-transform:uppercase;letter-spacing:1px'>Supported Operators</div>
  <span style='color:#22c55e'>&amp;</span> &nbsp;AND &nbsp;&nbsp;
  <span style='color:#22c55e'>+</span> &nbsp;OR &nbsp;&nbsp;
  <span style='color:#22c55e'>!</span> &nbsp;NOT<br>
  <span style='color:#22c55e'>(  )</span> &nbsp;Grouping<br><br>
  <div style='color:#60a5fa;font-weight:700;margin-bottom:6px;font-size:10px;
    text-transform:uppercase;letter-spacing:1px'>Autocorrect accepts</div>
  <span style='color:#a855f7'>a &amp; b</span> → A &amp; B<br>
  <span style='color:#a855f7'>A * B</span> → A &amp; B<br>
  <span style='color:#a855f7'>A || B</span> → A + B<br>
  <span style='color:#a855f7'>A and B</span> → A &amp; B<br>
  <span style='color:#a855f7'>AB</span> → A &amp; B
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─── Parse don't-cares and variable mapping ───────────────────────────────
dont_cares = []
if dc_raw.strip():
    try:
        dont_cares = [int(x.strip()) for x in dc_raw.split(',') if x.strip().isdigit()]
    except Exception:
        st.error("Invalid don't-care input. Use comma-separated integers.")

var_map = {}
for line in var_mapping_raw.strip().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip()
        if k and v:
            var_map[k] = v


# ═════════════════════════════════════════════════════════════════════════════
# AUTO-CORRECTION LAYER
# ═════════════════════════════════════════════════════════════════════════════

correction = auto_correct(expr_input)

if correction.changes or not correction.valid:
    with st.expander("🔧 Auto-Correction Engine", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Input received:**")
            st.code(correction.original, language=None)
        with c2:
            st.markdown("**Corrected expression:**")
            st.code(correction.corrected, language=None)

        if correction.changes:
            for change in correction.changes:
                st.markdown(f"<span class='chip-blue'>✏ {change}</span>", unsafe_allow_html=True)

        if not correction.valid:
            st.markdown(f"""
<div style='background:#2d0a0a;border:1px solid #991b1b;border-radius:8px;padding:14px;margin-top:8px'>
  <b style='color:#ef4444'>❌ Invalid Expression</b><br>
  <span style='color:#fca5a5;font-family:monospace'>Reason: {correction.error}</span><br><br>
  <b style='color:#e8e8f0'>💡 Suggested Fix:</b>
  <pre style='color:#79c0ff;background:#0d1117;padding:8px;border-radius:4px;margin-top:6px'>Try: (A & B & C) + (A & B & D)</pre>
  <span style='color:#8888a0;font-size:12px'>Use uppercase variables, &amp; for AND, + for OR, ! for NOT.</span>
</div>""", unsafe_allow_html=True)
            st.stop()
        elif correction.changes:
            st.success("✔ Expression corrected — running pipeline with fixed expression.")

# Use corrected expression going forward
expr_working = correction.corrected
variables     = extract_variables(expr_working)
n_vars        = len(variables)

if n_vars == 0:
    st.error("⚠️ No variables detected. Use uppercase letters (A–Z) in your expression.")
    st.stop()

# Method selection
if method_choice == "Force K-Map":
    use_kmap = True
elif method_choice == "Force QMC":
    use_kmap = False
else:
    use_kmap = (n_vars <= 4)

# ── Status bar pills ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px'>
  <div class='status-pill'>📝 {expr_working}</div>
  <div class='status-pill'>📦 Variables: {', '.join(variables)} ({n_vars})</div>
  <div class='status-pill'>🔧 Method: {'K-Map' if use_kmap else 'QMC'}</div>
  <div class='status-pill'>🚫 Don't-cares: {dont_cares if dont_cares else 'None'}</div>
</div>
""", unsafe_allow_html=True)

if not run_btn:
    st.markdown("""
<div style='background:#12121a;border:1px solid #2a2a3a;border-radius:10px;
  padding:40px;text-align:center;margin-top:20px'>
  <div style='font-size:2.5rem;margin-bottom:12px'>⚡</div>
  <div style='font-family:JetBrains Mono,monospace;font-size:1.1rem;
    color:#e8e8f0;font-weight:700;margin-bottom:8px'>
    Ready to Optimize
  </div>
  <div style='color:#8888a0;font-size:13px'>
    Configure your expression above and click
    <b style='color:#7c3aed'>▶ Run Full Optimization Pipeline</b>
  </div>
</div>""", unsafe_allow_html=True)
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# RUN FULL PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

with st.spinner("Running optimization pipeline…"):

    tt_rows, on_set, off_set = generate_truth_table(expr_working, variables, dont_cares)
    minterms = on_set

    t_qmc_start = time.perf_counter()
    prime_implicants, qmc_steps = quine_mccluskey(minterms, dont_cares, n_vars)
    qmc_time_ms = (time.perf_counter() - t_qmc_start) * 1000

    selected_pis, coverage_table, essential_idx = petricks_method(
        prime_implicants, minterms, n_vars)

    minimized_expr = build_expression_from_pis(selected_pis, variables)
    final_expr     = try_factor_expression(minimized_expr)

    orig_m  = compute_metrics(expr_working)
    min_m   = compute_metrics(minimized_expr)
    final_m = compute_metrics(final_expr)

    # BDD verification
    mismatch = []
    for i in range(2 ** n_vars):
        if i in dont_cares:
            continue
        assignment = {v: (i >> (n_vars - 1 - j)) & 1 for j, v in enumerate(variables)}
        v_orig = safe_eval(expr_working, assignment)
        try:
            v_opt = safe_eval(final_expr, assignment) if final_expr != '0' else 0
        except Exception:
            v_opt = 0
        if v_orig != v_opt:
            mismatch.append(i)
    bdd_pass = len(mismatch) == 0

    kmap_html = build_kmap_html(minterms, dont_cares, variables) if (use_kmap and n_vars <= 4) else ""
    orig_code = generate_c_code(expr_working, var_map, "Original")
    opt_code  = generate_c_code(final_expr,   var_map, "Optimized")


# ─── TABS ────────────────────────────────────────────────────────────────────
tab_pipeline, tab_analysis, tab_tests = st.tabs([
    "🔧 Optimization Pipeline",
    "📊 Analysis Dashboard",
    "🧪 Built-in Test Cases",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — OPTIMIZATION PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

with tab_pipeline:

    # ── STAGE 1 ──
    with st.expander("Stage 1 — Expression Parser", expanded=True):
        st.markdown("**Goal:** Convert Boolean expression into bit-packed integer minterms. "
                    "All further computation is bitwise — safe AST parser, NO `eval()`.")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**Parse tree (structural view):**")
            raw_terms = [t.strip() for t in re.split(r'\+', expr_working)]
            tree_lines = ["OR" if len(raw_terms) > 1 else ""]
            for t in raw_terms:
                tc = t.strip().strip('()')
                factors = [f.strip() for f in re.split(r'&', tc) if f.strip()]
                if len(factors) > 1:
                    tree_lines.append(f"  ├── AND({', '.join(factors)})")
                else:
                    tree_lines.append(f"  ├── {tc}")
            st.code('\n'.join(filter(None, tree_lines)), language=None)
        with c2:
            st.markdown("**Variables extracted:**")
            st.code(
                f"Variables = [{', '.join(variables)}]\n"
                f"Bit positions: {dict(enumerate(variables))}", language=None)

        st.markdown("**Minterm binary conversion:**")
        parse_rows = []
        for m in minterms:
            binary = format(m, f'0{n_vars}b')
            row = {v: binary[i] for i, v in enumerate(variables)}
            row['Binary'] = binary; row['Decimal'] = m; row['Minterm'] = f'm{m}'
            parse_rows.append(row)
        if parse_rows:
            st.dataframe(pd.DataFrame(parse_rows), use_container_width=True, hide_index=True)
        else:
            st.warning("No minterms — expression evaluates to 0 for all inputs.")
        st.success(f"ON-set minterms: **{{{', '.join(str(m) for m in minterms)}}}**")

    # ── STAGE 2 ──
    with st.expander("Stage 2 — Truth Table + Set Generation", expanded=True):
        st.markdown(f"**Goal:** Generate all 2^{n_vars} = {2**n_vars} input combinations "
                    "and classify each into ON-set (1), OFF-set (0), Don't-care (X).")

        def _style_out(val):
            if val == 1:
                return 'background-color:#052e16;color:#22c55e;font-weight:bold'
            if val == 'X':
                return 'background-color:#1c1400;color:#f59e0b;font-weight:bold'
            return 'color:#4a4a60'

        df_tt = pd.DataFrame(tt_rows)
        st.dataframe(
            df_tt.style.applymap(_style_out, subset=['Output']),
            use_container_width=True,
            height=min(400, 50 + 35 * len(tt_rows)),
            hide_index=True)

        c1, c2, c3 = st.columns(3)
        c1.success(f"**ON-set** (1): {{{', '.join(str(m) for m in on_set)}}}")
        c2.error(f"**OFF-set** (0): {len(off_set)} rows")
        c3.warning(f"**DC-set** (X): {{{', '.join(str(m) for m in dont_cares) if dont_cares else 'None'}}}")

    # ── STAGE 3 ──
    with st.expander("Stage 3 — Algorithm Decision", expanded=True):
        if use_kmap:
            st.info(f"✅ **Using K-Map** — {n_vars} variable(s) (n ≤ 4). "
                    "Gray code grid grouping with direct adjacency detection.")
        else:
            st.info(f"✅ **Using QMC** — {n_vars} variable(s) (n ≥ 5). "
                    "Hash-indexed grouping · XOR difference check · early elimination.")

        st.markdown(f"""
| Condition | Algorithm | Reason |
|-----------|-----------|--------|
| n ≤ 4 | K-Map | Visual grouping, Gray code |
| n ≥ 5 | QMC | Algorithmic, any variable count |
| **Selected** | **{'K-Map' if use_kmap else 'QMC'}** | {n_vars} variables |
""")

    # ── STAGE 4A — K-MAP ──
    if use_kmap and n_vars <= 4:
        with st.expander("Stage 4A — K-Map Simulation", expanded=True):
            st.markdown("**Goal:** Arrange minterms in Gray code order. Group adjacent 1s (+ X cells) "
                        "in powers of 2 to form prime implicants.")
            if kmap_html:
                st.markdown(kmap_html, unsafe_allow_html=True)
                st.caption("🟢 Green = 1 (ON-set)  ·  🟡 Yellow = X (Don't-care)  ·  ⬛ Dark = 0 (OFF-set)")
            st.markdown("**Prime implicants identified:**")
            if prime_implicants:
                pi_rows = []
                for pi in prime_implicants:
                    covered_on = [m for m in get_covered_minterms(pi, n_vars) if m in minterms]
                    pi_rows.append({
                        'Expression': term_to_str(pi, variables),
                        'Binary Pattern': term_to_binary(*pi, n_vars),
                        'Covers (ON-set)': str(covered_on),
                    })
                st.dataframe(pd.DataFrame(pi_rows), use_container_width=True, hide_index=True)
            else:
                st.warning("No prime implicants found.")

    # ── STAGE 4B — QMC ──
    if not use_kmap or n_vars > 4:
        with st.expander("Stage 4B — QMC Simulation", expanded=True):
            st.markdown("**Goal:** Systematically merge minterms using 3 optimizations:\n"
                        "① Hash-indexed grouping by popcount  "
                        "② XOR-based 1-bit difference check  "
                        "③ Early elimination of merged terms")
            for step in qmc_steps:
                st.markdown(f"**Iteration {step['iteration']}** — grouping by popcount:")
                group_rows = []
                for ones, terms in sorted(step['groups'].items()):
                    for t in terms:
                        group_rows.append({
                            'Popcount': ones,
                            'Binary': term_to_binary(*t, n_vars),
                            'Value': t[0], 'Mask': t[1],
                        })
                if group_rows:
                    st.dataframe(pd.DataFrame(group_rows), use_container_width=True, hide_index=True)
                if step['merges']:
                    merge_rows = [{
                        'Term 1': term_to_binary(*t1, n_vars),
                        'Term 2': term_to_binary(*t2, n_vars),
                        'XOR': format(t1[0] ^ t2[0], f'0{n_vars}b'),
                        'Combined': term_to_binary(*c, n_vars),
                    } for t1, t2, c in step['merges'][:30]]
                    st.dataframe(pd.DataFrame(merge_rows), use_container_width=True, hide_index=True)
                if step.get('primes_found'):
                    st.success(f"PIs this round: {[term_to_binary(*p, n_vars) for p in step['primes_found']]}")
            st.info(f"QMC: **{qmc_time_ms:.3f} ms** · **{len(prime_implicants)}** prime implicants")

    # ── STAGE 5 — PETRICK ──
    with st.expander("Stage 5 — Petrick's Method — Optimal Cover", expanded=True):
        st.markdown("**Goal:** Build PI table, identify essential PIs (only option for their minterms), "
                    "then greedily cover remaining minterms to form a minimal SOP.")
        if coverage_table:
            cover_rows = []
            for m, pi_indices in sorted(coverage_table.items()):
                pi_names  = [term_to_str(prime_implicants[i], variables) for i in pi_indices]
                essential = len(pi_indices) == 1
                cover_rows.append({
                    'Minterm': f'm{m}',
                    'Covered by': ', '.join(pi_names),
                    'Essential?': '✅ YES' if essential else 'No',
                })
            st.dataframe(pd.DataFrame(cover_rows), use_container_width=True, hide_index=True)
        if essential_idx:
            ess_names = [term_to_str(prime_implicants[i], variables) for i in essential_idx]
            st.info(f"Essential PIs: **{', '.join(ess_names)}**")
        for pi in selected_pis:
            covered_on = [m for m in get_covered_minterms(pi, n_vars) if m in minterms]
            st.write(f"• **{term_to_str(pi, variables)}** → covers {covered_on}")
        st.success(f"Minimized SOP: **`{minimized_expr}`**")

    # ── STAGE 6 — BDD VERIFICATION ──
    with st.expander("Stage 6 — BDD Verification", expanded=True):
        st.markdown("**Goal:** Verify minimized expression is logically identical to the original "
                    "across **all 2ⁿ** input combinations. Uses safe AST evaluator — no `eval()`.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original expression:**")
            st.code(expr_working, language=None)
        with c2:
            st.markdown("**Minimized expression:**")
            st.code(minimized_expr, language=None)

        if bdd_pass:
            st.markdown(
                "<div style='background:#052e16;color:#22c55e;padding:14px 18px;"
                "border-radius:8px;font-weight:700;font-size:1.05rem;border:1px solid #16a34a;"
                "margin-top:10px'>"
                "✅ BDD Verification PASSED — Original ≡ Optimized across all inputs</div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='background:#2d0a0a;color:#fca5a5;padding:14px 18px;"
                f"border-radius:8px;font-weight:700;border:1px solid #991b1b;margin-top:10px'>"
                f"❌ BDD Verification FAILED — mismatch at minterms {mismatch}</div>",
                unsafe_allow_html=True)

    # ── STAGE 7 — COST ──
    with st.expander("Stage 7 — Firmware Cost Optimization", expanded=True):
        st.markdown("**Goal:** Score equivalent expressions via embedded firmware cost model:\n"
                    "> **Cost = AND×2 + OR×1 + NOT×3** (NOT most expensive on MCUs)")
        cost_rows = [
            {'Expression': expr_working, 'AND': orig_m['and'], 'OR': orig_m['or'],
             'NOT': orig_m['not'], 'Cost Score': orig_m['cost'], 'Status': 'Original'},
            {'Expression': minimized_expr, 'AND': min_m['and'], 'OR': min_m['or'],
             'NOT': min_m['not'], 'Cost Score': min_m['cost'], 'Status': '✅ Minimized'},
        ]
        if final_expr != minimized_expr:
            cost_rows.append({
                'Expression': final_expr, 'AND': final_m['and'], 'OR': final_m['or'],
                'NOT': final_m['not'], 'Cost Score': final_m['cost'], 'Status': '⭐ Factored'})
        st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)
        saving = orig_m['cost'] - final_m['cost']
        pct    = (saving / orig_m['cost'] * 100) if orig_m['cost'] > 0 else 0
        st.success(f"Cost: **{orig_m['cost']}** → **{final_m['cost']}** — saving **{pct:.1f}%**")

    # ── STAGE 8 — REFACTORING ──
    with st.expander("Stage 8 — Refactoring + Depth Reduction", expanded=True):
        st.markdown("**Goal:** Factor common literals, flatten nested logic, reduce sequential CPU dependencies.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Before refactoring:**")
            st.code(minimized_expr, language=None)
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Ops",   min_m['total_ops'])
            mc2.metric("Depth", min_m['depth'])
            mc3.metric("Cost",  min_m['cost'])
        with c2:
            st.markdown("**After refactoring:**")
            st.code(final_expr, language=None)
            fc1, fc2, fc3 = st.columns(3)
            fc1.metric("Ops",   final_m['total_ops'],
                       delta=final_m['total_ops']-min_m['total_ops'], delta_color="inverse")
            fc2.metric("Depth", final_m['depth'],
                       delta=final_m['depth']-min_m['depth'], delta_color="inverse")
            fc3.metric("Cost",  final_m['cost'],
                       delta=final_m['cost']-min_m['cost'], delta_color="inverse")
        if final_expr != minimized_expr:
            st.info(f"Factoring applied: `{minimized_expr}` → `{final_expr}`")
        else:
            st.info("No further factoring possible — expression already optimal.")

    # ── STAGE 9 — FINAL OUTPUT ──
    with st.expander("Stage 9 — Final Optimized Output", expanded=True):
        st.markdown("### ✅ Final Optimized Boolean Expression")
        st.markdown(f"""
<div style='background:#0d1117;border:1px solid #22c55e;border-radius:10px;
  padding:22px 24px;margin:12px 0'>
  <div style='color:#8888a0;font-family:JetBrains Mono,monospace;
    font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px'>
    Final Optimized Expression
  </div>
  <div style='font-family:JetBrains Mono,monospace;font-size:22px;
    color:#22c55e;font-weight:700'>{final_expr}</div>
</div>""", unsafe_allow_html=True)

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Operations",  final_m['total_ops'],
                   delta=final_m['total_ops']-orig_m['total_ops'], delta_color="inverse")
        sm2.metric("Logic Depth", final_m['depth'],
                   delta=final_m['depth']-orig_m['depth'], delta_color="inverse")
        sm3.metric("Exec Cost",   final_m['cost'],
                   delta=final_m['cost']-orig_m['cost'], delta_color="inverse")
        sm4.metric("Expr Length", len(final_expr),
                   delta=len(final_expr)-len(expr_working), delta_color="inverse")

        st.markdown("### Generated Firmware C Code")
        st.code(opt_code, language='c')
        st.download_button(
            "⬇ Download C Code", data=opt_code,
            file_name="aura_pillar4_optimized.c", mime="text/plain",
            use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYSIS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

with tab_analysis:
    st.markdown("## Analysis Dashboard")
    st.caption("All 9 features — original vs optimized, side by side.")
    st.markdown("")

    # Feature 1
    with st.expander("Feature 1 — Expression Analysis", expanded=True):
        metrics_pairs = [
            ("Variables",        n_vars,              n_vars),
            ("Terms",            orig_m['terms'],     final_m['terms']),
            ("AND ops",          orig_m['and'],       final_m['and']),
            ("OR ops",           orig_m['or'],        final_m['or']),
            ("NOT ops",          orig_m['not'],       final_m['not']),
            ("Logic depth",      orig_m['depth'],     final_m['depth']),
            ("Expression length",len(expr_working),   len(final_expr)),
        ]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Original:** `{expr_working}`")
            for lbl, ov, _ in metrics_pairs:
                st.write(f"• {lbl}: **{ov}**")
        with c2:
            st.markdown(f"**Optimized:** `{final_expr}`")
            for lbl, ov, opt in metrics_pairs:
                diff = opt - ov
                col  = "green" if diff < 0 else ("red" if diff > 0 else "grey")
                ind  = f"({'−' if diff<0 else '+' if diff>0 else '='}{abs(diff)})" if diff else ""
                st.markdown(f"• {lbl}: **{opt}** <span style='color:{col}'>{ind}</span>",
                            unsafe_allow_html=True)

    # Feature 2
    with st.expander("Feature 2 — Truth Table", expanded=False):
        st.dataframe(
            pd.DataFrame(tt_rows).style.applymap(_style_out, subset=['Output']),
            use_container_width=True, height=300, hide_index=True)

    # Feature 3
    if use_kmap and n_vars <= 4 and kmap_html:
        with st.expander("Feature 3 — K-Map Visualization", expanded=False):
            st.markdown(kmap_html, unsafe_allow_html=True)
            st.caption("🟢 Green = 1  ·  🟡 Yellow = X  ·  ⬛ Dark = 0")

    # Feature 4
    with st.expander("Feature 4 — Simplified Expression Comparison", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original expression:**")
            st.code(expr_working, language=None)
        with c2:
            st.markdown("**Simplified expression:**")
            st.code(final_expr, language=None)
        saving_pct = (orig_m['cost'] - final_m['cost']) / max(orig_m['cost'], 1) * 100
        st.markdown(
            f"<div class='chip-green'>✅ {saving_pct:.1f}% cost reduction via minimization</div>",
            unsafe_allow_html=True)

    # Feature 5
    with st.expander("Feature 5 — Algorithm Comparison", expanded=True):
        st.dataframe(pd.DataFrame([
            {'Algorithm': 'K-Map',       'Best for': '≤4 vars', 'Time complexity': 'O(n·2^n)',
             'PIs found': len(prime_implicants), 'Result': minimized_expr[:50]},
            {'Algorithm': 'QMC+Petrick', 'Best for': 'any n',   'Time complexity': f'{qmc_time_ms:.3f} ms',
             'PIs found': len(prime_implicants), 'Result': minimized_expr[:50]},
        ]), use_container_width=True, hide_index=True)

    # Feature 6
    with st.expander("Feature 6 — Complexity Meter", expanded=True):
        st.markdown("**Formula:** `Score = 2×AND + 2×OR + 1×NOT + 3×depth + 2×terms`")
        c1, c2, c3 = st.columns(3)
        c1.metric("Original score",  orig_m['complexity'])
        c2.metric("Optimized score", final_m['complexity'],
                  delta=final_m['complexity']-orig_m['complexity'], delta_color="inverse")
        imp = (orig_m['complexity']-final_m['complexity'])/max(orig_m['complexity'],1)*100
        c3.metric("Improvement", f"{imp:.1f}%")
        st.progress(min(1.0, final_m['complexity']/max(orig_m['complexity'],1)))
        st.caption("Bar shows optimized score as fraction of original. Lower = better.")

    # Feature 7
    with st.expander("Feature 7 — Optimization Suggestions", expanded=True):
        suggestions = []
        terms_list = [t.strip().strip('()') for t in expr_working.split('+')]
        if len(terms_list) >= 2:
            def _get_lits(t):
                return set(l.strip() for l in t.split('&') if l.strip())
            lit_sets = [_get_lits(t) for t in terms_list]
            common   = lit_sets[0].copy()
            for s in lit_sets[1:]:
                common &= s
            if common:
                suggestions.append(f"**Common factor `{' & '.join(sorted(common))}` detected** — factoring reduces AND ops and expression length.")
        if orig_m['not'] > 0:
            suggestions.append(f"**{orig_m['not']} NOT op(s)** detected. NOT costs 3× more than OR on embedded MCUs.")
        if not dont_cares and n_vars >= 3:
            suggestions.append("**No don't-cares provided.** SSD states like (block_bad AND erase_count=0) may be impossible — adding them expands groups.")
        if orig_m['depth'] >= 2:
            suggestions.append(f"**Logic depth {orig_m['depth']}** → {final_m['depth']} after optimization. Lower depth = fewer sequential CPU dependencies.")
        if not minterms:
            suggestions.append("⚠ Expression = 0 for all inputs. Verify your expression.")
        elif len(minterms) == 2**n_vars:
            suggestions.append("ℹ Expression is a tautology (always 1). Can simplify to constant `1`.")
        if not suggestions:
            suggestions.append("✅ Expression is well-optimized for this variable/minterm set.")
        for s in suggestions:
            st.markdown(f"• {s}")

    # Feature 8
    with st.expander("Feature 8 — Firmware Efficiency Metrics", expanded=True):
        def _pct(a, b):
            return f"{(a-b)/max(a,1)*100:.1f}%"
        eff_rows = [
            {'Metric': 'Total operations',  'Before': orig_m['total_ops'],  'After': final_m['total_ops'],
             'Saved': orig_m['total_ops'] -final_m['total_ops'],  'Reduction': _pct(orig_m['total_ops'],  final_m['total_ops'])},
            {'Metric': 'Logic depth',       'Before': orig_m['depth'],      'After': final_m['depth'],
             'Saved': orig_m['depth']-final_m['depth'],           'Reduction': _pct(orig_m['depth'],      final_m['depth'])},
            {'Metric': 'AND operations',    'Before': orig_m['and'],        'After': final_m['and'],
             'Saved': orig_m['and']-final_m['and'],               'Reduction': _pct(orig_m['and'],        final_m['and'])},
            {'Metric': 'NOT operations',    'Before': orig_m['not'],        'After': final_m['not'],
             'Saved': orig_m['not']-final_m['not'],               'Reduction': _pct(orig_m['not'],        final_m['not'])},
            {'Metric': 'Execution cost',    'Before': orig_m['cost'],       'After': final_m['cost'],
             'Saved': orig_m['cost']-final_m['cost'],             'Reduction': _pct(orig_m['cost'],       final_m['cost'])},
            {'Metric': 'Complexity score',  'Before': orig_m['complexity'], 'After': final_m['complexity'],
             'Saved': orig_m['complexity']-final_m['complexity'], 'Reduction': _pct(orig_m['complexity'], final_m['complexity'])},
            {'Metric': 'Expression length', 'Before': len(expr_working),    'After': len(final_expr),
             'Saved': len(expr_working)-len(final_expr),          'Reduction': _pct(len(expr_working),    len(final_expr))},
        ]
        st.dataframe(pd.DataFrame(eff_rows), use_container_width=True, hide_index=True)

    # Feature 9
    with st.expander("Feature 9 — Firmware Code Output", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original (unoptimized):**")
            st.code(orig_code, language='c')
        with c2:
            st.markdown("**Optimized:**")
            st.code(opt_code, language='c')

    # Final comparison table
    st.markdown("---")
    st.markdown("### 📋 Final Comparison — Before vs After")
    st.dataframe(pd.DataFrame([
        {'Metric': 'Expression',      'Before': expr_working,        'After': final_expr,             'Δ': '—'},
        {'Metric': 'Variables',       'Before': n_vars,              'After': n_vars,                 'Δ': '—'},
        {'Metric': 'Terms',           'Before': orig_m['terms'],     'After': final_m['terms'],       'Δ': f"{final_m['terms']-orig_m['terms']:+d}"},
        {'Metric': 'Total ops',       'Before': orig_m['total_ops'], 'After': final_m['total_ops'],   'Δ': f"{final_m['total_ops']-orig_m['total_ops']:+d}"},
        {'Metric': 'Logic depth',     'Before': orig_m['depth'],     'After': final_m['depth'],       'Δ': f"{final_m['depth']-orig_m['depth']:+d}"},
        {'Metric': 'Exec cost',       'Before': orig_m['cost'],      'After': final_m['cost'],        'Δ': f"{final_m['cost']-orig_m['cost']:+d}"},
        {'Metric': 'Complexity',      'Before': orig_m['complexity'],'After': final_m['complexity'],  'Δ': f"{final_m['complexity']-orig_m['complexity']:+d}"},
        {'Metric': 'BDD Verified',    'Before': '—',                 'After': '✅ PASS' if bdd_pass else '❌ FAIL', 'Δ': '—'},
    ]), use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — BUILT-IN TEST CASES
# ═════════════════════════════════════════════════════════════════════════════

with tab_tests:
    st.markdown("## 🧪 Built-in Test Cases")
    st.caption("Auto-executed, hardcoded reference tests — demonstrates the full pipeline on known inputs.")
    st.markdown("---")

    for tc in BUILTIN_TESTS:
        with st.expander(f"📌 {tc['label']}", expanded=True):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**Description:** {tc['description']}")
                st.markdown(f"**Input:** `{tc['expr']}`")
                st.markdown(f"**Don't-cares:** `{tc['dont_cares'] or 'None'}`")
                st.markdown(f"**Expected (approx):** `{tc['expected_simplified']}`")
            try:
                cr  = auto_correct(tc['expr'])
                ex  = cr.corrected if cr.valid else tc['expr']
                vrs = extract_variables(ex)
                n   = len(vrs)
                _tt_rows, _on, _off = generate_truth_table(ex, vrs, tc['dont_cares'])
                _pis, _steps = quine_mccluskey(_on, tc['dont_cares'], n)
                _sel, _cov, _ess = petricks_method(_pis, _on, n)
                _min = build_expression_from_pis(_sel, vrs)
                _fin = try_factor_expression(_min)
                _om  = compute_metrics(ex)
                _fm  = compute_metrics(_fin)

                _mm = []
                for i in range(2**n):
                    if i in tc['dont_cares']:
                        continue
                    asgn = {v: (i>>(n-1-j))&1 for j,v in enumerate(vrs)}
                    if safe_eval(ex, asgn) != (safe_eval(_fin, asgn) if _fin != '0' else 0):
                        _mm.append(i)
                _pass = len(_mm) == 0

                with c2:
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Orig ops",  _om['total_ops'])
                    r2.metric("Opt ops",   _fm['total_ops'],
                              delta=_fm['total_ops']-_om['total_ops'], delta_color="inverse")
                    r3.metric("Cost −%",   f"{(_om['cost']-_fm['cost'])/max(_om['cost'],1)*100:.0f}%")
                    r4.metric("BDD",       "✅" if _pass else "❌")

                st.markdown(f"**Optimized result:** `{_fin}`")

                use_kmap_tc = use_kmap and n <= 4
                if use_kmap_tc:
                    col_tt, col_km = st.columns(2)
                    with col_tt:
                        df_tc = pd.DataFrame(_tt_rows)
                        st.dataframe(
                            df_tc.style.applymap(_style_out, subset=['Output']),
                            use_container_width=True,
                            height=min(220, 40 + 35*len(_tt_rows)),
                            hide_index=True)
                    with col_km:
                        km = build_kmap_html(_on, tc['dont_cares'], vrs)
                        if km:
                            st.markdown(km, unsafe_allow_html=True)
                elif n <= 4:
                    df_tc = pd.DataFrame(_tt_rows)
                    st.dataframe(
                        df_tc.style.applymap(_style_out, subset=['Output']),
                        use_container_width=True,
                        height=min(220, 40 + 35*len(_tt_rows)),
                        hide_index=True)

            except Exception as e:
                st.error(f"Test case error: {e}")

    st.markdown("---")
    st.markdown("### 📋 Sample Input → Output Reference")
    st.dataframe(pd.DataFrame([
        {"Input":  "(A & B & C) + (A & B & D)", "Method": "K-Map",
         "Expected": "AB(C + D)", "BDD": "✅", "Cost Δ": "~−19%", "Note": "A, B are common → factored out"},
        {"Input":  "A + !A",                     "Method": "K-Map",
         "Expected": "tautology",  "BDD": "✅", "Cost Δ": "0%",    "Note": "Always 1 — cannot reduce"},
        {"Input":  "(A & B) + (A & B & C)",      "Method": "K-Map",
         "Expected": "A & B",       "BDD": "✅", "Cost Δ": "~−30%", "Note": "Subsumption law"},
        {"Input":  "(!A & !B) + (!A & B) + (A & !B)", "Method": "K-Map",
         "Expected": "!A + !B",     "BDD": "✅", "Cost Δ": "~−40%", "Note": "DeMorgan adjacency"},
        {"Input":  "a & b & c",                  "Method": "Hybrid ✏",
         "Expected": "A & B & C",   "BDD": "✅", "Cost Δ": "0%",    "Note": "Autocorrect: lowercase → upper"},
        {"Input":  "A * B + A || C",             "Method": "Hybrid ✏",
         "Expected": "A & (B + C)", "BDD": "✅", "Cost Δ": "varies","Note": "Autocorrect: * → & and || → +"},
    ]), use_container_width=True, hide_index=True)
