"""
LSTM Health Predictor Training Script.
Architecture: 2-layer LSTM → Dense
Input: 12 SMART features × 60 timesteps
Output: [health_score, failure_prob, rul_days] — all normalized 0–1
Run this to generate models/lstm_health.pth and models/lstm_health.onnx
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


# ─── Data Generation ──────────────────────────────────────────────────────────

def generate_ssd_lifecycle(max_pe: int = 3000, seed: int = None):
    """
    Simulate one SSD life from fresh → end-of-life.
    Returns list of (features_60step, [health, fail_prob, rul]) per time window.
    """
    rng = np.random.default_rng(seed)
    n_snapshots = max_pe * 60  # ~180k snapshots per lifecycle
    bad_blocks = 2

    all_snaps = []
    for t in range(n_snapshots):
        wear = t / n_snapshots
        pe_avg = int(wear * max_pe)
        rber = 1e-7 * np.exp(pe_avg / 500.0)
        ecc_rate = rber * 1e9 * abs(1 + 0.3 * rng.standard_normal())
        temp = 40 + 20 * rng.random()

        # Poisson bad block emergence
        if rng.random() < 0.001 * max(wear, 0.01):
            bad_blocks += 1

        health = max(0.0, 1.0 - wear ** 0.8)
        failure_prob = min(1.0, wear ** 2 + (bad_blocks / 64) * 0.5)
        rul = max(0.0, (1 - wear))

        snap = np.array([
            min(ecc_rate / 100000, 1.0),
            min(bad_blocks / 64, 1.0),
            wear,
            pe_avg / max_pe,
            min(rber / 1e-3, 1.0),
            temp / 100.0,
            min(ecc_rate * 0.1 / 100000, 1.0),
            0.0,
            min(bad_blocks * 0.005, 1.0),
            0.0,
            0.0,
            min(rng.poisson(max(wear * 3, 0.01)) / 10, 1.0),
        ], dtype=np.float32)

        all_snaps.append((snap, np.array([health, failure_prob, rul], dtype=np.float32)))

    return all_snaps


def generate_dataset(n_lifecycles: int = 50, seq_len: int = 60):
    """Generate dataset: X shape (N, 60, 12), y shape (N, 3)."""
    print(f"Generating {n_lifecycles} synthetic SSD lifecycles (~{seq_len} windows each)...")
    X_list, y_list = [], []

    for i in range(n_lifecycles):
        snaps = generate_ssd_lifecycle(seed=i)
        # Sample ~100 windows per lifecycle
        step = max(1, len(snaps) // 100)
        for start in range(0, len(snaps) - seq_len, step):
            window = snaps[start:start + seq_len]
            features = np.stack([s[0] for s in window])  # (60, 12)
            label = window[-1][1]  # Use last timestep's label
            X_list.append(features)
            y_list.append(label)

    X = np.stack(X_list)
    y = np.stack(y_list)
    print(f"  Dataset shape: X={X.shape}, y={y.shape}")
    return X, y


# ─── Model ───────────────────────────────────────────────────────────────────

class LSTMHealthPredictor(nn.Module):
    def __init__(self, input_size=12, hidden1=64, hidden2=32):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True, dropout=0.2)
        self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden2, 16), nn.ReLU(),
            nn.Linear(16, 3), nn.Sigmoid()
        )

    def forward(self, x):
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        return self.fc(x[:, -1, :])


# ─── Training ────────────────────────────────────────────────────────────────

def train(save_dir: str = None):
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

    os.makedirs(save_dir, exist_ok=True)
    X, y = generate_dataset(n_lifecycles=50, seq_len=60)

    # Train/val split
    n = len(X)
    split = int(0.85 * n)
    idx = np.random.permutation(n)
    X_t, y_t = X[idx[:split]], y[idx[:split]]
    X_v, y_v = X[idx[split:]], y[idx[split:]]

    X_t_tensor = torch.tensor(X_t, dtype=torch.float32)
    y_t_tensor = torch.tensor(y_t, dtype=torch.float32)
    X_v_tensor = torch.tensor(X_v, dtype=torch.float32)
    y_v_tensor = torch.tensor(y_v, dtype=torch.float32)

    ds = TensorDataset(X_t_tensor, y_t_tensor)
    loader = DataLoader(ds, batch_size=64, shuffle=True)

    model = LSTMHealthPredictor()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    print("Training LSTM model (30 epochs)...")
    for epoch in range(30):
        model.train()
        total_loss = 0
        for xb, yb in loader:
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                val_pred = model(X_v_tensor)
                val_loss = criterion(val_pred, y_v_tensor).item()
            print(f"  Epoch {epoch+1:3d} — train_loss={total_loss/len(loader):.4f}  val_loss={val_loss:.4f}")

    # Save PyTorch model
    pth_path = os.path.join(save_dir, 'lstm_health.pth')
    torch.save(model.state_dict(), pth_path)
    print(f"Saved PyTorch model: {pth_path}")

    # Export ONNX
    model.eval()
    dummy = torch.zeros(1, 60, 12)
    try:
        onnx_path = os.path.join(save_dir, 'lstm_health.onnx')
        torch.onnx.export(model, dummy, onnx_path,
                          input_names=['smart_features'],
                          output_names=['predictions'],
                          dynamic_axes={'smart_features': {0: 'batch_size'}},
                          opset_version=14)
        print(f"Exported ONNX model: {onnx_path}")
    except Exception as e:
        print(f"ONNX export skipped: {e}")

    return model


if __name__ == '__main__':
    train()
