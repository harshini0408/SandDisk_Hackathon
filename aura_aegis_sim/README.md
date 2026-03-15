# 🔷 AURA
### Adaptive Unified Resource Architecture

AURA is an intelligent SSD firmware architecture designed to extend the lifespan and reliability of NAND flash storage. By integrating Machine Learning and real-time telemetry, AURA predicts failures, dynamically adjusts ECC (Error Correction Code) thresholds, and securely broadcasts diagnostics.

[**Live Demo (Streamlit)**](https://sanddisk-hackathon.onrender.com) 

---

## 🛠️ Tech Stack Used

This simulation and visualization platform was built entirely using pure Python and its data science ecosystem to rapidly prototype hardware-level firmware logic.

### **Frontend / Simulation UI**
* **[Streamlit](https://streamlit.io/):** The core framework powering the multi-page interactive web application, allowing rapid UI development in Python.
* **[Plotly Graph Objects](https://plotly.com/python/):** Used for rendering highly interactive and responsive time-series graphs, logic matrices, and the architectural connection diagrams.
* **Custom CSS (Injected via Streamlit):** Aggressively overrides Streamlit's base styling to enforce a persistent, responsive Dark Mode that matches standard IDE terminal colors regardless of the host OS system theme.

### **Backend / Machine Learning Engine**
* **[PyTorch](https://pytorch.org/):** Powers Pillar 1's deep learning components. Specifically, it runs the **LSTM (Long Short-Term Memory)** neural network that analyzes sequential SMART data to predict accurate Failure Probabilities and Remaining Useful Life (RUL).
* **[Scikit-Learn](https://scikit-learn.org/):** Powers Pillar 3's regression models. Used specifically for the **Voltage Shift model** which predicts the necessary reference voltage shifts based on block wear and dwell time.
* **[Joblib](https://joblib.readthedocs.io/):** Used to efficiently serialize and load the pre-trained Scikit-Learn `.pkl` models from disk into the Streamlit session state.

### **Data Handling & State Management**
* **[Pandas](https://pandas.pydata.org/):** Used for structuring and formatting raw telemetry data into structured, interactive dataframes (e.g., inside Pillar 2).
* **[NumPy](https://numpy.org/):** Handles the underlying numerical transformations, mathematical calculations for failure probability, and normalizations for the SMART graphs.
* **Streamlit Session State (`st.session_state`):** Acts as the central memory store for the `SSDSimulator` object, allowing the firmware state (bad blocks, wear leveling, etc.) to persist as the user navigates between the different Pillar pages.

---

## 🏗️ Project Structure

The project is structured as a Streamlit multi-page application with decoupled backend simulator logic.

```
aura_aegis_sim/
├── app.py                     # Main dashboard and entry point
├── requirements.txt           # Python dependencies (for Render/cloud deployment)
├── render.yaml                # Infrastructure-as-code configuration for Render deployment
├── .streamlit/
│   └── config.toml            # Enforces dark theme at the framework level
├── pages/                     # Streamlit multi-page interface routing
│   ├── 0_Manual.py            # Overview & usage guide for judges
│   ├── 1_Pillar1.py           # Health Monitoring & Diagnostics (LSTM)
│   ├── 2_Pillar2.py           # NAND Block Management
│   ├── 3_Pillar3.py           # Data Reliability & Error Correction
│   └── 4_Pillar4.py           # Firmware Logic Optimization
├── core/                      # Backend Simulation Engine
│   ├── ssd_simulator.py       # Core state machine (wear leveling, block tracking)
│   ├── smart_engine.py        # SMART attribute tracking and event logs
│   ├── bbt_engine.py          # Bad Block Table logic (Bloom filters, Cuckoo hashes)
│   ├── ldpc_engine.py         # Simulated Error Correction logic
│   └── lstm_predictor.py      # PyTorch model loader and inference engine
├── models/                    # Serialized Machine Learning artifacts
│   ├── lstm_model.pt          # PyTorch checkpoint
│   └── voltage_model.pkl      # Scikit-learn random forest model
├── crypto/                    # Over-the-air security logic
│   └── aes_ccm.py             
└── sections/                  # UI component modules (for Pillar 1 & 2)
```

---

## 🚀 Running Locally

To run the AURA simulator on your local machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/harshini0408/SandDisk_Hackathon
   cd aura_aegis_sim
   ```

2. **Create a virtual environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On macOS: source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Streamlit App:**
   ```bash
   streamlit run app.py
   ```
   *The application will automatically open in your default web browser at `http://localhost:8501`.*
