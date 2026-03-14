#!/usr/bin/env python3
"""
Comprehensive validation script for AURA-AEGIS
Checks all imports, data structures, and key functions
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("AURA-AEGIS Validation Script")
print("=" * 70)

def test_section(name, test_func):
    """Run a test section and report results."""
    print(f"\n[*] {name}...", end=" ")
    try:
        test_func()
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

# Track results
results = []

# Test 1: Core imports
def test_core_imports():
    from core.ssd_simulator import SSDSimulator, BlockInfo, SMARTSnapshot
    from core.bbt_engine import BBTEngine, BloomFilter, Bitmap, CuckooHashTable
    from core.ldpc_engine import compute_syndrome, hard_ldpc_decode, pipeline_read
    from core.smart_engine import METRIC_DEFS, get_metric_status, get_workload_context
    from core.lstm_predictor import predict, build_feature_sequence
    from core.kmap_qmc_engine import qmc_minimize, kmap_grid, bdd_verify_equivalent

results.append(test_section("Core module imports", test_core_imports))

# Test 2: Crypto imports
def test_crypto_imports():
    from crypto.aes_layer import encrypt_report, decrypt_report, generate_key, generate_iv
    from crypto.shamir_layer import split_secret, reconstruct_secret

results.append(test_section("Crypto module imports", test_crypto_imports))

# Test 3: OOB imports
def test_oob_imports():
    from oob.uart_simulator import generate_uart_dump, generate_ble_packet

results.append(test_section("OOB module imports", test_oob_imports))

# Test 4: Section imports
def test_section_imports():
    from sections.section1_nand import render_section1
    from sections.section2_ecc import render_section2
    from sections.section3_smart import render_section3
    from sections.section4_security import render_section4

results.append(test_section("Section UI imports", test_section_imports))

# Test 5: SSD Simulator
def test_ssd_simulator():
    from core.ssd_simulator import SSDSimulator
    sim = SSDSimulator('fresh')
    assert len(sim.blocks) == 64
    assert sim.health_score == 100.0
    assert sim.mode == 'normal'
    for _ in range(5):
        sim.tick(60)
    assert len(sim.smart_history) >= 5
    assert sim.health_score < 100.0
    snap = sim.get_latest_smart()
    assert snap is not None
    assert snap.ecc_rate >= 0

results.append(test_section("SSD Simulator (fresh preset)", test_ssd_simulator))

# Test 6: BBT Engine
def test_bbt_engine():
    from core.bbt_engine import BBTEngine
    bbt = BBTEngine()
    meta = bbt.mark_bad(5, 'FACTORY_DEFECT', 100)
    assert meta.block_idx == 5
    is_bad, tier = bbt.check_block(5)
    assert is_bad
    meta = bbt.get_metadata(5)
    assert meta is not None
    trace = bbt.write_trace(5, 100)
    assert len(trace) > 0

results.append(test_section("BBT Engine", test_bbt_engine))

# Test 7: LDPC Engine
def test_ldpc_engine():
    from core.ldpc_engine import generate_valid_codeword, inject_errors, compute_syndrome, hard_ldpc_decode
    cw = generate_valid_codeword()
    assert len(cw) == 16
    received, err_pos = inject_errors(cw, 2)
    assert len(received) == 16
    word, success, log = hard_ldpc_decode(received, max_iter=8)
    assert len(word) == 16
    assert isinstance(success, bool)

results.append(test_section("LDPC Engine", test_ldpc_engine))

# Test 8: SMART Engine
def test_smart_engine():
    from core.smart_engine import METRIC_DEFS, get_metric_status
    assert len(METRIC_DEFS) == 12
    status = get_metric_status(5, 10, 20)
    assert status in ('OK', 'WARNING', 'CRITICAL')

results.append(test_section("SMART Engine", test_smart_engine))

# Test 9: LSTM Predictor
def test_lstm_predictor():
    from core.lstm_predictor import build_feature_sequence, predict
    import numpy as np
    from core.ssd_simulator import SSDSimulator, SMARTSnapshot
    
    sim = SSDSimulator('fresh')
    for _ in range(70):
        sim.tick(60)
    
    feat = build_feature_sequence(sim.smart_history)
    assert feat.shape == (60, 12)
    result = predict(feat)
    assert 'health_score' in result
    assert 'failure_prob' in result
    assert 'rul_days' in result
    assert 0 <= result['health_score'] <= 100

results.append(test_section("LSTM Predictor", test_lstm_predictor))

# Test 10: Crypto Layer
def test_crypto_layer():
    from crypto.aes_layer import encrypt_report, decrypt_report
    report = {"test": "data", "value": 42}
    encrypted = encrypt_report(report)
    assert 'ciphertext' in encrypted
    assert 'key' in encrypted
    assert 'iv' in encrypted
    plaintext, ok = decrypt_report(encrypted['ciphertext'], encrypted['key'], encrypted['iv'])
    assert ok

results.append(test_section("Crypto Layer (AES-256-GCM)", test_crypto_layer))

# Test 11: Shamir Sharing
def test_shamir_sharing():
    from crypto.shamir_layer import split_secret, reconstruct_secret
    secret = b'test_secret_32_bytes___________'
    shares = split_secret(secret, k=3, n=5)
    assert len(shares) == 5
    recovered = reconstruct_secret(shares[:3], key_len=32)
    assert recovered == secret

results.append(test_section("Shamir Secret Sharing", test_shamir_sharing))

# Test 12: OOB Simulators
def test_oob_simulators():
    from oob.uart_simulator import generate_uart_dump, generate_ble_packet
    from core.ssd_simulator import SSDSimulator
    
    sim = SSDSimulator('fresh')
    sim.tick(60)
    uart_lines = generate_uart_dump(sim)
    assert isinstance(uart_lines, list)
    assert len(uart_lines) > 0
    assert any('AURA-AEGIS' in line for line in uart_lines)
    
    ble_pkt = generate_ble_packet(sim)
    assert 'payload' in ble_pkt
    assert 'length_bytes' in ble_pkt

results.append(test_section("OOB Simulators (UART/BLE)", test_oob_simulators))

# Test 13: K-Map / QMC Engine
def test_kmap_qmc_engine():
    from core.kmap_qmc_engine import kmap_grid, bdd_verify_equivalent, qmc_ldpc_demo
    from core.kmap_qmc_engine import RETIREMENT_MINTERMS, LDPC_ESCALATION_MINTERMS
    
    grid = kmap_grid(RETIREMENT_MINTERMS)
    assert len(grid) == 4
    assert len(grid[0]) == 4
    
    ok = bdd_verify_equivalent()
    assert ok == True
    
    result = qmc_ldpc_demo()
    assert 'prime_implicants' in result
    assert 'expression' in result

results.append(test_section("K-Map / QMC / BDD Engine", test_kmap_qmc_engine))

# Test 14: Models exist
def test_models_exist():
    import os
    if os.path.exists('models/voltage_model.pkl'):
        import joblib
        model = joblib.load('models/voltage_model.pkl')
        assert model is not None
    # LSTM model is optional (falls back to heuristic)

results.append(test_section("ML Models", test_models_exist))

# Test 15: Presets
def test_presets():
    from core.ssd_simulator import SSDSimulator
    
    for preset in ['fresh', 'middle_aged', 'end_of_life', 'critical']:
        sim = SSDSimulator(preset)
        assert sim.health_score >= 0
        bad_count = sum(1 for b in sim.blocks if b.state in ('BAD', 'RETIRED'))
        if preset == 'fresh':
            assert bad_count == 3  # factory defects
        elif preset == 'critical':
            assert sim.health_score < 20
            assert sim.anomaly_type == 'CRITICAL'

results.append(test_section("SSD Presets", test_presets))

# Summary
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
passed = sum(1 for r in results if r)
total = len(results)
print(f"\nPassed: {passed}/{total}")

if passed == total:
    print("\n✓ ALL TESTS PASSED! AURA-AEGIS is ready to run.")
    print("\nNext steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Open http://localhost:8501 in your browser")
    print("  3. Enjoy the demo!")
    sys.exit(0)
else:
    print(f"\n✗ {total - passed} test(s) failed. Please check errors above.")
    sys.exit(1)
