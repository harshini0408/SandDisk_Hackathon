"""
shared_sidebar.py — Common AURA sidebar rendered by all pillar pages.
Includes: Navigation, Hardware Connection status, and quick system stats.
"""
import streamlit as st
import os
import sys
import time

# ── Hardware connection status (simulated; replace with real serial when ESP32 connected) ──
def _hw_status():
    """Return simulated hardware connection state from session_state."""
    return st.session_state.get("hw_connected", False)

def _hw_port():
    return st.session_state.get("hw_port", "COM3")

def _hw_baud():
    return st.session_state.get("hw_baud", 115200)


def render_sidebar(current_pillar: str = ""):
    """
    Call this inside  `with st.sidebar:`  at the top of any pillar page.
    current_pillar: label like '1', '2', ... '5', 'sim' for highlighting.
    """
    with st.sidebar:
        # ── Logo / title ─────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-family:JetBrains Mono,monospace;font-size:1.1rem;"
            "font-weight:700;color:#e8e8f0;margin-bottom:4px'>🔷 AURA — AEGIS</div>"
            "<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
            "color:#4a4a60;margin-bottom:12px'>Adaptive Unified Reliability Architecture</div>",
            unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown("<div style='font-size:10px;color:#4a4a60;text-transform:uppercase;"
                    "letter-spacing:2px;margin-bottom:6px'>Navigation</div>",
                    unsafe_allow_html=True)

        st.page_link("app.py",                     label="🏠 Home")
        st.page_link("pages/0_Manual.py",          label="📖 Quick Manual")
        st.page_link("pages/1_Pillar1.py",         label="🧠 Pillar 1 — Health & Diagnostics")
        st.page_link("pages/2_Pillar2.py",         label="🗃️ Pillar 2 — NAND Block Mgmt")
        st.page_link("pages/3_Pillar3.py",         label="🛡️ Pillar 3 — ECC & Reliability")
        st.page_link("pages/4_Pillar4.py",         label="⚙️ Pillar 4 — Logic Optimization")
        st.page_link("pages/5_Pillar5.py",         label="🔐 Pillar 5 — Secure OOB")
        st.page_link("pages/6_SimController.py",   label="🎮 Simulation Controller")

        st.divider()

        # ── Hardware Connection Panel ─────────────────────────────────────────
        st.markdown("<div style='font-size:10px;color:#4a4a60;text-transform:uppercase;"
                    "letter-spacing:2px;margin-bottom:8px'>Hardware Connection</div>",
                    unsafe_allow_html=True)

        connected = _hw_status()
        dot_color = "#22c55e" if connected else "#ef4444"
        dot_label = "CONNECTED" if connected else "SIMULATED"

        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid "
            + dot_color + ";border-radius:6px;padding:10px 12px;"
            "font-family:JetBrains Mono,monospace;font-size:11px;margin-bottom:8px'>"
            "<div style='display:flex;align-items:center;gap:6px;margin-bottom:4px'>"
            "<div style='width:8px;height:8px;border-radius:50%;background:"
            + dot_color + ";flex-shrink:0'></div>"
            "<b style='color:" + dot_color + "'>" + dot_label + "</b></div>"
            "<div style='color:#8888a0;font-size:10px'>"
            "Port: <b style='color:#e8e8f0'>" + str(_hw_port()) + "</b><br>"
            "Baud: <b style='color:#e8e8f0'>" + str(_hw_baud()) + "</b><br>"
            "Interface: <b style='color:#e8e8f0'>UART / BLE</b><br>"
            "Target: <b style='color:#e8e8f0'>ESP32-S3</b></div></div>",
            unsafe_allow_html=True)

        if connected:
            if st.button("⏏ Disconnect", key="hw_disconnect_btn", use_container_width=True):
                st.session_state["hw_connected"] = False
                st.toast("Hardware disconnected", icon="⏏")
                st.rerun()
        else:
            if st.button("🔌 Connect", key="hw_connect_btn", use_container_width=True):
                st.session_state["hw_connected"] = True
                st.toast("✅ Hardware connected (simulated)", icon="🔌")
                st.rerun()

        # Port / baud config
        with st.expander("⚙ HW Config", expanded=False):
            port_opts = ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyACM0"]
            cur_port  = st.session_state.get("hw_port", "COM3")
            sel_port  = st.selectbox("Serial Port", port_opts,
                                     index=port_opts.index(cur_port) if cur_port in port_opts else 0,
                                     key="hw_port_sel", label_visibility="collapsed")
            st.session_state["hw_port"] = sel_port

            baud_opts = [9600, 57600, 115200, 230400]
            cur_baud  = st.session_state.get("hw_baud", 115200)
            sel_baud  = st.selectbox("Baud Rate", baud_opts,
                                     index=baud_opts.index(cur_baud) if cur_baud in baud_opts else 2,
                                     key="hw_baud_sel", label_visibility="collapsed")
            st.session_state["hw_baud"] = sel_baud

        st.divider()

        # ── Quick system stats from sc_state if available ─────────────────────
        sc_s = st.session_state.get("sc_state")
        if sc_s:
            sm = sc_s.get("smart_metrics", {})
            hs   = sm.get("health_score", 0)
            hc   = "#22c55e" if hs > 70 else "#f59e0b" if hs > 40 else "#ef4444"
            host = sc_s.get("host_status", "UNKNOWN")
            hoc  = "#22c55e" if host == "ACTIVE" else "#ef4444"
            evs  = len(sc_s.get("event_log", []))
            st.markdown(
                "<div style='font-size:10px;color:#4a4a60;text-transform:uppercase;"
                "letter-spacing:2px;margin-bottom:6px'>System Status</div>",
                unsafe_allow_html=True)
            st.markdown(
                "<div style='background:#12121a;border:1px solid #2a2a3a;border-radius:6px;"
                "padding:10px 12px;font-family:JetBrains Mono,monospace;font-size:11px'>"
                "Host: <b style='color:" + hoc + "'>" + host + "</b><br>"
                "Health: <b style='color:" + hc + "'>" + str(round(hs, 1)) + "%</b><br>"
                "Bad blocks: <b style='color:#ef4444'>" + str(sm.get("bad_blocks", 0)) + "</b><br>"
                "Events: <b style='color:#a855f7'>" + str(evs) + "</b></div>",
                unsafe_allow_html=True)

        # ── Scenario shortcut ──────────────────────────────────────────────────
        sc = st.session_state.get("sc_scenario")
        if sc:
            SC_NAMES = {1:"Boot",2:"Read",3:"Write",4:"Degrade",5:"Crash",6:"GC"}
            sc_label = SC_NAMES.get(sc, "?")
            st.markdown(
                "<div style='margin-top:8px;background:#1a1a26;border:1px solid #a855f7;"
                "border-radius:6px;padding:8px 10px;font-family:JetBrains Mono,monospace;"
                "font-size:11px;color:#a855f7'>⚡ Last Scenario: " + sc_label + "</div>",
                unsafe_allow_html=True)
            if st.button("◀ Back to Controller", key="sb_back_ctrl", use_container_width=True):
                st.switch_page("pages/6_SimController.py")
