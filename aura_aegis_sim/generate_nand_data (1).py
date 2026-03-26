import numpy as np
import pandas as pd
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

np.random.seed(42)
N = 15000

pe_cycles = np.random.randint(0, 5001, N)
temperature = np.random.uniform(20, 85, N)
retention_days = np.random.uniform(0, 365, N)
wear_level = pe_cycles / 5000 * 100
ecc_history = (pe_cycles * 0.008) + np.random.normal(0, 2, N)
ecc_history = np.clip(ecc_history, 0, None)

# Physics-based voltage shift formula
voltage_shift = (
    pe_cycles * 0.012
    + temperature * 0.04
    + retention_days * 0.08
    + wear_level * 0.15
    + np.random.normal(0, 3, N)  # sensor noise
)

df = pd.DataFrame({
    'pe_cycles': pe_cycles,
    'temperature': temperature,
    'retention_days': retention_days,
    'wear_level': wear_level,
    'ecc_correction_history': ecc_history,
    'optimal_voltage_shift_mv': voltage_shift
})

df.to_csv('nand_training_data.csv', index=False)
print(f"Generated {N} samples. Shift range: {voltage_shift.min():.1f} to {voltage_shift.max():.1f} mV")
