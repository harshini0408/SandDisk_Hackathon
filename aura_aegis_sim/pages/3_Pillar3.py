"""
AURA - Pillar 3: AEGIS - Adaptive ECC & Grade-Intelligent Supervision
Three-tab layout: Tab 1 = NAND Grid, Tab 2 = Decoder Pipeline, Tab 3 = Telemetry & Aging
Python 3.11 safe: no backslash inside f-string expressions.
"""
import streamlit as st
import time, os, sys, pickle, random
import numpy as np
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Pillar 3 - AEGIS | AURA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600;700&display=swap');
html,body,[data-testid="stApp"]{background:#0a0a0f!important;color:#e8e8f0!important;font-family:'Inter',sans-serif!important;}
h1,h2,h3,h4{font-family:'JetBrains Mono',monospace!important;color:#e8e8f0!important;}
[data-testid="stSidebar"]{background:#12121a!important;border-right:1px solid #2a2a3a;}
div[data-testid="stMetricValue"]{color:#a855f7!important;font-size:1.4rem!important;font-weight:700!important;}
div[data-testid="stMetricLabel"]{color:#8888a0!important;font-size:0.72rem!important;}
div[data-baseweb="tab-list"]{background:#12121a!important;border-bottom:1px solid #2a2a3a!important;}
div[data-baseweb="tab"]{color:#8888a0!important;}
div[data-baseweb="tab"][aria-selected="true"]{color:#3b82f6!important;border-bottom:2px solid #3b82f6!important;}
.stButton>button{background:linear-gradient(135deg,#1a1a2e,#2a1a3e)!important;border:1px solid #7c3aed!important;color:#e8e8f0!important;font-family:'JetBrains Mono',monospace!important;border-radius:6px!important;font-weight:600!important;}
.stButton>button:hover{border-color:#3b82f6!important;}
.sec-label{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;color:#8888a0;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;}
</style>
""", unsafe_allow_html=True)

# ─── LOAD ML MODEL ────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base, 'models', 'voltage_model.pkl')
    if os.path.exists(p):
        with open(p, 'rb') as fh:
            return pickle.load(fh)
    return None

MODEL = load_model()

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if 'blocks' not in st.session_state:
    random.seed(42)
    st.session_state.blocks = [
        {'id': i, 'pe_cycles': random.randint(0, 4800), 'ldpc_iterations': [],
         'retired': i in [3, 11], 'tier3_triggers': 0,
         'ldpc_avg': round(random.uniform(1, 5), 2)}
        for i in range(64)
    ]
if 'read_log'       not in st.session_state: st.session_state.read_log       = []
if 'selected_block' not in st.session_state: st.session_state.selected_block  = 7
if 'bbt'            not in st.session_state: st.session_state.bbt             = [1 if i in [3,11] else 0 for i in range(32)]
if 'tier_stats'     not in st.session_state: st.session_state.tier_stats      = {'t1':0,'t2':0,'t3':0}
if 'ps'             not in st.session_state: st.session_state.ps              = {'t1':'idle','t2':'idle','t3':'idle','t1e':'','t2e':'','t3e':''}

# ─── SHARED CONSTANTS & HELPERS ──────────────────────────────────────────────
HEALTH_TEXT_COLOR = {
    'healthy':'#22c55e', 'worn':'#f59e0b',
    'degraded':'#f97316', 'critical':'#ef4444', 'RETIRED':'#4a4a60'
}
BLOCK_COLORS = {
    'G': ('#22c55e','#052e16'),
    'W': ('#f59e0b','#3d2600'),
    'D': ('#f97316','#3d1200'),
    'C': ('#ef4444','#3d0000'),
    'X': ('#4a4a60','#1a1a1a'),
}

def health_label(blk):
    if blk['retired']: return 'RETIRED'
    pe = blk['pe_cycles']
    if pe < 1500: return 'healthy'
    if pe < 3000: return 'worn'
    if pe < 4500: return 'degraded'
    return 'critical'

def block_key(blk):
    if blk['retired']: return 'X'
    pe = blk['pe_cycles']
    if pe < 1500: return 'G'
    if pe < 3000: return 'W'
    if pe < 4500: return 'D'
    return 'C'

def rber_est(pe):
    return min(1e-3, 1e-7 * (1.05 ** (pe / 100)))

def route_read(bit_errors, block_health, pe_cycles, mdl):
    if bit_errors == 0:
        return {'tier':1,'latency_us':0.0,'status':'BYPASS','iterations':0,'mode':'Syndrome Zero'}
    if bit_errors <= 12:
        return {'tier':2,'mode':'BCH','latency_us':round(random.uniform(0.3,0.8),2),'iterations':0,'status':'BCH_CORRECTED'}
    max_iter = {'healthy':8,'worn':12,'degraded':20,'critical':20}.get(block_health, 8)
    capacity = max_iter * 3
    if bit_errors <= capacity:
        iters = min(int(bit_errors / 3) + 1, max_iter)
        return {'tier':2,'mode':'Hard LDPC','latency_us':round(iters*0.15,2),'iterations':iters,'status':'LDPC_CORRECTED'}
    vs = round(random.uniform(15, 45), 1)
    if mdl:
        try:
            vs = round(float(mdl.predict([[pe_cycles,45,30,pe_cycles/5000*100,pe_cycles*0.008]])[0]),1)
        except Exception:
            pass
    return {'tier':3,'mode':'ML Soft-LDPC','voltage_shift_mv':vs,
            'latency_us':round(random.uniform(3.2,5.8),2),'iterations':20,'status':'ML_RECOVERED'}

# ─── TIER HTML (safe string concat) ──────────────────────────────────────────
TIER_BOX_CSS = {
    'idle':   'background:#12121a;border:1px solid #2a2a3a;border-left:4px solid #4a4a60;',
    'active': 'background:#0d1e2e;border:1px solid #3b82f6;border-left:4px solid #3b82f6;box-shadow:0 0 12px rgba(59,130,246,.3);',
    'pass':   'background:#051e10;border:1px solid #22c55e;border-left:4px solid #22c55e;box-shadow:0 0 10px rgba(34,197,94,.3);',
    'fail':   'background:#1e0505;border:1px solid #ef4444;border-left:4px solid #ef4444;',
    'recover':'background:#0d0623;border:1px solid #a855f7;border-left:4px solid #a855f7;box-shadow:0 0 14px rgba(168,85,247,.4);',
}
TIER_STATUS = {
    'idle':   ('IDLE',        '#4a4a60'),
    'active': ('ACTIVE ...',  '#3b82f6'),
    'pass':   ('PASS OK',     '#22c55e'),
    'fail':   ('FAIL X',      '#ef4444'),
    'recover':('RECOVERED',   '#a855f7'),
}
TIER_ACCENT = {1:'#14b8a6', 2:'#f59e0b', 3:'#ff6b6b'}

def tier_html(num, label, desc, state, extra=''):
    bcss      = TIER_BOX_CSS.get(state, TIER_BOX_CSS['idle'])
    stxt,scol = TIER_STATUS.get(state, TIER_STATUS['idle'])
    ac        = TIER_ACCENT.get(num,'#888')
    xtra      = ('<div style="margin-top:6px;font-size:11px;color:#e8e8f0;font-family:JetBrains Mono,monospace">' + extra + '</div>') if extra else ''
    return (
        "<div style='" + bcss + "border-radius:10px;padding:14px 16px;margin-bottom:10px;transition:all 0.3s'>"
        "<div style='display:flex;justify-content:space-between;align-items:center'>"
        "<div><span style='font-size:10px;color:" + ac + ";font-weight:700;text-transform:uppercase;letter-spacing:1px'>Tier " + str(num) + "</span>"
        "<span style='font-size:13px;color:#e8e8f0;font-weight:700;margin-left:8px'>" + label + "</span></div>"
        "<span style='font-size:11px;color:" + scol + ";font-weight:700'>" + stxt + "</span></div>"
        "<div style='color:#8888a0;font-size:11px;margin-top:4px'>" + desc + "</div>" + xtra + "</div>"
    )

def render_pipeline(ph, t1='idle', t2='idle', t3='idle', t1e='', t2e='', t3e=''):
    arrow = "<div style='text-align:center;color:#2a2a3a;font-size:18px;margin:-2px 0'>↓</div>"
    ph.markdown(
        tier_html(1,'Syndrome Zero Bypass',    'Parity check H·r = 0  ·  0 µs bypass path',         t1, t1e) + arrow +
        tier_html(2,'BCH + Hard-Decision LDPC','Normalized Min-Sum  ·  up to 20 iterations',          t2, t2e) + arrow +
        tier_html(3,'ML Soft-Decision LDPC',   '3.3 KB Decision Tree  ·  voltage shift prediction',   t3, t3e),
        unsafe_allow_html=True
    )

def make_ldpc_chart(iters, block_id, alarm=False):
    xs  = list(range(1, len(iters)+1))
    lc  = '#ef4444' if alarm else '#3b82f6'
    fig = go.Figure()
    fig.add_hline(y=15, line_dash='dash', line_color='#ef4444',
                  annotation_text='  PRE-FAILURE THRESHOLD', annotation_position='top left',
                  annotation_font={'color':'#ef4444','size':10})
    fig.add_trace(go.Scatter(x=xs, y=iters, mode='lines+markers',
        line={'color':lc,'width':2.5}, marker={'size':5,'color':'#a855f7'},
        fill='tozeroy', fillcolor='rgba(59,130,246,0.07)'))
    fig.update_layout(
        title={'text':'LDPC Iters - Block ' + str(block_id),
               'font':{'family':'JetBrains Mono','size':13,'color':'#e8e8f0'}},
        yaxis={'range':[0,22],'gridcolor':'#1e1e2e','title':'Iterations'},
        xaxis={'gridcolor':'#1e1e2e','title':'Read #'},
        height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'color':'#8888a0'}, margin={'l':40,'r':10,'t':44,'b':30}, showlegend=False)
    return fig

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='display:flex;align-items:center;gap:12px;margin-bottom:4px'>"
    "<span style='font-size:1.8rem'>🛡️</span>"
    "<div><div style='font-family:JetBrains Mono,monospace;font-size:1.25rem;font-weight:700;color:#e8e8f0'>"
    "AEGIS — Adaptive ECC &amp; Grade-Intelligent Supervision</div>"
    "<div style='color:#8888a0;font-size:12px'>Pillar 3 &nbsp;·&nbsp;"
    "<span style='color:#22c55e'>■</span> Healthy &nbsp;"
    "<span style='color:#f59e0b'>■</span> Worn &nbsp;"
    "<span style='color:#f97316'>■</span> Degraded &nbsp;"
    "<span style='color:#ef4444'>■</span> Critical &nbsp;"
    "<span style='color:#4a4a60'>■</span> Retired</div></div></div>",
    unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🛡️ AURA Navigation")
    st.page_link("app.py",             label="Home",     icon="🏠")
    st.page_link("pages/0_Manual.py",  label="Manual",   icon="📖")
    st.page_link("pages/1_Pillar1.py", label="Pillar 1", icon="🧠")
    st.page_link("pages/2_Pillar2.py", label="Pillar 2", icon="🗃️")
    st.page_link("pages/3_Pillar3.py", label="Pillar 3", icon="🛡️")
    st.page_link("pages/4_Pillar4.py", label="Pillar 4", icon="⚙️")
    st.divider()
    if st.button("🔌 Cold Boot", key='cold_boot', use_container_width=True):
        cph = st.empty()
        for msg in ["[P2] BBT rebuilt — Bloom Filter online",
                    "[P3] ML model loaded (3.3 KB firmware RAM)",
                    "[P3] ECC thresholds calibrated per block"]:
            cph.success("✅ " + msg); time.sleep(0.4)
        cph.empty(); st.toast("AEGIS Online ✅", icon="🛡️")

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📦  NAND Block Grid",
    "⚡  Live Decoder Pipeline",
    "📊  Telemetry & Aging",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NAND BLOCK GRID
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 📦 NAND Physical Block Array (8 × 8 = 64 blocks)")
    st.markdown(
        "<div style='color:#8888a0;font-size:12px;margin-bottom:12px'>"
        "Select any block to target it for reads and aging. "
        "Colors update as blocks accumulate P/E cycles.</div>",
        unsafe_allow_html=True)

    # 8×8 colored HTML grid
    grid_html = "<div style='display:flex;flex-direction:column;gap:3px;margin-bottom:16px'>"
    for row in range(8):
        grid_html += "<div style='display:flex;gap:3px'>"
        for c in range(8):
            bid  = row * 8 + c
            blk  = st.session_state.blocks[bid]
            ekey = block_key(blk)
            tc, bg = BLOCK_COLORS.get(ekey, ('#888','#222'))
            border = '2px solid #ffffff' if bid == st.session_state.selected_block else '2px solid transparent'
            grid_html += (
                "<div style='width:46px;height:46px;background:" + bg + ";color:" + tc +
                ";border-radius:5px;border:" + border +
                ";display:flex;align-items:center;justify-content:center;"
                "font-family:JetBrains Mono,monospace;font-size:9px;font-weight:700'>"
                "B" + str(bid) + "</div>"
            )
        grid_html += "</div>"
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

    # Legend
    st.markdown(
        "<div style='display:flex;gap:16px;flex-wrap:wrap;font-family:JetBrains Mono,monospace;font-size:11px;margin-bottom:14px'>"
        "<span><span style='color:#22c55e'>■</span> Healthy (0–1500 P/E)</span>"
        "<span><span style='color:#f59e0b'>■</span> Worn (1500–3000)</span>"
        "<span><span style='color:#f97316'>■</span> Degraded (3000–4500)</span>"
        "<span><span style='color:#ef4444'>■</span> Critical (&gt;4500)</span>"
        "<span><span style='color:#4a4a60'>■</span> Retired (in BBT)</span></div>",
        unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#2a2a3a;margin:4px 0 12px'/>", unsafe_allow_html=True)

    # Block selector
    st.markdown("**Select Block:**")
    sc1, sc2, sc3 = st.columns([2, 1, 3])
    new_sel = sc1.number_input("Block ID", 0, 63, st.session_state.selected_block,
                               label_visibility='collapsed', key='block_num_t1')
    if sc2.button("Select", key='blk_go_t1', use_container_width=True):
        st.session_state.selected_block = int(new_sel)
        st.rerun()

    st.markdown("<hr style='border-color:#2a2a3a;margin:12px 0'/>", unsafe_allow_html=True)

    # Stats grid — two columns
    gs1, gs2 = st.columns(2)

    with gs1:
        st.markdown("**Selected Block Stats**")
        sid  = st.session_state.selected_block
        blk  = st.session_state.blocks[sid]
        hlbl = health_label(blk)
        hc   = HEALTH_TEXT_COLOR.get(hlbl, '#888')
        pe   = blk['pe_cycles']
        wear = round(pe / 5000 * 100, 1)
        rber = rber_est(pe)
        avgi = round(float(np.mean(blk['ldpc_iterations'][-20:])) if blk['ldpc_iterations'] else blk['ldpc_avg'], 2)

        rows = [
            ('Block ID',       str(sid),                   '#e8e8f0'),
            ('P/E Cycles',     str(pe) + ' / 5000',        '#e8e8f0'),
            ('Wear Level',     str(wear) + '%',             '#e8e8f0'),
            ('Avg LDPC Iters', str(avgi),                   '#e8e8f0'),
            ('RBER Estimate',  '{:.2e}'.format(rber),       '#e8e8f0'),
            ('Tier 3 Hits',    str(blk['tier3_triggers']),  '#ff6b6b'),
            ('Health Status',  hlbl.upper(),                hc),
        ]
        rows_html = ''
        for lbl_s, val_s, vc in rows:
            rows_html += (
                "<tr><td style='color:#8888a0;padding:4px 0;font-size:12px'>" + lbl_s + "</td>"
                "<td style='color:" + vc + ";text-align:right;font-weight:700;font-size:12px'>" + val_s + "</td></tr>"
            )
        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid " + hc +
            ";border-radius:8px;padding:16px;font-family:JetBrains Mono,monospace'>"
            "<table style='width:100%;border-collapse:collapse'>" + rows_html + "</table></div>",
            unsafe_allow_html=True)

    with gs2:
        st.markdown("**All Blocks Summary**")
        retired_n  = sum(1 for b in st.session_state.blocks if b['retired'])
        healthy_n  = sum(1 for b in st.session_state.blocks if not b['retired'] and b['pe_cycles'] < 1500)
        worn_n     = sum(1 for b in st.session_state.blocks if not b['retired'] and 1500 <= b['pe_cycles'] < 3000)
        degraded_n = sum(1 for b in st.session_state.blocks if not b['retired'] and 3000 <= b['pe_cycles'] < 4500)
        critical_n = sum(1 for b in st.session_state.blocks if not b['retired'] and b['pe_cycles'] >= 4500)

        sm1, sm2 = st.columns(2)
        sm1.metric("Healthy",  healthy_n)
        sm2.metric("Worn",     worn_n)
        sm3, sm4 = st.columns(2)
        sm3.metric("Degraded", degraded_n)
        sm4.metric("Critical", critical_n)
        sm5, sm6 = st.columns(2)
        sm5.metric("Retired",  retired_n)
        sm6.metric("Active",   64 - retired_n)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset All Blocks", key='reset_t1', use_container_width=True):
            random.seed(int(time.time()))
            st.session_state.blocks = [
                {'id':i,'pe_cycles':random.randint(0,4800),'ldpc_iterations':[],
                 'retired':i in [3,11],'tier3_triggers':0,'ldpc_avg':round(random.uniform(1,5),2)}
                for i in range(64)]
            st.session_state.bbt        = [1 if i in [3,11] else 0 for i in range(32)]
            st.session_state.read_log   = []
            st.session_state.tier_stats = {'t1':0,'t2':0,'t3':0}
            st.session_state.ps         = {'t1':'idle','t2':'idle','t3':'idle','t1e':'','t2e':'','t3e':''}
            st.rerun()

    # Mini RBER chart per health tier
    st.markdown("<hr style='border-color:#2a2a3a;margin:12px 0'/>", unsafe_allow_html=True)
    st.markdown("**RBER vs P/E Cycle Distribution**")
    pe_vals   = [b['pe_cycles'] for b in st.session_state.blocks if not b['retired']]
    rber_vals = [rber_est(p) for p in pe_vals]
    scatter   = go.Figure(go.Scatter(
        x=pe_vals, y=rber_vals, mode='markers',
        marker={'color':[b['pe_cycles'] for b in st.session_state.blocks if not b['retired']],
                'colorscale':'Plasma','size':7,'opacity':0.8},
        text=['B' + str(b['id']) for b in st.session_state.blocks if not b['retired']],
        hovertemplate='<b>%{text}</b><br>P/E: %{x}<br>RBER: %{y:.2e}<extra></extra>'
    ))
    scatter.update_layout(
        xaxis={'title':'P/E Cycles','gridcolor':'#1e1e2e'},
        yaxis={'title':'RBER Estimate','gridcolor':'#1e1e2e'},
        height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'color':'#8888a0'}, margin={'l':40,'r':10,'t':10,'b':40})
    st.plotly_chart(scatter, use_container_width=True, key='rber_scatter')

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LIVE DECODER PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ⚡ Live Decoder Pipeline")
    st.markdown(
        "<div style='color:#8888a0;font-size:12px;margin-bottom:14px'>"
        "Fire a read request on the selected block. Watch the packet travel through the three-tier ECC system.</div>",
        unsafe_allow_html=True)

    p2c1, p2c2, p2c3 = st.columns([1.5, 1.5, 1])

    with p2c1:
        st.markdown("**Decoder Pipeline**")
        pipeline_ph = st.empty()
        ps = st.session_state.ps
        render_pipeline(pipeline_ph, ps['t1'], ps['t2'], ps['t3'], ps['t1e'], ps['t2e'], ps['t3e'])
        result_ph = st.empty()

    with p2c2:
        st.markdown("**Request Configuration**")

        # Current block info banner
        sid  = st.session_state.selected_block
        blk  = st.session_state.blocks[sid]
        hlbl = health_label(blk)
        hc   = HEALTH_TEXT_COLOR.get(hlbl, '#888')
        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid " + hc +
            ";border-radius:8px;padding:10px 14px;margin-bottom:12px;font-family:JetBrains Mono,monospace;font-size:12px'>"
            "Target: <b>Block " + str(sid) + "</b> &nbsp;·&nbsp; "
            "P/E: <b>" + str(blk['pe_cycles']) + "</b> &nbsp;·&nbsp; "
            "Health: <span style='color:" + hc + ";font-weight:700'>" + hlbl.upper() + "</span>"
            + (" &nbsp;<span style='color:#ef4444;font-weight:700'>⚠ RETIRED</span>" if blk['retired'] else "") +
            "</div>",
            unsafe_allow_html=True)

        bit_errors  = st.slider("Injected Bit Errors", 0, 150, 0, key='err_slider_t2')
        hlth_ovr    = st.selectbox("Block Condition Override",
                                   ["auto","healthy","worn","degraded","critical"], key='hlth_t2')

        preset = st.selectbox("Quick Demo Preset", [
            "custom",
            "Moment 1 — Bypass (0 errors)",
            "Moment 2 — ML Recovery (80 errors)",
            "Moment 3 — Read Retired Block",
        ], key='preset_t2', label_visibility='collapsed')

        if "Moment 1" in preset: bit_errors = 0
        elif "Moment 2" in preset: bit_errors = 80

        fire_btn = st.button("▶  Fire Read Request", type='primary',
                             use_container_width=True, key='fire_t2')

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#0a0a14;border:1px solid #2a2a3a;border-radius:8px;"
            "padding:12px 14px;font-family:JetBrains Mono,monospace;font-size:11px'>"
            "<div style='color:#60a5fa;font-weight:700;margin-bottom:8px;font-size:10px;text-transform:uppercase'>Routing Logic</div>"
            "errors = 0 &nbsp;→&nbsp; <span style='color:#14b8a6'>Tier 1 Bypass</span><br>"
            "errors 1-12 &nbsp;→&nbsp; <span style='color:#f59e0b'>BCH correction</span><br>"
            "errors 13-60 &nbsp;→&nbsp; <span style='color:#f59e0b'>Hard LDPC</span><br>"
            "errors &gt; 60 &nbsp;→&nbsp; <span style='color:#ff6b6b'>ML Soft-LDPC</span><br>"
            "<span style='color:#ef4444'>RETIRED</span> &nbsp;→&nbsp; <span style='color:#ef4444'>Bloom Filter kill 0µs</span>"
            "</div>", unsafe_allow_html=True)

    with p2c3:
        st.markdown("**Session Stats**")
        tsd   = st.session_state.tier_stats
        total = tsd['t1'] + tsd['t2'] + tsd['t3']
        t1r   = round(tsd['t1']/total*100,1) if total else 0.0
        ai    = [b['ldpc_avg'] for b in st.session_state.blocks if b['ldpc_iterations'] and not b['retired']]
        avgt2 = round(float(np.mean(ai)),1) if ai else 0.0
        rber2 = rber_est(blk['pe_cycles'])
        st.metric("T1 Bypass",   str(t1r) + '%')
        st.metric("T3 Triggers", tsd['t3'])
        st.metric("Avg T2 Iters",avgt2)
        st.metric("RBER",        '{:.1e}'.format(rber2))

        if total > 0:
            donut = go.Figure(go.Pie(
                labels=['Tier 1','Tier 2','Tier 3'],
                values=[tsd['t1'],tsd['t2'],tsd['t3']],
                hole=0.55,
                marker_colors=['#14b8a6','#f59e0b','#ff6b6b'],
                textinfo='percent',
                textfont={'family':'JetBrains Mono','size':9,'color':'#e8e8f0'}
            ))
            donut.update_layout(
                showlegend=False, height=160,
                margin={'l':0,'r':0,'t':10,'b':0},
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(donut, use_container_width=True, key='donut_t2')

    # ── FIRE LOGIC ────────────────────────────────────────────────────────────
    if fire_btn:
        sid  = st.session_state.selected_block
        blk  = st.session_state.blocks[sid]
        hlbl = health_label(blk)
        eff  = hlbl if hlth_ovr == 'auto' else hlth_ovr

        render_pipeline(pipeline_ph)

        if blk['retired']:
            sid_s = str(sid)
            result_ph.markdown(
                "<div style='background:#1a0505;border:1px solid #ef4444;border-radius:8px;"
                "padding:14px;font-family:JetBrains Mono,monospace;margin-top:8px'>"
                "<b style='color:#ef4444'>🚫 BLOOM FILTER BLOCKED — 0.05 µs</b><br>"
                "<span style='color:#8888a0;font-size:11px'>Block " + sid_s + " is in the BBT. Pipeline never activated.</span><br>"
                "<span style='color:#22c55e;font-size:11px'>Zero latency rejection — UECC impossible</span></div>",
                unsafe_allow_html=True)
            st.session_state.read_log.append({'ts':time.strftime('%H:%M:%S'),'bid':sid,'tier':'BBT','lat':'0.05 us','outcome':'REJECTED','err':bit_errors})

        else:
            render_pipeline(pipeline_ph, t1='active', t1e='Running syndrome check H·r ...')
            time.sleep(0.6)
            res  = route_read(bit_errors, eff, blk['pe_cycles'], MODEL)
            t    = res['tier']
            lat  = res['latency_us']
            itr  = res.get('iterations', 0)
            lat_s = str(lat); sid_s = str(sid); err_s = str(bit_errors)

            if t == 1:
                render_pipeline(pipeline_ph, t1='pass', t1e='H·r = 0  |  No errors  |  0 µs')
                result_ph.markdown(
                    "<div style='background:#051e10;border:1px solid #22c55e;border-radius:8px;"
                    "padding:14px;font-family:JetBrains Mono,monospace;margin-top:8px'>"
                    "<b style='color:#22c55e'>✅ MOMENT 1 — SYNDROME ZERO BYPASS</b><br>"
                    "<span style='color:#8888a0;font-size:11px'>H·r = 0. Zero errors. Data returned instantly.</span><br>"
                    "<span style='color:#22c55e;font-size:12px'>Latency: 0 µs  |  Tier 1  |  No CPU overhead</span><br>"
                    "<span style='color:#4a4a60;font-size:10px'>[Pillar 4 QMC: 44% logic cost reduction]</span></div>",
                    unsafe_allow_html=True)
                st.session_state.tier_stats['t1'] += 1
                st.session_state.ps = {'t1':'pass','t2':'idle','t3':'idle','t1e':'H·r=0 BYPASS','t2e':'','t3e':''}

            elif t == 2:
                render_pipeline(pipeline_ph, t1='fail', t2='active', t1e='Syndrome != 0 — escalating')
                time.sleep(0.3)
                mode = res['mode']
                if itr > 0:
                    for i in range(1, itr + 1):
                        render_pipeline(pipeline_ph, t1='fail', t2='active',
                                        t1e='Syndrome != 0',
                                        t2e='Hard LDPC Iter ' + str(i) + ' / ' + str(itr))
                        time.sleep(0.1)
                t2done = mode + '  |  ' + str(itr) + ' iters  |  ' + lat_s + ' µs'
                render_pipeline(pipeline_ph, t1='fail', t2='pass', t1e='Syndrome != 0', t2e=t2done)
                warn = ''
                if itr >= 15:
                    warn = "<br><span style='color:#ef4444;font-weight:700'>⚠️ ITERS &gt;= 15 — Pre-failure flag sent to Pillar 1!</span>"
                result_ph.markdown(
                    "<div style='background:#1e1200;border:1px solid #f59e0b;border-radius:8px;"
                    "padding:14px;font-family:JetBrains Mono,monospace;margin-top:8px'>"
                    "<b style='color:#f59e0b'>" + mode.upper() + " CORRECTION</b><br>"
                    "<span style='color:#8888a0;font-size:11px'>Block " + sid_s + "  |  " + err_s + " errors  |  " + str(itr) + " iters</span><br>"
                    "<span style='color:#f59e0b;font-size:12px'>Latency: " + lat_s + " µs  |  Tier 2</span>"
                    + warn + "</div>",
                    unsafe_allow_html=True)
                blk['ldpc_iterations'].append(itr)
                blk['ldpc_avg'] = float(np.mean(blk['ldpc_iterations'][-20:]))
                st.session_state.tier_stats['t2'] += 1
                st.session_state.ps = {'t1':'fail','t2':'pass','t3':'idle','t1e':'Syndrome != 0','t2e':t2done,'t3e':''}

            else:
                render_pipeline(pipeline_ph, t1='fail', t2='fail', t3='active',
                                t1e='Syndrome != 0', t2e='LDPC exhausted')
                time.sleep(0.5)
                vs    = res.get('voltage_shift_mv', 0)
                vs_s  = str(vs); pe_s = str(blk['pe_cycles'])
                t3msg = 'ML: PE=' + pe_s + ' → ΔV=+' + vs_s + ' mV — RECOVERED'
                render_pipeline(pipeline_ph, t1='fail', t2='fail', t3='recover',
                                t1e='Syndrome != 0', t2e='LDPC exhausted', t3e=t3msg)
                result_ph.markdown(
                    "<div style='background:#0d0623;border:1px solid #a855f7;border-radius:8px;"
                    "padding:14px;font-family:JetBrains Mono,monospace;margin-top:8px'>"
                    "<b style='color:#a855f7'>✅ MOMENT 2 — ML SOFT-DECISION RECOVERY</b><br>"
                    "<span style='color:#8888a0;font-size:11px'>3.3 KB Decision Tree — optimal voltage offset predicted</span><br>"
                    "<span style='color:#a855f7;font-size:12px'>Shift: +" + vs_s + " mV  |  Latency: " + lat_s + " µs  |  Tier 3</span><br>"
                    "<span style='color:#ef4444;font-size:11px;font-weight:700'>⚠ Tier 3 → Pre-failure flag → Pillar 1 FTL</span><br>"
                    "<span style='color:#4a4a60;font-size:10px'>[SKLearn DecisionTree depth=4  |  3.4 KB  |  firmware-ready]</span></div>",
                    unsafe_allow_html=True)
                blk['ldpc_iterations'].append(20)
                blk['tier3_triggers'] += 1
                blk['ldpc_avg'] = float(np.mean(blk['ldpc_iterations'][-20:]))
                st.session_state.tier_stats['t3'] += 1
                st.session_state.ps = {'t1':'fail','t2':'fail','t3':'recover','t1e':'Syndrome != 0','t2e':'LDPC exhausted','t3e':t3msg}

            st.session_state.read_log.append({
                'ts':time.strftime('%H:%M:%S'),'bid':sid,
                'tier':'T' + str(t),'lat':lat_s + ' us',
                'outcome':res['status'],'err':bit_errors})

    # Read log (full width below)
    st.markdown("<hr style='border-color:#2a2a3a;margin:16px 0 8px'/>", unsafe_allow_html=True)
    st.markdown("**📋 Live Read Log — last 10 reads**")
    TC = {'T1':'#14b8a6','T2':'#f59e0b','T3':'#ff6b6b','BBT':'#ef4444'}
    if st.session_state.read_log:
        log_html = ''
        for e in reversed(st.session_state.read_log[-10:]):
            tc = TC.get(e['tier'], '#888')
            log_html += (
                "<div style='display:flex;gap:10px;align-items:center;padding:6px 12px;"
                "border-radius:6px;margin-bottom:4px;background:#1a1a26;"
                "font-family:JetBrains Mono,monospace;font-size:12px'>"
                "<span style='color:#4a4a60;min-width:60px'>" + e['ts'] + "</span>"
                "<span style='color:#8888a0;min-width:40px'>B" + str(e['bid']) + "</span>"
                "<span style='color:" + tc + ";font-weight:700;min-width:36px'>" + e['tier'] + "</span>"
                "<span style='color:#e8e8f0;min-width:60px'>" + e['lat'] + "</span>"
                "<span style='color:" + tc + ";min-width:120px'>" + e['outcome'] + "</span>"
                "<span style='color:#4a4a60'>" + str(e['err']) + " err</span></div>"
            )
        st.markdown(log_html, unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#4a4a60;font-family:monospace;font-size:12px'>No reads yet — fire a request above.</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TELEMETRY & AGING
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📊 Telemetry Dashboard & Block Aging")

    tc1, tc2 = st.columns([1.8, 1.2])

    with tc1:
        # Metrics row
        tsd   = st.session_state.tier_stats
        total = tsd['t1'] + tsd['t2'] + tsd['t3']
        t1r   = round(tsd['t1']/total*100,1) if total else 0.0
        ai    = [b['ldpc_avg'] for b in st.session_state.blocks if b['ldpc_iterations'] and not b['retired']]
        avgt2 = round(float(np.mean(ai)),1) if ai else 0.0
        sid3  = st.session_state.selected_block
        blk3  = st.session_state.blocks[sid3]
        rber3 = rber_est(blk3['pe_cycles'])

        tm1,tm2,tm3,tm4 = st.columns(4)
        tm1.metric("T1 Bypass",   str(t1r) + '%')
        tm2.metric("Avg T2 Iters", avgt2)
        tm3.metric("T3 ML Triggers", tsd['t3'])
        tm4.metric("RBER B" + str(sid3), '{:.1e}'.format(rber3))

        st.markdown("<hr style='border-color:#2a2a3a;margin:8px 0'/>", unsafe_allow_html=True)

        # LDPC chart for selected block
        iters_show = blk3['ldpc_iterations'][-40:] or [round(blk3['ldpc_avg'],1)]
        alarm_on   = any(x >= 15 for x in iters_show)
        chart_ph   = st.empty()
        chart_ph.plotly_chart(make_ldpc_chart(iters_show, sid3, alarm=alarm_on),
                              use_container_width=True, key='ldpc_chart_t3')

        st.markdown("<hr style='border-color:#2a2a3a;margin:4px 0'/>", unsafe_allow_html=True)

        # BBT Bitmap
        st.markdown("**Pillar 2 — BBT Bitmap (32 blocks)**")
        bbt_html = "<div style='display:flex;flex-wrap:wrap;gap:3px;margin-top:6px'>"
        for idx, bit in enumerate(st.session_state.bbt):
            state_s = "RETIRED" if bit else "OK"
            cv  = "#ef4444" if bit else "#22c55e"
            bgv = "#2d0a0a" if bit else "#052e16"
            bbt_html += (
                "<div style='width:28px;height:22px;background:" + bgv + ";color:" + cv +
                ";border-radius:3px;font-size:8px;text-align:center;line-height:22px;"
                "font-family:JetBrains Mono,monospace' title='B" + str(idx) + ": " + state_s + "'>"
                "B" + str(idx) + "</div>"
            )
        bbt_html += "</div>"
        rc = sum(st.session_state.bbt)
        bbt_html += (
            "<div style='color:#4a4a60;font-size:11px;font-family:JetBrains Mono,monospace;margin-top:6px'>"
            "RETIRED=" + str(rc) + "  /  ACTIVE=" + str(32-rc) + "</div>"
        )
        st.markdown(bbt_html, unsafe_allow_html=True)

    with tc2:
        st.markdown("**🔥 Moment 3 — Block Aging Simulation**")
        age_id  = st.session_state.selected_block
        age_blk = st.session_state.blocks[age_id]

        sid_s = str(age_id)
        pe_s  = str(age_blk['pe_cycles'])
        hlbl3 = health_label(age_blk)
        hc3   = HEALTH_TEXT_COLOR.get(hlbl3, '#888')

        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid " + hc3 +
            ";border-radius:8px;padding:12px;font-family:JetBrains Mono,monospace;font-size:12px;margin-bottom:12px'>"
            "Block <b>" + sid_s + "</b> &nbsp;·&nbsp; P/E: <b>" + pe_s + "</b><br>"
            "Status: <span style='color:" + hc3 + ";font-weight:700'>" + hlbl3.upper() + "</span></div>",
            unsafe_allow_html=True)

        if age_blk['retired']:
            st.error("Block " + sid_s + " already RETIRED. Go to Tab 1 and select another block.")
            st.markdown(
                "<div style='background:#051e10;border:1px solid #22c55e;border-radius:8px;"
                "padding:12px;font-family:JetBrains Mono,monospace;font-size:11px'>"
                "<b style='color:#22c55e'>Bloom Filter Active</b><br>"
                "Any read to Block " + sid_s + " returns 0.05 µs rejection.<br>"
                "Data was relocated to a healthy block by Pillar 1 FTL.</div>",
                unsafe_allow_html=True)
        else:
            age_btn = st.button(
                "▶  Age Block " + sid_s + " Until Retirement",
                type='primary', use_container_width=True, key='age_btn_t3')

            st.markdown(
                "<div style='color:#8888a0;font-size:11px;font-family:JetBrains Mono,monospace;margin-top:8px'>"
                "Simulates ~15-20 s of progressive wear.<br>"
                "At LDPC iter 15 the retirement cascade fires automatically<br>"
                "and runs to completion — unstoppable.</div>",
                unsafe_allow_html=True)

            if age_btn:
                age_chart  = st.empty()
                age_log    = st.empty()
                retired_f  = False

                for tick in range(60):
                    age_blk['pe_cycles'] = min(5100, age_blk['pe_cycles'] + random.randint(20,55))
                    itr_v = round(max(1.0, 2.0 + tick*0.37 + random.gauss(0,0.4)), 1)
                    age_blk['ldpc_iterations'].append(itr_v)
                    iters_v = age_blk['ldpc_iterations'][-35:]
                    age_chart.plotly_chart(
                        make_ldpc_chart(iters_v, age_id, alarm=(itr_v>=15)),
                        use_container_width=True, key='age_c_' + str(tick))
                    time.sleep(0.27)

                    if itr_v >= 15 and not retired_f:
                        retired_f = True
                        dest   = random.randint(200, 500)
                        dest_s = str(dest)
                        bit_s  = str(age_id % 32)
                        steps  = [
                            "AEGIS:    Pre-failure flag emitted. threshold=15 crossed.",
                            "PAYLOAD:  {block:" + sid_s + ", trigger:LDPC>15, dest:" + dest_s + "}",
                            "PILLAR 1: FTL copying block " + sid_s + " --> " + dest_s + " ...",
                            "PILLAR 1: Relocation COMPLETE. Block " + dest_s + " healthy.",
                            "PILLAR 2: BBT bit " + bit_s + " flipped 0 --> 1 (RETIRED).",
                            "PILLAR 1: Encrypting diagnostic report AES-256 ...",
                            "PILLAR 1: Shamir 3-of-5 key split pushed to distributed log.",
                            "PILLAR 4: Firmware decision tree pruned for next GC cycle.",
                            "STATUS:   UECC PREVENTED. Block " + sid_s + " RETIRED. NAND lifespan +1.5x.",
                        ]
                        shown = []
                        for s in steps:
                            shown.append(s)
                            age_log.code('\n'.join(shown), language='bash')
                            time.sleep(0.45)

                        age_blk['retired'] = True
                        if age_id < 32:
                            st.session_state.bbt[age_id] = 1
                        break

                if not retired_f:
                    age_log.info("Simulation ended. Block still operational.")