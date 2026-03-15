"""
LSTM Health Predictor — PyTorch model + inference wrapper.
Loads pre-trained model from models/lstm_health.pth.
Falls back to heuristic if model not trained yet.
"""
import numpy as np
import os
from typing import Optional

import streamlit as st  # type: ignore

TORCH_AVAILABLE = None

def _check_torch():
    global TORCH_AVAILABLE
    if TORCH_AVAILABLE is not None:
        return TORCH_AVAILABLE
    try:
        import torch  # type: ignore
        TORCH_AVAILABLE = True
    except ImportError:
        TORCH_AVAILABLE = False
    return TORCH_AVAILABLE

def _get_model_class():
    import torch  # type: ignore
    class LSTMHealthPredictorModel(torch.nn.Module):
        def __init__(self, input_size=12, hidden1=64, hidden2=32):
            super().__init__()
            self.lstm1 = torch.nn.LSTM(input_size, hidden1, batch_first=True, dropout=0.2)
            self.lstm2 = torch.nn.LSTM(hidden1, hidden2, batch_first=True)
            self.fc = torch.nn.Sequential(
                torch.nn.Linear(hidden2, 16),
                torch.nn.ReLU(),
                torch.nn.Linear(16, 3),
                torch.nn.Sigmoid()
            )

        def forward(self, x):
            x, _ = self.lstm1(x)
            x, _ = self.lstm2(x)
            return self.fc(x[:, -1, :])
    return LSTMHealthPredictorModel

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'lstm_health.pth')

@st.cache_resource
def _load_model():
    if not _check_torch():
        return None
    import torch  # type: ignore
    abs_path = os.path.abspath(MODEL_PATH)
    if not os.path.exists(abs_path):
        return None
    try:
        m_class = _get_model_class()
        m = m_class()
        m.load_state_dict(torch.load(abs_path, map_location='cpu'))
        m.eval()
        return m
    except Exception:
        return None


def _heuristic_predict(features_60: np.ndarray) -> tuple[float, float, float]:
    """Physics-based fallback when LSTM model is not loaded."""
    last = features_60[-1] if len(features_60) > 0 else features_60
    ecc_rate_norm = float(last[0])
    bad_block_norm = float(last[1])
    pe_norm = float(last[2])
    wear_norm = float(last[3])
    rber_norm = float(last[4])
    temp_norm = float(last[5])

    health = max(0.0, min(1.0,
        0.40 * (1 - wear_norm) +
        0.25 * (1 - bad_block_norm * 5) +
        0.20 * max(0, 1 - rber_norm * 10) +
        0.15 * (1 - ecc_rate_norm)
    ))
    failure_prob = min(1.0, wear_norm ** 2 + bad_block_norm * 2 + rber_norm * 5)
    rul = max(0.0, (1 - wear_norm) * (1 - bad_block_norm * 3))
    return health, failure_prob, rul


def predict(features_60: np.ndarray) -> dict:
    """
    features_60: np.ndarray of shape (60, 12)
    Returns: {health_score, failure_prob, rul_days, attention, source}
    """
    model = _load_model()

    if model is not None:
        try:
            import torch  # type: ignore
            x = torch.tensor(features_60[np.newaxis, :, :], dtype=torch.float32)
            with torch.no_grad():
                out = model(x).numpy()[0]
            health = float(out[0]) * 100
            failure_prob = float(out[1])
            rul = float(out[2]) * 365
            source = 'lstm'
        except Exception:
            model = None

    if model is None:
        h, fp, r = _heuristic_predict(features_60)
        health = h * 100
        failure_prob = fp
        rul = r * 365
        source = 'heuristic'

    # Generate synthetic attention heatmap (timesteps × features)
    # Brighter = higher attention weight
    attention = _compute_synthetic_attention(features_60)

    return {
        'health_score': max(0.0, min(100.0, health)),
        'failure_prob': max(0.0, min(1.0, failure_prob)),
        'rul_days': max(0.0, rul),
        'attention': attention,
        'source': source,
    }


def _compute_synthetic_attention(features: np.ndarray) -> np.ndarray:
    """
    Generate a (60, 12) attention weight matrix.
    Recent timesteps and high-variance features get higher weights.
    """
    n_steps, n_feats = features.shape
    # Temporal attention: recency bias, exponential
    time_weights = np.exp(np.linspace(-3, 0, n_steps))
    # Feature attention: variance-based
    feat_var = np.var(features, axis=0)
    feat_weights = feat_var / (feat_var.max() + 1e-9)
    # Outer product
    attention = np.outer(time_weights, feat_weights)
    attention /= attention.max() + 1e-9
    return attention


def build_feature_sequence(smart_history, n_steps: int = 60) -> np.ndarray:
    """
    Build (n_steps, 12) feature matrix from SMART history.
    Normalize to [0, 1].
    """
    fields = ['ecc_rate', 'uecc_count', 'bad_block_count', 'pe_avg',
              'wear_level', 'rber', 'temperature', 'read_latency_us',
              'retry_freq', 'reallocated', 'program_fail', 'erase_fail']

    norms = {
        'ecc_rate': 100000, 'uecc_count': 100, 'bad_block_count': 64,
        'pe_avg': 3000, 'wear_level': 1, 'rber': 1e-3,
        'temperature': 100, 'read_latency_us': 300, 'retry_freq': 500,
        'reallocated': 64, 'program_fail': 50, 'erase_fail': 50,
    }

    history = smart_history[-n_steps:]
    rows = []
    for snap in history:
        row = [min(1.0, getattr(snap, f, 0) / norms[f]) for f in fields]
        rows.append(row)

    # Pad with zeros if not enough history
    while len(rows) < n_steps:
        rows.insert(0, [0.0] * 12)

    return np.array(rows[-n_steps:], dtype=np.float32)


def anomaly_classify(failure_prob: float, health_score: float) -> str:
    if failure_prob > 0.70 or health_score < 20:
        return 'CRITICAL'
    if failure_prob > 0.40 or health_score < 40:
        return 'ACCELERATING'
    if failure_prob > 0.20 or health_score < 65:
        return 'WATCH'
    if health_score < 85:
        return 'SLOW_BURN'
    return 'NONE'
