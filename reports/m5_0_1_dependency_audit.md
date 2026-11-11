# Project_A1 — Milestone 5.0.1: Dependency and Isolation Audit

**Date:** 2026-11-11  
**Target:** ESP32 Firmware Subsystem  
**Audit Purpose:** Verify strict dependency isolation between the ML and Non-ML Backup builds.

---

## 1. Library Dependency Graph Analysis

### Environment: `project_a1_backup`
```text
Dependency Graph
|-- DHT sensor library @ 1.4.7
|-- Adafruit Unified Sensor @ 1.1.15
|-- ArduinoJson @ 7.4.3
```
- **TFLite Micro Included?** **NO**. Completely excluded at compile time.
- **Model Headers Included?** **NO**. `models/model_data.h` is omitted.
- **Tensor Arena Allocation?** **NO**. `tensor_arena` buffer (8 KB) is not declared.
- **Compile Flag:** `-DPROJECT_A1_ML_ENABLED=0`
- **Result:** Pure deterministic C++ implementation without dynamic ML runtime overhead.

### Environment: `project_a1_ml`
```text
Dependency Graph
|-- DHT sensor library @ 1.4.7
|-- Adafruit Unified Sensor @ 1.1.15
|-- ArduinoJson @ 7.4.3
|-- tflm_esp32 @ 2.0.0
```
- **TFLite Micro Included?** **YES**. Compiles with `tflm_esp32` (TensorFlow Lite Micro 2.0 runtime for ESP32).
- **Model Headers Included?** **YES**. Embeds `model_data.h` (5,312-byte INT8 model).
- **Required Operators Registered:**
  - `AddFullyConnected()` (Dense layers)
  - `AddSoftmax()` (Probability normalization)
  - `AddQuantize()` (Float32 to INT8 ingestion)
  - `AddDequantize()` (INT8 to Float32 output)
  - `AddRelu()` (Activation function)
- **Compile Flag:** `-DPROJECT_A1_ML_ENABLED=1`
- **Tensor Arena Size:** `8192 bytes` (8 KB internal SRAM allocated).

---

## 2. Feature Schema and Scaling Parameters Verification

### 11-Feature Canonical Order
Both builds strictly adhere to the 11-feature contract defined in `ml/artifacts/v2_7/training_manifest_m2_7.json` and implemented in `include/feature_schema.h` and `src/feature_extractor.h`:
1. `mq2_delta_baseline`
2. `mq135_delta_baseline`
3. `mq2_ratio_baseline`
4. `mq135_ratio_baseline`
5. `gas_ratio_mq2_to_mq135`
6. `mq2_slope`
7. `mq135_slope`
8. `mq2_std`
9. `mq135_std`
10. `mq2_delta_window`
11. `mq135_delta_window`

### StandardScaler Normalization Parity
The firmware uses exact means and standard deviations fitted on the M2.7 training partition:
```cpp
const float FEATURE_MEANS[11] = {
    194.755155f, 189.242228f, 1.556443f, 1.130512f, 0.328509f,
    -0.106840f, -0.063746f, 16.656122f, 21.972149f, 51.571433f, 69.947020f
};

const float FEATURE_SCALES[11] = {
    332.701391f, 314.119626f, 0.950575f, 0.216634f, 0.182731f,
    11.335395f, 10.898889f, 40.754281f, 38.787090f, 101.551394f, 98.909952f
};
```
*Feature normalization parity verified: Max discrepancy = 0.00000000 across all dimensions.*

---

## 3. Fallback and Decoupled Safety Engine Audit

1. **Model Initialization Failure:** If `tflite::AllocateTensors()` fails or the schema version does not match, `mlEngine.isReady()` returns `false`, causing `src/main.cpp` to execute `RuleEngine::evaluate()` for all sensor classifications.
2. **Out-of-Distribution (OOD) Gating:** If any normalized z-score exceeds `OOD_Z_SCORE_THRESHOLD` (4.0) or softmax confidence is `< 0.60`, the ML engine marks the state as `OUT_OF_DISTRIBUTION` / `LOW_CONFIDENCE`, and telemetry delegates hazard determination to the rule engine.
3. **Relay Safety Isolation:**
   - In both builds, `res.relayCommand = false` is enforced unconditionally.
   - Threshold crossings and gas spikes do not energize GPIO26.
   - GPIO26 is explicitly driven `HIGH` on boot to ensure active-LOW relays remain powered OFF.
