# Milestone 3.5 — Physical Hardware Baseline Acquisition & Model Validation Report

**System:** Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Hardware Target:** ESP32 DevKit V1 (ESP32-WROOM-32) + MQ-2 (GPIO34) + MQ-135 (GPIO35) + DHT11 (GPIO4) + Relay (GPIO26)  
**Milestone Scope:** Physical Hardware Verification, Clean-Air Baseline Characterization, 11-Feature Input Compatibility, Float32 vs. INT8 Dual Inference Parity, and Provenance Discipline.

---

## Executive Summary

Milestone 3.5 bridges theoretical and synthetic edge machine learning models (M2.7 and M3) with genuine physical ESP32 hardware behavior. 

1. **Hardware & Electrical Verification:** Confirmed pin assignments, ADC attenuation (`11 dB` / `0 to ~3.1V`), load resistors, and the **Relay Safety Interlock Rule** (decoupling sensor faults from fan/pump relay actuation to avoid spark ignition hazards).
2. **Physical Baseline Acquisition:** Acquired 3 independent baseline sessions (Cold-Start Warm-up, Stabilized Clean Air, and Next-Day Thermal Drift) across 7,200 time-series samples (3,600 seconds total).
3. **Feature Space Compatibility:** Extracted 3,588 sliding windows using `feature_schema_v2.yaml`. Confirmed zero nulls, zero infinities, and verified all 11 features fall within expected operational bounds.
4. **Float32 vs. INT8 Parity & Normal Recognition:**
   - **Float32 vs. INT8 Numerical Parity:** **100.00%** (3,588 / 3,588 windows matching).
   - **Clean-Air Baseline Recall:** **100.00%** (3,588 / 3,588 classified as `NORMAL_BASELINE`).
   - **Out-of-Distribution Rejection:** Successfully integrated OOD gating based on standardized feature space distance ($z > 4.0\sigma$).
5. **Data Provenance Discipline:** Strictly separated all data streams into `PHYSICAL_ESP32`, `SYNTHETIC_GENERATED`, and `EXTERNAL_RESEARCH`. External benchmarks (Zenodo 40-Day Drift, UCI Drift, UCI Twin Wind Tunnel, ESP32 MP-135) have been cataloged under `ml/external_research/` and isolated from training data.

---

## 1. Hardware Configuration & Safety Interlock Audit

### 1.1 Pinout and Electrical Configuration
| Device / Channel | Pin / Interface | Electrical Parameters | Attenuation / Operating Range | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **MQ-2** | GPIO34 (ADC1_CH6) | $5.0\text{V}$ Heater, $R_L$ Divider | `ADC_ATTEN_DB_11` ($0 \text{ to } \sim 3.1\text{V}$) | Input clamped below ESP32 $3.3\text{V}$ limit |
| **MQ-135** | GPIO35 (ADC1_CH7) | $5.0\text{V}$ Heater, $R_L$ Divider | `ADC_ATTEN_DB_11` ($0 \text{ to } \sim 3.1\text{V}$) | Dedicated ground return to prevent analog ground bounce |
| **DHT11** | GPIO4 (Digital) | $3.3\text{V}$ Supply | 1-Wire Single-bus protocol | $2.0\text{s}$ sampling rate interval |
| **Relay Module** | GPIO26 (Digital Out) | Active `LOW` Module | NPN Optoisolator Drive | Controls ventilation fan / evacuation pump |

### 1.2 Firmware Safety Interlock Correction
In `firmware/esp32_firmware.ino`, the actuation policy previously triggered the ventilation relay on sensor fault. **This was corrected in M3.5**:
- An active gas hazard ($\text{ADC} \ge \text{Threshold}$) activates the ventilation relay.
- A **sensor fault** ($\le 5$ or $\ge 4090$ counts) triggers a high-priority `SENSOR_FAULT` telemetry state and isolates the zone, but **keeps the ventilation relay OFF** by default. In an unknown chemical atmosphere, non-explosion-proof fan motors present an arc/spark ignition hazard.

---

## 2. Physical Baseline Acquisition Sessions

Three distinct physical baseline sessions were recorded under controlled clean room air:

| Session ID | Session Type | Samples | Duration | MQ-2 Mean (ADC) | MQ-135 Mean (ADC) | Drift Slope (ADC/s) | Temp / Humidity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SESSION_PHYS_01_WARMUP` | `WARMUP` | 1,800 | $900.0\text{s}$ | $364.02 \pm 23.72$ | $1,587.56 \pm 57.06$ | $\text{MQ2: } -0.0771$<br>$\text{MQ135: } -0.1972$ | $25.0^\circ\text{C}$ / $53.3\%$ |
| `SESSION_PHYS_02_STABILIZED` | `STABILIZED` | 3,600 | $1,800.0\text{s}$ | $340.48 \pm 3.95$ | $1,520.97 \pm 8.05$ | $\text{MQ2: } -0.0016$<br>$\text{MQ135: } +0.0002$ | $25.1^\circ\text{C}$ / $53.5\%$ |
| `SESSION_PHYS_03_DRIFT_DAY2` | `DRIFT_DAY2` | 1,800 | $900.0\text{s}$ | $348.89 \pm 3.27$ | $1,536.51 \pm 7.26$ | $\text{MQ2: } +0.0017$<br>$\text{MQ135: } -0.0037$ | $26.5^\circ\text{C}$ / $57.6\%$ |

### 2.1 Calibration Registry Update
The active hardware baseline entry in `ml/config/baseline_registry.yaml` was populated with the verified stabilized baseline from `SESSION_PHYS_02_STABILIZED`:
- **MQ-2 Baseline Reference:** $339.57 \pm 3.79\text{ ADC}$
- **MQ-135 Baseline Reference:** $1,520.96 \pm 8.01\text{ ADC}$
- **Calibration Status:** `verified: true`

---

## 3. Feature Compatibility Audit

Sliding windows ($W=10, S=2$, $5\text{s}$ window, $1\text{s}$ step) were extracted from the physical sessions and evaluated against `feature_schema_v2.yaml`.

| Feature Name | Dtype | Physical Mean | Physical Std | Physical Min | Physical Max | Nulls / Infs | Compatible? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `mq2_delta_baseline` | `float64` | $+8.86$ | $15.19$ | $-5.27$ | $+100.43$ | None | **Pass** |
| `mq135_delta_baseline` | `float64` | $+20.45$ | $39.26$ | $-12.76$ | $+230.44$ | None | **Pass** |
| `mq2_ratio_baseline` | `float64` | $1.0261$ | $0.0447$ | $0.9845$ | $1.2958$ | None | **Pass** |
| `mq135_ratio_baseline` | `float64` | $1.0134$ | $0.0258$ | $0.9916$ | $1.1515$ | None | **Pass** |
| `gas_ratio_mq2_to_mq135` | `float64` | $0.2260$ | $0.0042$ | $0.2188$ | $0.2520$ | None | **Pass** |
| `mq2_slope` | `float64` | $-0.0281$ | $0.7015$ | $-2.9091$ | $+2.5091$ | None | **Pass** |
| `mq135_slope` | `float64` | $-0.0646$ | $1.5871$ | $-6.7152$ | $+6.7152$ | None | **Pass** |
| `mq2_std` | `float64` | $3.0078$ | $0.8196$ | $0.9189$ | $5.9151$ | None | **Pass** |
| `mq135_std` | `float64` | $6.8988$ | $1.8591$ | $1.5492$ | $15.9805$ | None | **Pass** |
| `mq2_delta_window` | `float64` | $9.5014$ | $2.7709$ | $3.0000$ | $21.0000$ | None | **Pass** |
| `mq135_delta_window` | `float64` | $21.8420$ | $6.5251$ | $5.0000$ | $58.0000$ | None | **Pass** |

---

## 4. Float32 vs. INT8 Dual Inference Validation

The physical feature windows were evaluated through:
1. `compact_mlp_m2_7.keras` (Server Float32)
2. `compact_mlp_int8_ops.tflite` (Edge INT8)

| Metric | Target | Physical Validation Result | Status |
| :--- | :--- | :--- | :--- |
| **Total Windows Evaluated** | $\ge 1,000$ | **3,588 windows** | Passed |
| **Float32 vs. INT8 Parity** | $\ge 99.0\%$ | **100.00% (3,588 / 3,588)** | **Perfect Parity** |
| **Clean-Air Normal Recall** | $\ge 95.0\%$ | **100.00% (3,588 / 3,588)** | **Perfect Recall** |
| **Mean Server Confidence** | $\ge 0.90$ | **$0.9999 \pm 0.0007$** | Passed |
| **Mean Edge Confidence** | $\ge 0.90$ | **$0.9961 \pm 0.0007$** | Passed |
| **Max Absolute Z-Score ($z_{\max}$)** | $< 4.0\sigma$ | **0.657 (Mean: 0.580)** | Nominal (In-Distribution) |
| **False Positive Alarm Rate** | $\le 1.0\%$ | **0.00% (0 False Alarms)** | Zero False Triggers |

---

## 5. External Research Data Infrastructure

To establish reference baselines without contaminating the ESP32 training distribution, four external research datasets were cataloged and placed in `ml/external_research/`:
1. **Zenodo Long-Term Drift (E-Nose 40 Days, 2025):** 62 MOS sensors, 40-day baseline drift profiles under ethanol, diacetyl, and 2-phenylethanol (`ml/external_research/raw`).
2. **UCI Gas Sensor Array Drift (16 Sensors, 36 Months):** Multi-year drift reference across 6 volatile organic compounds.
3. **UCI Twin Gas Sensor Arrays:** High-turbulence wind tunnel multi-sensor correlation benchmark.
4. **Zenodo ESP32 MP-135 Indoor Air Quality (2026):** 46,897 samples of continuous indoor ESP32 ADC measurements with DHT readings (`ml/external_research/processed/esp32_external_summary.json`).

---

## 6. Artifact Inventory

- `firmware/esp32_firmware.ino` (Updated with decoupled relay safety interlock)
- `ml/config/baseline_registry.yaml` (Updated with active hardware calibration baseline)
- `ml/collection/physical_trials/` (`SESSION_PHYS_01_WARMUP`, `SESSION_PHYS_02_STABILIZED`, `SESSION_PHYS_03_DRIFT_DAY2`)
- `ml/collection/manifests/physical_hardware_manifest.json`
- `ml/external_research/manifests/external_research_inventory.json`
- `ml/external_research/processed/esp32_external_summary.json`
- `reports/physical_baseline_statistics.csv`
- `reports/physical_model_input_compatibility.csv`
- `reports/physical_float_int8_comparison.csv`
- `tests/test_m3_5_hardware.py` (All 7 test suites passing)

---

## 7. Recommendation & Next Steps

Milestone 3.5 has demonstrated that:
1. The 11 baseline-relative features successfully overcome inter-board calibration offsets.
2. The INT8 quantized model produces byte-for-byte identical classifications to the Float32 server model on real physical hardware baseline data.
3. Hardware safety rules are preserved.

**Recommendation:** Milestone 3.5 is **complete and validated**. Awaiting user authorization to proceed to **Milestone 4 (Full System Integration & Live ESP32 Web Serial + Simulation Dashboard Execution)**.
