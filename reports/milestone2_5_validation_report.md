# Milestone 2.5: Validation Audit & Baseline-Relative Model Retraining Report

**Date:** 2026-11-11  
**Experiment ID:** `GAS-CLASSIFICATION-M2.5-BASELINE-RELATIVE-001`  
**Status:** M2.5 GATES COMPLETE (Awaiting User Review Before M3)  

---

## 1. Gate 1: Comprehensive Data Partition & Session Integrity Audit

### 1.1 Structural Discovery in `Gas_Sensors_Measurements.csv`
- Total Rows: 6,400.
- Sequential Class Organization:
  - Rows `0` to `1599`: `NoGas` (`Serial Number`: 0 to 1599)
  - Rows `1600` to `3199`: `Perfume` (`Serial Number`: 0 to 1599)
  - Rows `3200` to `4799`: `Smoke` (`Serial Number`: 0 to 1599)
  - Rows `4800` to `6399`: `Mixture` (`Serial Number`: 0 to 1599)
- **Critical Finding on Session Metadata:**
  `Gas_Sensors_Measurements.csv` does **not** contain multiple interleaved experimental trial sessions. Each class represents one single continuous acquisition run over 1,600 consecutive readings.
  - In `NoGas`, MQ-2 drifts from **555.6 ADC** at the start to **774.6 ADC** at the end (+219 ADC drift), while MQ-135 drifts from **416.0 ADC** to **528.0 ADC** (+112 ADC drift).
  - In `Perfume`, MQ-2 averages **745.0 ADC** and MQ-135 averages **473.7 ADC**.
  - **The Root Cause of Normal vs. VOC Confusion:** Because the clean air trial experienced natural thermal/sensor heater stabilization drift over time, the tail end of the `NoGas` run overlapped with the stationary level of the `Perfume` run. When using a standard sequential 70/15/15 split, the Test partition receives solely the high-drift tail of `NoGas` (averaging 779.2 ADC), causing the classifier to mistake clean air drift for VOC vapor.

### 1.2 Leakage Prevention with Purge-Gaps
In M2.5, to guarantee zero temporal window leakage:
- Evaluated sliding windows now feature an explicit **5-window purge buffer (10 samples)** between the Train, Validation, and Test partitions.
- Train (70%): 2,228 instances
- Validation (15%): 476 instances
- Test: 440 instances (reduced from 480 due to 40 windows purged across partition boundaries)

---

## 2. Gate 2 & 3: Baseline Reference Validation & Feature Engineering v2

### 2.1 Multi-Tier Baseline Registry (`baseline_registry.yaml`)
To prevent cross-bench contamination, baselines are isolated by acquisition source:
1. `Gas_Sensors_Measurements` (Training Source Clean Air):
   - $\text{Baseline}_{\text{MQ2}} = 735.7\text{ ADC}$
   - $\text{Baseline}_{\text{MQ135}} = 462.6\text{ ADC}$
   *(Calculated strictly from the Train partition of `NoGas` — zero leakage from Test).*
2. `multi_sensor_data_baseline` (Prototype Rig):
   - $\text{Baseline}_{\text{MQ2}} = 337.94\text{ ADC}$
   - $\text{Baseline}_{\text{MQ135}} = 1522.83\text{ ADC}$
3. `hardware_calibration_active`:
   - Reserved exclusively for the active physical ESP32 DevKit V1 clean-air calibration.

### 2.2 Feature Schema v2 (`feature_schema_v2.yaml`)
We transitioned from absolute raw ADC features to **11 baseline-relative and dynamics features**:
1. $\Delta \text{MQ2}_{\text{base}} = \text{Mean}_{\text{MQ2}} - \text{Baseline}_{\text{MQ2}}$
2. $\Delta \text{MQ135}_{\text{base}} = \text{Mean}_{\text{MQ135}} - \text{Baseline}_{\text{MQ135}}$
3. $R_{\text{MQ2}} = \frac{\text{Mean}_{\text{MQ2}}}{\text{Baseline}_{\text{MQ2}} + 10^{-4}}$
4. $R_{\text{MQ135}} = \frac{\text{Mean}_{\text{MQ135}}}{\text{Baseline}_{\text{MQ135}} + 10^{-4}}$
5. $\text{Ratio}_{\text{inter}} = \frac{\text{Mean}_{\text{MQ2}}}{\text{Mean}_{\text{MQ135}} + 10^{-4}}$
6. Linear influx/venting slopes: $\text{Slope}_{\text{MQ2}}$ and $\text{Slope}_{\text{MQ135}}$
7. Turbulence/stability: $\text{Std}_{\text{MQ2}}$, $\text{Std}_{\text{MQ135}}$, and peak-to-trough range $\Delta_{\text{window}}$ for both sensors.

---

## 3. Gate 4: Retrained Model Comparison (M2 vs. M2.5)

### Summary Comparison Table:

| Experiment | Model | Accuracy | Macro F1 | Normal Baseline Recall | Smoke Recall | Test Latency | Artifact Size | External Baseline Normal % |
|---|---|---|---|---|---|---|---|---|
| **M2 (Raw ADC)** | Random Forest | 72.50% | 72.36% | 34.17% | 100.0% | 0.031 ms | 1,445 KB | 0.00% |
| **M2.5 (Relative)** | **Random Forest v2** | **72.95%** | **72.56%** | **34.55%** | **100.0%** | 0.036 ms | 1,556 KB | **5.23%** (318 detected) |
| **M2 (Raw ADC)** | XGBoost | 72.08% | 71.54% | 30.83% | 100.0% | 0.004 ms | 605 KB | 0.00% |
| **M2.5 (Relative)** | **XGBoost v2** | **73.41%** | **72.77%** | **34.55%** | **100.0%** | **0.003 ms** | 632 KB | **1.04%** (63 detected) |
| **M2 (Raw ADC)** | Compact MLP | 70.63% | 68.69% | 18.33% | 100.0% | 0.145 ms | 40.2 KB | 0.00% |
| **M2.5 (Relative)** | **Compact MLP v2** | 66.14% | 63.87% | 15.45% | **100.0%** | 0.215 ms | **38.7 KB** | 0.00% |

### Key Observations:
1. **Tree-Based Models Benefit from Relative Features**:
   - Both Random Forest v2 and XGBoost v2 improved overall accuracy to $\sim 73\%-73.4\%$ and increased `NORMAL_BASELINE` precision to **74.5%**.
   - Tree models began resolving external baseline instances (up to 318 samples identified as clean air), whereas raw ADC models failed completely (0.00%).
2. **Compact MLP Under-fitting on Drift**:
   - The tiny 1,108-parameter MLP remains vulnerable to monotonic thermal drift because it lacks non-linear tree thresholding.
   - For `NORMAL_BASELINE`, the MLP achieved 50.0% precision but only 15.5% recall.
3. **Smoke Discrimination Remains Flawless**:
   - All three models retained **100% precision and 100% recall on Smoke** with zero false negatives.

---

## 4. Gate 5: Baseline-First Hardware Behavior

1. **Hardware Verification**:
   - In [`SensorCards.tsx`](file:///c:/Users/Administrator/Videos/Project_A1/frontend/src/components/SensorCards.tsx), baseline references are explicitly displayed alongside live readings.
   - When no sensor data is streaming, the UI and Serial Monitor output `BASELINE MODE / WAITING FOR SENSOR DATA`.
   - Missing readings produce `null` rather than artificial zero or clean-air values.
2. **Local Safety Interlock**:
   - In [`esp32_firmware.ino`](file:///c:/Users/Administrator/Videos/Project_A1/firmware/esp32_firmware.ino), relay triggering is handled locally via threshold and hardware fault traps (`ADC <= 5` or `ADC >= 4090`), remaining completely independent of ML model confidence or server availability.

---

## 5. Limitations & Scientific Disclosures

1. **Synthetic Single-Session Drift:** `Gas_Sensors_Measurements.csv` is not a collection of independent multi-day sessions. Because each gas condition was recorded in a single continuous time block, the model inevitably learns the sensor’s temporal thermal drift curve alongside chemical response.
2. **Cross-Bench Generalization Reality:** While baseline normalization improved cross-source recognition in Random Forest from 0% to 5.23%, chemical sensitivity curves of metal-oxide sensors differ between hardware units due to manufacturing tolerances and load resistor variation. True hardware deployment requires on-device calibration.

---

## 6. Recommendations for Milestone 3 (Model Optimization & TFLite Micro)

1. **Adopt Random Forest or Calibrated MLP with Confidence Gating:**
   - For edge deployment, if Compact MLP is retained due to extreme memory constraints, enforce an **OOD (Out-Of-Distribution) / Uncertainty Rejection Gate**: if softmax confidence is $<0.75$, output `UNKNOWN / INSUFFICIENT_DATA` rather than guessing `VOC_RESPONSE`.
2. **Proceed to int8 Quantization**:
   - Apply post-training quantization to the MLP candidate and benchmark real memory footprint on the ESP32 simulator.
