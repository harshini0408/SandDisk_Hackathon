"""
event_bus.py — Central Event Bus for AURA Multi-Pillar Communication
=======================================================================
All pillars communicate via this shared, in-memory event queue stored in
st.session_state["event_bus"].

Event schema:
    {
        "ts":      "HH:MM:SS.mmm",
        "source":  "PILLAR_1" | "PILLAR_2" | "PILLAR_3" | "PILLAR_4",
        "type":    "PRE_FAILURE" | "DATA_RELOCATION" | "BLOCK_RETIRE"
                 | "FAST_REJECT" | "WEAR_UPDATE" | "LDPC_ESCALATE"
                 | "SMART_UPDATE" | "OPTIMIZER_APPLIED",
        "payload": { ... }              # Event-specific dict
    }

Data Flow:
    ESP32 → Pillar 1 (SMART)
    Pillar 3 (ECC stress) → PRE_FAILURE → Pillar 1 (Brain)
    Pillar 1 → DATA_RELOCATION → FTL map
    Pillar 1 → BLOCK_RETIRE → Pillar 2 (BBT)
    Pillar 2 (read check) → FAST_REJECT
    Pillar 4 (optimizer) → OPTIMIZER_APPLIED
"""

from __future__ import annotations
import time
import random
from datetime import datetime


# ── Constants ─────────────────────────────────────────────────────────────────
MAX_EVENTS      = 200     # rolling cap on event log
NUM_BLOCKS      = 64      # physical NAND blocks
LDPC_SAFE_LIMIT = 15      # iterations above which P3 raises flag
ECC_PREFAIL     = 380     # ECC count above which ML trigger fires


# ── EventBus ─────────────────────────────────────────────────────────────────
class EventBus:
    """
    Central message broker and state holder for all four pillars.
    One instance per Streamlit session, stored in session_state.
    """

    def __init__(self):
        # ── Event log ─────────────────────────────────────────────────────
        self._events: list[dict] = []

        # ── Pillar 2 state: BBT ──────────────────────────────────────────
        self.bitmap:      list[int] = [0] * NUM_BLOCKS  # 0=good, 1=bad
        self.bloom_set:   set[int]  = set()             # simulated Bloom filter
        self.retire_log:  list[dict] = []               # (block_id, reason, ts)

        # ── FTL state: relocation map ────────────────────────────────────
        self.ftl_map:  dict[int, int] = {}   # old_block → new_block
        self.ftl_log:  list[str]      = []   # human-readable log

        # ── Counters ─────────────────────────────────────────────────────
        self.pre_failure_count:   int = 0
        self.fast_reject_count:   int = 0
        self.relocation_count:    int = 0
        self.optimizer_savings:   float = 0.0  # cumulative % savings

        # ── Dedup: track last emitted block to avoid spam ─────────────────
        self._last_prefail_block: int = -1
        self._last_prefail_ts:    float = 0.0

        # ── LCD scroll buffer ─────────────────────────────────────────────
        self.lcd_lines: list[str] = [" " * 40] * 4   # 4-line × 40-char LCD

        # Seed a welcome message
        self._lcd_print("AURA AEGIS v1.0 READY")
        self._lcd_print("All pillars nominal...")

    # ── Core emit / query ─────────────────────────────────────────────────────

    def emit(self, source: str, event_type: str, payload: dict) -> dict:
        """Append one event to the bus. Returns the event dict."""
        ts = datetime.now().strftime("%H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}"
        evt = {"ts": ts, "source": source, "type": event_type, "payload": payload}
        self._events.append(evt)
        if len(self._events) > MAX_EVENTS:
            self._events = self._events[-MAX_EVENTS:]
        self._lcd_update(source, event_type, payload)
        return evt

    def get_events(self, filter_type: str | None = None) -> list[dict]:
        """Return all events, optionally filtered by type."""
        if filter_type:
            return [e for e in self._events if e["type"] == filter_type]
        return list(self._events)

    def get_recent(self, n: int = 30) -> list[dict]:
        """Return last N events (most recent last)."""
        return self._events[-n:]

    def clear(self):
        """Reset everything."""
        self.__init__()

    # ── State access ──────────────────────────────────────────────────────────

    def get_state(self) -> dict:
        return {
            "bitmap":            self.bitmap,
            "bloom_set":         self.bloom_set,
            "retire_log":        self.retire_log,
            "ftl_map":           self.ftl_map,
            "ftl_log":           self.ftl_log,
            "pre_failure_count": self.pre_failure_count,
            "fast_reject_count": self.fast_reject_count,
            "relocation_count":  self.relocation_count,
            "optimizer_savings": self.optimizer_savings,
        }

    # ── Cross-pillar cascade chain ────────────────────────────────────────────

    def process_pillar3_check(self, metrics: dict, ecc_warn: int = 250, ldpc_thresh: int = LDPC_SAFE_LIMIT) -> bool:
        """
        Called each monitoring tick with current SMART metrics.
        Implements the full P3 → P1 → P2 cascade when stress is detected.
        Returns True if PRE_FAILURE was emitted.
        """
        ecc             = metrics.get("ecc_count", 0)
        bad_blocks      = metrics.get("bad_blocks", 0)
        wear            = metrics.get("wear", 0.0)
        ldpc_iterations = min(20, int(ecc / 30))
        ml_trigger      = ecc > ECC_PREFAIL

        # ── Emit SMART_UPDATE every tick ─────────────────────────────────
        self.emit("PILLAR_1", "SMART_UPDATE", {
            "ecc": ecc, "bad_blocks": bad_blocks,
            "wear_pct": round(wear * 100, 1),
            "ldpc_iter": ldpc_iterations,
        })

        # ── Pillar 3: detect ECC stress ───────────────────────────────────
        prefail_triggered = (
            ecc > ecc_warn * 1.6 or       # ECC above critical threshold
            ldpc_iterations > ldpc_thresh or
            ml_trigger
        )

        if prefail_triggered:
            # Dedup: only re-emit for a new block or after 5s gap
            now = time.time()
            block_id = self._pick_stressed_block()
            if block_id != self._last_prefail_block or (now - self._last_prefail_ts) > 5.0:
                self._last_prefail_block = block_id
                self._last_prefail_ts    = now
                self._do_cascade(block_id, ecc, ldpc_iterations, ml_trigger)
                return True

        return False

    def _do_cascade(self, block_id: int, ecc: float, ldpc_iter: int, ml_trigger: bool):
        """Full cascade: P3 PRE_FAILURE → P1 relocate+retire → P2 BBT update."""

        # Step 1 — Pillar 3 emits PRE_FAILURE ─────────────────────────────
        self.emit("PILLAR_3", "PRE_FAILURE", {
            "block_id":       block_id,
            "ecc":            round(ecc, 0),
            "ldpc_iterations": ldpc_iter,
            "ml_trigger":     ml_trigger,
            "severity":       "HIGH" if ecc > 450 else "MEDIUM",
        })
        self.pre_failure_count += 1

        # Step 2 — Pillar 1 Brain: pick spare, relocate data ──────────────
        spare = self._find_spare(block_id)
        if spare >= 0:
            self.ftl_map[block_id] = spare
            log_entry = f"Block {block_id:02d} → {spare:02d}"
            self.ftl_log.append(log_entry)
            if len(self.ftl_log) > 20:
                self.ftl_log = self.ftl_log[-20:]

            self.emit("PILLAR_1", "DATA_RELOCATION", {
                "from_block": block_id,
                "to_block":   spare,
                "reason":     "PRE_FAILURE cascade",
            })
            self.relocation_count += 1

        # Step 3 — Pillar 1 → Pillar 2: retire the bad block ─────────────
        self.emit("PILLAR_1", "BLOCK_RETIRE", {
            "block_id": block_id,
            "reason":   f"LDPC={ldpc_iter} iter > safe limit",
        })

        # Step 4 — Pillar 2 BBT: flip bitmap + bloom filter ───────────────
        self._bbt_retire(block_id, reason=f"LDPC overrun ({ldpc_iter} iter)")

        # Step 5 — Simulate a read attempt → FAST_REJECT ──────────────────
        self._simulate_fast_reject(block_id)

        # Step 6 — Pillar 4: optimizer applied ────────────────────────────
        savings = min(40.0 + self.pre_failure_count * 0.5, 48.0)
        self.optimizer_savings = savings
        self.emit("PILLAR_4", "OPTIMIZER_APPLIED", {
            "before_ops": 10,
            "after_ops":  6,
            "savings_pct": round(savings, 1),
            "context":    f"ECC routing simplified after {self.pre_failure_count} failure(s)",
        })

    def _bbt_retire(self, block_id: int, reason: str = ""):
        """Pillar 2: mark block as bad in bitmap + bloom."""
        if 0 <= block_id < NUM_BLOCKS:
            self.bitmap[block_id] = 1
            self.bloom_set.add(block_id)
            self.retire_log.append({
                "block_id": block_id,
                "reason":   reason,
                "ts":       datetime.now().strftime("%H:%M:%S"),
            })
            if len(self.retire_log) > 20:
                self.retire_log = self.retire_log[-20:]
            self.emit("PILLAR_2", "BLOCK_RETIRE_ACK", {
                "block_id":      block_id,
                "bitmap_status": "BAD",
                "bloom_updated": True,
            })

    def _simulate_fast_reject(self, block_id: int):
        """Pillar 2 → Pillar 3: simulate a future read request being rejected at O(1)."""
        if self.bitmap[block_id] == 1:
            self.emit("PILLAR_2", "FAST_REJECT", {
                "block_id":       block_id,
                "check":          "BITMAP",
                "result":         "REJECTED — block marked BAD",
                "ecc_skipped":    True,
                "latency_us":     "< 1 µs (O(1))",
            })
            self.fast_reject_count += 1

    # ── Manual trigger (for demo button) ─────────────────────────────────────

    def manual_trigger_prefailure(self, block_id: int | None = None):
        """Force a PRE_FAILURE cascade on a specific or random block (demo use)."""
        if block_id is None:
            block_id = self._pick_stressed_block()
        self._last_prefail_block = -1   # reset dedup
        self._do_cascade(block_id, ecc=420.0, ldpc_iter=18, ml_trigger=True)

    # ── Pillar 2: wear leveling (read) ────────────────────────────────────────

    def query_bbt(self, block_id: int) -> bool:
        """Returns True if block is BAD (O(1) bitmap check)."""
        return self.bitmap[block_id] == 1 if 0 <= block_id < NUM_BLOCKS else False

    # ── LCD helpers ───────────────────────────────────────────────────────────

    def _lcd_update(self, source: str, event_type: str, payload: dict):
        """Format a compact LCD message for the inter-pillar communications."""
        short = {
            "PRE_FAILURE":       f"[P3] PRE-FAIL blk={payload.get('block_id','?')}",
            "DATA_RELOCATION":   f"[P1] RELOC {payload.get('from_block','?')}->{payload.get('to_block','?')}",
            "BLOCK_RETIRE":      f"[P1->P2] RETIRE blk={payload.get('block_id','?')}",
            "BLOCK_RETIRE_ACK":  f"[P2] BBT UPDATE blk={payload.get('block_id','?')} BAD",
            "FAST_REJECT":       f"[P2->P3] FAST-REJ blk={payload.get('block_id','?')} O(1)",
            "OPTIMIZER_APPLIED": f"[P4] OPT {payload.get('savings_pct','?')}% saved",
            "SMART_UPDATE":      f"[P1] ECC={payload.get('ecc',0):.0f} W={payload.get('wear_pct',0):.0f}%",
            "LDPC_ESCALATE":     f"[P3->P1] LDPC ESC iter={payload.get('iterations','?')}",
        }.get(event_type, f"[{source[-1]}] {event_type}")

        # Scroll LCD up, add new line at bottom
        line = short[:40].ljust(40)
        self.lcd_lines = self.lcd_lines[1:] + [line]

    def _lcd_print(self, text: str):
        self.lcd_lines = self.lcd_lines[1:] + [text[:40].ljust(40)]

    # ── Internal utilities ────────────────────────────────────────────────────

    def _pick_stressed_block(self) -> int:
        """Pick a random block that is not already retired."""
        good = [i for i in range(NUM_BLOCKS) if self.bitmap[i] == 0]
        return random.choice(good) if good else 0

    def _find_spare(self, exclude: int) -> int:
        """Find a healthy spare block for relocation (not already used or bad)."""
        used   = set(self.ftl_map.values()) | self.bloom_set | {exclude}
        spares = [i for i in range(NUM_BLOCKS) if i not in used]
        return random.choice(spares) if spares else -1


# ── Session state helpers (call from Streamlit pages) ─────────────────────────

def get_bus() -> EventBus:
    """Get or create the singleton EventBus from session_state."""
    import streamlit as st  # type: ignore
    if "event_bus" not in st.session_state:
        st.session_state["event_bus"] = EventBus()
    return st.session_state["event_bus"]


def emit_event(source: str, event_type: str, payload: dict) -> dict:
    """Convenience wrapper for get_bus().emit(...)."""
    return get_bus().emit(source, event_type, payload)
