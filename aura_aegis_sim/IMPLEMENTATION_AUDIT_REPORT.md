# AURA-AEGIS Implementation Audit Report

This document outlines the exact state of the currently implemented system in the `aura_aegis_sim` project based on a direct review of the codebase.

## 1. LIST ALL IMPLEMENTED COMPONENTS

*   **Streamlit Web Application (`app.py` & `pages/`)**: A multi-page interactive dashboard covering Homepage, Manual, and Pillars 1 through 4.
*   **SSD Simulator State Machine (`core/ssd_simulator.py`)**: Central simulation engine managing 64 logical blocks, handling P/E cycles, wear leveling, random failures, block retirements, and SMART metric generation.
*   **Bad Block Table Engine (`core/bbt_engine.py`)**: Manages bad block tracking using Bloom filters and Cuckoo hashing.
*   **Hardware Interface (`core/serial_reader.py`)**: A thread-safe serial reader designed to connect via UART (e.g., COM3) to external hardware.
*   **Sensor Mapping & Hardware Predictor (`core/sensor_mapper.py`, `core/hw_predictor.py`)**: Converts raw ADC values into SMART metrics and evaluates hardware health, returning status categories (HEALTHY, WARNING, CRITICAL) and RUL.
*   **Encryption & Security (`crypto/`)**: Contains implementations for AES encryption (`aes_layer.py`) and Shamir Secret Sharing (`shamir_layer.py`).
*   **Various Logic Engines (`core/`)**: Includes `ldpc_engine.py`, `kmap_qmc_engine.py`, `pillar4_engine.py`, `oob_engine.py`, and `smart_engine.py` representing specific subsystems of the SSD.

## 2. EXPLAIN CURRENT FUNCTIONAL FLOW

*   **Input**: The simulation advances via user-triggered ticks (manual or auto-run) or hardware inputs (sensor readings via UART).
*   **Processing**:
    *   During a tick, the `SSDSimulator` performs random writes to good blocks, incrementing their P/E counts.
    *   It simulates ECC corrections based on block wear and random probabilities.
    *   Blocks exceeding typical wear limits or hitting random failure chances are marked as BAD or RETIRED.
    *   The `SensorMapper` translates raw potentiometer readings into SSD metrics (wear, bad blocks, temp).
    *   The `hw_predictor` / LSTM models evaluate current SMART snapshots to compute a Health Score, Failure Probability, and Remaining Useful Life (RUL).
*   **Output**: State changes, event logs, and metric snapshots are rendered in real-time across the Streamlit UI components and visualizations.

## 3. HARDWARE INTEGRATION STATUS

*   **Connected Hardware**: The system is programmed to read from an ESP32 via UART/serial.
*   **Inputs Being Read**: It expects to read a single integer value (0–4095) representing a raw ADC reading (e.g., from a potentiometer). It falls back to a simulated value if the hardware is disconnected.
*   **Outputs Being Controlled**: The `SerialReader` includes a `send_feedback(signal: bytes)` method, capable of sending a single byte to the ESP32 (e.g., to toggle a hardware LED).
*   **Communication**: Communication occurs over a standard serial port (e.g., `COM3` at 115200 baud) managed by PySerial in a separate thread.

## 4. DATA BEING USED

*   **Block Metrics**: P/E count, state (GOOD, BAD, RETIRED, RESERVED, ACTIVE), last written timestamp.
*   **System SMART Metrics**: ECC correction rate, UECC count, bad block count, average P/E, wear level fraction, RBER (Raw Bit Error Rate), simulated temperature, read latency, retry frequency, reallocated sectors, program/erase fails.
*   **Hardware Sensor Data**: Raw ADC values (0–4095), mapped wear % (0-100), mapped temperature (40-50 °C).
*   **Calculated Health Data**: Health Score (0-100), Failure Probability (0.0-1.0), and RUL (days).

## 5. UI / DASHBOARD STATE

*   **Main Dashboard (`app.py`)**: Displays an overarching "HERO" status showing Health Score, RUL, total bad blocks, ECC fixes, wear limits, and simulation mode.
*   **Sidebar**: Contains navigation links, speed controls (1x, 5x, 20x, 100x), simulation mode selectors (normal, stress, aging, crash), preset triggers (Fresh, Mid-Age, Critical, End-Life), and manual fault injection controls.
*   **Pillar Pages**: Each page visualizes specific subsystem states (e.g., 8x8 block grid for wear, charts for SMART parameters, encrypted output displays, logic optimization statistics).

## 6. EVENT HANDLING

*   **Simulation Ticks**: The system handles discrete "Tick Once" commands or an "Auto Run" state.
*   **Fault Injection Events**:
    *   *Force Bad Block*: Manually transition a selected block to BAD.
    *   *Thermal Spike*: Sets the global temperature to 85°C, increasing simulated ECC errors.
    *   *Write Storm*: Injects massive write workloads rapidly advancing block wear.
    *   *Kill Host*: Triggers an immediate transition into 'crash' mode, initiating Out-Of-Band data dumps.
*   **Preset Triggers**: Resets the simulation state to defined boundaries ("Fresh", "Middle-Aged", "End-Life").

## 7. OUTPUT BEHAVIOR

*   **Visual Response**: The Streamlit interface updates instantly on state changes, changing UI element colors (Green -> Yellow -> Red) based on health thresholds. Graphs and 8x8 block grids adjust to display newly collected data.
*   **Logs**: System events (block retirements, ECC escalations, Thermal Spikes) are recorded as timestamped string arrays and displayed in the UI.
*   **Hardware Response**: The system can trigger the feedback mechanism to the ESP32 to signal hardware thresholds (like an LED activation) via the `send_feedback` UART command.
