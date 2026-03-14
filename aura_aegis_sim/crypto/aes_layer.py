"""
AES-256-GCM encryption/decryption for SSD diagnostic reports.
"""
import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    """Generate a random 256-bit AES key."""
    return os.urandom(32)


def generate_iv() -> bytes:
    """Generate a random 96-bit IV/nonce."""
    return os.urandom(12)


def encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt with AES-256-GCM. Returns ciphertext + 16-byte auth tag."""
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(iv, plaintext, None)


def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt and verify AES-256-GCM. Returns plaintext. Raises on tamper."""
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext, None)


def encrypt_report(report_dict: dict) -> dict:
    """
    Full pipeline: dict → JSON → AES-256-GCM cipher.
    Returns dict with key_hex, iv_hex, ciphertext_hex for display.
    """
    plaintext = json.dumps(report_dict, indent=2).encode('utf-8')
    key = generate_key()
    iv = generate_iv()
    ciphertext = encrypt(plaintext, key, iv)
    return {
        'plaintext': plaintext.decode('utf-8'),
        'key': key,
        'iv': iv,
        'ciphertext': ciphertext,
        'key_hex': key.hex(),
        'iv_hex': iv.hex(),
        'ciphertext_hex': ciphertext.hex(),
        'ciphertext_preview': ciphertext[:64].hex(),
    }


def decrypt_report(ciphertext: bytes, key: bytes, iv: bytes) -> tuple[str, bool]:
    """Attempt decryption. Returns (plaintext_str, success)."""
    try:
        plaintext = decrypt(ciphertext, key, iv)
        return plaintext.decode('utf-8'), True
    except Exception as e:
        return f"Decryption failed: {e}", False
