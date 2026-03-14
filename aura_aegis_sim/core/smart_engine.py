"""
SMART Engine — 12 metric collector, sparkline history, workload-aware anomaly detection.
"""
import numpy as np
from typing import Optional
from core.ssd_simulator import SSDSimulator, SMARTSnapshot


METRIC_DEFS = [
    {'id': 1,  'name': 'ECC Correction Rate',      'field': 'ecc_rate',        'unit': '/hr',    'source': 'PILLAR 2',
     'warn': 10000,  'crit': 50000,   'fmt': lambda v: f"{v:,.0f}"},
    {'id': 2,  'name': 'UECC Count',               'field': 'uecc_count',      'unit': '',       'source': 'PILLAR 2',
     'warn': 1,      'crit': 10,      'fmt': lambda v: f"{int(v)}"},
    {'id': 3,  'name': 'Bad Block Count',           'field': 'bad_block_count', 'unit': ' blks',  'source': 'PILLAR 1',
     'warn': 6,      'crit': 12,      'fmt': lambda v: f"{int(v)}"},
    {'id': 4,  'name': 'P/E Cycle Count (avg)',     'field': 'pe_avg',          'unit': f'/{3000}','source': 'PILLAR 1',
     'warn': 2100,   'crit': 2700,    'fmt': lambda v: f"{v:,.0f}"},
    {'id': 5,  'name': 'Wear Level Indicator',      'field': 'wear_level',      'unit': '%',      'source': 'PILLAR 1',
     'warn': 0.70,   'crit': 0.90,    'fmt': lambda v: f"{v*100:.1f}"},
    {'id': 6,  'name': 'RBER',                      'field': 'rber',            'unit': '',       'source': 'PILLAR 2',
     'warn': 1e-4,   'crit': 1e-3,    'fmt': lambda v: f"{v:.2e}"},
    {'id': 7,  'name': 'Temperature',               'field': 'temperature',     'unit': '°C',     'source': 'SENSOR',
     'warn': 65,     'crit': 75,      'fmt': lambda v: f"{v:.1f}"},
    {'id': 8,  'name': 'Read Latency',              'field': 'read_latency_us', 'unit': 'µs',     'source': 'FTL',
     'warn': 100,    'crit': 150,     'fmt': lambda v: f"{v:.1f}"},
    {'id': 9,  'name': 'Controller Retry Freq',     'field': 'retry_freq',      'unit': '/hr',    'source': 'PILLAR 2',
     'warn': 50,     'crit': 200,     'fmt': lambda v: f"{v:.1f}"},
    {'id': 10, 'name': 'Reallocated Sectors',       'field': 'reallocated',     'unit': '',       'source': 'PILLAR 1',
     'warn': 5,      'crit': 15,      'fmt': lambda v: f"{int(v)}"},
    {'id': 11, 'name': 'Program Fail Count',        'field': 'program_fail',    'unit': '',       'source': 'PILLAR 1',
     'warn': 1,      'crit': 5,       'fmt': lambda v: f"{int(v)}"},
    {'id': 12, 'name': 'Erase Fail Count',          'field': 'erase_fail',      'unit': '',       'source': 'PILLAR 1',
     'warn': 1,      'crit': 5,       'fmt': lambda v: f"{int(v)}"},
]


def get_metric_status(value: float, warn, crit) -> str:
    if value >= crit:
        return 'CRITICAL'
    if value >= warn:
        return 'WARNING'
    return 'OK'


def get_sparks(history: list[SMARTSnapshot], field: str, n: int = 24) -> list[float]:
    vals = [getattr(s, field) for s in history[-n:]]
    return vals


def normalize_for_chart(values: list[float]) -> list[float]:
    arr = np.array(values, dtype=float)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-10:
        return [0.5] * len(values)
    return ((arr - mn) / (mx - mn)).tolist()


def get_workload_context(metric_id: int, workload: str, value: float, history: list[SMARTSnapshot]) -> dict:
    """
    Return context-aware anomaly flag for a metric given the workload.
    """
    if metric_id != 1:
        return {'context': 'N/A', 'is_anomaly': False}

    # Compute baseline ECC rate for this workload
    baselines = {
        'Sequential large writes': 8000,
        'Random small writes': 12000,
        'Mostly reads': 1000,
        'Idle': 200,
    }
    baseline = baselines.get(workload, 3000)
    sigma = baseline * 0.3
    z = (value - baseline) / max(sigma, 1)
    is_anomaly = z > 3
    return {
        'context': f"{'ANOMALY' if is_anomaly else 'NORMAL'} — {z:.1f}σ {'above' if z > 0 else 'below'} {workload} baseline",
        'is_anomaly': is_anomaly,
        'z_score': z,
        'baseline': baseline,
    }
