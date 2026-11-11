# Milestone 4.5 AI Software Integration Report

**Subsystem:** Multi-Model Edge AI & Server ML Service  
**Features:** 11-Feature Exact Order per `feature_schema_v2.yaml`  

---

## 1. Multi-Model Architecture (`multi_model_service.py`)

The platform loads and compares 4 machine learning models simultaneously on every telemetry window:

| Model ID | Framework | Role | Quantization | Latency Est. |
| :--- | :--- | :--- | :--- | :--- |
| **`xgboost_v2_7`** | XGBoost / Scikit-Learn | Primary Server Inference | Float32 | $0.85\text{ ms}$ |
| **`random_forest_v2_7`** | Scikit-Learn | Ensemble Comparison | Float32 | $1.20\text{ ms}$ |
| **`compact_mlp_float32`** | TensorFlow / Keras | Server Deep Neural Network | Float32 | $1.45\text{ ms}$ |
| **`compact_mlp_int8_edge`** | TFLite Micro | Edge Target Reference | INT8 Ops | $0.31\text{ ms}$ |

---

## 2. Feature Schema & Normalization Order

Features are extracted and normalized strictly in accordance with `feature_schema_v2.yaml`:
1. `mq2_delta_baseline` (ADC counts)
2. `mq135_delta_baseline` (ADC counts)
3. `mq2_ratio_baseline` (dimensionless)
4. `mq135_ratio_baseline` (dimensionless)
5. `gas_ratio_mq2_to_mq135` (dimensionless cross-ratio)
6. `mq2_slope` (ADC/s rate of change)
7. `mq135_slope` (ADC/s rate of change)
8. `mq2_std` (turbulent stability)
9. `mq135_std` (turbulent stability)
10. `mq2_delta_window` (peak-to-trough range)
11. `mq135_delta_window` (peak-to-trough range)

---

## 3. Out-of-Distribution Gating ($z > 4.0\sigma$)

If incoming normalized sensor features exceed $4.0$ standard deviations from the training distribution, the system overrides any model output to `UNKNOWN_OOD`, preventing false confident predictions on unexpected atmospheric contaminants.
