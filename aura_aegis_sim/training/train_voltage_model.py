"""
Voltage Shift Regression Model Training Script (Pillar 2 Tier 3).
Inputs: [pe_count, temperature, ecc_history, wear_level]
Output: optimal_voltage_shift (mV)
Run this once to produce models/voltage_model.pkl
"""
import numpy as np
import joblib
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


def generate_voltage_data(n: int = 5000):
    """
    Physics-inspired voltage shift data:
    ΔV = 0.02*pe + 0.3*temp + 0.001*ecc + noise
    """
    rng = np.random.default_rng(42)
    pe = rng.uniform(0, 3000, n)
    temp = rng.uniform(20, 85, n)
    ecc = rng.exponential(5000, n)
    wear = pe / 3000.0
    delta_v = (
        0.02 * pe +
        0.3 * temp +
        0.001 * ecc +
        rng.normal(0, 5, n)
    )
    X = np.column_stack([pe, temp, ecc, wear])
    return X, delta_v


def train_voltage_model(save_path: str = None):
    if save_path is None:
        save_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'voltage_model.pkl')

    print("Generating voltage shift training data (5000 samples)...")
    X, y = generate_voltage_data(5000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training GradientBoostingRegressor...")
    model = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05,
                                      random_state=42, verbose=0)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"  MAE on test set: {mae:.2f} mV")
    print(f"  Feature importances: pe={model.feature_importances_[0]:.3f}, "
          f"temp={model.feature_importances_[1]:.3f}, "
          f"ecc={model.feature_importances_[2]:.3f}, "
          f"wear={model.feature_importances_[3]:.3f}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(model, save_path)
    print(f"Model saved to: {save_path}")
    return model


if __name__ == '__main__':
    train_voltage_model()
