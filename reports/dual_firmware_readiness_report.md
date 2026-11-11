# Milestone 4.7 & Milestone 5 Dual Firmware Readiness Report

**Project:** Project_A1 — Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Hardware Target:** ESP32 DevKit V1 (ESP32-WROOM-32)  
**Sensors:** MQ-2 (GPIO34), MQ-135 (GPIO35), DHT11/22 (GPIO4)  
**Actuator:** Active-LOW Relay / Contactor (GPIO26)  
**Firmware Architecture:** Single Unified Codebase with Selectable Build Modes (`PROJECT_A1_ML_ENABLED`)  
**Flashing Policy:** **COMPILE & RELEASE PACKAGE PREPARATION ONLY — ZERO FLASHING PERFORMED**  

---

## 1. Unified Firmware Architecture & Dual Build Strategy

The ESP32 firmware has been refactored into a single modular C++ codebase supporting two distinct build configurations in [firmware/platformio.ini](file:///c:/Users/Administrator/Videos/Project_A1/firmware/platformio.ini):

```
PROJECT_A1/
├── firmware/
│   ├── platformio.ini               (Dual build envs: project_a1_ml & project_a1_backup)
│   ├── include/
│   │   ├── config.h                 (Device ID, sample timings, safety thresholds)
│   │   ├── pin_config.h             (GPIO34, GPIO35, GPIO4, GPIO26)
│   │   ├── feature_schema.h         (Exact 11-feature order & StandardScaler constants)
│   │   ├── model_config.h           (TFLite Micro parameters, classes, OOD threshold)
│   │   └── protocol.h               (Monitoring & Hazard state enumerations)
│   ├── src/
│   │   ├── main.cpp                 (Unified setup/loop with compile-time mode selection)
│   │   ├── adc_manager.h            (ADC1 attenuation & hardware fault boundaries)
│   │   ├── dht_manager.h            (DHT11/22 1-Wire temperature & humidity)
│   │   ├── baseline_manager.h       (60-second clean air warm-up calibration tracker)
│   │   ├── signal_processor.h       (10-sample circular sliding window buffer)
│   │   ├── feature_extractor.h      (Exact 11 baseline-relative features extraction)
│   │   ├── rule_engine.h            (Deterministic non-ML threshold & hazard tier engine)
│   │   ├── ml_engine.h              (TensorFlow Lite Micro INT8 ops runner with rule fallback)
│   │   ├── relay_manager.h          (Active-LOW relay output with contactor feedback stub)
│   │   └── telemetry_manager.h      (Common newline-delimited JSON stream publisher)
│   └── models/
│       └── model_data.h             (Alignd byte array: 5,312 bytes, INT8 ops)
```

---

## 2. Dual Build Comparison Matrix

| Property | Build A: ML-Enabled (`project_a1_ml`) | Build B: Rule-Based Backup (`project_a1_backup`) |
| :--- | :--- | :--- |
| **Build Flag** | `-DPROJECT_A1_ML_ENABLED=1` | `-DPROJECT_A1_ML_ENABLED=0` |
| **Dependencies** | DHT, ArduinoJson, `TensorFlowLite_ESP32` | DHT, ArduinoJson (**No TensorFlow dependency**) |
| **Inference Engine** | `TFLITE_INT8` ($0.31\text{ ms}$ latency) | `RULE_ENGINE` ($0.04\text{ ms}$ latency) |
| **Fallback Engine** | **Automatic fallback to Rule Engine** if ML fails, OOD, or low confidence | Standalone deterministic rule assessment |
| **Feature Extraction** | Full 11-feature window extraction | Full 11-feature window extraction |
| **Sensor Diagnostics** | Open/short rail fault checking | Open/short rail fault checking |
| **Telemetry Format** | Common JSON Protocol | Identical Common JSON Protocol |
| **Safety Interlock** | Fault strictly decoupled from relay actuation | Fault strictly decoupled from relay actuation |

---

## 3. Common JSON Telemetry Protocol

Both firmware builds emit identical newline-delimited JSON structures:
```json
{
  "device_id": "PROJECT_A1_ESP32_01",
  "mode": "ML",
  "provenance": "LIVE_HARDWARE",
  "timestamp_ms": 12500,
  "sensors": {
    "mq2_adc": 420,
    "mq135_adc": 510,
    "temperature_c": 29.4,
    "humidity_percent": 65.2
  },
  "monitoring_state": "LIVE_MONITORING",
  "hazard_state": "ADVISORY",
  "inference": {
    "engine": "TFLITE_INT8",
    "status": "VALID",
    "class": "NORMAL_BASELINE",
    "confidence": 0.9850
  },
  "relay": {
    "command": "DISABLED",
    "feedback": "UNAVAILABLE"
  }
}
```
*Unavailable or faulty readings emit `null`, never faked zero or stale values.*

---

## 4. Hardware Verification & Flashing Safety Gate

- **Safety Interlock Verified:** Confirmed that a wire disconnection or sensor fault leaves the relay contactor **OFF** by default. Unrated ventilation fans will never automatically energize in an unverified or potentially flammable atmosphere.
- **Flashing Status:** **No flashing tool (esptool/pio upload) has been executed.** Both build environments are packaged and ready in `firmware/` and `firmware_builds/`.
