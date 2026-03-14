"""
LDPC Engine — ECC / LDPC Correction Pipeline
Tier 1: Syndrome check (H·r mod 2)
Tier 2: Hard-decision bit-flip LDPC (8–20 iterations)
Tier 3: ML-assisted soft decode (voltage shift model)
BCH: Simulated BCH for metadata blocks
"""
import numpy as np
from typing import Optional


# Fixed parity-check matrix H (6 × 16 sparse binary)
# Rows = parity checks, Cols = bit positions
H_MATRIX = np.array([
    [1,1,0,1,0,0,1,0,0,1,0,0,1,0,0,1],
    [0,1,1,0,1,0,0,1,0,0,1,0,0,1,0,0],
    [1,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0,0,1],
    [1,0,0,0,1,0,0,1,1,0,0,0,1,1,0,0],
    [0,1,0,0,0,1,1,0,0,0,0,1,1,0,1,0],
], dtype=np.uint8)

N_BITS = 16
N_CHECKS = 6


def compute_syndrome(codeword: np.ndarray) -> np.ndarray:
    """Compute syndrome s = H · r (mod 2)."""
    return (H_MATRIX @ codeword) % 2


def inject_errors(codeword: np.ndarray, num_errors: int, seed: int = None) -> tuple:
    """Return (corrupted_word, error_positions)."""
    rng = np.random.default_rng(seed)
    positions = rng.choice(N_BITS, size=min(num_errors, N_BITS), replace=False)
    corrupted = codeword.copy()
    corrupted[positions] ^= 1
    return corrupted, positions.tolist()


def hard_ldpc_decode(
    received: np.ndarray,
    max_iter: int = 8,
    threshold: int = 2
) -> tuple[np.ndarray, bool, list[dict]]:
    """
    Gallager bit-flipping LDPC decoder.
    Returns (decoded_word, success, iteration_log).
    iteration_log entries: {'iter': i, 'failed_checks': list, 'flipped': list, 'passing': int}
    """
    word = received.copy()
    log = []

    for i in range(1, max_iter + 1):
        syndrome = compute_syndrome(word)
        passing = int(N_CHECKS - syndrome.sum())

        # Count failed checks per bit
        failed_per_bit = []
        for bit in range(N_BITS):
            count = sum(H_MATRIX[chk, bit] and syndrome[chk] for chk in range(N_CHECKS))
            failed_per_bit.append(int(count))

        flipped = [b for b, c in enumerate(failed_per_bit) if c > threshold]

        log.append({
            'iter': i,
            'failed_checks': failed_per_bit,
            'flipped': flipped,
            'passing': passing,
        })

        if syndrome.sum() == 0:
            return word, True, log

        for b in flipped:
            word[b] ^= 1

    # Final check
    syndrome = compute_syndrome(word)
    return word, bool(syndrome.sum() == 0), log


def bch_decode(received: np.ndarray, t: int = 2) -> tuple[np.ndarray, bool]:
    """
    Simulated BCH decoder (corrects up to t errors).
    Real BCH uses GF arithmetic; here we simulate by counting syndrome weight.
    """
    syndrome = compute_syndrome(received)
    error_weight = int(syndrome.sum())
    if error_weight == 0:
        return received, True
    if error_weight <= t:
        # Try to correct by flipping the most suspicious bits
        word = received.copy()
        failed_per_bit = [
            sum(H_MATRIX[chk, bit] and syndrome[chk] for chk in range(N_CHECKS))
            for bit in range(N_BITS)
        ]
        worst = sorted(range(N_BITS), key=lambda b: failed_per_bit[b], reverse=True)[:t]
        for b in worst:
            word[b] ^= 1
        return word, compute_syndrome(word).sum() == 0
    return received, False


def tier1_check(received: np.ndarray) -> tuple[bool, np.ndarray]:
    """Tier 1 bypass: return (clean, syndrome)."""
    s = compute_syndrome(received)
    return s.sum() == 0, s


def voltage_shift_soft_decode(
    received: np.ndarray,
    delta_v: float,
    model=None,
    max_iter: int = 40
) -> tuple[np.ndarray, bool, int]:
    """
    Tier 3: Apply voltage shift (flip marginal bits) then hard-decode.
    Returns (word, success, iters_used).
    """
    adjusted = received.copy()
    # Simulate marginal bits flipping based on voltage correction
    rng = np.random.default_rng(int(abs(delta_v * 100)))
    flip_prob = min(0.15, abs(delta_v) / 300.0)
    for i in range(N_BITS):
        if rng.random() < flip_prob:
            adjusted[i] ^= 1

    word, success, log = hard_ldpc_decode(adjusted, max_iter=max_iter, threshold=1)
    return word, success, len(log)


def pipeline_read(
    received: np.ndarray,
    pe_count: int = 0,
    voltage_model=None,
    pe_features: Optional[np.ndarray] = None,
) -> dict:
    """
    Full ECC pipeline: Tier1 → BCH → Hard LDPC → Soft LDPC → UECC.
    Returns dict with tier, success, iterations, word.
    """
    # Tier 1: syndrome check
    clean, syndrome = tier1_check(received)
    if clean:
        return {'tier': 1, 'success': True, 'iterations': 0, 'word': received, 'syndrome': syndrome}

    # Tier 2a: BCH attempt (metadata blocks)
    if pe_count < 500:
        word, ok = bch_decode(received)
        if ok:
            return {'tier': '2a-BCH', 'success': True, 'iterations': 1, 'word': word, 'syndrome': syndrome}

    # LDPC cap scales with wear
    wear_pct = pe_count / 3000.0
    ldpc_cap = int(8 + 12 * wear_pct)  # 8 → 20 as wear increases

    # Tier 2b: Hard LDPC
    word, ok, log = hard_ldpc_decode(received, max_iter=ldpc_cap)
    if ok:
        return {'tier': '2b-LDPC', 'success': True, 'iterations': len(log), 'word': word,
                'syndrome': syndrome, 'ldpc_log': log}

    # Tier 3: Soft LDPC + ML voltage shift
    delta_v = 0.0
    if voltage_model is not None and pe_features is not None:
        try:
            delta_v = float(voltage_model.predict([pe_features])[0])
        except Exception:
            delta_v = 0.02 * pe_count + 10.0

    word, ok, iters = voltage_shift_soft_decode(received, delta_v)
    if ok:
        return {'tier': 3, 'success': True, 'iterations': iters, 'word': word,
                'syndrome': syndrome, 'delta_v': delta_v}

    # UECC: unrecoverable
    return {'tier': 'UECC', 'success': False, 'iterations': ldpc_cap, 'word': received,
            'syndrome': syndrome}


def generate_valid_codeword() -> np.ndarray:
    """Generate a random valid codeword (in the null space of H)."""
    rng = np.random.default_rng()
    # Start with random info bits, compute parity via Gaussian elimination simulation
    word = rng.integers(0, 2, N_BITS, dtype=np.uint8)
    # Iteratively correct until syndrome = 0
    for _ in range(100):
        s = compute_syndrome(word)
        if s.sum() == 0:
            return word
        for chk in range(N_CHECKS):
            if s[chk]:
                candidates = [b for b in range(N_BITS) if H_MATRIX[chk, b]]
                if candidates:
                    word[candidates[0]] ^= 1
    return word
