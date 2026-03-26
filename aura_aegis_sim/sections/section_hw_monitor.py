"""
section_hw_monitor.py — Hardware Monitor Section for Pillar 1
Real-time ESP32 potentiometer dashboard with SMART metrics and AI prediction.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import math
import os

from core.sensor_mapper import SensorMapper  # type: ignore
from core.hw_predictor import predict        # type: ignore


# ── Session-state helpers ─────────────────────────────────────────────────────

def _init_hw_state():
    defaults = {
        "hw_monitoring":   False,
        "hw_connected":    False,
        "hw_reader":       None,
        "hw_mapper":       SensorMapper(),
        "hw_sim_offset":   0.0,   # drives the simulation sine wave
        "hw_last_raw":     0,
        "hw_log":          [],    # recent event log lines
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _safe_import_serial():
    try:
        import serial  # type: ignore
        return True
    except ImportError:
        return False


# ── Simulated sensor (no hardware) ───────────────────────────────────────────

def _sim_sensor_value(offset: float) -> int:
    """
    Generates a slowly rising sine-based value so the demo
    eventually crosses WARNING and CRITICAL thresholds.
    """
    base_raw   = min(4095, int(offset * 8))           # slow climb
    ripple     = int(200 * math.sin(offset * 0.5))    # ±200 ripple
    return max(0, min(4095, base_raw + ripple))


# ── Sidebar hardware controls ─────────────────────────────────────────────────

def render_hw_sidebar(ecc_warn_ref: list, bb_crit_ref: list):
    """
    Renders the ESP32 hardware sidebar controls.
    Updates ecc_warn_ref[0] and bb_crit_ref[0] with slider values.
    """
    st.markdown("---")
    st.markdown("### 🔌 ESP32 Hardware")

    # Serial availability check
    serial_ok = _safe_import_serial()

    if serial_ok:
        from core.serial_reader import SerialReader  # type: ignore
        available_ports = SerialReader.list_ports()
    else:
        available_ports = ["COM3", "COM4", "/dev/ttyUSB0"]

    port = st.selectbox("COM Port", available_ports, key="hw_port")
    baud = st.selectbox("Baud Rate", [9600, 115200], index=1, key="hw_baud")

    # Connection status pill
    if st.session_state.hw_connected:
        st.markdown(
            '<span style="background:#14532d;color:#22c55e;padding:3px 10px;'
            'border-radius:12px;font-size:12px;font-family:monospace">● Connected</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background:#2d1a1a;color:#ef4444;padding:3px 10px;'
            'border-radius:12px;font-size:12px;font-family:monospace">○ Disconnected</span>',
            unsafe_allow_html=True,
        )

    col_c, col_d = st.columns(2)
    with col_c:
        if st.button("🔗 Connect", key="hw_connect_btn"):
            if serial_ok:
                from core.serial_reader import SerialReader  # type: ignore
                reader = SerialReader(port=port, baud=int(baud))
                ok = reader.connect()
                if ok:
                    st.session_state.hw_reader    = reader
                    st.session_state.hw_connected = True
                    _log_event(f"Connected to {port} @ {baud} baud")
                else:
                    st.session_state.hw_connected = False
                    _log_event(f"⚠ Could not open {port} — using simulation")
            else:
                _log_event("pyserial not installed — using simulation")
            st.rerun()

    with col_d:
        if st.button("⛔ Disconnect", key="hw_disconnect_btn"):
            _hw_disconnect()
            st.rerun()

    st.markdown("**Thresholds:**")
    ecc_warn = st.slider("ECC Warn ≥", 50, 550, 250, 50, key="ecc_warn_slider")
    bb_crit  = st.slider("Bad Block Crit ≥", 20, 110, 80, 5, key="bb_crit_slider")
    ecc_warn_ref[0] = ecc_warn
    bb_crit_ref[0]  = bb_crit


def _hw_disconnect():
    reader = st.session_state.get("hw_reader")
    if reader:
        reader.disconnect()
    st.session_state.hw_reader    = None
    st.session_state.hw_connected = False
    _log_event("Disconnected from hardware")


def _log_event(msg: str):
    log = st.session_state.get("hw_log", [])
    ts  = time.strftime("%H:%M:%S")
    log.append(f"[{ts}] {msg}")
    st.session_state.hw_log = log[-30:]   # keep last 30 lines


# ── Main render ───────────────────────────────────────────────────────────────

def render_hw_monitor(ecc_warn: int = 250, bb_crit: int = 80):
    """
    Renders the full hardware monitor section inside Pillar 1.
    Should be called from the main page after the sidebar is rendered.
    """
    _init_hw_state()

    st.markdown("---")

    # ── Judge info box ────────────────────────────────────────────────────
    st.info(
        "**Hardware Demo** — This dashboard simulates SSD health monitoring using real-time "
        "hardware input. The ESP32 streams NAND wear data via UART, which is converted into "
        "SMART metrics and analyzed using an LSTM-based model to predict failure and estimate "
        "**Remaining Useful Life (RUL)**. Turn the potentiometer to drive the simulation live."
    )

    # ── Status banner placeholder ─────────────────────────────────────────
    banner_ph = st.empty()

    st.markdown("---")
    st.markdown("### 📊 SMART Telemetry  <span style='font-size:11px;color:#8888a0'>Simulated NAND Wear Input</span>", unsafe_allow_html=True)

    # ── 5-column metrics row ──────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    metric_ph = {
        "sensor":  m1.empty(),
        "wear":    m2.empty(),
        "bb":      m3.empty(),
        "ecc":     m4.empty(),
        "temp":    m5.empty(),
    }

    # ── Wear gauge ────────────────────────────────────────────────────────
    st.markdown("**Wear Level**")
    wear_gauge_ph = st.empty()

    # ── Real-time chart ───────────────────────────────────────────────────
    st.markdown("#### 📈 Live SMART Time-Series  <span style='font-size:11px;color:#8888a0'>AI Failure Prediction</span>", unsafe_allow_html=True)
    chart_ph = st.empty()

    # ── AI prediction panel ───────────────────────────────────────────────
    col_rul, col_fp = st.columns([1, 1])
    rul_ph = col_rul.empty()
    fp_ph  = col_fp.empty()

    # ── Start / Stop controls ─────────────────────────────────────────────
    st.markdown("---")
    ctrl_l, ctrl_r, ctrl_dl = st.columns([1, 1, 3])
    with ctrl_l:
        start_btn = st.button("▶ Start Monitoring", key="hw_start_btn",
                              type="primary", use_container_width=True)
    with ctrl_r:
        stop_btn  = st.button("⏹ Stop Monitoring",  key="hw_stop_btn",
                              use_container_width=True)

    # ── Event log ─────────────────────────────────────────────────────────
    with st.expander("📋 Event Log", expanded=False):
        log_ph = st.empty()

    # ── Download button ───────────────────────────────────────────────────
    with ctrl_dl:
        mapper: SensorMapper = st.session_state.hw_mapper
        hist = mapper.get_history()
        if hist:
            df_dl = pd.DataFrame(hist)
            csv_bytes = df_dl.to_csv(index=False).encode()
            st.download_button(
                "⬇ Download CSV",
                data=csv_bytes,
                file_name="ssd_health_log.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ── Button state transitions ──────────────────────────────────────────
    if start_btn:
        st.session_state.hw_monitoring   = True
        st.session_state.hw_mapper.clear_history()
        st.session_state.hw_sim_offset   = 0.0
        _log_event("🟢 Monitoring started")

    if stop_btn:
        st.session_state.hw_monitoring = False
        _log_event("⏹ Monitoring stopped")

    # ── Live update loop ──────────────────────────────────────────────────
    if st.session_state.hw_monitoring:
        _run_monitor_loop(
            banner_ph, metric_ph, wear_gauge_ph, chart_ph,
            rul_ph, fp_ph, log_ph,
            ecc_warn=ecc_warn, bb_crit=bb_crit,
        )
    else:
        # Render last known state when stopped
        mapper: SensorMapper = st.session_state.hw_mapper
        hist = mapper.get_history()
        if hist:
            latest   = hist[-1]
            pred     = predict(hist, ecc_thresh_warn=ecc_warn, bb_thresh_crit=bb_crit)
            _render_banner(banner_ph, pred)
            _render_metrics(metric_ph, latest)
            _render_gauge(wear_gauge_ph, latest["wear"])
            _render_chart(chart_ph, hist)
            _render_prediction(rul_ph, fp_ph, pred)
        else:
            _render_idle_banner(banner_ph)

        log_ph.text("\n".join(st.session_state.get("hw_log", ["No events yet."])))


# ── Loop ──────────────────────────────────────────────────────────────────────

def _run_monitor_loop(banner_ph, metric_ph, wear_gauge_ph, chart_ph,
                      rul_ph, fp_ph, log_ph,
                      ecc_warn: int, bb_crit: int):
    """
    Single-iteration update called on each Streamlit rerun.
    """
    mapper: SensorMapper = st.session_state.hw_mapper
    reader               = st.session_state.get("hw_reader")
    connected            = st.session_state.hw_connected

    # ── Read raw sensor value ─────────────────────────────────────────────
    if connected and reader and reader.is_connected:
        raw = reader.read_value()
        _log_event(f"HW read: raw={raw}")
    else:
        # Simulation: slowly rising signal with ripple
        offset = st.session_state.hw_sim_offset
        raw    = _sim_sensor_value(offset)
        st.session_state.hw_sim_offset = offset + 1.0

    # ── Map + store ───────────────────────────────────────────────────────
    latest = mapper.add_sample(raw)
    hist   = mapper.get_history()

    # ── Predict ───────────────────────────────────────────────────────────
    ecc_crit = int(ecc_warn * 1.6)   # crit = 1.6× warn threshold
    pred = predict(hist,
                   ecc_thresh_warn=ecc_warn,
                   ecc_thresh_crit=ecc_crit,
                   bb_thresh_crit=bb_crit)

    # ── Hardware LED feedback ─────────────────────────────────────────────
    if connected and reader and reader.is_connected:
        reader.send_feedback(b"1" if pred["status"] == "CRITICAL" else b"0")

    # ── Persist to CSV (data/history.csv) ────────────────────────────────
    _append_csv(latest, pred)

    # ── Render UI ─────────────────────────────────────────────────────────
    _render_banner(banner_ph, pred)
    _render_metrics(metric_ph, latest)
    _render_gauge(wear_gauge_ph, latest["wear"])
    _render_chart(chart_ph, hist)
    _render_prediction(rul_ph, fp_ph, pred)

    log_lines = st.session_state.get("hw_log", [])
    log_ph.text("\n".join(log_lines[-15:]))

    # ── Pause then rerun ──────────────────────────────────────────────────
    time.sleep(0.35)
    st.rerun()


# ── CSV Logging ───────────────────────────────────────────────────────────────

def _append_csv(latest: dict, pred: dict):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "history.csv")

    row = {**latest, "status": pred["status"], "rul": pred["rul"]}
    df  = pd.DataFrame([row])
    hdr = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=hdr, index=False)


# ── Render helpers ────────────────────────────────────────────────────────────

def _render_idle_banner(ph):
    ph.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a26,#12121a);'
        'border:1px solid #2a2a3a;border-radius:10px;padding:14px 20px;'
        'display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:28px">⚪</span>'
        '<div><div style="color:#e8e8f0;font-family:monospace;font-size:16px;font-weight:700">'
        'STANDBY — Press ▶ Start Monitoring</div>'
        '<div style="color:#8888a0;font-size:11px">No data yet</div></div></div>',
        unsafe_allow_html=True,
    )


def _render_banner(ph, pred: dict):
    s     = pred["status"]
    color = pred["color"]
    icon  = pred["icon"]
    rul   = pred["rul"]
    fp    = pred["failure_prob"]
    trend = pred["trend"]
    trend_arrow = {"rising": "↑", "falling": "↓", "stable": "→"}.get(trend, "→")
    grad  = {
        "HEALTHY":  "linear-gradient(135deg,#052e16,#14532d)",
        "WARNING":  "linear-gradient(135deg,#1c1000,#3d2400)",
        "CRITICAL": "linear-gradient(135deg,#200000,#450000)",
    }.get(s, "linear-gradient(135deg,#1a1a26,#12121a)")

    ph.markdown(
        f'<div style="background:{grad};border:1.5px solid {color};border-radius:10px;'
        f'padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:32px">{icon}</span>'
        f'<div><div style="color:{color};font-family:monospace;font-size:20px;font-weight:700">{s}</div>'
        f'<div style="color:#8888a0;font-size:11px">{pred["description"][:80]}…'
        f'</div></div></div>'
        f'<div style="display:flex;gap:28px;">'
        f'<div style="text-align:center">'
        f'<div style="color:{color};font-size:28px;font-weight:700">{rul}</div>'
        f'<div style="color:#8888a0;font-size:10px">ESTIMATED RUL</div></div>'
        f'<div style="text-align:center">'
        f'<div style="color:#3b82f6;font-size:28px;font-weight:700">{fp*100:.0f}%</div>'
        f'<div style="color:#8888a0;font-size:10px">FAILURE PROB</div></div>'
        f'<div style="text-align:center">'
        f'<div style="color:#a855f7;font-size:24px;font-weight:700">{trend_arrow} {trend.upper()}</div>'
        f'<div style="color:#8888a0;font-size:10px">ECC TREND</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _render_metrics(metric_ph: dict, m: dict):
    metric_ph["sensor"].metric("🎚️ Sensor Value",  f"{m['sensor_raw']} / 4095")
    metric_ph["wear"].metric("⚙️ Wear Level",     f"{m['wear_pct']:.1f} %")
    metric_ph["bb"].metric("🧱 Bad Blocks",       f"{m['bad_blocks']:.0f}")
    metric_ph["ecc"].metric("🔁 ECC Count",        f"{m['ecc_count']:.0f}")
    metric_ph["temp"].metric("🌡️ Temperature",    f"{m['temperature']:.1f} °C")


def _render_gauge(ph, wear: float):
    pct = max(0.0, min(1.0, wear))
    color = "#22c55e" if pct < 0.50 else "#f59e0b" if pct < 0.75 else "#ef4444"
    bar_w = int(pct * 100)
    ph.markdown(
        f'<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:6px;'
        f'height:20px;overflow:hidden;position:relative;">'
        f'<div style="background:{color};width:{bar_w}%;height:100%;'
        f'border-radius:6px;transition:width 0.3s ease;"></div>'
        f'<span style="position:absolute;top:2px;left:8px;font-family:monospace;'
        f'font-size:11px;color:#e8e8f0;font-weight:bold">'
        f'{pct*100:.1f}% NAND Wear</span></div>',
        unsafe_allow_html=True,
    )


def _render_chart(ph, hist: list):
    if len(hist) < 2:
        ph.info("Accumulating data…")
        return

    df = pd.DataFrame(hist)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df["ecc_count"],
        name="ECC Count", mode="lines",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df["bad_blocks"],
        name="Bad Blocks", mode="lines",
        line=dict(color="#ef4444", width=2),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df["temperature"],
        name="Temperature (°C)", mode="lines",
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#12121a",
        xaxis=dict(title="Sample #", color="#8888a0",
                   showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(title="Value", color="#8888a0",
                   showgrid=True, gridcolor="#1e1e2e"),
        legend=dict(bgcolor="#1a1a26", font=dict(color="#e8e8f0", size=9),
                    orientation="h", y=-0.3),
        font=dict(color="#e8e8f0"),
    )
    ph.plotly_chart(fig, use_container_width=True, key="hw_chart")


def _render_prediction(rul_ph, fp_ph, pred: dict):
    s      = pred["status"]
    color  = pred["color"]
    rul    = pred["rul"]
    fp     = pred["failure_prob"]

    # RUL card
    rul_ph.markdown(
        f'<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:8px;'
        f'padding:16px;text-align:center;">'
        f'<div style="color:#8888a0;font-size:11px;font-family:monospace;'
        f'margin-bottom:4px">⏳ REMAINING USEFUL LIFE</div>'
        f'<div style="color:{color};font-family:JetBrains Mono,monospace;'
        f'font-size:36px;font-weight:700;line-height:1">{rul}</div>'
        f'<div style="color:#8888a0;font-size:10px;margin-top:4px">'
        f'AI Failure Prediction Engine</div></div>',
        unsafe_allow_html=True,
    )

    # Failure probability bar
    bar_w  = int(fp * 100)
    fp_col = "#22c55e" if fp < 0.3 else "#f59e0b" if fp < 0.6 else "#ef4444"
    fp_ph.markdown(
        f'<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:8px;padding:16px">'
        f'<div style="color:#8888a0;font-size:11px;font-family:monospace;margin-bottom:8px">'
        f'🤖 FAILURE PROBABILITY</div>'
        f'<div style="background:#0a0a0f;border-radius:6px;height:16px;overflow:hidden;">'
        f'<div style="background:{fp_col};width:{bar_w}%;height:100%;border-radius:6px;'
        f'transition:width 0.3s ease;"></div></div>'
        f'<div style="color:{fp_col};font-size:24px;font-weight:700;margin-top:6px">'
        f'{fp*100:.1f}%</div>'
        f'<div style="color:#8888a0;font-size:10px">Heat Alert: '
        f'{"🔥 YES" if pred["heat_alert"] else "✓ No"}</div></div>',
        unsafe_allow_html=True,
    )
