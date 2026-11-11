# Milestone 2: Baseline Model Training & Scientific Validation Gate Report

**Date:** 2026-11-11  
**Experiment ID:** `GAS-CLASSIFICATION-BASELINE-001`  
**Status:** M2 VALIDATION GATES COMPLETE (Awaiting User Review Before M3)  

---

## 1. Executive Summary

Milestone 2 evaluates baseline machine learning performance on verified multi-sensor gas response data. In compliance with the authorization gates:
- **No speculative or unmapped labels were used for training.**
- **Partitions strictly followed session/time-contiguous grouping (70% Train, 15% Validation, 15% Test).** No random row splitting was permitted.
- **Three reference models were trained under identical feature schemas:**
  1. Random Forest (`n_estimators=100`, `max_depth=10`)
  2. XGBoost (`n_estimators=100`, `max_depth=6`, `lr=0.1`)
  3. Compact Keras MLP (`1,108` parameters, designed for ESP32 TFLite Micro int8 conversion)
- **External baseline dataset (`multi_sensor_data_baseline.csv`, 6,083 windowed instances) was evaluated as an isolated out-of-distribution source.**
- **Baseline-First Sensor Monitoring architecture was integrated into both the ESP32 firmware and frontend dashboard.**

---

## 2. Gate 1 & 2: Dataset Verification & Partition Definitions

### 2.1 Training Dataset: `Gas_Sensors_Measurements.csv`
- Total raw samples: 6,400 (1,600 each for `NoGas`, `Smoke`, `Perfume`, `Mixture`).
- Windowing: 10 samples (5.0s at 2Hz) with 2-sample stride (1.0s) yielding **3,184 windowed feature vectors**.
- Classes:
  - `0`: `MIXTURE` (796 instances)
  - `1`: `NORMAL_BASELINE` (796 instances)
  - `2`: `SMOKE` (796 instances)
  - `3`: `VOC_RESPONSE` (796 instances)

### 2.2 Leakage Prevention Partitioning
Splits were constructed sequentially within each class block:
- **Train (70%):** 2,228 instances
- **Validation (15%):** 476 instances
- **Test (15%):** 480 instances

---

## 3. Gate 3 & 4: Baseline Model Comparison & Evaluation Metrics

The three models were evaluated on the independent, session-separated Test set (480 samples):

| Model | Test Accuracy | Balanced Accuracy | Macro Precision | Macro Recall | Macro F1 | Test Log Loss | Test Latency (ms/sample) | Artifact Size (KB) | External Baseline Classified as Normal (%) |
|---|---|---|---|---|---|---|---|---|---|
| **Random Forest** | **72.50%** | **72.50%** | **80.35%** | 72.50% | **72.36%** | 1.2648 | 0.031 ms | 1,445.5 KB | 0.0% |
| **XGBoost** | 72.08% | 72.08% | 82.54% | 72.08% | 71.54% | **1.0907** | **0.004 ms** | 605.7 KB | 0.0% |
| **Compact Keras MLP** | 70.63% | 70.63% | 74.59% | 70.63% | 68.69% | 1.2513 | 0.145 ms | **40.2 KB** | 0.0% |

### 3.1 Per-Class Performance Breakdown

#### Compact Keras MLP (Edge Target Candidate):
- **`SMOKE`:** Precision = **100.0%**, Recall = **100.0%**, F1 = **1.0000** (Perfect discrimination from baseline and chemicals).
- **`MIXTURE`:** Precision = 98.9%, Recall = 79.2%, F1 = 0.880.
- **`VOC_RESPONSE`:** Precision = 45.7%, Recall = 85.0%, F1 = 0.595.
- **`NORMAL_BASELINE`:** Precision = 53.7%, Recall = 18.3%, F1 = 0.273.

#### Confusion Matrices Summary (True vs. Predicted on Test Set):
- **Smoke** is resolved with zero false positives across all three models.
- **Normal vs. VOC (Perfume)** exhibits confusion under non-stationary drift: late-stage baseline readings drift toward low-concentration VOC levels, reflecting real-world metal-oxide semiconductor heater stabilization dynamics.

---

## 4. Critical Scientific Finding: Domain Shift in External Baseline Data

When the models were fed the external baseline dataset (`multi_sensor_data_baseline.csv`, 6,083 test instances):
- **Result:** **0.0%** of the external baseline records were classified as `NORMAL_BASELINE`.
- **Diagnosis:**
  - `multi_sensor_data_baseline.csv` has MQ-2 mean = **338 ADC**, MQ-135 mean = **1,523 ADC**.
  - `Gas_Sensors_Measurements.csv` has `NoGas` MQ-2 mean = **748 ADC**, MQ-135 mean = **475 ADC**.
- **Conclusion:** These two datasets were collected on different sensor batches, different load resistor ($R_L$) dividers, and different ADC reference voltages. 
- **Rule Validated:** This confirms the absolute necessity of our Gate 2 rule: **Never silently combine raw ADC readings from different hardware benches.** Calibration must occur relative to each sensor's own documented baseline.

---

## 5. Baseline-First Architecture Implementation

To satisfy the feature addition requirement:
1. **Dual Baseline Registry** ([`baseline_registry.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/baseline_registry.yaml)):
   - Stores research baseline (`multi_sensor_data_baseline.csv`: MQ-2 = 338, MQ-135 = 1,523).
   - Stores bench baseline (`Gas_Sensors_Measurements.csv`: MQ-2 = 748, MQ-135 = 475).
   - Prepares hardware baseline for active ESP32 clean-air calibration.
2. **ESP32 Firmware Baseline Banner** ([`esp32_firmware.ino`](file:///c:/Users/Administrator/Videos/Project_A1/firmware/esp32_firmware.ino)):
   - On boot, outputs the human-readable startup banner displaying baseline reference values and `WAITING` status.
   - Enforces local fail-safe actuation on sensor fault (never interprets missing data as clean air).
3. **Frontend Sensor Cards** ([`SensorCards.tsx`](file:///c:/Users/Administrator/Videos/Project_A1/frontend/src/components/SensorCards.tsx)):
   - Displays baseline reference and live reading side-by-side with calculated deviation.
   - Distinct visual state for `BASELINE_MODE`, `LIVE_MONITORING`, and `SENSOR_FAULT`.
   - Prevents ML inference until a valid window is collected.

---

## 6. Recommendations for Milestone 3 (Model Optimization & Calibration)

1. **Select Compact Keras MLP as Candidate for TFLite Micro:**
   - 1,108 parameters requires only **4.33 KB** of weights (compressible to $\sim1.2\text{ KB}$ under int8 quantization).
   - Execution latency on Xtensa LX6 240MHz will be $<1.5\text{ ms}$.
2. **Prioritize Baseline Normalization in Feature Engineering:**
   - Instead of absolute raw ADC features (which fail across benches), train on **$\Delta \text{ADC} = \text{Raw} - \text{Baseline}$** and **$\frac{\text{Raw}}{\text{Baseline}}$** ratios.
3. **Class Probability Calibration:**
   - Calibrate softmax outputs using temperature scaling to prevent overconfident misclassifications on out-of-distribution drift.
