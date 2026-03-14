#!/usr/bin/env python3
"""Quick model training script for AURA-AEGIS"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

# Train voltage model
print("=" * 60)
print("Training Voltage Shift Model...")
print("=" * 60)
try:
    from training.train_voltage_model import train_voltage_model
    train_voltage_model()
    print("✓ Voltage model trained successfully\n")
except Exception as e:
    print(f"✗ Voltage model training failed: {e}\n")
    import traceback
    traceback.print_exc()

# Train LSTM model
print("=" * 60)
print("Training LSTM Health Predictor...")
print("=" * 60)
try:
    from training.train_lstm import train
    train()
    print("✓ LSTM model trained successfully\n")
except Exception as e:
    print(f"✗ LSTM model training failed: {e}\n")
    import traceback
    traceback.print_exc()

# Verify models exist
print("=" * 60)
print("Verifying models...")
print("=" * 60)
models_dir = os.path.join(os.path.dirname(__file__), 'models')
if os.path.exists(models_dir):
    files = os.listdir(models_dir)
    print(f"Models in {models_dir}:")
    for f in files:
        size = os.path.getsize(os.path.join(models_dir, f)) / (1024*1024)
        print(f"  - {f} ({size:.1f} MB)")
else:
    print(f"Models directory not found: {models_dir}")

print("\nDone!")
