"""
SSD Simulator — Central state machine for the AURA-AEGIS demo.
Manages all 64 blocks, P/E counts, SMART metrics, events, and simulation modes.
"""
import time
import math
import random
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from core.bbt_engine import BBTEngine, BlockMeta


# Block states
STATE_GOOD      = 'GOOD'
STATE_BAD       = 'BAD'
STATE_RETIRED   = 'RETIRED'
STATE_RESERVED  = 'RESERVED'
STATE_ACTIVE    = 'ACTIVE'

# Fail reasons
REASON_FACTORY  = 'FACTORY_DEFECT'
REASON_ERASE    = 'ERASE_FAIL'
REASON_PROGRAM  = 'PROGRAM_FAIL'
REASON_WEAR     = 'WEAR_RETIREMENT'
REASON_PREDICT  = 'PREDICTIVE_RETIREMENT'

MAX_PE = 3000
RETIRE_THRESHOLD = 0.90  # 90% of max PE
TOTAL_BLOCKS = 64
RESERVED_BLOCKS = {0, 1}
FACTORY_BAD = {5, 11, 23}


@dataclass
class BlockInfo:
    idx: int
    state: str = STATE_GOOD
    pe_count: int = 0
    fail_reason: Optional[str] = None
    fail_ts: Optional[float] = None
    last_written: float = 0.0


@dataclass
class SMARTSnapshot:
    t: float
    ecc_rate: float          # ① corrections/hr
    uecc_count: int          # ②
    bad_block_count: int     # ③
    pe_avg: float            # ④
    wear_level: float        # ⑤ 0–1
    rber: float              # ⑥
    temperature: float       # ⑦ °C
    read_latency_us: float   # ⑧ µs
    retry_freq: float        # ⑨ /hr
    reallocated: int         # ⑩
    program_fail: int        # ⑪
    erase_fail: int          # ⑫


class SSDSimulator:
    def __init__(self, preset: str = 'fresh'):
        self.blocks: list[BlockInfo] = [BlockInfo(idx=i) for i in range(TOTAL_BLOCKS)]
        self.bbt = BBTEngine()
        self.events: list[str] = []
        self.smart_history: list[SMARTSnapshot] = []
        self.sim_time: float = 0.0
        self.mode: str = 'normal'
        self.speed: float = 1.0
        self.ecc_corrections: int = 0
        self.uecc_count: int = 0
        self.program_fails: int = 0
        self.erase_fails: int = 0
        self.reallocated: int = 0
        self.temperature: float = 42.0
        self.ldpc_iter_caps: dict[int, int] = {}  # per block override
        self.tier1_bypasses: int = 0
        self.tier2_corrections: int = 0
        self.tier3_escalations: int = 0
        self.health_score: float = 100.0
        self.failure_prob: float = 0.0
        self.rul_days: float = 365.0
        self.anomaly_type: str = 'NONE'
        self.workload: str = 'Sequential large writes'
        self.lstm_attention: Optional[np.ndarray] = None
        self._rng = random.Random(42)
        self._tick_count: int = 0
        self._apply_preset(preset)

    def _apply_preset(self, preset: str):
        if preset == 'fresh':
            pass
        elif preset == 'middle_aged':
            for i, blk in enumerate(self.blocks):
                if i in RESERVED_BLOCKS:
                    continue
                blk.pe_count = self._rng.randint(1000, 2000)
            self._mark_initial_bad_blocks(FACTORY_BAD | {11, 23}, REASON_FACTORY)
        elif preset == 'end_of_life':
            for i, blk in enumerate(self.blocks):
                if i in RESERVED_BLOCKS:
                    continue
                blk.pe_count = self._rng.randint(2400, 2900)
            self._mark_initial_bad_blocks({5, 11, 23, 31, 37, 42, 53, 59}, REASON_FACTORY)
        elif preset == 'critical':
            for i, blk in enumerate(self.blocks):
                if i in RESERVED_BLOCKS:
                    continue
                blk.pe_count = self._rng.randint(2700, 3000)
            self._mark_initial_bad_blocks({5, 11, 23, 31, 37, 42, 53, 59}, REASON_FACTORY)
            self.health_score = 15.0
            self.failure_prob = 0.82
            self.rul_days = 3.0
            self.anomaly_type = 'CRITICAL'
        # Always mark reserved blocks
        for i in RESERVED_BLOCKS:
            self.blocks[i].state = STATE_RESERVED
        # Seed factory bad blocks for fresh/default
        if preset == 'fresh':
            self._mark_initial_bad_blocks(FACTORY_BAD, REASON_FACTORY)

    def _mark_initial_bad_blocks(self, bad_set: set, reason: str):
        for idx in bad_set:
            if idx >= TOTAL_BLOCKS or idx in RESERVED_BLOCKS:
                continue
            if self.blocks[idx].state not in (STATE_BAD, STATE_RETIRED):
                self.blocks[idx].state = STATE_BAD
                self.blocks[idx].fail_reason = reason
                self.blocks[idx].fail_ts = self.sim_time
                self.bbt.mark_bad(idx, reason, self.blocks[idx].pe_count)

    def _log_event(self, msg: str):
        ts = self._format_ts(self.sim_time)
        self.events.append(f"[{ts}] {msg}")
        if len(self.events) > 100:
            self.events.pop(0)

    def _format_ts(self, t: float) -> str:
        h = int(t) // 3600
        m = (int(t) % 3600) // 60
        s = int(t) % 60
        return f"T+{h:02d}:{m:02d}:{s:02d}"

    def good_blocks(self) -> list[int]:
        return [
            i for i, b in enumerate(self.blocks)
            if b.state == STATE_GOOD and i not in RESERVED_BLOCKS
        ]

    def _avg_pe(self) -> float:
        goodish = [b.pe_count for b in self.blocks if b.state in (STATE_GOOD, STATE_ACTIVE)]
        return float(np.mean(goodish)) if goodish else 0.0

    def _wear_level(self) -> float:
        return self._avg_pe() / MAX_PE

    def _compute_rber(self) -> float:
        avg_pe = self._avg_pe()
        return 1e-7 * math.exp(avg_pe / 500.0)

    def tick(self, dt_seconds: float = 1.0):
        """Advance simulation by dt_seconds of simulated time."""
        self._tick_count += 1
        self.sim_time += dt_seconds

        write_rate = {'normal': 2, 'stress': 15, 'aging': 30, 'crash': 1}[self.mode]
        num_writes = self._rng.randint(write_rate, write_rate * 3)

        # Temperature drift
        base_temp = {'normal': 42, 'stress': 65, 'aging': 50, 'crash': 45}[self.mode]
        self.temperature = base_temp + self._rng.gauss(0, 3)
        self.temperature = max(20, min(85, self.temperature))

        # Perform writes
        candidates = self.good_blocks()
        for _ in range(num_writes):
            if not candidates:
                break
            idx = self._rng.choice(candidates)
            self.blocks[idx].pe_count += 1
            self.blocks[idx].state = STATE_ACTIVE
            self.blocks[idx].last_written = self.sim_time

            # ECC simulation
            wear = self.blocks[idx].pe_count / MAX_PE
            rber = 1e-7 * math.exp(self.blocks[idx].pe_count / 500.0)
            ecc_prob = min(0.9, rber * 1e6 * (1 + 0.5 * wear))

            if self._rng.random() < ecc_prob:
                self.ecc_corrections += 1
                if self._rng.random() < (wear ** 4):
                    tier = self._rng.choice([3, 'UECC'])
                    if tier == 'UECC':
                        self.uecc_count += 1
                        self._log_event(f"UECC on Block {idx} — P/E {self.blocks[idx].pe_count} — unrecoverable")
                    else:
                        self.tier3_escalations += 1
                        self._log_event(f"LDPC escalated to Tier 3 on Block {idx} — soft decode succeeded")
                elif wear > 0.5 and self._rng.random() < wear * 0.3:
                    self.tier2_corrections += 1
                else:
                    self.tier1_bypasses += 1

            # Check wear retirement
            if self.blocks[idx].pe_count >= int(MAX_PE * RETIRE_THRESHOLD):
                self._retire_block(idx, REASON_WEAR)
                candidates = self.good_blocks()
            else:
                # Random fail events
                fail_chance = 0.0005 * (1 + wear * 3) * (1.5 if self.mode == 'stress' else 1.0)
                if self._rng.random() < fail_chance:
                    fail_type = self._rng.choice([REASON_ERASE, REASON_PROGRAM])
                    if fail_type == REASON_ERASE:
                        self.erase_fails += 1
                    else:
                        self.program_fails += 1
                    self._mark_bad(idx, fail_type)
                    candidates = self.good_blocks()
                else:
                    self.blocks[idx].state = STATE_GOOD

        self._update_smart()
        self._update_health()

    def _retire_block(self, idx: int, reason: str):
        if self.blocks[idx].state in (STATE_BAD, STATE_RETIRED, STATE_RESERVED):
            return
        self.blocks[idx].state = STATE_RETIRED
        self.blocks[idx].fail_reason = reason
        self.blocks[idx].fail_ts = self.sim_time
        self.bbt.mark_bad(idx, reason, self.blocks[idx].pe_count)
        self.reallocated += 1
        self._log_event(
            f"Block {idx} retired — P/E count {self.blocks[idx].pe_count}/{MAX_PE} — {reason}"
        )

    def _mark_bad(self, idx: int, reason: str):
        if self.blocks[idx].state in (STATE_BAD, STATE_RETIRED, STATE_RESERVED):
            return
        self.blocks[idx].state = STATE_BAD
        self.blocks[idx].fail_reason = reason
        self.blocks[idx].fail_ts = self.sim_time
        self.bbt.mark_bad(idx, reason, self.blocks[idx].pe_count)
        self._log_event(f"Block {idx} marked BAD — reason: {reason}")

    def force_bad(self, idx: int):
        self._mark_bad(idx, REASON_PROGRAM)

    def inject_thermal_spike(self):
        self.temperature = 85.0
        self._log_event("THERMAL SPIKE injected — temperature: 85°C for 30s")
        # Fast-forward: boost ecc rate
        self.ecc_corrections += 500
        self.tier3_escalations += 20

    def inject_write_storm(self):
        self._log_event("WRITE STORM injected — 10,000 writes in simulated 5s")
        for _ in range(200):
            cands = self.good_blocks()
            if not cands:
                break
            idx = self._rng.choice(cands)
            self.blocks[idx].pe_count += 5
            if self.blocks[idx].pe_count >= int(MAX_PE * RETIRE_THRESHOLD):
                self._retire_block(idx, REASON_WEAR)
        self.ecc_corrections += 2000

    def kill_host(self):
        self._log_event("HOST CRASH DETECTED — PCIe bus unresponsive — triggering OOB dump")
        self.mode = 'crash'

    def fast_forward_wear(self, block_idx: int, target_pe: int = 2700):
        blk = self.blocks[block_idx]
        if blk.state in (STATE_BAD, STATE_RETIRED, STATE_RESERVED):
            return False
        blk.pe_count = target_pe
        self._retire_block(block_idx, REASON_WEAR)
        return True

    def predictive_retire(self, block_idx: int):
        blk = self.blocks[block_idx]
        if blk.state not in (STATE_GOOD, STATE_ACTIVE):
            return False
        self._retire_block(block_idx, REASON_PREDICT)
        self._log_event(
            f"LSTM → Predictive retirement: Block {block_idx} — projected failure avoided"
        )
        return True

    def set_ldpc_cap(self, block_idx: int, cap: int):
        self.ldpc_iter_caps[block_idx] = cap
        self._log_event(
            f"LSTM → LDPC ceiling for Block {block_idx} raised to {cap} iterations"
        )

    def _update_smart(self):
        snap = SMARTSnapshot(
            t=self.sim_time,
            ecc_rate=self.ecc_corrections * 3600 / max(self.sim_time, 1),
            uecc_count=self.uecc_count,
            bad_block_count=sum(1 for b in self.blocks if b.state in (STATE_BAD, STATE_RETIRED)),
            pe_avg=self._avg_pe(),
            wear_level=self._wear_level(),
            rber=self._compute_rber(),
            temperature=self.temperature,
            read_latency_us=75.0 + 12.0 * self._wear_level() + self._rng.gauss(0, 2),
            retry_freq=self.tier3_escalations * 3600 / max(self.sim_time, 1),
            reallocated=self.reallocated,
            program_fail=self.program_fails,
            erase_fail=self.erase_fails,
        )
        self.smart_history.append(snap)
        if len(self.smart_history) > 10000:
            self.smart_history = self.smart_history[-5000:]

    def _update_health(self):
        wear = self._wear_level()
        bad_ratio = sum(1 for b in self.blocks if b.state in (STATE_BAD, STATE_RETIRED)) / TOTAL_BLOCKS
        rber = self._compute_rber()
        ecc_score = max(0, 1 - self.tier3_escalations / max(self.ecc_corrections + 1, 1))

        raw = (
            0.40 * (1 - wear) +
            0.25 * (1 - bad_ratio * 5) +
            0.20 * max(0, 1 - rber * 1e6) +
            0.15 * ecc_score
        )
        self.health_score = max(0.0, min(100.0, raw * 100))
        self.failure_prob = min(1.0, wear ** 2 + bad_ratio * 2 + rber * 1e5)
        self.rul_days = max(0.0, (1 - wear) * 365 * (1 - bad_ratio * 3))

        if self.failure_prob > 0.7 or self.health_score < 20:
            self.anomaly_type = 'CRITICAL'
        elif self.failure_prob > 0.4 or self.health_score < 40:
            self.anomaly_type = 'ACCELERATING'
        elif self.failure_prob > 0.2 or self.health_score < 65:
            self.anomaly_type = 'WATCH'
        elif wear > 0.3:
            self.anomaly_type = 'SLOW_BURN'
        else:
            self.anomaly_type = 'NONE'

    def get_latest_smart(self) -> Optional[SMARTSnapshot]:
        return self.smart_history[-1] if self.smart_history else None

    def get_smart_history_array(self, n: int = 200) -> dict:
        history = self.smart_history[-n:]
        if not history:
            return {}
        fields = ['ecc_rate', 'uecc_count', 'bad_block_count', 'pe_avg',
                  'wear_level', 'rber', 'temperature', 'read_latency_us',
                  'retry_freq', 'reallocated', 'program_fail', 'erase_fail']
        return {
            't': [s.t for s in history],
            **{f: [getattr(s, f) for s in history] for f in fields}
        }

    def block_color(self, idx: int) -> str:
        if idx in RESERVED_BLOCKS:
            return '#6b7280'
        blk = self.blocks[idx]
        if blk.state == STATE_RESERVED:
            return '#6b7280'
        if blk.state == STATE_ACTIVE:
            return '#3b82f6'
        if blk.state == STATE_BAD:
            if blk.fail_reason == REASON_FACTORY:
                return '#7f1d1d'
            return '#ef4444'
        if blk.state == STATE_RETIRED:
            return '#7c3aed'
        pe_ratio = blk.pe_count / MAX_PE
        if pe_ratio < 0.2:
            return '#22c55e'
        if pe_ratio < 0.5:
            return '#84cc16'
        if pe_ratio < 0.8:
            return '#eab308'
        if pe_ratio < 0.9:
            return '#f97316'
        return '#ef4444'

    def simulate_write_burst(self, n: int = 10) -> list[list[str]]:
        """Return trace lines for n write requests."""
        traces = []
        good = self.good_blocks()
        if not good:
            return traces
        choose = self._rng.choices(good, k=min(n, len(good)))
        # Mix in known bad blocks for drama
        bad = [i for i, b in enumerate(self.blocks)
               if b.state in (STATE_BAD,) and i not in RESERVED_BLOCKS]
        for i in range(min(3, len(bad))):
            choose[i] = bad[i]
        self._rng.shuffle(choose)
        for idx in choose:
            trace = self.bbt.write_trace(idx, self.blocks[idx].pe_count)
            traces.append(trace)
        return traces

    def wear_retirement_trace(self, block_idx: int = 7) -> list[str]:
        """Return step-by-step retirement trace for a block."""
        blk = self.blocks[block_idx]
        pe = blk.pe_count or 2700
        spare = self.good_blocks()
        spare_idx = spare[0] if spare else 52
        lines = [
            f"Phase D triggered — Block {block_idx} P/E count: {pe}/{MAX_PE}",
            f"  Step 1: Copy valid data Block {block_idx} → Block {spare_idx} (spare)",
            f"  Step 2: Bitmap bit {block_idx} = 1 (one instruction)",
            f"  Step 3: Cuckoo insert → {{key:{block_idx}, reason:WEAR_RETIREMENT, pe:{pe}}}",
            f"  Step 4: Bloom filter updated (H1,H2,H3 for {block_idx} set to 1)",
            f"  Step 5: BBT persisted to NAND Block 0 with new CRC: 0x{self.bbt.crc:08X}",
            f"  Step 6: SMART counters ④⑤⑩ updated → Pillar 4 LSTM re-runs",
        ]
        return lines
