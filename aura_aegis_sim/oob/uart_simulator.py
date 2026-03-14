"""
UART and BLE OOB Communication Simulators.
"""
import time
from datetime import datetime, timezone


def generate_uart_dump(sim) -> list[str]:
    """Generate UART emergency dump lines from simulator state."""
    snap = sim.get_latest_smart()
    ecc_peak = snap.ecc_rate * 2.1 if snap else 12440
    bad = snap.bad_block_count if snap else 4
    wear = snap.wear_level * 100 if snap else 61.6
    temp = snap.temperature if snap else 67

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    crc_str = f"0x{sim.bbt.crc:08X}"

    lines = [
        "[UART:115200] AURA-AEGIS EMERGENCY DIAGNOSTIC DUMP",
        "[UART:115200] =====================================",
        f"[UART:115200] Timestamp: {ts}",
        "[UART:115200] Trigger: HOST_UNRESPONSIVE (timeout: 5000ms)",
        "[UART:115200]",
        "[UART:115200] HEALTH SNAPSHOT:",
        f"[UART:115200]   health_score:    {sim.health_score:.0f} / 100",
        f"[UART:115200]   rul_estimate:    {sim.rul_days:.0f} days",
        f"[UART:115200]   anomaly_type:    {sim.anomaly_type}",
        f"[UART:115200]   failure_prob:    {sim.failure_prob*100:.1f}%",
        "[UART:115200]",
        "[UART:115200] SMART LOG (last 72 hours, 4320 snapshots):",
        f"[UART:115200]   ecc_rate peak:  {ecc_peak:,.0f} corrections/hr",
        f"[UART:115200]   bad_blocks:     {int(bad)} ({len([b for b in sim.blocks if b.fail_reason=='FACTORY_DEFECT'])} factory + {int(bad) - len([b for b in sim.blocks if b.fail_reason=='FACTORY_DEFECT'])} runtime)",
        f"[UART:115200]   wear_level:     {wear:.1f}%",
        f"[UART:115200]   temp_peak:      {temp:.0f}°C",
        "[UART:115200]",
        f"[UART:115200] BBT BACKUP: CRC verified ✓ ({crc_str})",
        "[UART:115200] ENCRYPTED REPORT: b2c4f8a9... (512 bytes)",
        "[UART:115200] KEY SHARES AVAILABLE: 2/5 on-device",
        "[UART:115200]",
        "[UART:115200] DUMP COMPLETE. AWAITING HOST RECOVERY.",
    ]
    return lines


def generate_ble_packet(sim) -> dict:
    """Generate a simulated BLE beacon packet."""
    anomaly_short = {'NONE': 'NRM', 'SLOW_BURN': 'SLW', 'WATCH': 'WCH',
                     'ACCELERATING': 'ACC', 'CRITICAL': 'CRT'}.get(sim.anomaly_type, 'UNK')
    payload = f"[AURA][health:{sim.health_score:.0f}][prob:{sim.failure_prob*100:.0f}][rul:{sim.rul_days:.0f}d][anomaly:{anomaly_short}]"
    return {
        'payload': payload,
        'length_bytes': len(payload.encode()),
        'rssi_dbm': -67,
        'interval_s': 30,
        'device': 'Fleet Management Receiver',
    }
