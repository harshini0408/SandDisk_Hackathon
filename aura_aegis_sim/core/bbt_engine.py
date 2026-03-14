"""
BBT Engine — Bad Block Table with 3-tier lookup
Tier 1a: Bloom Filter (256-bit) — probabilistic pre-check
Tier 1b: Bitmap (64-bit) — O(1) bit arithmetic
Tier 2:  Cuckoo Hash Table — exact metadata lookup
"""
import hashlib
import struct
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class BlockMeta:
    block_idx: int
    reason: str  # FACTORY_DEFECT | ERASE_FAIL | PROGRAM_FAIL | WEAR_RETIREMENT | PREDICTIVE_RETIREMENT
    pe_count: int
    timestamp: float = field(default_factory=time.time)


class BloomFilter:
    """256-bit bloom filter for fast bad-block pre-screening."""

    BITS = 256

    def __init__(self):
        self.data = bytearray(32)  # 256 bits = 32 bytes

    def _hashes(self, idx: int):
        h1 = (idx * 7 + 3) % self.BITS
        h2 = (idx * 13 + 7) % self.BITS
        h3 = (idx * 19 + 11) % self.BITS
        return h1, h2, h3

    def add(self, idx: int):
        for h in self._hashes(idx):
            self.data[h // 8] |= (1 << (h % 8))

    def check(self, idx: int) -> bool:
        """Return True if idx MIGHT be bad (1-in-bloom).
        Return False means DEFINITELY good (0-in-bloom)."""
        return all((self.data[h // 8] >> (h % 8)) & 1 for h in self._hashes(idx))

    def bit_grid(self):
        """Return 16×16 grid (list of lists) for visualization."""
        bits = []
        for byte in self.data:
            for b in range(8):
                bits.append((byte >> b) & 1)
        return [bits[i*16:(i+1)*16] for i in range(16)]

    def set_positions(self, idx: int):
        return self._hashes(idx)

    def reset(self):
        self.data = bytearray(32)


class Bitmap:
    """64-bit bitmap — one bit per block, O(1) check via shift-and-mask."""

    def __init__(self, num_blocks=64):
        self.num_blocks = num_blocks
        self.data = bytearray(num_blocks // 8)

    def set_bad(self, idx: int):
        byte = idx >> 3
        bit = idx & 7
        self.data[byte] |= (1 << bit)

    def is_bad(self, idx: int) -> bool:
        byte = idx >> 3
        bit = idx & 7
        return bool((self.data[byte] >> bit) & 1)

    def clear(self, idx: int):
        byte = idx >> 3
        bit = idx & 7
        self.data[byte] &= ~(1 << bit)

    def grid_rows(self):
        """Return list of 8 strings like '00100000' for display."""
        rows = []
        for byte in self.data:
            rows.append(format(byte, '08b')[::-1])  # LSB first (bit 0 = block 0)
        return rows

    def binary_repr(self):
        return ' '.join(format(b, '08b') for b in self.data)

    def reset(self):
        self.data = bytearray(self.num_blocks // 8)


class CuckooHashTable:
    """Two-table cuckoo hash for O(1) worst-case bad block metadata."""

    SIZE = 16  # slots per table

    def __init__(self):
        self.t1: list[Optional[BlockMeta]] = [None] * self.SIZE
        self.t2: list[Optional[BlockMeta]] = [None] * self.SIZE

    def _h1(self, idx: int) -> int:
        return (idx * 31 + 17) % self.SIZE

    def _h2(self, idx: int) -> int:
        return (idx * 37 + 23) % self.SIZE

    def insert(self, meta: BlockMeta) -> bool:
        idx = meta.block_idx
        for _ in range(32):
            pos1 = self._h1(idx)
            if self.t1[pos1] is None:
                self.t1[pos1] = meta
                return True
            meta, self.t1[pos1] = self.t1[pos1], meta
            idx = meta.block_idx
            pos2 = self._h2(idx)
            if self.t2[pos2] is None:
                self.t2[pos2] = meta
                return True
            meta, self.t2[pos2] = self.t2[pos2], meta
            idx = meta.block_idx
        return False  # cycle detected (very rare, would trigger rehash)

    def lookup(self, idx: int) -> Optional[BlockMeta]:
        pos1 = self._h1(idx)
        if self.t1[pos1] and self.t1[pos1].block_idx == idx:
            return self.t1[pos1]
        pos2 = self._h2(idx)
        if self.t2[pos2] and self.t2[pos2].block_idx == idx:
            return self.t2[pos2]
        return None

    def h1_pos(self, idx: int) -> int:
        return self._h1(idx)

    def h2_pos(self, idx: int) -> int:
        return self._h2(idx)

    def table_snapshot(self):
        """Return (t1, t2) as lists of (slot, meta_or_None)."""
        return list(self.t1), list(self.t2)

    def reset(self):
        self.t1 = [None] * self.SIZE
        self.t2 = [None] * self.SIZE


class BBTEngine:
    """Unified Bad Block Table with 3-tier lookup."""

    def __init__(self):
        self.bloom = BloomFilter()
        self.bitmap = Bitmap()
        self.cuckoo = CuckooHashTable()
        self.crc = 0
        self._bad_count = 0

    def mark_bad(self, idx: int, reason: str, pe_count: int) -> BlockMeta:
        meta = BlockMeta(block_idx=idx, reason=reason, pe_count=pe_count)
        self.bloom.add(idx)
        self.bitmap.set_bad(idx)
        self.cuckoo.insert(meta)
        self._update_crc()
        self._bad_count += 1
        return meta

    def check_block(self, idx: int) -> tuple[bool, str]:
        """
        Returns (is_bad, tier_used).
        Tier: 'bloom_miss' | 'bitmap' | 'cuckoo'
        """
        if not self.bloom.check(idx):
            return False, 'bloom_miss'
        if self.bitmap.is_bad(idx):
            return True, 'bitmap+cuckoo'
        return False, 'bitmap'

    def get_metadata(self, idx: int) -> Optional[BlockMeta]:
        return self.cuckoo.lookup(idx)

    def _update_crc(self):
        data = bytes(self.bitmap.data) + bytes(self.bloom.data)
        self.crc = struct.unpack('>I', hashlib.md5(data).digest()[:4])[0]

    def bad_count(self) -> int:
        return self._bad_count

    def write_trace(self, idx: int, pe_count: int) -> list[str]:
        """Generate a human-readable trace for a write to `idx`."""
        lines = [f"Write Request → Block {idx}"]
        h1, h2, h3 = self.bloom.set_positions(idx)
        b1 = (self.bloom.data[h1 // 8] >> (h1 % 8)) & 1
        b2 = (self.bloom.data[h2 // 8] >> (h2 % 8)) & 1
        b3 = (self.bloom.data[h3 // 8] >> (h3 % 8)) & 1
        bloom_hit = b1 and b2 and b3
        lines.append(
            f"  ↳ B1: Bloom → H1={h1}, H2={h2}, H3={h3} → bits={b1},{b2},{b3} "
            f"→ {'MAYBE BAD → check bitmap' if bloom_hit else 'DEFINITELY GOOD'}"
        )
        if not bloom_hit:
            lines.append(f"  ↳ Write proceeds directly. P/E {idx}: {pe_count} → {pe_count+1}")
            return lines

        is_bad = self.bitmap.is_bad(idx)
        byte_pos = idx >> 3
        bit_pos = idx & 7
        byte_val = format(self.bitmap.data[byte_pos], '08b')
        lines.append(
            f"  ↳ B2: Bitmap[{byte_pos}] = {byte_val} → bit {bit_pos} = "
            f"{'1 → CONFIRMED BAD' if is_bad else '0 → FALSE POSITIVE → GOOD'}"
        )
        if not is_bad:
            lines.append(f"  ↳ Write proceeds. P/E {idx}: {pe_count} → {pe_count+1}")
            return lines

        meta = self.cuckoo.lookup(idx)
        if meta:
            lines.append(
                f"  ↳ B3: Cuckoo → T1[H1({idx})] → key={idx}, match! → "
                f"{{reason: {meta.reason}, pe_count: {meta.pe_count}}}"
            )
        lines.append(f"  ↳ B4: BAD_BLOCK logged → SMART counter #3 updated")
        lines.append(f"  ↳ B5: FTL remaps → spare block selected → write proceeds")
        return lines
