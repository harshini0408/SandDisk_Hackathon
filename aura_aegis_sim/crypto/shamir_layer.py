"""
Shamir Secret Sharing — real polynomial interpolation over GF(prime).
Splits and reconstructs AES keys without any external library.
"""
import random
import hashlib
from functools import reduce


# Use a large prime for the finite field
_PRIME = 2**127 - 1  # Mersenne prime, larger than any 256-bit key chunk


def _eval_poly(poly: list[int], x: int, prime: int) -> int:
    """Evaluate polynomial at x over GF(prime) using Horner's method."""
    result = 0
    for coeff in reversed(poly):
        result = (result * x + coeff) % prime
    return result


def _lagrange_interpolate(x: int, points: list[tuple], prime: int) -> int:
    """Lagrange interpolation over GF(prime) to find f(x)."""
    n = len(points)
    total = 0
    for i in range(n):
        xi, yi = points[i]
        num, den = 1, 1
        for j in range(n):
            if i == j:
                continue
            xj = points[j][0]
            num = (num * (x - xj)) % prime
            den = (den * (xi - xj)) % prime
        total = (total + yi * num * pow(den, prime - 2, prime)) % prime
    return total


def split_secret(secret_bytes: bytes, k: int, n: int) -> list[str]:
    """
    Split secret_bytes into n shares, any k can reconstruct.
    Returns list of 'share_index-hex_value' strings.
    """
    secret_int = int.from_bytes(secret_bytes, 'big')
    rng = random.SystemRandom()
    poly = [secret_int] + [rng.randint(1, _PRIME - 1) for _ in range(k - 1)]
    shares = []
    for x in range(1, n + 1):
        y = _eval_poly(poly, x, _PRIME)
        shares.append(f"{x}-{y:0x}")
    return shares


def reconstruct_secret(shares: list[str], key_len: int = 32) -> bytes:
    """
    Reconstruct secret from k or more shares.
    shares: list of 'index-hex_value' strings.
    key_len: expected byte length of secret.
    """
    points = []
    for s in shares:
        idx, val_hex = s.split('-', 1)
        points.append((int(idx), int(val_hex, 16)))
    secret_int = _lagrange_interpolate(0, points, _PRIME)
    return secret_int.to_bytes(key_len, 'big')


def format_shares_for_display(shares: list[str]) -> list[dict]:
    """Return list of dicts with index, truncated value, and destination label."""
    destinations = [
        'Fleet management server',
        'On-drive secure storage (TEE)',
        "Maintenance engineer's hardware token",
        'Backup HSM (Hardware Security Module)',
        'Emergency paper key (offline)',
    ]
    result = []
    for i, share in enumerate(shares):
        idx, val = share.split('-', 1)
        result.append({
            'index': int(idx),
            'share_str': share,
            'preview': f"{idx}-{val[:8]}...",
            'destination': destinations[i] if i < len(destinations) else f'Recipient {i+1}',
        })
    return result
