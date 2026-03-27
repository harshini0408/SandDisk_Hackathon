"""
section_hw_monitor.py — Hardware Monitor Section for Pillar 1
Real-time ESP32 SMART telemetry dashboard with AI prediction.

Data path (hardware connected):
  ESP32 → serial (COM5) → SerialReader.read_once() → get_smart() dict
  → hw_predictor.predict() → UI + LED feedback

Data path (simulation fallback):
  _sim_smart() generates a rising-wear synthetic dict using the same schema.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import math
import os

from core.hw_predictor import predict  # type: ignore

# ── Simulation ────────────────────────────────────────────────────────────────

def _sim_smart(offset: float) -> dict:
    """
    Generate a synthetic SMART dict that slowly climbs across all 12 fields.
    Schema matches exactly what SerialReader.get_smart() returns.
    """
    wear_raw = min(100, int(offset * 0.5))          # 0→100 over ~200 ticks
    ripple   = int(5 * math.sin(offset * 0.4))
    wear     = max(0, min(100, wear_raw + ripple))

    frac = wear / 100.0
    return {
        "wear":         wear,
        "ecc":          int(100 + frac * 500),
        "uecc":         int(frac ** 3 * 5),
        "bad_blocks":   int(10 + frac * 100),
        "pe_cycles":    int(frac * 3000),
        "rber":         round(1e-7 * math.exp(frac * 6), 8),
        "temperature":  int(40 + frac * 10),
        "latency":      int(75 + frac * 50),
        "retry":        int(frac * 30),
        "relocated":    int(frac * 25),
        "program_fail": int(frac * 10),
        "erase_fail":   int(frac * 8),
    }


# ── Adapts new smart dict to hw_predictor's expected keys ────────────────────

def _smart_to_predictor(s: dict) -> dict:
    """
    hw_predictor.predict() expects dicts with keys:
      ecc_count, bad_blocks, wear (0–1 fraction), temperature
    Map the new 12-field smart dict to that schema.
    """
    return {
        "ecc_count":   s["ecc"],
        "bad_blocks":  s["bad_blocks"],
        "wear":        s["wear"] / 100.0,   # convert 0–100 → 0–1
        "wear_pct":    s["wear"],
        "temperature": s["temperature"],
        "sensor_raw":  s["wear"],           # kept for CSV compatibility
    }


# ── Session-state helpers ─────────────────────────────────────────────────────

def _init_hw_state():
    defaults = {
        "hw_monitoring":    False,
        "hw_connected":     False,
        "hw_reader":        None,
        "hw_sim_offset":    0.0,
        "hw_log":           [],
        "hw_smart_history": [],   # list of 12-field smart dicts
        "hw_last_event":    None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _safe_import_serial() -> bool:
    try:
        import serial  # type: ignore
        return True
    except ImportError:
        return False


# ── Sidebar hardware controls ─────────────────────────────────────────────────

def render_hw_sidebar(ecc_warn_ref: list, bb_crit_ref: list):
    """Renders the ESP32 hardware sidebar controls."""
    st.markdown("---")
    st.markdown("### 🔌 ESP32 Hardware")

    serial_ok = _safe_import_serial()
    if serial_ok:
        from core.serial_reader import SerialReader  # type: ignore
        available_ports = SerialReader.list_ports()
    else:
        available_ports = ["COM3", "COM4", "COM5", "/dev/ttyUSB0"]

    # Default to COM5 per project spec
    default_idx = available_ports.index("COM5") if "COM5" in available_ports else 0
    port = st.selectbox("COM Port", available_ports, index=default_idx, key="hw_port")
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
                    st.session_state.hw_smart_history = []
                    _log_event(f"✅ Connected to {port} @ {baud} baud — Hardware Mode Active")
                else:
                    st.session_state.hw_connected = False
                    _log_event(f"⚠ Could not open {port} — using simulation fallback")
            else:
                _log_event("pyserial not installed — using simulation fallback")
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
    _log_event("🔌 Disconnected from hardware — simulation fallback active")


def _log_event(msg: str):
    log = st.session_state.get("hw_log", [])
    ts  = time.strftime("%H:%M:%S")
    log.append(f"[{ts}] {msg}")
    st.session_state.hw_log = log[-50:]


# ── Main render ───────────────────────────────────────────────────────────────

def render_hw_monitor(ecc_warn: int = 250, bb_crit: int = 80):
    """Renders the full hardware monitor section inside Pillar 1."""
    _init_hw_state()

    st.markdown("---")

    st.info(
        "**Hardware Demo** — ESP32 streams structured SMART telemetry via UART (COM5). "
        "Potentiometer drives wear level → all 12 SMART metrics update in real-time. "
        "Buttons on ESP32 trigger firmware events (WRITE / FAIL / REBOOT). "
        "Streamlit sends LED feedback (GREEN / YELLOW / RED) back to ESP32."
    )

    # ── Connection status banner (always visible) ─────────────────────────
    _render_hw_status_bar()

    st.markdown("---")
    st.markdown(
        "### 📊 SMART Telemetry  "
        "<span style='font-size:11px;color:#8888a0'>12-Field Hardware Input</span>",
        unsafe_allow_html=True,
    )

    # ── 5 metric placeholders ─────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    metric_ph = {
        "wear":    m1.empty(),
        "bb":      m2.empty(),
        "ecc":     m3.empty(),
        "uecc":    m4.empty(),
        "temp":    m5.empty(),
    }

    st.markdown("**Wear Level**")
    wear_gauge_ph = st.empty()

    # ── Last ESP32 event display ──────────────────────────────────────────
    event_ph = st.empty()

    # ── Live chart ────────────────────────────────────────────────────────
    st.markdown(
        "#### 📈 Live SMART Time-Series  "
        "<span style='font-size:11px;color:#8888a0'>AI Failure Prediction</span>",
        unsafe_allow_html=True,
    )
    chart_ph = st.empty()

    # ── AI prediction panels ──────────────────────────────────────────────
    col_rul, col_fp = st.columns([1, 1])
    rul_ph = col_rul.empty()
    fp_ph  = col_fp.empty()

    # ── Controls ──────────────────────────────────────────────────────────
    st.markdown("---")
    ctrl_l, ctrl_r, ctrl_dl = st.columns([1, 1, 3])
    with ctrl_l:
        start_btn = st.button("▶ Start Monitoring", key="hw_start_btn",
                              type="primary", use_container_width=True)
    with ctrl_r:
        stop_btn  = st.button("⏹ Stop Monitoring",  key="hw_stop_btn",
                              use_container_width=True)

    with ctrl_dl:
        hist = st.session_state.get("hw_smart_history", [])
        if hist:
            df_dl     = pd.DataFrame(hist)
            csv_bytes = df_dl.to_csv(index=False).encode()
            st.download_button(
                "⬇ Download CSV", data=csv_bytes,
                file_name="ssd_smart_log.csv", mime="text/csv",
                use_container_width=True,
            )

    with st.expander("📋 Event Log", expanded=False):
        log_ph = st.empty()

    # ── Button state transitions ──────────────────────────────────────────
    if start_btn:
        st.session_state.hw_monitoring     = True
        st.session_state.hw_smart_history  = []
        st.session_state.hw_sim_offset     = 0.0
        _log_event("🟢 Monitoring started")

    if stop_btn:
        st.session_state.hw_monitoring = False
        _log_event("⏹ Monitoring stopped")

    # ── Live update loop ──────────────────────────────────────────────────
    if st.session_state.hw_monitoring:
        _run_monitor_loop(
            metric_ph, wear_gauge_ph, event_ph,
            chart_ph, rul_ph, fp_ph, log_ph,
            ecc_warn=ecc_warn, bb_crit=bb_crit,
        )
    else:
        hist = st.session_state.get("hw_smart_history", [])
        if hist:
            latest = hist[-1]
            pred   = _predict_from_smart(hist, ecc_warn, bb_crit)
            _render_metrics(metric_ph, latest)
            _render_gauge(wear_gauge_ph, latest["wear"] / 100.0)
            _render_chart(chart_ph, hist)
            _render_prediction(rul_ph, fp_ph, pred)
        else:
            _render_idle_banner(metric_ph["wear"])

        log_ph.text("\n".join(st.session_state.get("hw_log", ["No events yet."])))


# ── Monitor loop ──────────────────────────────────────────────────────────────

def _run_monitor_loop(metric_ph, wear_gauge_ph, event_ph,
                      chart_ph, rul_ph, fp_ph, log_ph,
                      ecc_warn: int, bb_crit: int):
    """Single-iteration update — called on each Streamlit rerun."""
    reader    = st.session_state.get("hw_reader")
    connected = st.session_state.hw_connected

    # ── Acquire SMART snapshot ────────────────────────────────────────────
    if connected and reader and reader.is_connected:
        # Non-blocking: read one line, update internal state
        reader.read_once()
        smart = reader.get_smart()

        # Consume any ESP32 event
        ev = reader.get_last_event()
        if ev:
            st.session_state.hw_last_event = ev
            _log_event(f"📡 ESP32 EVENT: {ev}")
    else:
        # Simulation fallback
        offset = st.session_state.hw_sim_offset
        smart  = _sim_smart(offset)
        st.session_state.hw_sim_offset = offset + 1.0
        # Mark as disconnected if reader was live but dropped
        if connected and reader and not reader.is_connected:
            _hw_disconnect()

    # ── Append to rolling history (keep last 200) ─────────────────────────
    hist = st.session_state.hw_smart_history
    hist.append(smart)
    if len(hist) > 200:
        hist = hist[-200:]
    st.session_state.hw_smart_history = hist

    # ── Predict ───────────────────────────────────────────────────────────
    ecc_crit = int(ecc_warn * 1.6)
    pred = _predict_from_smart(hist, ecc_warn, bb_crit, ecc_crit)

    # ── LED feedback ──────────────────────────────────────────────────────
    if connected and reader and reader.is_connected:
        if smart["uecc"] > 0 or pred["status"] == "CRITICAL":
            reader.send_led("RED")
        elif pred["status"] == "WARNING":
            reader.send_led("YELLOW")
        else:
            reader.send_led("GREEN")

    # ── Persist row to CSV ────────────────────────────────────────────────
    _append_csv(smart, pred)

    # ── Render ────────────────────────────────────────────────────────────
    _render_metrics(metric_ph, smart)
    _render_gauge(wear_gauge_ph, smart["wear"] / 100.0)
    _render_event(event_ph, st.session_state.get("hw_last_event"))
    _render_chart(chart_ph, hist)
    _render_prediction(rul_ph, fp_ph, pred)

    log_lines = st.session_state.get("hw_log", [])
    log_ph.text("\n".join(log_lines[-20:]))

    time.sleep(0.2)   # ~5 Hz — matches ESP32 send rate
    st.rerun()


# ── Prediction helper ─────────────────────────────────────────────────────────

def _predict_from_smart(hist: list, ecc_warn: int, bb_crit: int,
                        ecc_crit: int | None = None) -> dict:
    """Convert a list of 12-field smart dicts to predictor format and call predict()."""
    if ecc_crit is None:
        ecc_crit = int(ecc_warn * 1.6)
    mapped_hist = [_smart_to_predictor(s) for s in hist]
    return predict(mapped_hist,
                   ecc_thresh_warn=ecc_warn,
                   ecc_thresh_crit=ecc_crit,
                   bb_thresh_crit=bb_crit)


# ── CSV logging ───────────────────────────────────────────────────────────────

def _append_csv(smart: dict, pred: dict):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "history.csv")
    row = {**smart, "status": pred["status"], "rul": pred["rul"]}
    df  = pd.DataFrame([row])
    hdr = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=hdr, index=False)


# ── Render helpers ────────────────────────────────────────────────────────────

def _render_hw_status_bar():
    """Show 'Hardware Mode Active (COM5)' or 'Hardware Disconnected'."""
    connected = st.session_state.hw_connected
    if connected:
        port = st.session_state.get("hw_port", "COM5")
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#052e16,#14532d);'
            f'border:1.5px solid #22c55e;border-radius:8px;padding:10px 16px;margin-bottom:6px;'
            f'font-family:monospace;font-size:13px;color:#22c55e;">'
            f'✅ <b>Hardware Mode Active ({port})</b> — ESP32 streaming SMART telemetry'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#1c1000,#3d2400);'
            'border:1.5px solid #f59e0b;border-radius:8px;padding:10px 16px;margin-bottom:6px;'
            'font-family:monospace;font-size:13px;color:#f59e0b;">'
            '⚠️ <b>Hardware Disconnected</b> — Running on simulation fallback'
            '</div>',
            unsafe_allow_html=True,
        )


def _render_idle_banner(ph):
    ph.markdown(
        '<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:10px;'
        'padding:14px 20px;display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:28px">⚪</span>'
        '<div style="color:#e8e8f0;font-family:monospace;font-size:16px;font-weight:700">'
        'STANDBY — Press ▶ Start Monitoring</div></div>',
        unsafe_allow_html=True,
    )


def _render_metrics(metric_ph: dict, s: dict):
    metric_ph["wear"].metric("⚙️ Wear",          f"{s['wear']} %")
    metric_ph["bb"].metric("🧱 Bad Blocks",       f"{s['bad_blocks']}")
    metric_ph["ecc"].metric("🔁 ECC Count",        f"{s['ecc']:,}")
    metric_ph["uecc"].metric("💀 UECC",            f"{s['uecc']}",
                             delta="‼ CRITICAL" if s["uecc"] > 0 else "OK",
                             delta_color="inverse" if s["uecc"] > 0 else "normal")
    metric_ph["temp"].metric("🌡️ Temperature",    f"{s['temperature']} °C")


def _render_gauge(ph, wear_frac: float):
    pct   = max(0.0, min(1.0, wear_frac))
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


def _render_event(ph, event: str | None):
    if not event:
        ph.empty()
        return
    colors = {"WRITE": "#3b82f6", "FAIL": "#ef4444", "REBOOT": "#f59e0b"}
    col = colors.get(event, "#8888a0")
    ph.markdown(
        f'<div style="background:#12121a;border:1px solid {col};border-radius:6px;'
        f'padding:6px 14px;font-family:monospace;font-size:12px;color:{col};'
        f'display:inline-block;margin:4px 0;">'
        f'📡 Last ESP32 Event: <b>{event}</b></div>',
        unsafe_allow_html=True,
    )


def _render_chart(ph, hist: list):
    if len(hist) < 2:
        ph.info("Accumulating data…")
        return

    df = pd.DataFrame(hist)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df["ecc"],
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
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df["wear"],
        name="Wear (%)", mode="lines",
        line=dict(color="#a855f7", width=1.5),
    ))

    fig.update_layout(
        height=260,
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
    s     = pred["status"]
    color = pred["color"]
    rul   = pred["rul"]
    fp    = pred["failure_prob"]

    rul_ph.markdown(
        f'<div style="background:#1a1a26;border:1px solid #2a2a3a;border-radius:8px;'
        f'padding:16px;text-align:center;">'
        f'<div style="color:#8888a0;font-size:11px;font-family:monospace;margin-bottom:4px">'
        f'⏳ REMAINING USEFUL LIFE</div>'
        f'<div style="color:{color};font-family:JetBrains Mono,monospace;'
        f'font-size:36px;font-weight:700;line-height:1">{rul}</div>'
        f'<div style="color:#8888a0;font-size:10px;margin-top:4px">'
        f'AI Failure Prediction Engine</div></div>',
        unsafe_allow_html=True,
    )

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
