import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pickle
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

df = pd.read_csv('nand_training_data.csv')
FEATURES = ['pe_cycles', 'temperature', 'retention_days', 'wear_level', 'ecc_correction_history']
X, y = df[FEATURES], df['optimal_voltage_shift_mv']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# max_depth=4 keeps model under 2KB — critical for firmware claim
model = DecisionTreeRegressor(max_depth=4, min_samples_leaf=50, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, preds):.2f} mV")

os.makedirs('models', exist_ok=True)
model_path = os.path.join('models', 'voltage_model.pkl')

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

size_kb = os.path.getsize(model_path) / 1024
print(f"Model size: {size_kb:.2f} KB")  # Should be well under 2 KB
