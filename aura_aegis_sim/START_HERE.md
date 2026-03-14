# 🎯 START HERE — AURA-AEGIS Quick Launch Guide

## ⚡ 30-Second Quick Start

### For Windows Users
```bash
cd d:\SandDisk\aura_aegis_sim
run.bat
```
**Click the app link that appears in terminal** 🚀

### For Mac/Linux Users
```bash
cd /path/to/aura_aegis_sim
python install_and_run.py
```

That's it! The app will automatically:
- ✅ Install dependencies
- ✅ Create ML models
- ✅ Run validation
- ✅ Open in browser at http://localhost:8501

---

## 🎮 What You'll See (60 seconds into launch)

You'll get a dashboard with:

```
┌────────────────────────────────────────────────────────────────┐
│  AURA-AEGIS Dashboard               Health Score: 87/100 ▮▮▮▮▯  │
│  RUL: 45 days | Anomalies: 3 | ⚠ WARNING                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Section 1: NAND] [Section 2: ECC] [Section 3: SMART] [4: ...] │
│                                                                 │
│  ┌─ Section 1: NAND Block Grid ─────┐  ┌─ Sidebar Controls ──┐ │
│  │  ░ ░ ░ ░ ░ ░ ░ ░                 │  │ Speed: [20×]        │ │
│  │  ░ ░ ░ ░ ░ ░ ░ ░                 │  │ Mode: [Normal ▼]    │ │
│  │  ░ ░ ░ ░ ░ ░ ░ ░                 │  │ Preset: [Fresh ▼]   │ │
│  │  ░ ░ ░ ░ ░ ░ ░ ░                 │  │                     │ │
│  │  (Click a block to inspect)       │  │ [Auto Run ☑]        │ │
│  └─────────────────────────────────┘  └─────────────────────┘ │
│                                                                 │
│  ┌─ Section 2: ECC Correction Demo ──────────────────────────┐ │
│  │ Inject 0-4 errors into a 16-bit codeword                  │ │
│  │ See how multi-tier ECC catches them                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Try This 5-Minute Demo

### Step 1: Fresh Device (2 min)
1. **Sidebar**: Set Speed to "5×"
2. **Sidebar**: Load Preset "Fresh"
3. **Sidebar**: Check "Auto Run"
4. **Watch**: Everything stays green! SMART metrics stable, blocks healthy

### Step 2: Inject Some Stress (2 min)
1. **Sidebar**: Click "Thermal Spike" button
2. **Sidebar**: Click "Write Storm" button
3. **Watch**: Blocks turn amber ⚠️, SMART metrics rise, ECC corrections increase
4. **Section 2**: See LDPC decoder work harder

### Step 3: Inspect Details (1 min)
1. **Section 1**: Click on one of the amber blocks
2. **Pop-up**: See detailed block info (P/E count, temperature, etc.)
3. **Section 3**: See health score dropping, RUL countdown starting

---

## 🎨 4 Interactive Sections

### 🔷 Section 1: NAND Memory
**What it shows**: Physical block storage visualization
- **8×8 block grid** - Each block shows wear status (green=fresh, amber=worn, red=failed)
- **Click any block** - See detailed info (P/E cycles, temperature, error rate)
- **BBT visualizations** - See how bad block table works
- **Write trace** - Watch how writes are distributed across blocks

### 🔷 Section 2: ECC/LDPC Engine
**What it shows**: Error correction in action
- **Syndrome demo** - Inject 0-4 errors, see if they're detected
- **LDPC decoder trace** - Watch bit-flip algorithm iterations
- **Voltage shift model** - ML-enhanced error recovery
- **ECC rate chart** - How corrections increase with wear

### 🔷 Section 3: SMART + LSTM
**What it shows**: Health metrics & ML prediction
- **12 SMART attributes** - Real-time metrics with sparklines
- **Health score gauge** - 0-100 overall health
- **RUL counter** - Days until predicted failure
- **LSTM attention heatmap** - Which metrics matter most
- **Time-series chart** - 14-day history of each metric

### 🔷 Section 4: Security & Crypto
**What it shows**: Encryption & secret sharing
- **AES-256-GCM** - Encrypt diagnostic reports
- **Shamir secrets** - Split keys across locations
- **UART dump** - Emergency firmware recovery
- **Logic optimization** - K-map/QMC demos
- **BDD verification** - Boolean circuit analysis

---

## 🕹️ Sidebar Controls (Always Available)

```
┌─────────────────────────────────┐
│  SIMULATION SPEED               │
│  ○ 1×   ○ 5×   ◉ 20×   ○ 100×  │
├─────────────────────────────────┤
│  OPERATING MODE                 │
│  ◉ Normal   ○ Stress            │
│  ○ Aging    ○ Crash             │
├─────────────────────────────────┤
│  QUICK PRESETS                  │
│  ○ Fresh  ○ Mid-Aged            │
│  ○ End-Life  ◉ Custom            │
├─────────────────────────────────┤
│  FAULT INJECTION                │
│  [Force Bad Block] [Thermal]    │
│  [Write Storm]  [Kill Host]     │
├─────────────────────────────────┤
│  SIMULATION CONTROL             │
│  ☑ Auto Run                     │
│  [Single Step] [Reset]          │
└─────────────────────────────────┘
```

---

## 🚀 Play With These Features

### Experiment 1: Wear Progression
1. Load "Fresh" preset
2. Set speed to 100× (ultra-fast)
3. Auto-run for 30 seconds
4. Watch: Blocks turn amber gradually, health score drops

### Experiment 2: Thermal Stress
1. Load "Mid-Aged" preset
2. Click "Thermal Spike"
3. Watch: RBER jumps, ECC corrections spike
4. See: Voltage shift model adapts

### Experiment 3: Encryption
1. Go to Section 4
2. Click "Generate Report"
3. Click "Encrypt with AES-256"
4. See: Key, IV, ciphertext all displayed

### Experiment 4: LSTM Prediction
1. Go to Section 3
2. Scroll down to "LSTM Health Gauge"
3. Watch: Attention heatmap shows which metrics drive predictions
4. Try: Different presets to see different failure patterns

---

## 📚 Documentation (More Details)

### Need quick answers?
- 📖 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - UI controls & shortcuts (2 min read)

### Need setup help?
- 🔧 **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Complete installation guide (5 min read)
- 🐛 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix any problems (varies)

### Need to understand the tech?
- 📘 **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Deep technical dive (20 min read)
- 📘 **[MAIN_README.md](MAIN_README.md)** - Full project overview (10 min read)

### Need everything?
- 📚 **[INDEX.md](INDEX.md)** - Complete documentation index

---

## ✅ Troubleshooting (Common Issues)

### ❌ "Port 8501 already in use"
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### ❌ "Module not found" or "streamlit not found"
```bash
# Reinstall dependencies
python check_dependencies.py
# or
pip install -r requirements.txt
```

### ❌ "Models not found"
```bash
# Recreate models
python setup_models.py
```

### ❌ Something else?
👉 See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for comprehensive help

---

## 🎯 What This Project Is

AURA-AEGIS is a **complete SSD firmware simulation system** showing:

- **4 Physical Pillars** - Real SSD physics (wear, temperature, failures)
- **4 Interactive Sections** - Visualize everything happening
- **ML Intelligence** - LSTM prediction with attention heatmaps
- **Enterprise Security** - AES encryption, Shamir secrets
- **Beautiful UI** - Dark theme, real-time charts

Perfect for:
- 🎓 Learning SSD firmware architecture
- 🔬 Testing reliability algorithms
- 🏭 Prototyping firmware features
- 🎪 Impressing at a hackathon

---

## 🎓 Learn the Basics

### What is a P/E Cycle?
Program/Erase - each time you write to a flash block. Limited cycles (~10,000) before wear.

### What is RBER?
Raw Bit Error Rate - how many bits get corrupted during read. Increases with wear & heat.

### What is LDPC?
Low-Density Parity-Check code - error correction that tries to fix bit errors automatically.

### What is LSTM?
Long Short-Term Memory neural network - learns patterns in SMART metrics to predict failures.

### What is AES-256?
Advanced Encryption Standard with 256-bit key - military-grade encryption for data protection.

---

## 🎮 Demo Scripts (Copy & Paste)

### Quick Demo (5 min)
1. Set Speed: 20×
2. Load Preset: Fresh
3. Auto-run ✓
4. *[Wait 30 seconds]*
5. Click: Thermal Spike
6. *[Watch metrics climb]*
7. Go to Section 4
8. Click: Generate & Encrypt Report

### Full Demo (15 min)
1. Fresh SSD (5 min) - stability at start
2. Mid-aged SSD (5 min) - inject faults
3. End-life SSD (3 min) - watch failures
4. Crypto demo (2 min) - AES & Shamir

---

## 🚀 Next Steps

### Immediate (Now)
1. ✅ Run the app using launcher
2. ✅ Explore the 4 sections
3. ✅ Try a demo scenario

### Short-term (Next 30 min)
1. 📖 Read QUICK_REFERENCE.md
2. 🎮 Experiment with controls
3. 🔬 Inject different faults

### Deep-dive (Next 1-2 hours)
1. 📖 Read IMPLEMENTATION_GUIDE.md
2. 💻 Review the source code
3. 🧪 Run validation suite
4. 🔧 Customize parameters

---

## ✨ Key Features (At a Glance)

✅ **Real Physics** - P/E cycles, temperature effects, wear modeling  
✅ **Error Correction** - 5-tier LDPC pipeline with ML enhancement  
✅ **Health Prediction** - LSTM model with attention visualization  
✅ **Security** - AES-256-GCM, Shamir secrets, UART dump  
✅ **Beautiful UI** - Dark theme, real-time charts, responsive  
✅ **Interactive** - Click blocks, inject faults, watch simulation  
✅ **Complete** - 100% functional, tested, documented  
✅ **Ready** - Works on Windows/Mac/Linux, one-click launch  

---

## 💬 Questions?

| Question | Answer |
|----------|--------|
| **How do I start?** | Run `run.bat` or `python install_and_run.py` |
| **What if I get errors?** | Check TROUBLESHOOTING.md or run `python check_dependencies.py` |
| **How do I use the UI?** | Check QUICK_REFERENCE.md |
| **How does it work?** | Check IMPLEMENTATION_GUIDE.md |
| **What's the status?** | Run `python PROJECT_STATUS.py` |

---

## 🎉 Ready to Go!

```bash
# Windows
cd d:\SandDisk\aura_aegis_sim
run.bat

# Mac/Linux
cd /path/to/aura_aegis_sim
python install_and_run.py
```

**The browser will open automatically in ~30 seconds** 🚀

Enjoy exploring AURA-AEGIS! 🔷

---

*P.S. - If something doesn't work, just run `python check_dependencies.py` and it'll fix it automatically!*
