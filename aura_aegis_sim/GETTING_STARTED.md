# 🚀 GETTING STARTED WITH AURA-AEGIS

## Quick Start (Recommended)

### Option 1: Windows (Batch File)
```bash
cd d:\SandDisk\aura_aegis_sim
run.bat
```

### Option 2: Any OS (Python Script)
```bash
cd d:\SandDisk\aura_aegis_sim
python install_and_run.py
```

### Option 3: Manual Setup
```bash
cd d:\SandDisk\aura_aegis_sim

# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup ML models
python setup_models.py

# 3. Run validation (optional)
python validate.py

# 4. Launch the app
streamlit run app.py
```

---

## System Requirements

- **Python**: 3.8+ (tested on 3.10+)
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB free space

---

## Troubleshooting

### "streamlit: command not found" or "Import could not be resolved"
**Solution**: Dependencies aren't installed
```bash
pip install -r requirements.txt
```

### Port 8501 already in use
**Solution**: Streamlit is already running or port is blocked. Either:
- Stop the existing process: `lsof -i :8501` (Mac/Linux) or `netstat -ano` (Windows)
- Use a different port: `streamlit run app.py --server.port 8502`

### ModuleNotFoundError: No module named 'core'
**Solution**: Make sure you're in the correct directory
```bash
cd d:\SandDisk\aura_aegis_sim
python app.py  # WRONG - use streamlit instead
streamlit run app.py  # CORRECT
```

### Models not loading / LSTM errors
**Solution**: Recreate the models
```bash
python setup_models.py
```

---

## Project Structure

```
aura_aegis_sim/
├── app.py                    # Main Streamlit application
├── run.bat                   # Windows launcher
├── install_and_run.py        # Cross-platform launcher
├── requirements.txt          # Python dependencies
├── setup_models.py           # ML model creation
├── validate.py               # Validation suite
│
├── core/                     # Core simulation engines
│   ├── ssd_simulator.py      # Main SSD simulator
│   ├── bbt_engine.py         # Bad Block Table engine
│   ├── ldpc_engine.py        # LDPC error correction
│   ├── smart_engine.py       # SMART metrics
│   ├── lstm_predictor.py     # ML predictor
│   └── kmap_qmc_engine.py    # Logic optimization
│
├── sections/                 # Streamlit UI sections
│   ├── section1_nand.py      # NAND/BBT visualization
│   ├── section2_ecc.py       # ECC/LDPC engine
│   ├── section3_smart.py     # SMART+LSTM analytics
│   └── section4_security.py  # Security & crypto
│
├── crypto/                   # Encryption & security
│   ├── aes_layer.py          # AES-256-GCM
│   └── shamir_layer.py       # Secret sharing
│
├── oob/                      # Out-of-band communication
│   └── uart_simulator.py     # UART emergency dump
│
├── training/                 # Model training scripts
│   ├── train_lstm.py         # LSTM trainer
│   ├── train_voltage_model.py # Voltage model trainer
│   └── generate_training_data.py
│
├── models/                   # Pre-trained models
│   └── voltage_model.pkl     # GradientBoosting model
│
└── docs/                     # Documentation
    ├── README.md
    ├── IMPLEMENTATION_GUIDE.md
    ├── QUICK_REFERENCE.md
    └── PROJECT_COMPLETE.md
```

---

## First Run Experience

1. **Dependencies Install** (~30 seconds)
2. **Models Setup** (~20 seconds) 
   - Creates voltage_model.pkl
   - Creates lstm_health.pth
3. **Validation** (~10 seconds)
   - 15 tests run automatically
4. **App Launch** 
   - Opens browser to `http://localhost:8501`
   - Ready to interact!

---

## UI Overview (4 Sections)

### 🔷 Section 1: NAND Memory
- Interactive 8×8 block grid
- Block wear tracking
- Bad Block Table visualization
- Write trace simulation

### 🔷 Section 2: ECC/LDPC Engine
- Syndrome computation demo
- LDPC bit-flip decoder
- ML voltage shift model
- ECC rate charts

### 🔷 Section 3: SMART + LSTM
- 12 SMART metrics (with sparklines)
- Health scoring & RUL prediction
- LSTM attention heatmap
- Workload classification

### 🔷 Section 4: Security
- Diagnostic report encryption
- AES-256-GCM encryption UI
- Shamir secret sharing
- UART emergency dump
- Logic optimization (K-map/QMC/BDD)

---

## Controls (Persistent Header & Sidebar)

### Header (Always Visible)
- **Health Score**: 0-100 gauge
- **RUL Countdown**: Days until failure
- **Anomaly Badge**: Status indicator
- **Channel Status**: Connection indicators
- **Event Ticker**: Real-time events

### Sidebar
- **Speed**: 1× / 5× / 20× / 100× simulation speed
- **Mode**: Normal / Stress / Aging / Crash
- **Presets**: Fresh / Mid-Aged / End-Life / Critical
- **Injectors**: Force bad blocks, thermal spikes, write storms
- **Auto-run**: Continuous simulation
- **Step**: Single-step simulation

---

## Demo Scenarios

### Scenario 1: Fresh SSD (5 minutes)
1. Load "Fresh" preset
2. Set speed to 20×
3. Enable auto-run
4. Watch NAND blocks stay green
5. Observe stable SMART metrics

### Scenario 2: Worn SSD (10 minutes)
1. Load "Mid-Aged" preset
2. Set speed to 5×
3. Inject write storm
4. See blocks transition to amber
5. Watch ECC corrections increase

### Scenario 3: End-of-Life (15 minutes)
1. Load "End-Life" preset
2. Inject thermal spike
3. Force bad blocks
4. Watch multi-tier ECC cascade
5. See RUL countdown to 0

### Scenario 4: Security Demo (10 minutes)
1. Go to Section 4
2. Generate diagnostic report
3. Encrypt with AES-256-GCM
4. Show Shamir secret splitting
5. Demonstrate UART emergency dump

---

## Key Features

✅ **Real Physics Models**
- Wear modeling (P/E cycling)
- Temperature effects on RBER
- Exponential failure curve

✅ **Advanced ECC**
- 5-tier correction pipeline
- Hard LDPC decoder
- Soft-decision ML enhancement

✅ **ML Integration**
- PyTorch LSTM predictor
- Attention heatmap visualization
- Synthetic training data pipeline

✅ **Enterprise Security**
- AES-256-GCM encryption
- Shamir (k,n) secret sharing
- OOB channels (UART, BLE)

✅ **Beautiful UI**
- Dark theme (production-ready)
- Real-time charts & animations
- Responsive design

---

## Next Steps

1. **Run the app** using one of the methods above
2. **Explore the sections** using the navigation tabs
3. **Try the demo scenarios** for guided walkthroughs
4. **Check documentation** in each section for deep dives
5. **Modify parameters** in the sidebar to see effects

---

## Support & Documentation

- **README.md** - Full project overview
- **IMPLEMENTATION_GUIDE.md** - Technical deep-dive
- **QUICK_REFERENCE.md** - Commands & shortcuts
- **PROJECT_COMPLETE.md** - Feature checklist
- **INDEX.md** - Documentation index

For issues or questions, check the troubleshooting section above or review the inline code comments.

Happy simulating! 🚀
