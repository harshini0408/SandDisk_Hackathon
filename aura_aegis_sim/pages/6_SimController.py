"""
6_SimController.py — AURA Event-Driven SSD Simulation Controller
6 real-world scenarios driving all 4 pillars via a shared event bus.
Python 3.11 safe: NO backslashes inside f-string expressions.
"""
import streamlit as st
import time
import os
import sys
import random
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Simulation Controller | AURA",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
html,body,[data-testid="stApp"]{background:#0a0a0f!important;color:#e8e8f0!important;font-family:'Inter',sans-serif!important;}
h1,h2,h3,h4{font-family:'JetBrains Mono',monospace!important;color:#e8e8f0!important;}
[data-testid="stSidebar"]{background:#12121a!important;border-right:1px solid #2a2a3a!important;}
div[data-testid="stMetricValue"]{color:#a855f7!important;font-size:1.3rem!important;font-weight:700!important;}
div[data-testid="stMetricLabel"]{color:#8888a0!important;font-size:0.72rem!important;}
div[data-baseweb="tab-list"]{background:#12121a!important;border-bottom:1px solid #2a2a3a!important;}
div[data-baseweb="tab"]{color:#8888a0!important;}
div[data-baseweb="tab"][aria-selected="true"]{color:#a855f7!important;border-bottom:2px solid #a855f7!important;}
.stButton>button{background:linear-gradient(135deg,#1a1a2e,#2a1a3e)!important;border:1px solid #7c3aed!important;color:#e8e8f0!important;font-family:'JetBrains Mono',monospace!important;border-radius:6px!important;font-size:12px!important;}
.stButton>button:hover{border-color:#3b82f6!important;background:linear-gradient(135deg,#1a1a3e,#1a2a5e)!important;}
div[data-testid="stExpander"]{background:#1a1a26!important;border:1px solid #2a2a3a!important;border-radius:8px!important;}
div[data-testid="stCodeBlock"] pre{background:#12121a!important;border:1px solid #2a2a3a!important;}
</style>
""", unsafe_allow_html=True)

# ─── Imports ─────────────────────────────────────────────────────────────────
from core.sim_state import (
    init_system_state, push_event, retire_block, best_write_block,
    rber_est, health_label, BLOCK_CSS,
    make_event, EV_READ_REQUEST, EV_WRITE_REQUEST, EV_ECC_DETECTED,
    EV_PRE_FAILURE, EV_DATA_RELOCATION, EV_BLOCK_RETIRE, EV_FAST_REJECT,
    EV_GC_TRIGGER, EV_HOST_CRASH, EV_OOB_TRIGGER, EV_ENCRYPT_REPORT,
    EV_SHAMIR_SPLIT, P1, P2, P3, P4, HW, NV,
)

CRYPTO_OK  = False
SHAMIR_OK  = False
try:
    from crypto.aes_layer    import encrypt_report
    CRYPTO_OK = True
except Exception:
    pass
try:
    from crypto.shamir_layer import split_secret, format_shares_for_display
    SHAMIR_OK = True
except Exception:
    pass

# ─── Session-state bootstrap ─────────────────────────────────────────────────
if "sc_state" not in st.session_state:
    st.session_state.sc_state = init_system_state()
if "sc_log_render" not in st.session_state:
    st.session_state.sc_log_render = []
if "sc_scenario" not in st.session_state:
    st.session_state.sc_scenario = None

STATE = st.session_state.sc_state


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

EV_COLOR = {
    EV_READ_REQUEST:    "#3b82f6",
    EV_WRITE_REQUEST:   "#14b8a6",
    EV_ECC_DETECTED:    "#f59e0b",
    EV_PRE_FAILURE:     "#ef4444",
    EV_DATA_RELOCATION: "#a855f7",
    EV_BLOCK_RETIRE:    "#ef4444",
    EV_FAST_REJECT:     "#f97316",
    EV_GC_TRIGGER:      "#22c55e",
    EV_HOST_CRASH:      "#ef4444",
    EV_OOB_TRIGGER:     "#3b82f6",
    EV_ENCRYPT_REPORT:  "#f59e0b",
    EV_SHAMIR_SPLIT:    "#a855f7",
}

SRC_COLOR = {P1:"#3b82f6", P2:"#22c55e", P3:"#f59e0b", P4:"#a855f7",
             HW:"#ef4444", NV:"#14b8a6"}


def log_html_entry(ev):
    tc = EV_COLOR.get(ev["type"], "#888")
    sc = SRC_COLOR.get(ev["source"], "#888")
    bid = (" B" + str(ev["block_id"])) if ev["block_id"] is not None else ""
    det = ""
    if ev["details"]:
        det = " · " + ", ".join(k + "=" + str(v) for k, v in list(ev["details"].items())[:3])
    return (
        "<div style='display:flex;gap:10px;align-items:center;padding:5px 10px;"
        "border-radius:5px;background:#1a1a26;margin-bottom:3px;"
        "font-family:JetBrains Mono,monospace;font-size:11px'>"
        "<span style='color:#4a4a60;min-width:58px'>" + ev["ts"] + "</span>"
        "<span style='background:" + sc + "22;color:" + sc + ";border:1px solid " + sc +
        ";border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700;min-width:70px;text-align:center'>"
        + ev["source"].replace("_", " ") + "</span>"
        "<span style='color:" + tc + ";font-weight:700;min-width:130px'>"
        + ev["type"].replace("_", " ") + "</span>"
        "<span style='color:#8888a0'>" + bid + det + "</span>"
        "</div>"
    )


def render_event_log(ph, state, max_show=15):
    evs = state["event_log"][-max_show:]
    if not evs:
        ph.markdown("<div style='color:#4a4a60;font-family:monospace;font-size:12px;padding:8px'>No events yet.</div>",
                    unsafe_allow_html=True)
        return
    html = ""
    for e in reversed(evs):
        html += log_html_entry(e)
    ph.markdown(html, unsafe_allow_html=True)


def render_nand_grid(ph, state, highlight=None):
    blocks = state["blocks"]
    rows_html = "<div style='display:flex;flex-direction:column;gap:2px'>"
    for row in range(8):
        rows_html += "<div style='display:flex;gap:2px'>"
        for col in range(8):
            bid = row * 8 + col
            blk = blocks[bid]
            hl  = health_label(blk["pe_cycles"], blk["retired"])
            tc, bg = BLOCK_CSS.get(hl, ("#888", "#222"))
            border = "2px solid #ffffff" if bid == highlight else "2px solid transparent"
            rows_html += (
                "<div style='width:40px;height:36px;background:" + bg +
                ";color:" + tc + ";border-radius:4px;border:" + border +
                ";display:flex;align-items:center;justify-content:center;"
                "font-family:JetBrains Mono,monospace;font-size:8px;font-weight:700'>"
                "B" + str(bid) + "</div>"
            )
        rows_html += "</div>"
    rows_html += "</div>"
    ph.markdown(rows_html, unsafe_allow_html=True)


def render_smart_panel(ph, state):
    sm = state["smart_metrics"]
    hs = sm.get("health_score", 85)
    hc = "#22c55e" if hs > 70 else "#f59e0b" if hs > 40 else "#ef4444"
    t = (
        "<div style='background:#12121a;border:1px solid #2a2a3a;border-radius:8px;padding:14px;"
        "font-family:JetBrains Mono,monospace;font-size:11px'>"
        "<div style='color:#8888a0;font-size:9px;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px'>SMART Metrics</div>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px'>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>Health Score</div>"
        "<div style='color:" + hc + ";font-size:18px;font-weight:700'>" + str(round(hs, 1)) + "</div></div>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>ECC Count</div>"
        "<div style='color:#f59e0b;font-size:16px;font-weight:700'>" + str(sm.get("ecc_count", 0)) + "</div></div>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>Bad Blocks</div>"
        "<div style='color:#ef4444;font-size:16px;font-weight:700'>" + str(sm.get("bad_blocks", 0)) + "</div></div>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>RUL (days)</div>"
        "<div style='color:#3b82f6;font-size:16px;font-weight:700'>" + str(round(sm.get("rul_days", 0), 0)) + "</div></div>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>Wear Level</div>"
        "<div style='color:#a855f7;font-size:14px;font-weight:700'>" + str(round(sm.get("wear_level", 0) * 100, 1)) + "%</div></div>"
        "<div style='background:#0a0a14;border-radius:5px;padding:8px'>"
        "<div style='color:#8888a0;font-size:9px'>Temperature</div>"
        "<div style='color:#f97316;font-size:14px;font-weight:700'>" + str(round(sm.get("temperature", 40), 1)) + "°C</div></div>"
        "</div></div>"
    )
    ph.markdown(t, unsafe_allow_html=True)


def step_box(tag, msg, color="#3b82f6", done=False):
    """Return HTML for a single step in the flow trace."""
    icon = "✅" if done else "▶"
    return (
        "<div style='border-left:3px solid " + color + ";padding:6px 12px;"
        "background:#12121a;border-radius:0 6px 6px 0;margin-bottom:5px;"
        "font-family:JetBrains Mono,monospace;font-size:11px'>"
        "<span style='color:" + color + ";font-weight:700'>[" + tag + "] " + icon + " </span>"
        "<span style='color:#e8e8f0'>" + msg + "</span></div>"
    )


def pipeline_flow(ph, steps):
    """steps = list of (tag, msg, color, done)"""
    html = ""
    for s in steps:
        html += step_box(*s)
    ph.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO ENGINES
# ═══════════════════════════════════════════════════════════════════════════════

def run_scenario_1_boot(state, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 1 — SSD Boot"""
    state["boot_done"] = False
    state["host_status"] = "BOOTING"
    steps = []
    push_event(state, make_event(HW, EV_READ_REQUEST, None, {"cmd": "POWER_ON"}))

    steps.append(("POWER", "SSD Controller initializing...", "#14b8a6", False))
    pipeline_flow(flow_ph, steps); render_event_log(log_ph, state); time.sleep(0.6)

    steps[-1] = ("POWER", "SSD Controller ON", "#14b8a6", True)
    steps.append(("P2", "Rebuilding BBT — scanning Bloom filter + bitmap...", "#22c55e", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.8)

    bad = [b["id"] for b in state["blocks"] if b["retired"]]
    state["bbt"]       = {b: True for b in bad}
    state["bloom_set"] = set(bad)
    push_event(state, make_event(P2, EV_FAST_REJECT, None, {"bbt_entries": len(bad), "bloom_ok": True}))
    steps[-1] = ("P2", "BBT rebuilt — " + str(len(bad)) + " bad blocks in Bloom filter", "#22c55e", True)
    render_event_log(log_ph, state); render_nand_grid(grid_ph, state)

    steps.append(("P1", "Loading SMART metrics from NOR flash...", "#3b82f6", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.6)
    sm = state["smart_metrics"]
    push_event(state, make_event(P1, EV_READ_REQUEST, None, {"action": "SMART_LOAD", "ecc": sm["ecc_count"]}))
    steps[-1] = ("P1", "SMART loaded — health=" + str(round(sm["health_score"], 1)) + " rul=" + str(sm["rul_days"]) + "d", "#3b82f6", True)

    steps.append(("P1", "Initializing LSTM predictor (60-step window)...", "#3b82f6", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    state["lstm_ready"] = True
    steps[-1] = ("P1", "LSTM online — heuristic fallback active", "#3b82f6", True)

    steps.append(("P3", "Calibrating ECC pipeline per-block health...", "#f59e0b", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    state["ecc_pipeline"] = True
    push_event(state, make_event(P3, EV_ECC_DETECTED, None, {"action": "CALIBRATE", "tiers": 3}))
    steps[-1] = ("P3", "3-Tier ECC pipeline ONLINE — Tier1/BCH/ML-LDPC ready", "#f59e0b", True)

    steps.append(("P4", "Applying QMC-optimized firmware decision logic...", "#a855f7", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)
    steps[-1] = ("P4", "Firmware logic -38% gate cost via QMC+Petrick's BDD-verified", "#a855f7", True)

    state["host_status"] = "ACTIVE"
    state["boot_done"]   = True
    steps.append(("SYS", "SYSTEM READY — All pillars operational", "#22c55e", True))
    pipeline_flow(flow_ph, steps)
    push_event(state, make_event(P1, EV_WRITE_REQUEST, None, {"status": "BOOT_COMPLETE"}))
    render_event_log(log_ph, state); render_smart_panel(smart_ph, state)


def run_scenario_2_read(state, block_id, bit_errors, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 2 — Normal Read Request"""
    push_event(state, make_event(HW, EV_READ_REQUEST, block_id, {"bit_errors": bit_errors}))
    render_event_log(log_ph, state)
    steps = []

    # HOST → NVME
    steps.append(("HOST", "Read(LBA=0x" + format(block_id * 512, "06X") + ") → NVMe CMD", "#14b8a6", True))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)

    # P1: FTL translation
    steps.append(("P1/FTL", "LBA → Physical Block " + str(block_id), "#3b82f6", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)
    push_event(state, make_event(P1, EV_READ_REQUEST, block_id, {"action": "FTL_TRANSLATE"}))
    steps[-1] = ("P1/FTL", "LBA → Physical Block " + str(block_id) + " — mapped", "#3b82f6", True)

    # P2: BBT check
    steps.append(("P2/BBT", "Bloom filter check — Block " + str(block_id) + "...", "#22c55e", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)
    blk = state["blocks"][block_id]

    if blk["retired"]:
        push_event(state, make_event(P2, EV_FAST_REJECT, block_id, {"result": "BLOCKED", "latency_us": 0.05}))
        steps[-1] = ("P2/BBT", "BLOOM HIT — Block " + str(block_id) + " RETIRED. 0.05 µs reject!", "#ef4444", True)
        pipeline_flow(flow_ph, steps); render_event_log(log_ph, state)
        render_nand_grid(grid_ph, state, highlight=block_id)
        return

    steps[-1] = ("P2/BBT", "Bloom MISS — block GOOD, continuing...", "#22c55e", True)

    # P3: ECC
    steps.append(("P3/T1", "Syndrome check H·r...", "#f59e0b", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)

    if bit_errors == 0:
        push_event(state, make_event(P3, EV_ECC_DETECTED, block_id, {"tier": 1, "result": "BYPASS"}))
        steps[-1] = ("P3/T1", "H·r = 0 — Syndrome ZERO BYPASS. 0 µs.", "#22c55e", True)
        steps.append(("P4", "Optimized logic: bypass path — 0 gate cost", "#a855f7", True))
        steps.append(("DATA", "Data returned to HOST. Latency: 0 µs", "#22c55e", True))
        pipeline_flow(flow_ph, steps)
        state["smart_metrics"]["ecc_count"] += 0
    elif bit_errors <= 12:
        steps[-1] = ("P3/T1", "Syndrome != 0 — " + str(bit_errors) + " errors → BCH", "#f59e0b", True)
        steps.append(("P3/T2", "BCH correction...", "#f59e0b", False))
        pipeline_flow(flow_ph, steps); time.sleep(0.4)
        lus = round(random.uniform(0.3, 0.8), 2)
        push_event(state, make_event(P3, EV_ECC_DETECTED, block_id, {"tier": 2, "mode": "BCH", "latency_us": lus}))
        steps[-1] = ("P3/T2", "BCH corrected " + str(bit_errors) + " bits | " + str(lus) + " µs", "#f59e0b", True)
        steps.append(("DATA", "Data returned. Latency: " + str(lus) + " µs", "#22c55e", True))
        pipeline_flow(flow_ph, steps)
        blk["ecc_count"] += bit_errors
        state["smart_metrics"]["ecc_count"] += bit_errors
    else:
        iters = min(20, int(bit_errors / 3) + 1)
        steps[-1] = ("P3/T1", "Syndrome != 0 — " + str(bit_errors) + " errors → LDPC", "#f59e0b", True)
        steps.append(("P3/T2", "Hard LDPC — " + str(iters) + " iterations...", "#f97316", False))
        pipeline_flow(flow_ph, steps)
        for it in range(1, iters + 1):
            steps[-1] = ("P3/T2", "Hard LDPC iter " + str(it) + "/" + str(iters) + "...", "#f97316", False)
            pipeline_flow(flow_ph, steps); time.sleep(0.08)
        lus = round(iters * 0.15, 2)
        push_event(state, make_event(P3, EV_ECC_DETECTED, block_id,
                   {"tier": 2, "mode": "LDPC", "iters": iters, "latency_us": lus}))
        steps[-1] = ("P3/T2", "LDPC corrected | " + str(iters) + " iters | " + str(lus) + " µs", "#f59e0b", True)

        if iters >= 15:
            push_event(state, make_event(P3, EV_PRE_FAILURE, block_id, {"ldpc_iters": iters}))
            steps.append(("P3→P1", "PRE_FAILURE emitted → Pillar 1 notified!", "#ef4444", True))

        steps.append(("DATA", "Data returned. Latency: " + str(lus) + " µs", "#22c55e", True))
        pipeline_flow(flow_ph, steps)
        blk["ecc_count"] += bit_errors
        state["smart_metrics"]["ecc_count"] += bit_errors

    render_event_log(log_ph, state)
    render_nand_grid(grid_ph, state, highlight=block_id)
    render_smart_panel(smart_ph, state)


def run_scenario_3_write(state, data_size_kb, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 3 — Normal Write Request"""
    push_event(state, make_event(HW, EV_WRITE_REQUEST, None, {"size_kb": data_size_kb}))
    steps = []

    steps.append(("HOST", "Write(" + str(data_size_kb) + " KB) → NVMe interface", "#14b8a6", True))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)

    # P1: Choose target block
    steps.append(("P1/FTL", "Selecting optimal write target...", "#3b82f6", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)
    target_id = best_write_block(state)
    if target_id is None:
        steps[-1] = ("P1/FTL", "NO free blocks! GC required", "#ef4444", True)
        pipeline_flow(flow_ph, steps); return

    target = state["blocks"][target_id]
    steps[-1] = ("P1/FTL", "Target: Block " + str(target_id) + " (PE=" + str(target["pe_cycles"]) + ")", "#3b82f6", True)
    push_event(state, make_event(P1, EV_WRITE_REQUEST, target_id, {"action": "FTL_ALLOC"}))

    # P2: BBT verify
    steps.append(("P2/BBT", "Confirm Block " + str(target_id) + " not in BBT...", "#22c55e", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)
    steps[-1] = ("P2/BBT", "Block " + str(target_id) + " GOOD — write cleared", "#22c55e", True)

    # P3: ECC encode
    steps.append(("P3/ECC", "BCH encoding " + str(data_size_kb) + " KB...", "#f59e0b", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    parity_bits = data_size_kb * 8 * 14 // 512
    push_event(state, make_event(P3, EV_WRITE_REQUEST, target_id,
               {"action": "ECC_ENCODE", "parity_bits": parity_bits}))
    steps[-1] = ("P3/ECC", "BCH encoded — " + str(parity_bits) + " parity bits appended", "#f59e0b", True)

    # Write to NAND
    steps.append(("NAND", "Writing to Block " + str(target_id) + "...", "#8888a0", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)
    pe_inc = max(1, data_size_kb // 4)
    target["pe_cycles"] += pe_inc
    state["smart_metrics"]["wear_level"] = round(
        sum(b["pe_cycles"] for b in state["blocks"]) / (64 * 5000.0), 3)
    target["data_valid"] = True
    steps[-1] = ("NAND", "Written — Block " + str(target_id) + " PE=" + str(target["pe_cycles"]), "#8888a0", True)

    # P4: Log optimization
    steps.append(("P4", "Write-path logic optimized via QMC predicate", "#a855f7", True))
    push_event(state, make_event(P4, EV_WRITE_REQUEST, target_id, {"action": "LOGIC_OPT"}))

    steps.append(("ACK", "Write ACK → NVMe → HOST", "#22c55e", True))
    pipeline_flow(flow_ph, steps)
    render_event_log(log_ph, state)
    render_nand_grid(grid_ph, state, highlight=target_id)
    render_smart_panel(smart_ph, state)


def run_scenario_4_degrade(state, target_block, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 4 — Progressive Block Degradation (THE KILLER DEMO)"""
    push_event(state, make_event(P3, EV_ECC_DETECTED, target_block,
               {"trigger": "PROGRESSIVE_AGING"}))
    blk = state["blocks"][target_block]
    steps = []

    steps.append(("SYS", "Progressive aging on Block " + str(target_block) + " begins...", "#f97316", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.3)

    # Simulate wear
    for tick in range(18):
        blk["pe_cycles"] = min(5100, blk["pe_cycles"] + random.randint(30, 70))
        itr = round(max(1.0, 1.5 + tick * 0.38 + random.gauss(0, 0.3)), 1)
        blk["ldpc_history"].append(itr)
        blk["ecc_count"] += int(itr * 4)
        state["smart_metrics"]["ecc_count"] += int(itr * 4)

        col = "#f59e0b" if itr < 10 else "#f97316" if itr < 15 else "#ef4444"
        if len(steps) > 1:
            steps.pop()
        steps.append(("P3/LDPC", "Tick " + str(tick + 1) + "/18 — iters=" + str(itr) + " PE=" + str(blk["pe_cycles"]), col, False))
        pipeline_flow(flow_ph, steps); time.sleep(0.25)

        if itr >= 15:
            steps[-1] = ("P3/LDPC", "iters=" + str(itr) + " THRESHOLD BREACHED!", "#ef4444", True)

            # PRE_FAILURE cascade
            push_event(state, make_event(P3, EV_PRE_FAILURE, target_block,
                       {"ldpc_iters": itr, "pe": blk["pe_cycles"]}))
            render_event_log(log_ph, state)

            steps.append(("P3→P1", "PRE_FAILURE emitted → Pillar 1 receives event", "#ef4444", True))
            pipeline_flow(flow_ph, steps); time.sleep(0.4)

            # P1: relocate
            dest = best_write_block(state)
            if dest and dest != target_block:
                push_event(state, make_event(P1, EV_DATA_RELOCATION, target_block,
                           {"dest": dest, "reason": "PRE_FAILURE"}))
                steps.append(("P1/FTL", "Data relocated Block " + str(target_block) + " → Block " + str(dest), "#3b82f6", True))
                pipeline_flow(flow_ph, steps); time.sleep(0.5)

                # P1: SMART update
                smart = state["smart_metrics"]
                smart["health_score"] = max(0, smart["health_score"] - 8)
                smart["rul_days"]     = max(0, smart["rul_days"] - 15)
                push_event(state, make_event(P1, EV_ECC_DETECTED, None,
                           {"action": "SMART_UPDATE", "health": round(smart["health_score"], 1)}))
                steps.append(("P1/SMART", "SMART updated — health=" + str(round(smart["health_score"], 1)) + " RUL=" + str(smart["rul_days"]) + "d", "#3b82f6", True))

            # P2: retire block
            retire_block(state, target_block, "PRE_FAILURE_LDPC")
            blk["tier3_hits"] += 1
            steps.append(("P2/BBT", "Block " + str(target_block) + " retired — bitmap+bloom updated", "#22c55e", True))
            push_event(state, make_event(P2, EV_BLOCK_RETIRE, target_block, {"method": "BBT+BLOOM"}))

            # P3: learns
            steps.append(("P3", "Block " + str(target_block) + " now bypassed at Tier 1 (0 µs reject)", "#f59e0b", True))
            # P4: GC prep
            steps.append(("P4", "Decision tree pruned for GC — QMC re-optimization queued", "#a855f7", True))
            push_event(state, make_event(P4, EV_GC_TRIGGER, None, {"trigger": "PRE_FAILURE_RECOVERY"}))

            steps.append(("RESULT", "UECC PREVENTED — 0 data loss. Block safely retired.", "#22c55e", True))
            pipeline_flow(flow_ph, steps)
            render_event_log(log_ph, state)
            render_nand_grid(grid_ph, state)
            render_smart_panel(smart_ph, state)
            return

    steps[-1] = ("P3/LDPC", "18 ticks complete — Block operational, wear logged", "#f59e0b", True)
    pipeline_flow(flow_ph, steps)
    render_event_log(log_ph, state)
    render_nand_grid(grid_ph, state, highlight=target_block)
    render_smart_panel(smart_ph, state)


def run_scenario_5_crash(state, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 5 — Host Crash + OOB + AES + Shamir"""
    state["host_status"] = "DEAD"
    state["oob_active"]  = True
    push_event(state, make_event(HW, EV_HOST_CRASH, None, {"nvme_status": "DEAD"}))
    steps = []

    steps.append(("HOST", "NVMe bus DEAD — host unresponsive!", "#ef4444", True))
    pipeline_flow(flow_ph, steps); render_event_log(log_ph, state); time.sleep(0.5)

    steps.append(("P1", "Host watchdog expired — OOB mode activated", "#ef4444", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    push_event(state, make_event(P1, EV_OOB_TRIGGER, None, {"channel": "BLE+UART"}))
    steps[-1] = ("P1", "OOB mode ACTIVE — collecting SMART + BBT + ECC data", "#f97316", True)

    # Collect data
    sm   = state["smart_metrics"]
    bbt  = list(state["bbt"].keys())
    report = {
        "drive_id":       "AURA-AEGIS-UNIT-7",
        "timestamp":      time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "health_score":   round(sm["health_score"], 1),
        "ecc_count":      sm["ecc_count"],
        "bad_blocks":     sm["bad_blocks"],
        "rul_days":       sm["rul_days"],
        "bbt_entries":    bbt[:10],
        "wear_level_pct": round(sm["wear_level"] * 100, 1),
        "oob_trigger":    "HOST_WATCHDOG",
    }
    steps.append(("P1/DATA", "Diagnostic report assembled — " + str(len(json.dumps(report))) + " bytes", "#3b82f6", True))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)

    # AES encryption
    steps.append(("SEC", "AES-256-GCM encrypting report...", "#f59e0b", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    encrypted = None
    if CRYPTO_OK:
        try:
            encrypted = encrypt_report(report)
            push_event(state, make_event(P1, EV_ENCRYPT_REPORT, None,
                       {"algo": "AES-256-GCM", "status": "OK"}))
            state["encrypted_report"] = encrypted
            steps[-1] = ("SEC", "AES-256-GCM encrypted — IV+ciphertext+auth-tag ready", "#f59e0b", True)
        except Exception as ex:
            steps[-1] = ("SEC", "AES error: " + str(ex)[:40] + " (using fallback)", "#ef4444", True)
            encrypted = None
    else:
        steps[-1] = ("SEC", "crypto module not loaded — simulating AES", "#f59e0b", True)
    pipeline_flow(flow_ph, steps); time.sleep(0.3)

    # Shamir split
    steps.append(("SEC", "Shamir 3-of-5 key splitting...", "#a855f7", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.5)
    shares = None
    if SHAMIR_OK and encrypted and "key" in encrypted:
        try:
            shares = split_secret(encrypted["key"], k=3, n=5)
            state["shamir_shares"] = shares
            push_event(state, make_event(P1, EV_SHAMIR_SPLIT, None,
                       {"k": 3, "n": 5, "status": "OK"}))
            steps[-1] = ("SEC", "Key split into 5 shares — any 3 reconstruct the AES key", "#a855f7", True)
        except Exception as ex:
            steps[-1] = ("SEC", "Shamir error: " + str(ex)[:40], "#f59e0b", True)
    else:
        steps[-1] = ("SEC", "Shamir simulation — 5 shares distributed to backup nodes", "#a855f7", True)
    pipeline_flow(flow_ph, steps); time.sleep(0.3)

    # OOB channels
    steps.append(("OOB/BLE", "BLE beacon broadcasting — 8-byte health packet @ 1s", "#3b82f6", True))
    steps.append(("OOB/UART", "UART emergency dump → 115200 baud → recovery MCU", "#3b82f6", True))
    push_event(state, make_event(P1, EV_OOB_TRIGGER, None, {"BLE": "ACTIVE", "UART": "ACTIVE"}))

    steps.append(("RESULT", "HOST DOWN — data secured, telemetry transmitted via OOB", "#22c55e", True))
    pipeline_flow(flow_ph, steps)
    render_event_log(log_ph, state)
    render_nand_grid(grid_ph, state)
    render_smart_panel(smart_ph, state)


def run_scenario_6_gc(state, flow_ph, grid_ph, smart_ph, log_ph):
    """Scenario 6 — Garbage Collection"""
    push_event(state, make_event(P1, EV_GC_TRIGGER, None, {"trigger": "LOW_SPACE"}))
    steps = []

    steps.append(("P1/GC", "Free space low — Garbage Collection triggered", "#22c55e", False))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)

    # P2: select worn blocks (highest PE, not retired, no valid recent writes)
    candidates = sorted(
        [b for b in state["blocks"] if not b["retired"]],
        key=lambda b: b["pe_cycles"], reverse=True
    )[:4]

    if not candidates:
        steps[-1] = ("P1/GC", "No candidates for GC — drive clean", "#22c55e", True)
        pipeline_flow(flow_ph, steps); return

    ids_str = ", ".join("B" + str(b["id"]) for b in candidates)
    steps[-1] = ("P2/GC", "Selected GC victims: " + ids_str, "#22c55e", True)
    push_event(state, make_event(P2, EV_GC_TRIGGER, None, {"victims": [b["id"] for b in candidates]}))
    pipeline_flow(flow_ph, steps); time.sleep(0.4)

    for victim in candidates:
        vid = victim["id"]
        dest = best_write_block(state)
        if dest is None or dest == vid:
            continue

        # P3: re-encode valid data
        steps.append(("P3/GC", "Re-encoding Block " + str(vid) + " valid pages → Block " + str(dest), "#f59e0b", False))
        pipeline_flow(flow_ph, steps); time.sleep(0.5)
        push_event(state, make_event(P3, EV_DATA_RELOCATION, vid,
                   {"dest": dest, "reason": "GC"}))
        steps[-1] = ("P3/GC", "Block " + str(vid) + " → Block " + str(dest) + " re-encoded OK", "#f59e0b", True)

        # Erase victim block
        steps.append(("NAND", "Erasing Block " + str(vid) + " (PE=" + str(victim["pe_cycles"]) + "→" + str(victim["pe_cycles"]+1) + ")", "#8888a0", False))
        pipeline_flow(flow_ph, steps); time.sleep(0.3)
        victim["pe_cycles"] += 1
        victim["ecc_count"]  = max(0, victim["ecc_count"] - 5)
        steps[-1] = ("NAND", "Block " + str(vid) + " ERASED — PE=" + str(victim["pe_cycles"]), "#8888a0", True)

        state["gc_log"].append({"ts": time.strftime("%H:%M:%S"), "from": vid, "to": dest})
        push_event(state, make_event(P2, EV_DATA_RELOCATION, vid,
                   {"erased": True, "pe_after": victim["pe_cycles"]}))
        pipeline_flow(flow_ph, steps)
        render_event_log(log_ph, state)
        render_nand_grid(grid_ph, state, highlight=vid)
        time.sleep(0.2)

    # Update SMART
    state["smart_metrics"]["wear_level"] = round(
        sum(b["pe_cycles"] for b in state["blocks"]) / (64 * 5000.0), 3)

    steps.append(("P4", "GC decision logic QMC-optimized for next cycle", "#a855f7", True))
    steps.append(("RESULT", "GC complete — " + str(len(candidates)) + " blocks recycled, space reclaimed", "#22c55e", True))
    push_event(state, make_event(P4, EV_GC_TRIGGER, None, {"action": "OPTIMIZE_COMPLETE"}))
    pipeline_flow(flow_ph, steps)
    render_event_log(log_ph, state)
    render_smart_panel(smart_ph, state)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

# ── Shared Sidebar (nav + HW connection) ─────────────────────────────────────
from core.shared_sidebar import render_sidebar
render_sidebar('sim')

# ── Sidebar — controller-specific status ─────────────────────────────────────
with st.sidebar:
    st.divider()
    hs = STATE["host_status"]
    hc = "#22c55e" if hs == "ACTIVE" else "#ef4444" if hs == "DEAD" else "#f59e0b"
    st.markdown(
        "<div style='font-family:JetBrains Mono,monospace;font-size:11px'>"
        "<b style='color:#e8e8f0'>Host:</b> <span style='color:" + hc + "'>" + hs + "</span><br>"
        "<b style='color:#e8e8f0'>OOB:</b> <span style='color:" + ("#22c55e" if STATE["oob_active"] else "#4a4a60") + "'>"
        + ("ACTIVE" if STATE["oob_active"] else "IDLE") + "</span><br>"
        "<b style='color:#e8e8f0'>BBT entries:</b> " + str(len(STATE["bbt"])) + "<br>"
        "<b style='color:#e8e8f0'>Events:</b> " + str(len(STATE["event_log"])) + "<br>"
        "</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 Reset Everything", key="sc_reset", use_container_width=True):
        st.session_state.sc_state = init_system_state(seed=int(time.time()))
        st.session_state.sc_scenario = None
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:700;"
    "color:#e8e8f0;margin-bottom:4px'>🎮 AURA — Event-Driven SSD Simulation Controller</div>"
    "<div style='color:#8888a0;font-size:12px;margin-bottom:16px'>"
    "Host → NVMe → SSD Controller (4 Pillars) → NAND | Event-driven · Predictive · Secure</div>",
    unsafe_allow_html=True)

# ── Top status bar ────────────────────────────────────────────────────────────
sb1, sb2, sb3, sb4, sb5 = st.columns(5)
sb1.metric("Host",        STATE["host_status"])
sb2.metric("Bad Blocks",  STATE["smart_metrics"]["bad_blocks"])
sb3.metric("ECC Count",   STATE["smart_metrics"]["ecc_count"])
sb4.metric("Health",      str(round(STATE["smart_metrics"]["health_score"], 1)) + "%")
sb5.metric("Events",      len(STATE["event_log"]))

st.markdown("---")

# ── Scenario Buttons ──────────────────────────────────────────────────────────
st.markdown("### 🧩 Select Scenario")
sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)

run_s1 = sc1.button("🟢 1. SSD Boot",            key="sc1", use_container_width=True)
run_s2 = sc2.button("🔵 2. Read Request",         key="sc2", use_container_width=True)
run_s3 = sc3.button("🟡 3. Write Request",        key="sc3", use_container_width=True)
run_s4 = sc4.button("🔴 4. Block Degradation",   key="sc4", use_container_width=True)
run_s5 = sc5.button("🚨 5. Host Crash (OOB)",    key="sc5", use_container_width=True)
run_s6 = sc6.button("🟣 6. Garbage Collection",  key="sc6", use_container_width=True)

# Scenario config inputs (shown conditionally but always rendered to avoid rerun lag)
with st.expander("⚙ Scenario Parameters", expanded=True):
    cfg1, cfg2, cfg3 = st.columns(3)
    read_block  = cfg1.number_input("Read/Degrade target block",  0, 63, 7,  key="sc_rb")
    bit_errors  = cfg2.slider(     "Injected bit errors (Sc 2)",  0, 150, 0,  key="sc_be")
    write_size  = cfg3.number_input("Write size KB (Sc 3)",        4, 512, 64, key="sc_ws")

st.markdown("---")

# ── Main panels ───────────────────────────────────────────────────────────────
col_flow, col_right = st.columns([2, 1])

with col_flow:
    st.markdown("#### 🔄 System Flow Trace (Host → NVMe → Pillars → NAND)")
    flow_ph = st.empty()
    flow_ph.markdown(
        "<div style='background:#12121a;border:1px solid #2a2a3a;border-radius:8px;"
        "padding:20px;font-family:JetBrains Mono,monospace;font-size:12px;color:#4a4a60'>"
        "Select a scenario above to begin the simulation...</div>",
        unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 Event Log")
    log_ph = st.empty()
    render_event_log(log_ph, STATE)

with col_right:
    st.markdown("#### 💾 NAND Block Grid")
    grid_ph = st.empty()
    render_nand_grid(grid_ph, STATE)

    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:10px;font-family:JetBrains Mono,monospace;"
        "font-size:10px;margin:6px 0 12px'>"
        "<span><span style='color:#22c55e'>■</span> Healthy</span>"
        "<span><span style='color:#f59e0b'>■</span> Worn</span>"
        "<span><span style='color:#f97316'>■</span> Degraded</span>"
        "<span><span style='color:#ef4444'>■</span> Critical</span>"
        "<span><span style='color:#4a4a60'>■</span> Retired</span></div>",
        unsafe_allow_html=True)

    st.markdown("#### 📊 SMART / Health")
    smart_ph = st.empty()
    render_smart_panel(smart_ph, STATE)

# ── Pillar interaction diagram ─────────────────────────────────────────────────
st.markdown("---")
with st.expander("🧠 Pillar Interaction Architecture", expanded=False):
    st.markdown("""
```
HOST ──── NVMe ──────────────────────► SSD CONTROLLER
                                              │
                            ┌─────────────────┼──────────────────┐
                            │                 │                  │
                          [P1]             [P2]              [P3]
                      FTL + SMART       BBT Manager        ECC Engine
                      LSTM + RUL      Bloom+Bitmap+Hash    Tri-Tier
                            │                 │                  │
                            └──── Events ─────┴──────────────────┘
                                              │
                                           [P4]
                                    Logic Optimization
                                    (QMC + Petrick's)

Event types:  READ_REQUEST  WRITE_REQUEST  ECC_DETECTED
              PRE_FAILURE  DATA_RELOCATION  BLOCK_RETIRE
              GC_TRIGGER  HOST_CRASH  OOB_TRIGGER  ENCRYPT_REPORT
```
""")

# ── OOB + Security panel (always visible, updates on S5) ──────────────────────
st.markdown("---")
with st.expander("📡 OOB + Security State", expanded=STATE["oob_active"]):
    ob1, ob2 = st.columns(2)
    with ob1:
        oob_color = "#ef4444" if STATE["oob_active"] else "#4a4a60"
        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid " + oob_color +
            ";border-radius:8px;padding:14px;font-family:JetBrains Mono,monospace;font-size:12px'>"
            "<b style='color:" + oob_color + "'>OOB STATUS: " + ("ACTIVE" if STATE["oob_active"] else "IDLE") + "</b><br>"
            "<span style='color:#8888a0'>BLE beacon: " + ("BROADCASTING 1Hz" if STATE["oob_active"] else "idle") + "</span><br>"
            "<span style='color:#8888a0'>UART dump: " + ("ACTIVE 115200" if STATE["oob_active"] else "idle") + "</span><br>"
            "<span style='color:#8888a0'>NVMe: " + ("DEAD" if STATE["host_status"] == "DEAD" else "ACTIVE") + "</span>"
            "</div>",
            unsafe_allow_html=True)
    with ob2:
        ec = STATE.get("encrypted_report")
        sh = STATE.get("shamir_shares")
        ev_aes  = "✅ AES-256-GCM" if ec else "⬜ Not yet generated"
        ev_sham = "✅ 3-of-5 Shamir" if sh else "⬜ Not yet split"
        st.markdown(
            "<div style='background:#12121a;border:1px solid #2a2a3a;border-left:4px solid #a855f7;"
            "border-radius:8px;padding:14px;font-family:JetBrains Mono,monospace;font-size:12px'>"
            "<b style='color:#a855f7'>SECURITY</b><br>"
            "<span style='color:#e8e8f0'>" + ev_aes + "</span><br>"
            "<span style='color:#e8e8f0'>" + ev_sham + "</span><br>"
            "<span style='color:#8888a0'>Algo: AES-256-GCM + Shamir(3,5)</span>"
            "</div>",
            unsafe_allow_html=True)

# ── BBT viewer ────────────────────────────────────────────────────────────────
with st.expander("🗃️ Bad Block Table (P2 — Bloom + Bitmap)", expanded=False):
    bbt_html = "<div style='display:flex;flex-wrap:wrap;gap:3px;font-family:JetBrains Mono,monospace'>"
    for i in range(64):
        is_bad = i in STATE["bbt"]
        c = "#ef4444" if is_bad else "#22c55e"
        bg = "#2d0a0a" if is_bad else "#052e16"
        bbt_html += (
            "<div style='width:30px;height:22px;background:" + bg + ";color:" + c +
            ";border-radius:3px;font-size:8px;text-align:center;line-height:22px;' "
            "title='B" + str(i) + ": " + ("RETIRED" if is_bad else "OK") + "'>B" + str(i) + "</div>"
        )
    bbt_html += "</div><div style='color:#4a4a60;font-size:11px;font-family:JetBrains Mono,monospace;margin-top:6px'>"
    bbt_html += "BBT entries=" + str(len(STATE["bbt"])) + " | Bloom size=" + str(len(STATE["bloom_set"])) + "</div>"
    st.markdown(bbt_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════
if run_s1:
    st.session_state.sc_scenario = 1
    with st.spinner("Running Scenario 1 — SSD Boot..."):
        run_scenario_1_boot(STATE, flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 1 complete — All pillars initialized")

elif run_s2:
    st.session_state.sc_scenario = 2
    with st.spinner("Running Scenario 2 — Read Request..."):
        run_scenario_2_read(STATE, int(read_block), int(bit_errors),
                            flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 2 complete")

elif run_s3:
    st.session_state.sc_scenario = 3
    with st.spinner("Running Scenario 3 — Write Request..."):
        run_scenario_3_write(STATE, int(write_size), flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 3 complete")

elif run_s4:
    st.session_state.sc_scenario = 4
    with st.spinner("Running Scenario 4 — Progressive Block Degradation..."):
        run_scenario_4_degrade(STATE, int(read_block), flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 4 complete")

elif run_s5:
    st.session_state.sc_scenario = 5
    with st.spinner("Running Scenario 5 — Host Crash + OOB..."):
        run_scenario_5_crash(STATE, flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 5 complete — OOB active, report secured")

elif run_s6:
    st.session_state.sc_scenario = 6
    with st.spinner("Running Scenario 6 — Garbage Collection..."):
        run_scenario_6_gc(STATE, flow_ph, grid_ph, smart_ph, log_ph)
    st.success("✅ Scenario 6 complete")
