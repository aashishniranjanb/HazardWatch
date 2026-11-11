# Milestone 5.0 Firmware Safety & Architecture Audit Report

**Project:** Project_A1 — Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Phase:** Milestone 5.0 (Pre-Commissioning Audit & Dual-Build Preparation)  
**Target Hardware:** ESP32 DevKit V1 (ESP32-WROOM-32) + MQ-2 + MQ-135 + DHT11 + Relay Module  
**Operational Policy:** **ZERO FLASHING / UPLOAD OPERATIONS PERFORMED DURING M5.0**  

---

## 1. Executive Summary

Milestone 5.0 resolves the two critical pre-flashing safety and architectural prerequisites identified prior to physical ESP32 commissioning:
1. **Relay Safety Interlock Correction:** Decoupled all automated threshold crossings, model predictions, unknown states, and sensor faults from the relay/air pump actuator. The relay defaults to safe **OFF** (`HIGH` on active-LOW modules) in all automated conditions.
2. **Dual Firmware Release Package:** Packaged two independent, production-grade firmware environments:
   - `PROJECT_A1_ML`: TinyML edge inference build using TensorFlow Lite Micro INT8 ops with automatic rule-based fallback.
   - `PROJECT_A1_BACKUP`: Standalone deterministic rule-based build with **zero dependency on TensorFlow Lite Micro or model headers**.
3. **Exact 11-Feature Parity:** Verified that C++ feature extraction matches the Python ML training pipeline with **0.00000000 max absolute discrepancy**.

---

## 2. Safety Audit: Resolution of Automatic Relay Actuation (Issue 1)

> [!CAUTION]
> **Industrial Atmosphere Safety Mandate:**
> The MQ-2 and MQ-135 sensors are non-certified, low-cost metal oxide semiconductor elements, and the prototype air pump is an unrated DC motor. Operating an ordinary electric motor in an unverified or volatile industrial atmosphere introduces a severe electrical spark/arc ignition hazard.

### Corrections Enforced in Firmware:
- **Default State:** The relay output pin (`GPIO26`) is initialized `HIGH` (Active-LOW off state).
- **Automated Threshold Crossing:** Massive gas spikes ($\text{ADC} \ge 600$ or $\Delta \ge 500$) transition `hazard_state` to `HAZARD_CRITICAL` and emit pattern notifications, but **commanded relay state remains FALSE (Disabled)**.
- **Sensor Faults:** Open circuit or rail short ($\le 5$ or $\ge 4090$ counts) flags `HAZARD_SENSOR_FAULT` and forces relay **OFF**.
- **Out-of-Distribution & ML Predictions:** Model predictions never directly command relay actuation; predictions serve strictly as advisory decision support.
- **Manual Isolation:** Contactor control is isolated strictly to deliberate manual operator overrides.

---

## 3. Dual Firmware Build Architecture (Issue 2)

```
firmware/
├── platformio.ini                  (Unified dual-target configuration)
├── release/
│   ├── PROJECT_A1_ML/              (Build A: Full TinyML Edge Model + Fallback)
│   │   ├── main.cpp                (TFLM interpreter + automatic rule fallback)
│   │   ├── ml_engine.h             (TFLite Micro runner, arena allocation, OOD gate)
│   │   ├── model_config.h          (Arena size: 8 KB, OOD z: 4.0, min conf: 0.60)
│   │   └── models/model_data.h     (INT8 ops model: 5,312 bytes)
│   │
│   └── PROJECT_A1_BACKUP/          (Build B: Non-ML Deterministic Backup)
│       ├── main.cpp                (Standalone deterministic rule engine)
│       ├── rule_engine.h           (Baseline deviation & threshold hazard tiers)
│       └── [NO TENSORFLOW OR MODEL_DATA.H DEPENDENCIES]
```

### Dependency Verification:
- **Build A (`PROJECT_A1_ML`):** Compiles with `TensorFlowLite_ESP32`, `DHT sensor library`, and `ArduinoJson`. Employs circular sliding window, extracts 11 features, standardizes via trained weights, and runs INT8 inference. If tensor allocation fails or input is OOD ($z > 4.0\sigma$), it seamlessly falls back to the local rule engine without halting.
- **Build B (`PROJECT_A1_BACKUP`):** Scanned and confirmed to contain **zero occurrences** of TensorFlow Lite, tensor arenas, or binary model headers. Can be compiled on any standard Arduino ESP32 core without AI libraries.

---

## 4. Hardware Electrical Specifications for M5.1

Prior to flashing in M5.2, the physical test bench must adhere to these verified electrical constraints:

| Component | ESP32 Pin | Interface Type | Electrical Safeguards & Signal Scaling |
| :--- | :--- | :--- | :--- |
| **MQ-2 Analog Output** | `GPIO34` | ADC1_CH6 | Voltage divider required: sensor output ($0–5\text{V}$) scaled to $\le 3.1\text{V}$ (11 dB attenuation). |
| **MQ-135 Analog Output** | `GPIO35` | ADC1_CH7 | Voltage divider required: scaled to $\le 3.1\text{V}$. Dedicated analog ground return. |
| **DHT11 / DHT22** | `GPIO4` | Digital 1-Wire | $4.7\text{k}\Omega$ pull-up to $3.3\text{V}$. Minimum $2.0\text{s}$ polling interval. |
| **Relay Module IN** | `GPIO26` | Digital Output | Optoisolated active-LOW drive. **Keep pump power supply disconnected.** |
| **Sensor Heaters** | VIN / 5V | Power Rail | Requires regulated $5.0\text{V} \pm 0.1\text{V}$, $\ge 1.5\text{A}$ capacity (sensors draw $\sim 180\text{ mA}$ each). |
| **Common Ground** | GND | Common Plane | ESP32 GND, sensor GND, and 5V power supply GND tied together. |
