#!/usr/bin/env python3
"""
Quick setup script to create minimal models for AURA-AEGIS demo
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Create models directory
os.makedirs('models', exist_ok=True)

print("=" * 70)
print("AURA-AEGIS Model Setup")
print("=" * 70)

# 1. Voltage model (simple sklearn gradient boosting)
print("\n[1/2] Creating voltage shift model...")
try:
    import numpy as np
    import joblib
    from sklearn.ensemble import GradientBoostingRegressor
    
    # Generate minimal training data
    n = 1000
    rng = np.random.default_rng(42)
    X = np.column_stack([
        rng.uniform(0, 3000, n),      # pe_count
        rng.uniform(20, 85, n),        # temperature
        rng.exponential(3000, n),      # ecc_history
        np.linspace(0, 1, n),          # wear_level
    ])
    y = 0.02 * X[:, 0] + 0.3 * X[:, 1] + 0.001 * X[:, 2] + rng.normal(0, 5, n)
    
    model = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    joblib.dump(model, 'models/voltage_model.pkl')
    print("  ✓ Voltage model created: models/voltage_model.pkl")
except Exception as e:
    print(f"  ✗ Failed to create voltage model: {e}")
    import traceback
    traceback.print_exc()

# 2. LSTM model (PyTorch)
print("\n[2/2] Creating LSTM health predictor model...")
try:
    import torch
    import torch.nn as nn
    
    class LSTMHealthPredictor(nn.Module):
        def __init__(self, input_size=12, hidden1=64, hidden2=32):
            super().__init__()
            self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True, dropout=0.2)
            self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
            self.fc = nn.Sequential(
                nn.Linear(hidden2, 16),
                nn.ReLU(),
                nn.Linear(16, 3),
                nn.Sigmoid()
            )
        
        def forward(self, x):
            x, _ = self.lstm1(x)
            x, _ = self.lstm2(x)
            return self.fc(x[:, -1, :])
    
    model = LSTMHealthPredictor()
    torch.save(model.state_dict(), 'models/lstm_health.pth')
    print("  ✓ LSTM model created: models/lstm_health.pth")
except Exception as e:
    print(f"  ✗ Failed to create LSTM model: {e}")
    import traceback
    traceback.print_exc()

# Verify
print("\n" + "=" * 70)
print("Verification")
print("=" * 70)
if os.path.exists('models'):
    files = sorted(os.listdir('models'))
    if files:
        print("Models created:")
        for f in files:
            path = os.path.join('models', f)
            size = os.path.getsize(path) / 1024
            print(f"  ✓ {f} ({size:.1f} KB)")
    else:
        print("  ✗ models directory is empty")
else:
    print("  ✗ models directory does not exist")

print("\n" + "=" * 70)
print("Setup complete! You can now run: streamlit run app.py")
print("=" * 70)
