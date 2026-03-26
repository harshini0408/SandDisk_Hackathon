"""
sim_state.py — Shared global state + event system for the Simulation Controller.
All pillars and the controller import from here.
"""
from __future__ import annotations
import time
import random
from typing import List, Dict, Any

# ── Event type constants ──────────────────────────────────────────────────────
EV_READ_REQUEST    = "READ_REQUEST"
EV_WRITE_REQUEST   = "WRITE_REQUEST"
EV_ECC_DETECTED    = "ECC_DETECTED"
EV_PRE_FAILURE     = "PRE_FAILURE"
EV_DATA_RELOCATION = "DATA_RELOCATION"
EV_BLOCK_RETIRE    = "BLOCK_RETIRE"
EV_FAST_REJECT     = "FAST_REJECT"
EV_GC_TRIGGER      = "GC_TRIGGER"
EV_HOST_CRASH      = "HOST_CRASH"
EV_OOB_TRIGGER     = "OOB_TRIGGER"
EV_ENCRYPT_REPORT  = "ENCRYPT_REPORT"
EV_SHAMIR_SPLIT    = "SHAMIR_SPLIT"

# ── Pillar source tags ────────────────────────────────────────────────────────
P1 = "PILLAR_1"
P2 = "PILLAR_2"
P3 = "PILLAR_3"
P4 = "PILLAR_4"
HW = "HOST"
NV = "NVME"


def make_event(source: str, ev_type: str, block_id: int | None = None,
               details: Dict[str, Any] | None = None) -> Dict:
    return {
        "ts":       time.strftime("%H:%M:%S"),
        "source":   source,
        "type":     ev_type,
        "block_id": block_id,
        "details":  details or {},
    }


# ── Default system_state factory ─────────────────────────────────────────────
def init_system_state(seed: int = 42) -> Dict:
    rng = random.Random(seed)
    blocks = []
    for i in range(64):
        pe = rng.randint(0, 4500)
        retired = i in (3, 11, 29)
        blocks.append({
            "id":            i,
            "pe_cycles":     pe,
            "ecc_count":     int(pe * 0.08 + rng.uniform(0, 5)),
            "ldpc_avg":      round(rng.uniform(1, 6), 1),
            "ldpc_history":  [],
            "retired":       retired,
            "tier3_hits":    0,
            "data_valid":    not retired,
        })

    bad = [b["id"] for b in blocks if b["retired"]]
    return {
        "blocks":        blocks,
        "bbt":           {b: True for b in bad},
        "bloom_set":     set(bad),
        "smart_metrics": {
            "ecc_count":     sum(b["ecc_count"] for b in blocks),
            "bad_blocks":    len(bad),
            "wear_level":    round(sum(b["pe_cycles"] for b in blocks) / (64 * 5000.0), 3),
            "temperature":   42.0,
            "rul_days":      180.0,
            "health_score":  85.0,
        },
        "event_log":     [],
        "host_status":   "ACTIVE",
        "oob_active":    False,
        "lstm_ready":    False,
        "ecc_pipeline":  False,
        "boot_done":     False,
        "current_scenario": None,
        "active_pillar": None,
        "relocations":   [],
        "gc_log":        [],
        "encrypted_report": None,
        "shamir_shares":    None,
    }


def push_event(state: Dict, ev: Dict):
    """Add event to the log (keep last 60)."""
    state["event_log"].append(ev)
    if len(state["event_log"]) > 60:
        state["event_log"] = state["event_log"][-60:]


def retire_block(state: Dict, block_id: int, reason: str) -> Dict:
    """Mark block as retired, update BBT + Bloom filter."""
    blk = state["blocks"][block_id]
    blk["retired"] = True
    blk["data_valid"] = False
    state["bbt"][block_id] = True
    state["bloom_set"].add(block_id)
    state["smart_metrics"]["bad_blocks"] += 1
    push_event(state, make_event(P2, EV_BLOCK_RETIRE, block_id,
               {"reason": reason, "pe_cycles": blk["pe_cycles"]}))
    return blk


def best_write_block(state: Dict) -> int | None:
    """Pillar 2: choose lowest-PE non-retired block."""
    candidates = [b for b in state["blocks"] if not b["retired"]]
    if not candidates:
        return None
    return min(candidates, key=lambda b: b["pe_cycles"])["id"]


def rber_est(pe: int) -> float:
    return min(1e-3, 1e-7 * (1.05 ** (pe / 100)))


def health_label(pe: int, retired: bool) -> str:
    if retired:
        return "RETIRED"
    if pe < 1500:
        return "healthy"
    if pe < 3000:
        return "worn"
    if pe < 4500:
        return "degraded"
    return "critical"


BLOCK_CSS = {
    "healthy":  ("#22c55e", "#052e16"),
    "worn":     ("#f59e0b", "#3d2600"),
    "degraded": ("#f97316", "#3d1200"),
    "critical": ("#ef4444", "#3d0000"),
    "RETIRED":  ("#4a4a60", "#1a1a1a"),
}
