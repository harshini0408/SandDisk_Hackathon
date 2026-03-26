"""Section 3: SMART Analytics + LSTM Prediction"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from core.smart_engine import METRIC_DEFS, get_metric_status, get_sparks, get_workload_context
from core.lstm_predictor import predict, build_feature_sequence, anomaly_classify


METRIC_COLORS = [
    '#22c55e','#ef4444','#f59e0b','#3b82f6',
    '#a855f7','#14b8a6','#f97316','#84cc16',
    '#06b6d4','#ec4899','#8b5cf6','#10b981',
]


def _sparkline(values, color):
    if not values:
        return go.Figure()
    # Convert hex color to rgba for fill
    if color.startswith('#'):
        # Remove the # and get RGB values
        hex_color = color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        fillcolor = f'rgba({r},{g},{b},0.15)'
    elif 'rgb' in color:
        fillcolor = color.replace(')', ',0.15)').replace('rgb', 'rgba')
    else:
        fillcolor = color
    
    fig = go.Figure(go.Scatter(y=values, mode='lines', line=dict(color=color, width=1.5),
                               fill='tozeroy', fillcolor=fillcolor))
    fig.update_layout(
        height=50, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
    )
    return fig


def render_smart_cards(sim):
    st.markdown("#### 📊 12 SMART Metrics — Live Feed")
    snap = sim.get_latest_smart()
    if snap is None:
        st.info("Awaiting first SMART snapshot...")
        return

    rows = [METRIC_DEFS[i:i+4] for i in range(0, 12, 4)]
    for row_defs in rows:
        cols = st.columns(4)
        for col, mdef in zip(cols, row_defs):
            val = getattr(snap, mdef['field'], 0)
            status = get_metric_status(val, mdef['warn'], mdef['crit'])
            dot_color = {'OK': '#22c55e', 'WARNING': '#f59e0b', 'CRITICAL': '#ef4444'}[status]
            display_val = mdef['fmt'](val) + mdef['unit']
            sparks = get_sparks(sim.smart_history, mdef['field'])
            color = METRIC_COLORS[mdef['id'] - 1]

            with col:
                st.markdown(f"""
<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:8px;padding:10px;margin:3px 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="color:#8888a0;font-size:11px;font-family:monospace">⓪{mdef['id']} {mdef['name']}</span>
    <span style="width:8px;height:8px;border-radius:50%;background:{dot_color};display:inline-block"></span>
  </div>
  <div style="color:{color};font-size:22px;font-weight:bold;margin:4px 0">{display_val}</div>
  <div style="color:#4a4a60;font-size:10px">FROM {mdef['source']}</div>
</div>
""", unsafe_allow_html=True)
                if len(sparks) > 2:
                    st.plotly_chart(_sparkline(sparks, color), use_container_width=True,
                                   key=f"spark_{mdef['id']}")


def render_smart_timeseries(sim):
    st.markdown("#### 📉 Live SMART Time-Series")
    hist = sim.get_smart_history_array(500)
    if not hist or 'ecc_rate' not in hist:
        st.info("Accumulating SMART history...")
        return

    t = hist['t']
    
    fields = ['ecc_rate','uecc_count','bad_block_count','pe_avg',
              'wear_level','rber','temperature','read_latency_us',
              'retry_freq','reallocated','program_fail','erase_fail']
    names = ['ECC Rate','UECC','Bad Blocks','P/E Avg','Wear','RBER',
             'Temp','Latency','Retries','Reallocated','Prog Fail','Erase Fail']
    
    # Let user dynamically choose metrics
    name_to_fld = dict(zip(names, fields))
    selected_names = st.multiselect(
        "Select metrics to visualize (normalized 0–1):",
        options=names,
        default=['ECC Rate', 'Temp', 'Wear'],
        key="smart_ts_select"
    )
    
    if not selected_names:
        st.warning("Please select at least one metric to visualize.")
        return

    fig = go.Figure()
    fill_fields = {'ecc_rate', 'bad_block_count', 'rber'}

    for name in selected_names:
        fld = name_to_fld[name]
        i = fields.index(fld)
        vals = hist[fld]
        mx = max(max(vals), 1e-12)
        norm = [v / mx for v in vals]
        fill = 'tozeroy' if fld in fill_fields else 'none'
        color = METRIC_COLORS[i]
        
        # Convert hex color to rgba with alpha channel
        if color.startswith('#'):
            hex_color = color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            fillcolor = f'rgba({r},{g},{b},0.1)'
        else:
            fillcolor = color
            
        fig.add_trace(go.Scatter(
            x=t, y=norm, name=name, mode='lines',
            line=dict(color=color, width=1.5),
            fill=fill,
            fillcolor=fillcolor,
        ))

    fig.update_layout(
        height=280, margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor='#0a0a0f', plot_bgcolor='#12121a',
        xaxis=dict(title='Simulated time (s)', color='#8888a0', showgrid=False),
        yaxis=dict(title='Normalized (0-1)', color='#8888a0', showgrid=True, gridcolor='#2a2a3a'),
        legend=dict(bgcolor='#1a1a26', font=dict(color='#e8e8f0', size=9),
                    orientation='h', y=-0.25),
        font=dict(color='#e8e8f0'),
    )
    st.plotly_chart(fig, use_container_width=True, key="smart_ts")

    if st.button("💥 Inject Failure Event (ECC spike)", key="inject_fail_btn"):
        sim.inject_write_storm()
        st.rerun()


def render_workload_tagger(sim):
    st.markdown("#### 🏷️ Workload Tagger — Contextual Anomaly Detection")
    workloads = ['Sequential large writes', 'Random small writes', 'Mostly reads', 'Idle']
    sim.workload = st.selectbox("Current workload:", workloads,
                                index=workloads.index(sim.workload) if sim.workload in workloads else 0,
                                key="workload_sel")

    snap = sim.get_latest_smart()
    if snap:
        ctx = get_workload_context(1, sim.workload, snap.ecc_rate, sim.smart_history)
        is_anom = ctx['is_anomaly']
        color = '#ef4444' if is_anom else '#22c55e'
        st.markdown(f"""
<div style="background:#1a1a26;border-left:4px solid {color};padding:12px;border-radius:4px;margin:8px 0">
<b style="color:{color}">Sentinel</b>: <span style="color:#e8e8f0">
ECC rate = {snap.ecc_rate:,.0f}/hr during <b>{sim.workload}</b>.
{ctx['context']}</span>
</div>
""", unsafe_allow_html=True)


def render_lstm_engine(sim):
    st.markdown("#### 🤖 LSTM Health Engine")

    feat_seq = build_feature_sequence(sim.smart_history)
    result = predict(feat_seq)
    hs = result['health_score']
    fp = result['failure_prob']
    rul = result['rul_days']
    anomaly = anomaly_classify(fp, hs)

    # Health gauge
    hs_color = '#22c55e' if hs > 70 else '#f59e0b' if hs > 40 else '#ef4444'
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=hs,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Health Score", 'font': {'color': '#e8e8f0', 'size': 14}},
        number={'font': {'color': hs_color, 'size': 40}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#8888a0'},
            'bar': {'color': hs_color},
            'steps': [
                {'range': [0, 40], 'color': '#2d0707'},
                {'range': [40, 70], 'color': '#2d1d07'},
                {'range': [70, 100], 'color': '#072d18'},
            ],
            'bgcolor': '#1a1a26',
            'bordercolor': '#2a2a3a',
        }
    ))
    fig_gauge.update_layout(
        height=220, margin=dict(l=20,r=20,t=30,b=10),
        paper_bgcolor='#0a0a0f', font=dict(color='#e8e8f0'),
    )

    g_col, m_col = st.columns([1, 1])
    with g_col:
        st.plotly_chart(fig_gauge, use_container_width=True, key="health_gauge")
    with m_col:
        anomaly_colors = {'NONE':'#22c55e','SLOW_BURN':'#84cc16','WATCH':'#f59e0b',
                          'ACCELERATING':'#f97316','CRITICAL':'#ef4444'}
        ac = anomaly_colors.get(anomaly, '#8888a0')
        st.markdown(f"""
<div style="padding:10px">
  <div style="margin:6px 0"><span style="color:#8888a0">Failure Probability</span><br>
    <div style="background:#1a1a26;height:12px;border-radius:6px;overflow:hidden;margin-top:4px">
      <div style="background:#ef4444;width:{fp*100:.0f}%;height:100%;border-radius:6px"></div>
    </div>
    <span style="color:#ef4444;font-size:18px;font-weight:bold">{fp*100:.1f}%</span>
  </div>
  <div style="margin:6px 0"><span style="color:#8888a0">Estimated RUL</span><br>
    <span style="color:#3b82f6;font-size:18px;font-weight:bold">~{rul:.0f} days</span></div>
  <div style="margin:6px 0"><span style="color:#8888a0">Anomaly Type</span><br>
    <span style="background:{ac};color:white;padding:3px 10px;border-radius:12px;font-size:13px;font-weight:bold">{anomaly}</span>
  </div>
  <div style="margin:6px 0;color:#8888a0;font-size:11px">Source: {result['source'].upper()}</div>
</div>
""", unsafe_allow_html=True)

    # Attention heatmap
    st.markdown("##### LSTM Attention — What drove this prediction?")
    attn = result['attention']
    feat_names = ['ECC','UECC','BadBlks','P/E','Wear','RBER','Temp','Latency','Retry','Reallocated','ProgFail','EraseFail']
    fig_attn = go.Figure(go.Heatmap(
        z=attn, colorscale='Plasma', showscale=True,
        xaxis='x', yaxis='y',
        hovertemplate='Time step %{y}<br>Feature: %{x}<br>Weight: %{z:.3f}<extra></extra>',
    ))
    fig_attn.update_layout(
        height=220, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor='#0a0a0f', plot_bgcolor='#0a0a0f',
        xaxis=dict(tickvals=list(range(12)), ticktext=feat_names,
                   tickfont=dict(size=9, color='#8888a0'), showgrid=False),
        yaxis=dict(title='Time steps →', color='#8888a0', showgrid=False),
        font=dict(color='#e8e8f0'),
    )
    st.plotly_chart(fig_attn, use_container_width=True, key="attn_heatmap")


def render_lstm_commands(sim):
    st.markdown("#### 🔗 LSTM Engine → Pillar 2 & 3 Commands")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        target_block = st.number_input("Predictive retire block:", 0, 63, 44, key="pred_block")
        if st.button("⚡ LSTM → Retire Block Proactively", key="pred_retire_btn"):
            ok = sim.predictive_retire(int(target_block))
            if ok:
                st.session_state['cmd_log'] = [
                    "LSTM OUTPUT: Anomaly detected",
                    f"Root cause: Block {target_block} P/E trajectory → projected failure",
                    f"COMMAND → Pillar 1: Phase D triggered for Block {target_block}",
                    "  Copying valid pages to spare block...",
                    f"  Bitmap bit {target_block} = 1 ✓",
                    "  Cuckoo hash insert: {reason:PREDICTIVE_RETIREMENT} ✓",
                    "  BBT persisted ✓",
                    "RESULT: Block retired. Zero data loss.",
                ]
            else:
                st.warning(f"Block {target_block} not available for retirement.")
    with col_p2:
        if st.button("📈 LSTM → Raise LDPC Cap (blocks 30–39)", key="ldpc_raise_btn"):
            for b in range(30, 40):
                sim.set_ldpc_cap(b, 20)
            st.session_state['cmd_log'] = [
                "LSTM OUTPUT: RBER spike detected on blocks 30–39",
                "Current LDPC iteration cap: 8",
                "COMMAND → Pillar 2: LDPC ceiling for blocks 30–39: 8 → 20",
                "Context-aware protection escalated.",
                "RESULT: 2.5× more correction power on worn block range.",
            ]

    if 'cmd_log' in st.session_state:
        for line in st.session_state['cmd_log']:
            color = '#22c55e' if 'RESULT' in line or '✓' in line else '#14b8a6' if 'COMMAND' in line else '#e8e8f0'
            st.markdown(f'<span style="font-family:monospace;font-size:12px;color:{color}">{line}</span>', unsafe_allow_html=True)


def render_section3(sim):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("## 🔷 SECTION 3 — SMART Analytics + LSTM Prediction")
    render_smart_cards(sim)
    st.markdown("---")
    render_smart_timeseries(sim)
    st.markdown("---")
    render_workload_tagger(sim)
    st.markdown("---")
    render_lstm_engine(sim)
    st.markdown("---")
    render_lstm_commands(sim)
    st.markdown('</div>', unsafe_allow_html=True)
