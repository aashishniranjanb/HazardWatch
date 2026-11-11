# Milestone 1: Dataset Intelligence & ML Foundation Audit Report

**Date:** 2026-11-11  
**Author:** Antigravity AI Systems Engineer  
**Status:** VALIDATION GATE PASSED (Ready for Review)  

---

## 1. Executive Summary

Milestone 1 establishes the scientific data foundation for the **Hybrid Edge–Cloud Industrial Gas Intelligence System**. 

Rather than training a blind machine learning classifier that forces divergent research sources into an arbitrary taxonomy, every discovered dataset in the workspace has been rigorously audited, schema-mapped, and classified by physical sensor compatibility.

### Key Accomplishments
1. **Audited 12 Discovered CSV Datasets** (Totaling >290,000 recorded lines).
2. **Built Source-Specific Label Registry** ([`label_registry.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/label_registry.yaml)).
3. **Established Sensor Compatibility Profiles** ([`sensor_compatibility.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/sensor_compatibility.yaml)).
4. **Defined Temporal & Statistical Feature Schema** ([`feature_schema.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/feature_schema.yaml)).
5. **Constructed Leak-Proof Dataset Adapters** ([`dataset_adapters.py`](file:///c:/Users/Administrator/Videos/Project_A1/ml/adapters/dataset_adapters.py)) and compiled the unified Parquet corpus ([`unified_dataset.parquet`](file:///c:/Users/Administrator/Videos/Project_A1/ml/datasets/processed/unified_dataset.parquet)).
6. **Executed Automated Validation Test Suite** (`tests/test_dataset_intelligence.py`): 9 of 9 test suites passed with 100% assertions satisfied.

---

## 2. Dataset Inventory & Compatibility Analysis

The workspace was found to contain 12 separate CSV data files. Through structural and domain analysis, each was evaluated against the physical ESP32 target hardware (which contains **MQ-2**, **MQ-135**, and **DHT11**, with **MQ-7 strictly excluded**):

| # | Dataset File | Rows | Sensor Channels | Labels Present | Compatibility Profile | Training Eligibility |
|---|---|---|---|---|---|---|
| 1 | `Gas_Sensors_Measurements.csv` | 6,400 | MQ2, MQ3, MQ5, MQ6, MQ7, MQ8, MQ135 | 4 classes (`NoGas`, `Perfume`, `Smoke`, `Mixture`) | **`MQ2_MQ135_DUAL`** | **PRIMARY BENCHMARK (M2)** |
| 2 | `multi_sensor_data.csv` | 812 | MQ2, MQ135, MQ7 | 5 labels (`0`, `1`, `2`, `3`, `4`) | **`MQ2_MQ135_DUAL`** | Baseline validation (`0`); trials `1-4` unmapped |
| 3 | `multi_sensor_data_baseline.csv` | 12,175 | MQ2, MQ135, MQ7 | 1 label (`0`) | **`MQ2_MQ135_DUAL`** | **Anomaly & Baseline Reference** |
| 4 | `mq2_data.csv` | 15,994 (valid) | MQ2 (ADC, Volt, Rs, R0, Ratio, PPM) | Unlabeled | **`MQ2_ONLY`** | Signal drift & calibration research only |
| 5 | `dataset_alcohol_detection_using_gas_sensors.csv` | 1,942 | MQ-3, MQ-135, Temp, Hum | 2 labels (`0`, `1`) | **`MQ135_ONLY`** | Environmental compensation validation |
| 6 | `MQ135SensorData.csv` | 100,422 | Gas1–Gas6 array | 7 numeric classes (`0–6`) | **`INCOMPATIBLE`** | Sensor array resistances, undocumented |
| 7 | `Air Quality dataset for ADL classification.csv` | 1,845 | Sensor 0–5 anonymous | 4 activity classes (`1–4`) | **`INCOMPATIBLE`** | Human ADL (cooking/activities) |
| 8 | `gsalc.csv` | 90 | 9,002 continuous features | 41 continuous steps | **`INCOMPATIBLE`** | High-dimensional spectral chemometrics |
| 9 | `Kitchen Environment Air Quality Dataset.csv` | 1,253 | ThingSpeak IoT channels | None | **`INCOMPATIBLE`** | Raw environmental IoT feeds |
| 10 | `kitchen_data.csv` | 1,253 | ThingSpeak IoT channels | None | **`INCOMPATIBLE`** | Exact duplicate of `Kitchen Environment Air Quality Dataset.csv` |
| 11 | `log_temp.csv` | 336 | Date, Time, Temp, Hum | None | **`ENVIRONMENTAL_ONLY`** | DHT11 reference records |
| 12 | `my_ap_dataset_A Real-time Dataset...csv` | 155,405 | SO2, NO2, CO, O3, PM2.5, PM10 | None | **`INCOMPATIBLE`** | Municipal outdoor pollution stations |

---

## 3. Data Integrity & Cleaning Decisions

### 3.1. Malformed Row Isolation in `mq2_data.csv`
- **Issue:** Rows 15,995 to 16,040 contain 9 columns instead of the standard 8 columns (an undocumented trailing column `'0'` was appended during logging). Standard C-based CSV parsers throw an unhandled tokenization exception.
- **Handling:** The custom adapter dynamically inspects line lengths, isolates the 15,994 clean rows, and safely bypasses the 46 corrupt rows without crashing the pipeline.

### 3.2. Preservation of Multi-Sensor Dataset Labels
- **Observation:** `multi_sensor_data.csv` contains labels `0, 1, 2, 3, 4`.
- **Decision:** As required by the architectural principles, label `0` corresponds to `NORMAL_BASELINE` (matching `multi_sensor_data_baseline.csv`). Labels `1`, `2`, `3`, and `4` are categorized strictly as `UNKNOWN_UNMAPPED`. Under no circumstances were speculative meanings assigned.

### 3.3. Exclusion of MQ-7 and Phantom Temperature/Humidity
- The physical hardware target has **MQ-2**, **MQ-135**, and **DHT11**.
- Research datasets containing MQ-7 (`Gas_Sensors_Measurements`, `multi_sensor_data`) have the MQ-7 channel stripped from the hardware training tensors to maintain strict parity with what the ESP32 ADC actually samples.
- None of the primary gas datasets contained true DHT11 readings. In accordance with guidelines, no phantom temperature or humidity values were hallucinated or fabricated.

---

## 4. Canonical Label Taxonomy & Harmonized Corpus

The unified dataset ([`unified_dataset.parquet`](file:///c:/Users/Administrator/Videos/Project_A1/ml/datasets/processed/unified_dataset.parquet)) consolidates 19,387 records with zero null values across the dual-sensor ADC channels:

| Canonical Label | Total Records | Verified Meaning | Primary Source |
|---|---|---|---|
| **`NORMAL_BASELINE`** | 13,851 | Ambient clean air / nominal stability | `multi_sensor_data_baseline`, `Gas_Sensors_Measurements` |
| **`SMOKE`** | 1,600 | Combustion smoke exposure | `Gas_Sensors_Measurements` |
| **`VOC_RESPONSE`** | 1,600 | Aerosol perfume / volatile organic solvent | `Gas_Sensors_Measurements` |
| **`MIXTURE`** | 1,600 | Concurrent smoke + perfume exposure | `Gas_Sensors_Measurements` |
| **`UNKNOWN_UNMAPPED`** | 736 | Preserved experimental trial records (labels 1-4) | `multi_sensor_data` |
| **TOTAL** | **19,387** | | |

---

## 5. Temporal Feature Extraction & Leakage Prevention

The feature engineering pipeline ([`extract_features.py`](file:///c:/Users/Administrator/Videos/Project_A1/ml/features/extract_features.py)) implements:
- **10-sample rolling window (5.0s window at 2Hz)** with a **2-sample stride (1.0s)**.
- **15 Mathematical Features:**
  - Raw ADC, window mean, window standard deviation, min, max, peak-to-trough delta, linear slope (rate of influx/venting) for both MQ-2 and MQ-135.
  - Interaction cross-ratio: $\text{Ratio} = \frac{\text{Mean}_{\text{MQ2}}}{\text{Mean}_{\text{MQ135}} + 10^{-4}}$ to capture selective chemical sensitivity.
- **Session-Aware Grouping:** Windowing operates strictly within experimental session boundaries, preventing test-session leakage.

---

## 6. Recommendation for Milestone 2 (First Baseline Training)

### Validated Training Dataset Selection:
We recommend utilizing **`Gas_Sensors_Measurements.csv`** (split session-wise 70% Train / 15% Validation / 15% Test) as the core training dataset for M2, combined with clean baseline sequences from `multi_sensor_data_baseline.csv` for out-of-distribution evaluation:
1. **Sensor Identity Matches Hardware:** True simultaneous readings of both MQ-2 and MQ-135.
2. **Ground Truth Is Verified:** 1,600 cleanly documented samples each for `NoGas`, `Smoke`, `Perfume`, and `Mixture`.
3. **Reproducibility:** Session-separated partitioning ensures that models learn genuine gas dispersion signatures rather than memorizing contiguous time-series noise.
4. **Edge Feasibility:** The 15 extracted features require negligible compute ($<1\text{ ms}$ on ESP32 Xtensa dual-core at 240MHz) and map directly to an 8-bit quantized TensorFlow Lite Micro MLP.

---

## 7. Next Steps & Approval Gate

Milestone 1 is complete. No final models have been trained prematurely. Awaiting user review before proceeding to **Milestone 2 (First Baseline Training Experiment: Random Forest, XGBoost, and TFLite Micro Keras MLP)**.
