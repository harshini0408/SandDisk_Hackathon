"""
Generate training data for use in external analysis / Backblaze integration.
Standalone script that writes CSV files with synthetic SSD lifecycle data.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd

def generate_lifecycle_csv(n_lifecycles: int = 10, out_dir: str = None):
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(out_dir, exist_ok=True)

    all_rows = []
    for lc in range(n_lifecycles):
        rng = np.random.default_rng(lc)
        n_steps = 3000 * 60
        bad_blocks = 2
        for t in range(0, n_steps, 60):  # one row per 60 steps
            wear = t / n_steps
            pe = int(wear * 3000)
            rber = 1e-7 * np.exp(pe / 500)
            ecc_rate = rber * 1e9 * abs(1 + 0.3 * rng.standard_normal())
            temp = 40 + 20 * rng.random()
            if rng.random() < 0.001 * max(wear, 0.01):
                bad_blocks += 1
            all_rows.append({
                'lifecycle_id': lc,
                'time_step': t,
                'ecc_rate': ecc_rate,
                'bad_block_count': bad_blocks,
                'pe_avg': pe,
                'wear_level': wear,
                'rber': rber,
                'temperature': temp,
                'health_label': max(0, 1 - wear**0.8),
                'failure_prob_label': min(1, wear**2 + (bad_blocks/64) * 0.5),
                'rul_label': max(0, 1 - wear),
            })

    df = pd.DataFrame(all_rows)
    csv_path = os.path.join(out_dir, 'synthetic_lifecycles.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(df)} rows to {csv_path}")
    return df


if __name__ == '__main__':
    generate_lifecycle_csv(n_lifecycles=20)
