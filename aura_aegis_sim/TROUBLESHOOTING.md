# 🔧 AURA-AEGIS TROUBLESHOOTING & DIAGNOSTIC GUIDE

## Quick Diagnostics

Run this to get a complete health report:

```bash
cd d:\SandDisk\aura_aegis_sim
python check_dependencies.py
python validate.py
```

---

## Common Issues & Solutions

### ❌ Issue: "Python not found" or "python: command not found"

**Symptoms:**
- `python: command not found`
- `'python' is not recognized as an internal or external command`

**Causes:**
- Python not installed
- Python not in system PATH
- Using wrong Python command

**Solutions:**

1. **Check if Python is installed:**
   ```bash
   python --version
   # or
   python3 --version
   ```

2. **Add Python to PATH (Windows):**
   - Open Control Panel → System → Advanced system settings
   - Click "Environment Variables"
   - Find "Path" in System variables, click Edit
   - Add Python installation directory (e.g., `C:\Python311`)
   - Restart command prompt

3. **Use python3 instead:**
   ```bash
   python3 --version
   python3 -m pip install -r requirements.txt
   python3 install_and_run.py
   ```

4. **Install Python:**
   - Download from https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Restart computer

---

### ❌ Issue: "Module not found" or "No module named 'streamlit'"

**Symptoms:**
- `ModuleNotFoundError: No module named 'streamlit'`
- `ImportError: cannot import name 'X'`

**Causes:**
- Dependencies not installed
- Using wrong Python environment
- Virtual environment not activated

**Solutions:**

1. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   # or
   python check_dependencies.py
   ```

2. **Verify installation:**
   ```bash
   python -c "import streamlit; print('OK')"
   python -c "import plotly; print('OK')"
   python -c "import numpy; print('OK')"
   ```

3. **If using virtualenv, activate it:**
   ```bash
   # Windows
   venv\Scripts\activate.bat
   # Then install
   pip install -r requirements.txt
   ```

4. **Force reinstall specific package:**
   ```bash
   python -m pip install --force-reinstall streamlit
   ```

---

### ❌ Issue: "Port 8501 already in use"

**Symptoms:**
- `Address already in use`
- `OSError: [Errno 48] Address already in use`

**Causes:**
- Streamlit app already running
- Another process using port 8501
- Streamlit didn't shut down properly

**Solutions:**

1. **Use different port:**
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **Find and kill process using port 8501 (Windows):**
   ```bash
   # Find process
   netstat -ano | findstr :8501
   # Kill process (replace PID with actual number)
   taskkill /PID <PID> /F
   ```

3. **Find and kill process using port 8501 (Mac/Linux):**
   ```bash
   lsof -i :8501
   kill -9 <PID>
   ```

4. **Wait a few seconds and try again:**
   Sometimes Streamlit takes time to fully shut down

---

### ❌ Issue: "Models not found" or "LSTM model loading failed"

**Symptoms:**
- `FileNotFoundError: [Errno 2] No such file or directory: 'models/lstm_health.pth'`
- LSTM predictions showing "N/A" or errors

**Causes:**
- Models not created
- setup_models.py didn't run
- Models directory deleted

**Solutions:**

1. **Recreate models:**
   ```bash
   python setup_models.py
   ```

2. **Check if models directory exists:**
   ```bash
   # Windows
   dir models\
   # Mac/Linux
   ls -la models/
   ```

3. **Manually create models:**
   ```bash
   python training/train_voltage_model.py
   python training/train_lstm.py
   ```

4. **Check setup_models.py output:**
   ```bash
   python setup_models.py -v
   ```

---

### ❌ Issue: "Validation tests failing"

**Symptoms:**
- `validate.py` shows red ✗ marks
- Test output shows failures

**Causes:**
- Core modules have issues
- Dependencies partially installed
- File structure corrupted

**Solutions:**

1. **Run validation with verbose output:**
   ```bash
   python validate.py
   # Read the detailed output
   ```

2. **Check individual core modules:**
   ```bash
   python -c "from core.ssd_simulator import SSDSimulator; print('SSD OK')"
   python -c "from core.bbt_engine import BadBlockTable; print('BBT OK')"
   python -c "from core.ldpc_engine import hard_ldpc_decode; print('LDPC OK')"
   python -c "from core.smart_engine import SMARTEngine; print('SMART OK')"
   ```

3. **Reinstall from scratch:**
   ```bash
   # 1. Remove Python environment (if using venv)
   # 2. Create fresh venv
   python -m venv venv
   # 3. Activate it
   venv\Scripts\activate  # Windows
   # 4. Install fresh
   pip install -r requirements.txt
   python setup_models.py
   ```

---

### ❌ Issue: "App starts but shows blank page or errors"

**Symptoms:**
- Streamlit app opens but shows no content
- Red error banners in app
- "Something went wrong"

**Causes:**
- Streamlit cache corrupted
- App.py has runtime error
- Missing imports or circular dependencies

**Solutions:**

1. **Clear Streamlit cache:**
   ```bash
   # Windows
   rmdir /S /Q %USERPROFILE%\.streamlit
   # Mac/Linux
   rm -rf ~/.streamlit
   ```

2. **Start fresh:**
   ```bash
   streamlit run app.py --logger.level=debug 2>&1 | head -100
   ```

3. **Check app.py syntax:**
   ```bash
   python -m py_compile app.py
   ```

4. **Run app with error output:**
   ```bash
   python -c "import app"  # This will show import errors
   ```

---

### ❌ Issue: "GPU/CUDA errors with PyTorch"

**Symptoms:**
- `RuntimeError: CUDA out of memory`
- `NotImplementedError: Function 'gpu_setup' not implemented for backend 'CPU'`
- PyTorch warnings about CUDA

**Causes:**
- GPU not available or not configured
- PyTorch trying to use CUDA unnecessarily

**Solutions:**

1. **Use CPU-only version (recommended for demo):**
   ```bash
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   ```

2. **Reinstall without GPU:**
   ```bash
   python setup_models.py --no-cuda
   ```

3. **The app falls back automatically:**
   - LSTM predictor has CPU fallback
   - Models will use CPU if GPU unavailable
   - No changes needed

---

### ❌ Issue: "Slow performance or crashes on startup"

**Symptoms:**
- App takes >30 seconds to load
- Memory usage high
- Occasional crashes

**Causes:**
- Training data too large
- LSTM model initialization slow
- Too many simultaneous updates

**Solutions:**

1. **Skip validation on startup:**
   ```bash
   # Edit run.bat or install_and_run.py
   # Comment out the validation.py line
   ```

2. **Pre-compile models (one-time cost):**
   ```bash
   python setup_models.py
   # Wait for completion, then next runs will be faster
   ```

3. **Use faster speed preset:**
   - In sidebar: set Speed to "1×"
   - Gives UI more time to render

4. **Check system resources:**
   ```bash
   # Windows - check Task Manager
   # Mac/Linux - check top or Activity Monitor
   ```

---

### ❌ Issue: "Crypto or Shamir operations failing"

**Symptoms:**
- "Encryption failed" in Section 4
- Shamir split/reconstruct showing errors
- AES operations timing out

**Causes:**
- cryptography library not installed
- Key generation issues

**Solutions:**

1. **Reinstall cryptography:**
   ```bash
   pip install --force-reinstall cryptography
   ```

2. **Check if cryptography works:**
   ```bash
   python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('OK')"
   ```

3. **Test Shamir layer:**
   ```bash
   python -c "from crypto.shamir_layer import shamir_split; print('OK')"
   ```

---

### ❌ Issue: "ECC/LDPC simulation seems wrong or slow"

**Symptoms:**
- LDPC decoder takes too long
- Syndrome computation seems stuck
- Bit-flip decoder not converging

**Causes:**
- Max iterations too high
- Large codeword size
- Inefficient algorithm

**Solutions:**

1. **Check LDPC iteration cap:**
   - Go to Section 2
   - Look at "LDPC cap for P/E=X: Y iterations"
   - Y should be between 8-40

2. **Lower iteration cap:**
   - Edit `core/ldpc_engine.py`
   - Reduce `MAX_ITERATIONS` (default: 40)

3. **Use smaller test:**
   - Section 2 → "Generate new codeword"
   - Set errors to 1-2
   - Should complete in <1 second

---

## Diagnostic Commands

### Full System Check
```bash
# 1. Check Python version
python --version

# 2. Check dependencies
python check_dependencies.py

# 3. Test core modules
python -c "from core.ssd_simulator import SSDSimulator; s = SSDSimulator(); print(f'SSD created: {s}')"

# 4. Test imports
python -c "import streamlit; import plotly; import numpy; import pandas; import sklearn; import cryptography; import joblib; print('All imports OK')"

# 5. Run full validation
python validate.py

# 6. Start app in debug mode
streamlit run app.py --logger.level=debug
```

### Model Check
```bash
# Check if voltage model exists
python -c "import joblib; m = joblib.load('models/voltage_model.pkl'); print(f'Voltage model OK: {m}')"

# Check if LSTM model exists
python -c "import torch; m = torch.load('models/lstm_health.pth'); print(f'LSTM model OK')"

# Regenerate both
python setup_models.py
```

### Performance Check
```bash
# Time the startup
python -c "import time; t=time.time(); import app; print(f'Import time: {time.time()-t:.2f}s')"

# Check memory usage
python -c "import psutil, os; p=psutil.Process(os.getpid()); print(f'Memory: {p.memory_info().rss/1024/1024:.1f}MB')"
```

---

## Getting Help

1. **Check documentation:**
   - `GETTING_STARTED.md` - Quick start guide
   - `README.md` - Full project overview
   - `IMPLEMENTATION_GUIDE.md` - Technical details
   - `QUICK_REFERENCE.md` - UI shortcuts

2. **Enable debug logging:**
   ```bash
   streamlit run app.py --logger.level=debug
   ```

3. **Check app output carefully** - error messages often indicate the solution

4. **Review inline code comments** - most functions have detailed docstrings

5. **Try the auto-repair scripts:**
   ```bash
   python setup_models.py     # Recreate models
   python check_dependencies.py  # Fix dependencies
   python validate.py          # Run tests
   ```

---

## Success Indicators ✓

When everything is working:

- ✓ `python check_dependencies.py` shows all green checkmarks
- ✓ `python validate.py` shows "PASS" for all 15 tests
- ✓ App starts within 5-10 seconds
- ✓ All 4 sections render with data
- ✓ Sidebar controls are responsive
- ✓ Charts update smoothly
- ✓ No red error messages

**Enjoy the simulation!** 🚀

