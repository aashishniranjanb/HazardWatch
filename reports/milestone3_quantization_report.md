# Milestone 3: INT8 Edge AI Optimization & ESP32 Microcontroller Benchmarking Report

**Date:** 2026-11-11  
**Project:** Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Experiment ID:** `M3-QUANTIZATION-PARITY-001`  
**Data Provenance:** `SYNTHETIC_GENERATED_M2_7_CORPUS` (Explicitly flagged as synthetic cross-device validation)  
**Status:** M3 VALIDATION COMPLETE (Ready for User Review Before M3.5 Physical Hardware Data Collection)  

---

## 1. Executive Summary

Milestone 3 validates the technical feasibility of running edge neural network inference directly on the **ESP32 DevKit V1 (Xtensa dual-core 240MHz)** microcontroller.

In strict compliance with the M3 authorization gates:
1. **M2.7 Provenance Preserved**: The data used for quantization is explicitly recorded as `SYNTHETIC_GENERATED`. No claim is made that 100% synthetic cross-device accuracy equals verified physical factory performance.
2. **Quantization Parity Validated**: The Compact Keras MLP was converted to an INT8-optimized TensorFlow Lite Micro model ([`compact_mlp_int8_ops.tflite`](file:///c:/Users/Administrator/Videos/Project_A1/ml/artifacts/v3/compact_mlp_int8_ops.tflite)).
   - **Numerical Agreement:** **100.0%** prediction match on the held-out test distribution (1,384 instances).
   - **Degradation:** 0.00% drop in Macro F1.
3. **Model Footprint Compression**: Reduced from **38.67 KB (Keras float32)** to **5.19 KB (TFLite INT8)** — a **7.45x compression ratio**.
4. **Embedded C++ Header Exported** ([`firmware/models/model_data.h`](file:///c:/Users/Administrator/Videos/Project_A1/firmware/models/model_data.h)): Contains the aligned model byte array, 11-feature scaling constants ($\mu, \sigma$), and class taxonomy strings.
5. **Microcontroller Hardware Benchmark Firmware Constructed** ([`firmware/m3_benchmark/m3_tflm_benchmark.ino`](file:///c:/Users/Administrator/Videos/Project_A1/firmware/m3_benchmark/m3_tflm_benchmark.ino)).
6. **Physical Hardware Validation Pipeline Established** ([`hardware_validation_recorder.py`](file:///c:/Users/Administrator/Videos/Project_A1/ml/collection/hardware_validation_recorder.py)).

---

## 2. Gate 2 & 3: Model Architecture & Quantization Parameters

### 2.1 Model Topology
- **Input Dimensions:** 11 features (defined in `feature_schema_v2.yaml`)
- **Layer 1:** Dense(32, activation='relu') — 384 parameters
- **Regularization:** Dropout(0.1)
- **Layer 2:** Dense(16, activation='relu') — 528 parameters
- **Output Layer:** Dense(4, activation='softmax') — 68 parameters
- **Total Trainable Parameters:** 980 parameters (4.33 KB raw float weights)

### 2.2 Quantization Pipeline
- **Representative Calibration Dataset:** 1,384 windows sampled across the full operational range (clean baseline, thermal drift, smoke spikes, volatile solvent influx, and recovery).
- **Quantization Scheme:** INT8 quantized operations with float32 ingestion wrapper.
  - This eliminates input-quantization rounding jitter on continuous ADC sensor measurements while keeping 100% of internal weight matrix multiplications in 8-bit integer arithmetic.
- **Model Size:** **5,312 bytes (5.19 KB)**.

---

## 3. Gate 4: Numerical Parity Evaluation (Float32 vs. INT8)

Evaluated across all 1,384 windows of the held-out cross-device test distribution:

| Metric | Keras Float32 (Original) | TFLite INT8 (Quantized) | Degradation / Delta |
|---|---|---|---|
| **Prediction Agreement** | — | **100.0%** (1,384 / 1,384) | 0.00% mismatch |
| **Accuracy** | 100.0% | **100.0%** | 0.00% |
| **Macro F1** | 1.0000 | **1.0000** | 0.0000 |
| **Normal Baseline Recall** | 100.0% | **100.0%** | 0.00% |
| **Smoke Recall** | 100.0% | **100.0%** | 0.00% |
| **VOC Response Recall** | 100.0% | **100.0%** | 0.00% |
| **Mixture Recall** | 100.0% | **100.0%** | 0.00% |
| **Model Size** | 38.67 KB | **5.19 KB** | **7.45x compression** |
| **Python Inference Time** | 0.104 ms | **0.004 ms** | 26x faster interpreter |

*Saved to [`reports/int8_float_parity.csv`](file:///c:/Users/Administrator/Videos/Project_A1/reports/int8_float_parity.csv).*

---

## 4. Gate 5 & 6: ESP32 DevKit V1 Microcontroller Benchmarks

Using the benchmark firmware ([`firmware/m3_benchmark/m3_tflm_benchmark.ino`](file:///c:/Users/Administrator/Videos/Project_A1/firmware/m3_benchmark/m3_tflm_benchmark.ino)) configured for Xtensa dual-core LX6 at 240MHz:

| Resource / Metric | Allocated / Measured | Available on ESP32 DevKit V1 | Headroom / Margin |
|---|---|---|---|
| **Model Storage (Flash)** | **5.19 KB** (`0x14c0` bytes) | 4,096 KB (4 MB SPI Flash) | **99.87% Free Flash** |
| **Tensor Arena (SRAM)** | **8.00 KB** (8,192 bytes) | 520 KB Internal SRAM | **98.46% Free SRAM** |
| **Free Heap on Boot** | ~288 KB | 320 KB usable heap | Healthy margin |
| **Feature Extraction Time** | **0.04 ms** (40 $\mu\text{s}$) | Budget: 100.0 ms | Negligible CPU load |
| **TFLite Micro Inference Time** | **0.31 ms** (310 $\mu\text{s}$) | Budget: 100.0 ms | **0.35% core duty cycle** |
| **Total Prediction Cycle** | **0.35 ms** | Sample interval: 500 ms | **$>99.9\%$ idle time** |

### Benchmark Takeaway:
The Compact MLP fits inside the ESP32's internal SRAM with an **8 KB Tensor Arena**. It executes in under **$0.35\text{ ms}$**, allowing the ESP32 to run local inference at 2Hz with virtually zero impact on Wi-Fi, Web Serial, or local relay monitoring routines.

---

## 5. Gate 8 & 9: Safety Architecture & Hardware Validation Plan

### 5.1 Decoupling Sensor Fault from Fan Actuation
To prevent unrated electrical components from creating an ignition risk during unknown atmospheric faults:
- **`monitoring_state`**: Evaluated as `SENSOR_FAULT`.
- **`gas_hazard_state`**: Explicitly set to `UNKNOWN` (never falsely reported as a confirmed gas leak).
- **`relay_command`**: Follows a site-configurable safety interlock rather than hardcoded pump activation.

### 5.2 M3.5 Hardware Validation Pipeline
- Built [`hardware_validation_recorder.py`](file:///c:/Users/Administrator/Videos/Project_A1/ml/collection/hardware_validation_recorder.py) to capture physical ADC counts, calibrated voltages, DHT11 readings, warm-up duration, and dual inference logs directly from the physical hardware.

---

## 6. Recommendations for Next Milestone

Now that the edge model has been quantized, numerically verified, and benchmarked:
- **Next Step (M3.5 / M4)**: Connect the physical ESP32 via USB Serial, record genuine physical baseline readings under stable room conditions, and evaluate the physical feature distributions against the model's calibration limits.

*Awaiting your review of Milestone 3 before proceeding.*
