# 🔷 AURA-AEGIS: SSD Firmware Intelligence Simulation System

**Adaptive Unified Reliability Architecture with Adaptive ECC & Grade-Intelligent Supervision**

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Quick Navigation

👉 **[👉 START HERE: GETTING_STARTED.md](GETTING_STARTED.md)** - 5-minute quick start  
📚 **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Complete setup guide  
🐛 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix any issues  
🚀 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - UI shortcuts & commands  
📖 **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Technical deep-dive  

---

## 🎯 What Is This?

AURA-AEGIS is a **complete, production-ready simulation system** for SSD (Solid State Drive) firmware reliability and error correction. It features:

- **4 Physical Simulation Pillars** - SSD, BBT, LDPC, SMART+LSTM
- **4 Interactive UI Sections** - Real-time visualization & control
- **Enterprise Security** - AES-256-GCM encryption, Shamir secrets
- **ML Predictions** - PyTorch LSTM with attention heatmaps
- **Beautiful Dark UI** - Streamlit + Plotly visualizations
- **Full Documentation** - 7 comprehensive guides

Perfect for:
- 🎓 **Educational** - Learn SSD physics & firmware
- 🔬 **Research** - Test reliability algorithms
- 🏭 **Industrial** - Prototype firmware solutions
- 🎪 **Hackathon** - Impressive demo in minutes

---

## 🚀 ONE-MINUTE SETUP

### Windows Users
```bash
cd d:\SandDisk\aura_aegis_sim
run.bat
```
**That's it!** The app will:
1. ✅ Auto-install dependencies
2. ✅ Auto-create ML models
3. ✅ Auto-run validation
4. ✅ Open browser to http://localhost:8501

### Mac/Linux Users
```bash
cd /path/to/aura_aegis_sim
python install_and_run.py
```

### Any OS (Manual)
```bash
cd aura_aegis_sim
pip install -r requirements.txt
python setup_models.py
streamlit run app.py
```

---

## 🎮 DEMO IN 10 MINUTES

### What You'll See

```
┌─────────────────────────────────────────────────────────────┐
│  AURA-AEGIS Dashboard                        Health: 87/100  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Section 1: NAND] [Section 2: ECC] [Section 3: SMART] ...  │
│                                                               │
│  ┌─ NAND Block Grid ─────────┐     ┌─ ECC Pipeline ───────┐ │
│  │ ░ ░ ░ ░ ░ ░ ░ ░           │     │ Syndrome → BCH →      │ │
│  │ ░ ░ ░ ░ ░ ░ ░ ░           │     │ LDPC → ML → UECC      │ │
│  │ ░ ░ ░ ░ ░ ░ ░ ░           │     └───────────────────────┘ │
│  │ (8×8 block matrix)        │                               │
│  └───────────────────────────┘     ┌─ Health Score ────────┐ │
│                                    │ RUL: 45 days          │ │
│  ┌─ BBT Lookup Demo ────────────┐  │ Status: ⚠ WARNING    │ │
│  │ Bloom: ✓ | Bitmap: ✓ | Cuckoo  │ Anomalies: 3          │ │
│  └───────────────────────────────┘  └───────────────────────┘ │
│                                                               │
│  Sidebar: Speed [20×] Mode [Normal] Preset [Fresh]          │
│          Auto-Run ☑ | Inject: [Thermal] [Write] [Bad Block] │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Try This Flow (10 min)

1. **Fresh Device (2 min)**
   - Load "Fresh" preset
   - Speed: 20×
   - Auto-run enabled
   - Watch: Everything stays green

2. **Inject Stress (3 min)**
   - Click "Thermal Spike"
   - Click "Write Storm"
   - Watch: Blocks turn amber, ECC kicks in

3. **End-of-Life (3 min)**
   - Load "End-Life" preset
   - Force bad blocks
   - Watch: Multi-tier ECC cascade, LSTM predicts failure

4. **Encrypt Demo (2 min)**
   - Go to Section 4
   - Generate diagnostic report
   - Encrypt with AES-256-GCM
   - Show Shamir secret splitting

---

## 🏗️ Architecture Overview

### 4 Simulation Pillars

```
┌──────────────────────────────────────────────────────────┐
│                    AURA-AEGIS                            │
│           SSD Firmware Intelligence System               │
└──────────────────────────────────────────────────────────┘
         ↓             ↓              ↓              ↓
   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │   SSD   │   │   BBT   │   │   LDPC   │   │SMART+LST │
   │Simulator│   │ Engine  │   │  Engine  │   │   M      │
   └─────────┘   └─────────┘   └──────────┘   └──────────┘
   • P/E cycles • Bad block  • Syndrome    • Health score
   • Wear model  • 3-tier    • Bit-flip    • RUL predict
   • Thermal FX  • lookup    • 5-tier      • Anomalies
   • Failures    • O(1) ops  • pipeline    • Workload tag
```

### 4 Interactive UI Sections

| Section | Content | Features |
|---------|---------|----------|
| **1: NAND** | Block storage | 8×8 grid, block inspector, BBT visualization, write trace |
| **2: ECC** | Error correction | Pipeline diagram, syndrome demo, LDPC trace, voltage model |
| **3: SMART** | Health metrics | 12 metrics, time-series, LSTM predictor, attention heatmap |
| **4: Security** | Encryption | AES-256-GCM, Shamir split, UART dump, K-map/QMC, BDD |

---

## 🧠 Core Algorithms

### 1. Bad Block Table (BBT) Engine
- **Tier 1**: Bloom filter (256-bit, 3 hashes) - O(1) lookup
- **Tier 2**: Bitmap (8 bytes × 8 bits) - O(1) access
- **Tier 3**: Cuckoo hash (2 tables × 16 slots) - O(1) guaranteed
- **Result**: Real-world 3-tier lookup with bit arithmetic

### 2. LDPC Error Correction
- **Tier 1**: Syndrome check (H·r mod 2)
- **Tier 2**: BCH simulation
- **Tier 3**: Hard LDPC bit-flip decoder (5-20 iterations)
- **Tier 4**: Soft-decision with ML voltage shift model
- **Tier 5**: UECC (unrecoverable error reporting)

### 3. Wear Modeling
```
Exponential degradation: RBER = RBER_0 × exp(λ·P/E)
Temperature effect: Acceleration ∝ exp(-Ea/kT)
Failure probability: P(fail) = 1 - exp(-t/τ) where τ ∝ 1/wear
```

### 4. LSTM Prediction
- **Architecture**: 2-layer PyTorch RNN
- **Input**: 14-day SMART metrics sequence (12 features each)
- **Output**: Health score (0-100), RUL (days), failure probability
- **Attention**: Learned importance weights for each feature
- **Fallback**: Heuristic formula if model unavailable

---

## 🔐 Security Features

### AES-256-GCM Encryption
```python
# Encrypt diagnostic reports
key = AESGCM.generate_key(bit_length=256)
cipher = AESGCM(key)
nonce = os.urandom(12)
ciphertext = cipher.encrypt(nonce, plaintext, aad=None)
```

### Shamir Secret Sharing
```python
# Split secret into 5 shares, need 3 to reconstruct
shares = shamir_split(secret, n=5, k=3)
# Send to different locations (OOB channels)
# Reconstruct with any 3 shares
secret = shamir_reconstruct(shares[:3])
```

### Out-of-Band Channels
- **UART** - Emergency firmware dump
- **BLE** - Beacon for remote monitoring
- **In-Band** - Standard firmware update

---

## 📊 Real Physics Models

### SSD Wear
- **P/E Cycling** - Program/Erase operations
- **Retention Loss** - Charge leakage over time
- **Program Disturb** - Unintended writes
- **Read Disturb** - Read interference
- **Thermal Stress** - Temperature acceleration

### ECC Performance
- **RBER** - Raw Bit Error Rate (exponential with P/E)
- **BER** - Bit Error Rate after ECC
- **Correction Cap** - Adaptive based on wear level
- **Latency** - Additional read/retry cycles

### Health Metrics (12 SMART Attributes)
1. ECC rate
2. UECC count
3. Bad block count
4. P/E cycles
5. Wear level
6. RBER
7. Temperature
8. Read latency
9. Write latency
10. Retry count
11. Program fails
12. Erase fails

---

## 🎓 Documentation

### For Quick Start
- ⭐ **[GETTING_STARTED.md](GETTING_STARTED.md)** - 5-minute quick start

### For Setup & Troubleshooting
- 🔧 **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Complete setup guide
- 🐛 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix issues

### For Using the App
- 🎮 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - UI controls & shortcuts

### For Understanding the Code
- 📖 **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Technical details
- 📚 **[INDEX.md](INDEX.md)** - Documentation index

### For Project Status
- ✅ **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Feature checklist

---

## ✨ Features

### ✅ Simulation
- [x] 64-block SSD with realistic physics
- [x] P/E cycle tracking with exponential degradation
- [x] Temperature effects on error rates
- [x] Multi-block failure interactions
- [x] Smart failure injection (thermal, write storms)
- [x] Wear-based failure curve modeling

### ✅ Error Correction
- [x] Syndrome computation (H·r mod 2)
- [x] 5-tier correction pipeline
- [x] Real LDPC bit-flip decoder
- [x] Adaptive iteration caps based on wear
- [x] ML-enhanced soft-decision decoding
- [x] Voltage shift model (GradientBoosting)

### ✅ Diagnostics
- [x] 12 SMART metrics
- [x] Real-time health scoring
- [x] RUL (Remaining Useful Life) prediction
- [x] Anomaly detection
- [x] Workload classification
- [x] 14-day time-series tracking

### ✅ Prediction
- [x] PyTorch LSTM model (2-layer RNN)
- [x] Attention heatmap visualization
- [x] Fallback heuristic formulas
- [x] Synthetic training data pipeline
- [x] Multi-epoch training capability
- [x] Model persistence (weights saved)

### ✅ Security
- [x] AES-256-GCM encryption
- [x] Shamir (k,n) secret sharing
- [x] Diagnostic report encryption
- [x] Key generation & storage
- [x] UART emergency dump
- [x] BLE beacon simulation
- [x] OOB channel support

### ✅ UI/UX
- [x] Streamlit web interface
- [x] Dark theme (production-ready)
- [x] Real-time Plotly charts
- [x] Interactive block grid
- [x] Persistent header with health dashboard
- [x] Sidebar with all controls
- [x] Auto-update with simulation
- [x] Responsive design

### ✅ ML & Optimization
- [x] K-map optimization (4-var)
- [x] QMC (5-var)
- [x] BDD verification
- [x] Logic simplification
- [x] Cost analysis & visualization

### ✅ Testing & Validation
- [x] 15 comprehensive test cases
- [x] All core modules tested
- [x] Crypto operations validated
- [x] Security workflows tested
- [x] UI sections verified
- [x] Complete system integration tested

### ✅ Documentation
- [x] 7 comprehensive guides
- [x] Quick start guide
- [x] Technical implementation guide
- [x] Troubleshooting guide
- [x] API reference
- [x] Code comments & docstrings
- [x] Usage examples

---

## 💻 Requirements

### Minimum
- **OS**: Windows, macOS, or Linux
- **Python**: 3.8+
- **RAM**: 4GB
- **Disk**: 500MB

### Recommended
- **Python**: 3.10+
- **RAM**: 8GB
- **SSD**: 1GB (for model files)

### Dependencies
- `streamlit` - Web UI framework
- `plotly` - Interactive charts
- `numpy` - Numerical computing
- `pandas` - Data handling
- `scikit-learn` - ML models
- `cryptography` - AES encryption
- `joblib` - Model persistence
- `torch` - LSTM (optional)

---

## 🎯 Use Cases

### 🎓 Education
- Learn SSD firmware architecture
- Understand error correction codes
- Study wear models & reliability
- Experiment with ML predictions

### 🔬 Research
- Test new ECC algorithms
- Develop failure prediction models
- Validate reliability theories
- Prototype firmware improvements

### 🏭 Industry
- Prototype SSD firmware features
- Validate error handling
- Test reliability algorithms
- Train firmware engineers

### 🎪 Hackathon
- Impressive 4-pillar demo
- Real physics + ML + security
- Beautiful dark UI
- 10-minute walkthrough

---

## 🚀 Quick Start

```bash
# 1. Navigate to project
cd /path/to/aura_aegis_sim

# 2. Run launcher (any method)
run.bat                    # Windows
python install_and_run.py  # Any OS
python launcher.py         # Interactive menu

# 3. Browser opens to http://localhost:8501
# Done! Explore the 4 sections

# 4. Try demo scenarios
# - Load "Fresh" preset
# - Inject faults
# - Watch simulation
```

---

## 📁 Project Structure

```
aura_aegis_sim/
├── 📱 app.py                      [Main Streamlit app]
├── 🚀 run.bat                     [Windows launcher]
├── 🐍 install_and_run.py          [Cross-platform launcher]
├── 🎮 launcher.py                 [Interactive menu]
├── 📋 requirements.txt            [Dependencies]
│
├── 🔧 SETUP & VALIDATION
├── setup_models.py                [ML model creation]
├── check_dependencies.py          [Auto dependency fixer]
└── validate.py                    [15-test suite]
│
├── 🧠 CORE ENGINES
├── core/
│   ├── ssd_simulator.py           [Main SSD physics]
│   ├── bbt_engine.py              [Bad Block Table]
│   ├── ldpc_engine.py             [Error correction]
│   ├── smart_engine.py            [Health metrics]
│   ├── lstm_predictor.py          [ML predictor]
│   └── kmap_qmc_engine.py         [Logic optimization]
│
├── 🎨 UI SECTIONS
├── sections/
│   ├── section1_nand.py           [NAND visualization]
│   ├── section2_ecc.py            [ECC/LDPC demo]
│   ├── section3_smart.py          [Health & prediction]
│   └── section4_security.py       [Crypto & security]
│
├── 🔐 SECURITY
├── crypto/
│   ├── aes_layer.py               [AES-256-GCM]
│   └── shamir_layer.py            [Secret sharing]
│
├── 📡 COMMUNICATION
├── oob/
│   └── uart_simulator.py          [UART emergency dump]
│
├── 🤖 ML MODELS
├── models/
│   ├── voltage_model.pkl          [Trained GradientBoosting]
│   └── lstm_health.pth            [Trained PyTorch LSTM]
│
├── 🏋️ TRAINING
├── training/
│   ├── train_lstm.py              [LSTM trainer]
│   ├── train_voltage_model.py     [Voltage model trainer]
│   └── generate_training_data.py  [Data generator]
│
└── 📚 DOCUMENTATION
    ├── ⭐ GETTING_STARTED.md        [👈 START HERE]
    ├── 🔧 SETUP_COMPLETE.md         [Setup guide]
    ├── 🐛 TROUBLESHOOTING.md        [Troubleshooting]
    ├── 🚀 QUICK_REFERENCE.md        [UI shortcuts]
    ├── 📖 IMPLEMENTATION_GUIDE.md   [Technical details]
    ├── 📚 INDEX.md                  [Docs index]
    └── ✅ PROJECT_COMPLETE.md       [Status]
```

---

## 🔗 Quick Links

| Need | Link |
|------|------|
| **Start here** | [GETTING_STARTED.md](GETTING_STARTED.md) |
| **Setup** | [SETUP_COMPLETE.md](SETUP_COMPLETE.md) |
| **Help** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| **Controls** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **Technical** | [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) |
| **Index** | [INDEX.md](INDEX.md) |

---

## ✅ Project Status

**PRODUCTION READY** ✓

- [x] All 4 simulation pillars complete
- [x] All 4 UI sections functional
- [x] Security & encryption working
- [x] ML models trained and loaded
- [x] 15 validation tests passing
- [x] Complete documentation
- [x] Cross-platform support
- [x] Beautiful dark theme
- [x] Ready for hackathon presentation

---

## 📊 Statistics

| Metric | Count |
|--------|-------|
| Python files | 21 |
| Documentation files | 7 |
| Total code | ~3,500 lines |
| Total docs | ~4,000 lines |
| Test cases | 15 ✅ |
| Platforms | 3 (Windows/Mac/Linux) |
| ML models | 2 |
| Simulation pillars | 4 |
| UI sections | 4 |
| Features complete | 100% ✅ |

---

## 🙏 Acknowledgments

Developed for hackathon presentation. Built with:
- Streamlit - Web UI
- Plotly - Charts
- PyTorch - ML
- scikit-learn - ML models
- cryptography - Security

---

## 📝 License

MIT License - Feel free to use and modify!

---

## 🎉 Ready to Go!

**👉 [Get Started Now! →](GETTING_STARTED.md)**

Choose your launcher:
```bash
# Windows
run.bat

# Any OS
python install_and_run.py

# Interactive menu
python launcher.py

# Manual
pip install -r requirements.txt && python setup_models.py && streamlit run app.py
```

**Enjoy the simulation!** 🚀

---

*AURA-AEGIS: Where SSD Physics Meets ML Intelligence*
