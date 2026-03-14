# 📋 AURA-AEGIS — Complete Documentation Index

## 🎯 Start Here

**New to the project?** Start with these in order:

1. **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** (5 min read)
   - ✅ What's included
   - ✅ 3-minute demo script
   - ✅ Key highlights
   - ✅ Quick start

2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (3 min read)
   - ✅ All commands at a glance
   - ✅ UI controls
   - ✅ Troubleshooting
   - ✅ Keyboard shortcuts

3. **[README.md](README.md)** (10 min read)
   - ✅ Full project overview
   - ✅ Feature descriptions
   - ✅ Architecture explanation
   - ✅ Physics model details

4. **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** (20 min read)
   - ✅ Complete implementation details
   - ✅ Algorithm pseudocode
   - ✅ Interactive scenarios
   - ✅ Presentation tips
   - ✅ Troubleshooting guide

---

## 🔧 Getting Started

### Quick Start (30 seconds)
```bash
run.bat
```

### Manual Start (1 minute)
```bash
pip install -r requirements.txt
python setup_models.py
streamlit run app.py
```

### Validate Everything (30 seconds)
```bash
python validate.py
```

---

## 📚 Complete Documentation

### Overview Documents
| File | Purpose | Read Time |
|------|---------|-----------|
| **PROJECT_COMPLETE.md** | Status & highlights | 5 min |
| **README.md** | Full overview & guide | 10 min |
| **IMPLEMENTATION_GUIDE.md** | Technical deep-dive | 20 min |
| **QUICK_REFERENCE.md** | Commands & cheat sheet | 3 min |
| **This file** | Documentation index | 2 min |

### Project Files
| File | Purpose |
|------|---------|
| **app.py** | Main Streamlit application (entry point) |
| **run.bat** | Windows one-click launcher |
| **validate.py** | Test suite (15 tests) |
| **setup_models.py** | ML model creation |
| **requirements.txt** | Python dependencies |
| **COMPLETION_STATUS.py** | Feature completion checklist |

---

## 🏗️ Architecture Overview

### Pillar 1: NAND Block Management (`core/bbt_engine.py`)
- 3-tier bad block lookup
- Bloom filter (256-bit) → Bitmap (64-bit) → Cuckoo hash (16 slots × 2 tables)
- O(1) lookups with real bit arithmetic

### Pillar 2: ECC Correction (`core/ldpc_engine.py`)
- 5-tier AEGIS pipeline
- Real LDPC bit-flip decoder with syndrome computation
- Adaptive iteration caps based on block wear
- Soft-decode with ML voltage shift

### Pillar 4: LSTM Prediction (`core/lstm_predictor.py`, `core/smart_engine.py`)
- 12 SMART metrics collector
- 2-layer PyTorch LSTM
- Outputs: [health_score, failure_prob, rul_days]
- Synthetic attention visualization

### Pillar 3: Logic Optimization (`core/kmap_qmc_engine.py`)
- K-map (4-variable) with 42.8% cost reduction
- Quine-McCluskey algorithm (5+ variables)
- BDD verification

### Security (`crypto/`, `oob/`)
- AES-256-GCM encryption
- Shamir Secret Sharing (3-of-5)
- UART/BLE OOB dump generators

---

## 🎮 UI Sections

| Section | File | Features |
|---------|------|----------|
| **Section 1: NAND** | `sections/section1_nand.py` | 8×8 grid, block inspector, BBT viz, write trace, wear demo |
| **Section 2: ECC** | `sections/section2_ecc.py` | Pipeline diagram, syndrome demo, LDPC trace, voltage model |
| **Section 3: SMART+LSTM** | `sections/section3_smart.py` | 12 metric cards, time-series, LSTM gauge, attention map |
| **Section 4: Security** | `sections/section4_security.py` | Crypto pipeline, Shamir split, OOB channels, K-map/QMC |

---

## 🧪 Testing & Validation

### Run All Tests
```bash
python validate.py
```

**Tests 15 major subsystems:**
- Core module imports
- Crypto layer
- OOB simulators
- Section UI rendering
- SSD simulator functionality
- BBT engine
- LDPC decoder
- SMART engine
- LSTM predictor
- Encryption/decryption
- Shamir sharing
- Logic optimization
- ML models
- Presets

---

## 🚀 Demo Scripts

### 3-Minute Hackathon Demo
See **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** "3-Minute Demo" section

### Show Pillar Interconnection
See **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** "Interactive Demo Scenarios"

### Show Security
See **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** "Scenario 5: OOB Security"

---

## 📖 Code Documentation

### Core Classes
- `SSDSimulator` - Main simulator with all 64 blocks
- `BlockInfo` - Individual block state
- `SMARTSnapshot` - One moment in time for 12 metrics
- `BBTEngine` - Bad Block Table with 3-tier lookup
- `LSTMHealthPredictor` - PyTorch model for health prediction

### Key Functions
- `ssd_simulator.tick()` - Advance simulation by dt seconds
- `bbt_engine.mark_bad()` - Mark a block as bad
- `ldpc_engine.pipeline_read()` - Full ECC pipeline
- `lstm_predictor.predict()` - LSTM health prediction
- `aes_layer.encrypt_report()` - AES encryption
- `shamir_layer.split_secret()` - Split key into shares

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────┐
│ User Actions (Sidebar)                              │
│ - Speed, Mode, Presets, Inject events               │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ SSD Simulator (core/ssd_simulator.py)               │
│ - 64 blocks, wear model, write simulation          │
│ - Generates SMART snapshots                        │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┴───────────────┐
    ↓                            ↓
Section 1: NAND           Section 2: ECC            Section 3: SMART+LSTM         Section 4: Crypto
- Block grid             - Syndrome check          - Metric cards               - AES encryption
- BBT inspector          - LDPC trace              - LSTM gauge                 - Shamir split
- Write trace           - Voltage model            - Attention map              - OOB dump
- Wear demo             - ECC rate chart           - Pillar commands            - K-map/QMC

                              ↓
┌─────────────────────────────────────────────────────┐
│ Header Dashboard                                    │
│ - Health gauge, RUL, anomaly, channels, ticker     │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Key Technical Claims

✅ **O(1) bad block lookup**
   - See: `core/bbt_engine.py` Bloom filter + Bitmap + Cuckoo

✅ **Real LDPC decoder**
   - See: `core/ldpc_engine.py` hard_ldpc_decode() and syndrome computation

✅ **21-day failure prediction**
   - See: `core/lstm_predictor.py` LSTM with attention visualization

✅ **AES-256-GCM encryption**
   - See: `crypto/aes_layer.py` with cryptography library

✅ **Shamir secret sharing**
   - See: `crypto/shamir_layer.py` polynomial interpolation over GF

✅ **K-map / QMC optimization**
   - See: `core/kmap_qmc_engine.py` 42.8% cost reduction proof

✅ **Pillar interconnection**
   - See: `app.py` calls all sections in real-time

---

## 🔗 Quick Links

### To Launch
- `run.bat` (Windows)
- `streamlit run app.py` (any OS)

### To Understand Code
- Start with: `core/ssd_simulator.py` (lines 1-150)
- Then: `core/bbt_engine.py` (3-tier lookup)
- Then: `core/ldpc_engine.py` (LDPC decoder)
- Then: Any `sections/section*.py` (UI rendering)

### To Learn Algorithms
- LDPC: Read `core/ldpc_engine.py` comments
- LSTM: Read `core/lstm_predictor.py` + `IMPLEMENTATION_GUIDE.md`
- K-map: See `core/kmap_qmc_engine.py` + README section
- Shamir: See `crypto/shamir_layer.py` comments

### To Extend/Integrate
- Add real SMART data: Modify `core/ssd_simulator.py` _update_smart()
- Train better LSTM: Run `training/train_lstm.py` with real data
- Deploy to firmware: Use `core/bbt_engine.py` + ONNX model

---

## 📞 Support

| Problem | Solution |
|---------|----------|
| **App won't start** | Run `python validate.py` |
| **Can't find file** | Check project directory structure above |
| **ModuleNotFoundError** | `pip install -r requirements.txt` |
| **Models missing** | `python setup_models.py` |
| **Questions on algorithm** | Read source code + comments (well-documented) |
| **Questions on UI** | Look at `sections/section*.py` (Streamlit examples) |

---

## 📋 Checklist for Success

Before presenting:
- [ ] Run `python validate.py` (all 15 tests pass)
- [ ] Run `streamlit run app.py` (opens http://localhost:8501)
- [ ] Try "Fresh Drive" preset
- [ ] Set mode to "Stress"
- [ ] Toggle "Auto Run" and watch health degrade
- [ ] Click "Inspect Block" in Section 1
- [ ] Show LDPC Tier 3 escalation in Section 2
- [ ] Click "LSTM → Retire Block" in Section 3
- [ ] Watch block turn purple in Section 1
- [ ] Show encryption → Shamir split in Section 4
- [ ] Read through **PROJECT_COMPLETE.md** for presentation tips

---

## 🎉 You're All Set!

**AURA-AEGIS is 100% complete and ready to demo.**

```bash
# One command to start:
run.bat
```

**Enjoy! 🚀**
