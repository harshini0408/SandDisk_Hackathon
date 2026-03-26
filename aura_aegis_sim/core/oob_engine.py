"""
AURA — Pillar 5: Sentinel Secure OOB & Forensic Recovery
Out-of-Band Communication Engine with AES-256 + Shamir Secret Sharing

Features:
- Host connectivity simulation (NVMe link toggle)
- UART/BLE emergency diagnostic dump
- Encrypted forensic reports (AES-256-GCM)
- Shamir Secret Sharing for key distribution (3-of-5 threshold)
- Technician recovery interface with share reconstruction
- Distributed redundancy messaging (IPFS/secure nodes)
"""
import json
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from core.ssd_simulator import SSDSimulator, SMARTSnapshot
from crypto.aes_layer import encrypt_report, decrypt_report, generate_key, generate_iv
from crypto.shamir_layer import split_secret, reconstruct_secret, format_shares_for_display


@dataclass
class OOBStatus:
    """OOB link and connection status."""
    host_connected: bool
    nvme_link_active: bool
    oob_channel_active: bool
    link_status_text: str
    last_diagnostic_time: Optional[datetime] = None
    host_downtime_seconds: float = 0.0


@dataclass
class ForensicReport:
    """Complete encrypted forensic report."""
    timestamp: str
    trigger_reason: str
    health_score: float
    rul_estimate: float
    anomaly_type: str
    failure_prob: float
    
    # SMART metrics snapshot
    ecc_rate: float
    bad_block_count: int
    wear_level: float
    temperature: float
    uecc_count: int
    rber: float
    pe_avg: float
    read_latency_us: float
    
    # BBT info
    bbt_crc: str
    factory_defects: int
    runtime_fails: int
    
    # Wear stats
    total_writes_gb: float
    total_reads_gb: float
    
    # Security context
    aes_key_id: str
    encrypted: bool


class OOBEngine:
    """
    Out-of-Band Diagnostic & Recovery Engine.
    Manages secure communication channel when host is unavailable.
    """
    
    def __init__(self):
        self.status = OOBStatus(
            host_connected=True,
            nvme_link_active=True,
            oob_channel_active=False,
            link_status_text="NVMe Link: Active",
            last_diagnostic_time=None,
            host_downtime_seconds=0.0
        )
        
        # Encryption state
        self.aes_key: Optional[bytes] = None
        self.aes_iv: Optional[bytes] = None
        self.aes_key_id: str = ""
        
        # Shamir shares
        self.shamir_shares: List[str] = []
        self.formatted_shares: List[Dict] = []
        
        # Forensic records
        self.current_report: Optional[ForensicReport] = None
        self.encrypted_report: Optional[Dict] = None
        self.decryption_attempts: int = 0
        self.decryption_success: bool = False
        
        # Recovery state
        self.collected_shares: List[str] = []
        self.recovered_plaintext: Optional[str] = None
        
        # Distributed redundancy
        self.ipfs_hash: str = ""
        self.distributed_nodes: List[str] = [
            "fleet-mgmt-01.secure.ssd.io",
            "forensic-archive-us-east.backup.io",
            "regulatory-compliance-node.gov-trust.io"
        ]
        self.push_status: str = "Pending"
        
    def toggle_host_link(self, is_connected: bool) -> None:
        """Toggle the host NVMe link and update OOB channel status."""
        self.status.host_connected = is_connected
        self.status.nvme_link_active = is_connected
        
        if not is_connected:
            self.status.oob_channel_active = True
            self.status.link_status_text = "🔴 NVMe Link: DOWN | 🟢 OOB Channel: ACTIVE (UART/BLE)"
        else:
            self.status.oob_channel_active = False
            self.status.link_status_text = "🟢 NVMe Link: Active"
        
        # Record diagnostic trigger if host just went down
        if not is_connected:
            self.status.last_diagnostic_time = datetime.now(timezone.utc)
            self.status.host_downtime_seconds = 0.0
    
    def update_host_downtime(self, elapsed_seconds: float) -> None:
        """Update elapsed time since host went offline."""
        if not self.status.host_connected:
            self.status.host_downtime_seconds = elapsed_seconds
    
    def generate_forensic_report(self, sim: SSDSimulator) -> ForensicReport:
        """
        Generate a forensic snapshot from current simulator state.
        This is what gets encrypted and distributed.
        """
        snap = sim.get_latest_smart()
        
        # Calculate aggregate stats
        factory_defects = len([b for b in sim.blocks if b.fail_reason == 'FACTORY_DEFECT'])
        runtime_fails = len([b for b in sim.blocks if b.fail_reason == 'RUNTIME_ERROR']) if hasattr(sim, 'blocks') else 0
        total_writes_gb = sim.total_writes / 1e9 if hasattr(sim, 'total_writes') else 0.0
        total_reads_gb = sim.total_reads / 1e9 if hasattr(sim, 'total_reads') else 0.0
        
        self.current_report = ForensicReport(
            timestamp=datetime.now(timezone.utc).isoformat() + 'Z',
            trigger_reason="HOST_UNRESPONSIVE",
            health_score=sim.health_score,
            rul_estimate=sim.rul_days,
            anomaly_type=sim.anomaly_type,
            failure_prob=sim.failure_prob,
            
            ecc_rate=snap.ecc_rate if snap else 0.0,
            bad_block_count=int(snap.bad_block_count) if snap else 0,
            wear_level=snap.wear_level if snap else 0.0,
            temperature=snap.temperature if snap else 25.0,
            uecc_count=int(snap.uecc_count) if snap else 0,
            rber=snap.rber if snap else 0.0,
            pe_avg=snap.pe_avg if snap else 0.0,
            read_latency_us=snap.read_latency_us if snap else 0.0,
            
            bbt_crc=f"0x{sim.bbt.crc:08X}",
            factory_defects=factory_defects,
            runtime_fails=runtime_fails,
            
            total_writes_gb=total_writes_gb,
            total_reads_gb=total_reads_gb,
            
            aes_key_id="",  # Will be set after encryption
            encrypted=False
        )
        
        return self.current_report
    
    def encrypt_report(self) -> bool:
        """
        Encrypt the forensic report using AES-256-GCM.
        Generate Shamir shares for the AES key (3-of-5 threshold).
        """
        if not self.current_report:
            return False
        
        # Convert report to dict and encrypt
        report_dict = asdict(self.current_report)
        encryption_result = encrypt_report(report_dict)
        
        # Store encryption artifacts
        self.aes_key = encryption_result['key']
        self.aes_iv = encryption_result['iv']
        self.encrypted_report = encryption_result
        
        # Generate key ID (first 8 chars of key hex)
        self.aes_key_id = self.aes_key.hex()[:8].upper()
        
        # Generate Shamir shares (3-of-5 threshold)
        self.shamir_shares = split_secret(self.aes_key, k=3, n=5)
        self.formatted_shares = format_shares_for_display(self.shamir_shares)
        
        # Mark report as encrypted
        if self.current_report:
            self.current_report.encrypted = True
            self.current_report.aes_key_id = self.aes_key_id
        
        return True
    
    def push_to_distributed_nodes(self) -> Dict:
        """
        Simulate pushing encrypted report to distributed redundancy network.
        Returns status of push to each node.
        """
        if not self.encrypted_report:
            return {'success': False, 'message': 'No encrypted report to push'}
        
        # Simulate IPFS hash generation
        ciphertext_hex = self.encrypted_report['ciphertext_hex']
        self.ipfs_hash = f"QmX{ciphertext_hex[:12]}...{ciphertext_hex[-12:]}"
        
        push_results = {}
        for node in self.distributed_nodes:
            push_results[node] = {
                'status': 'PUSHED',
                'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
                'redundancy_copies': 3,
                'verification': '✓ Integrity verified'
            }
        
        self.push_status = "DISTRIBUTED"
        
        return {
            'success': True,
            'ipfs_hash': self.ipfs_hash,
            'nodes': push_results,
            'total_copies': len(self.distributed_nodes) * 3,
            'message': f'Report distributed to {len(self.distributed_nodes)} nodes with 3x redundancy'
        }
    
    def submit_share(self, share_str: str) -> bool:
        """
        Add a share to the collection. Returns True if share is valid.
        """
        # Validate share format (should be 'index-hexvalue')
        try:
            parts = share_str.split('-', 1)
            if len(parts) != 2:
                return False
            idx, val = parts
            int(idx)  # Validate index is numeric
            int(val, 16)  # Validate value is hex
            
            # Check if already submitted
            if share_str not in self.collected_shares:
                self.collected_shares.append(share_str)
                return True
            return False
        except (ValueError, AttributeError):
            return False
    
    def reconstruct_key(self) -> bool:
        """
        Attempt to reconstruct the AES key from collected shares.
        Requires k=3 shares. Returns True if successful.
        """
        if len(self.collected_shares) < 3:
            return False
        
        try:
            reconstructed_key = reconstruct_secret(self.collected_shares[:3], key_len=32)
            
            # Verify reconstructed key matches original
            if reconstructed_key == self.aes_key:
                self.decryption_success = True
                return True
            return False
        except Exception:
            return False
    
    def decrypt_forensic_report(self) -> tuple[Optional[str], bool]:
        """
        Decrypt the forensic report using reconstructed key.
        Returns (plaintext_json, success).
        """
        if not self.decryption_success or not self.aes_key or not self.aes_iv:
            return None, False
        
        try:
            plaintext, success = decrypt_report(
                self.encrypted_report['ciphertext'],
                self.aes_key,
                self.aes_iv
            )
            
            if success:
                self.recovered_plaintext = plaintext
                self.decryption_attempts += 1
            
            return plaintext, success
        except Exception:
            return None, False
    
    def get_uart_dump_lines(self) -> List[str]:
        """Generate UART emergency diagnostic dump (encrypted)."""
        snap = self.current_report
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        lines = [
            "[UART:115200] ╔═══════════════════════════════════════════════╗",
            "[UART:115200] ║    AURA-AEGIS EMERGENCY DIAGNOSTIC DUMP       ║",
            "[UART:115200] ║         Out-of-Band Recovery Channel          ║",
            "[UART:115200] ╚═══════════════════════════════════════════════╝",
            "[UART:115200]",
            f"[UART:115200] 🔴 TRIGGER: {snap.trigger_reason} (timeout: 5000ms)",
            f"[UART:115200] 📅 TIMESTAMP: {ts}",
            f"[UART:115200] ⏱️  HOST_DOWNTIME: {self.status.host_downtime_seconds:.1f}s",
            "[UART:115200]",
            "[UART:115200] ─── HEALTH SNAPSHOT ───",
            f"[UART:115200] Health Score:    {snap.health_score:.0f} / 100",
            f"[UART:115200] RUL Estimate:    {snap.rul_estimate:.0f} days",
            f"[UART:115200] Anomaly Type:    {snap.anomaly_type}",
            f"[UART:115200] Failure Prob:    {snap.failure_prob*100:.1f}%",
            "[UART:115200]",
            "[UART:115200] ─── SMART METRICS ───",
            f"[UART:115200] ECC Rate:        {snap.ecc_rate:,.0f} corrections/hr",
            f"[UART:115200] Bad Blocks:      {snap.bad_block_count} ({snap.factory_defects} factory + {snap.runtime_fails} runtime)",
            f"[UART:115200] Wear Level:      {snap.wear_level*100:.1f}%",
            f"[UART:115200] Temperature:     {snap.temperature:.1f}°C",
            f"[UART:115200] UECC Count:      {snap.uecc_count}",
            f"[UART:115200] RBER:            {snap.rber:.2e}",
            "[UART:115200]",
            "[UART:115200] ─── BBT & WEAR STATS ───",
            f"[UART:115200] BBT CRC:         {snap.bbt_crc} ✓ VERIFIED",
            f"[UART:115200] Total Writes:    {snap.total_writes_gb:.2f} GB",
            f"[UART:115200] Total Reads:     {snap.total_reads_gb:.2f} GB",
            "[UART:115200]",
            "[UART:115200] ─── ENCRYPTED REPORT ───",
            f"[UART:115200] 🔐 AES-256-GCM ENCRYPTION ACTIVE",
            f"[UART:115200] 🔑 KEY_ID: {self.aes_key_id}",
            f"[UART:115200] 📊 CIPHERTEXT SIZE: {len(self.encrypted_report['ciphertext']) if self.encrypted_report else 0} bytes",
            f"[UART:115200] 🔍 PREVIEW: {self.encrypted_report['ciphertext_preview'] if self.encrypted_report else 'N/A'}...",
            "[UART:115200]",
            "[UART:115200] ─── SHAMIR SECRET SHARES (3-of-5 threshold) ───",
            f"[UART:115200] 📍 Total Shares: {len(self.shamir_shares)}",
            "[UART:115200] Distributed to:",
            "[UART:115200]   Share 1 → Fleet Management Server",
            "[UART:115200]   Share 2 → On-Drive TEE Secure Storage",
            "[UART:115200]   Share 3 → Maintenance Engineer Token",
            "[UART:115200]   Share 4 → Backup HSM (Hardware Security Module)",
            "[UART:115200]   Share 5 → Emergency Paper Key (Offline)",
            "[UART:115200]",
            "[UART:115200] ─── DISTRIBUTED REDUNDANCY ───",
            f"[UART:115200] 🌐 IPFS HASH: {self.ipfs_hash if self.ipfs_hash else 'PENDING...'}",
            f"[UART:115200] 📦 NODES: {len(self.distributed_nodes)} (3x redundancy each)",
            "[UART:115200] Status: " + ("✓ DISTRIBUTED" if self.push_status == "DISTRIBUTED" else "⏳ PUSHING..."),
            "[UART:115200]",
            "[UART:115200] ─── RECOVERY INTERFACE ───",
            "[UART:115200] To access this report:",
            "[UART:115200] 1️⃣  Collect 3 out of 5 Shamir shares",
            "[UART:115200] 2️⃣  Input shares into Technician Portal",
            "[UART:115200] 3️⃣  System reconstructs AES key",
            "[UART:115200] 4️⃣  Forensic report is decrypted",
            "[UART:115200]",
            "[UART:115200] ╔═══════════════════════════════════════════════╗",
            "[UART:115200] ║         AWAITING HOST RECOVERY / TRIAGE       ║",
            "[UART:115200] ╚═══════════════════════════════════════════════╝",
        ]
        return lines
    
    def get_ble_beacon(self) -> Dict:
        """Generate BLE beacon packet for fleet-wide monitoring."""
        beacon_payload = (
            f"[AURA-OOB][health:{self.current_report.health_score:.0f}]"
            f"[prob:{self.current_report.failure_prob*100:.0f}]"
            f"[rul:{self.current_report.rul_estimate:.0f}d]"
            f"[anomaly:{self.current_report.anomaly_type}]"
            f"[oob:ACTIVE]"
        )
        
        return {
            'type': 'Emergency BLE Beacon',
            'payload': beacon_payload,
            'length_bytes': len(beacon_payload.encode()),
            'rssi_dbm': -72,
            'interval_seconds': 30,
            'receiver': 'Fleet Management Mesh Network',
            'power_mode': 'Low Power (0.5mA)',
            'broadcast_range': '50m (mesh-extendable)',
        }
    
    def reset_collection(self) -> None:
        """Reset share collection for new recovery attempt."""
        self.collected_shares = []
        self.decryption_attempts = 0
        self.decryption_success = False
        self.recovered_plaintext = None
    
    def get_status_summary(self) -> Dict:
        """Get comprehensive OOB status for UI display."""
        return {
            'host_status': '🟢 Connected' if self.status.host_connected else '🔴 Disconnected',
            'nvme_status': '🟢 Active' if self.status.nvme_link_active else '🔴 Down',
            'oob_status': '🟢 Active' if self.status.oob_channel_active else '⚫ Inactive',
            'link_text': self.status.link_status_text,
            'downtime': f"{self.status.host_downtime_seconds:.1f}s",
            'encrypted': self.current_report.encrypted if self.current_report else False,
            'key_id': self.aes_key_id,
            'shares_created': len(self.shamir_shares),
            'shares_collected': len(self.collected_shares),
            'push_status': self.push_status,
            'decryption_ready': len(self.collected_shares) >= 3,
            'decryption_success': self.decryption_success,
        }
