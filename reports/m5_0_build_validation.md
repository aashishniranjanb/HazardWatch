# Milestone 5.0 Dual-Build Compilation & Validation Report

**Project:** Project_A1 — Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Framework:** Arduino Core for ESP32 / PlatformIO Build Specification  
**Flashing State:** **ZERO UPLOADS EXECUTED — RELEASE PACKAGES VALIDATED ON DISK**  

---

## 1. Release Package Manifest

Both builds are packaged in dedicated directories ready for physical flashing:

### Build A: `firmware/release/PROJECT_A1_ML/`
- **Target Microcontroller:** ESP32 DevKit V1 (ESP32-WROOM-32)
- **Source Files:** `main.cpp`, `adc_manager.h`, `dht_manager.h`, `baseline_manager.h`, `signal_processor.h`, `feature_extractor.h`, `rule_engine.h`, `ml_engine.h`, `relay_manager.h`, `telemetry_manager.h`
- **Model Byte Array:** `models/model_data.h` (5,312 bytes, INT8 ops)
- **Tensor Arena Allocation:** 8,192 bytes ($8\text{ KB}$ internal SRAM)
- **Build Flag:** `-DPROJECT_A1_ML_ENABLED=1`
- **Libraries Required:** `TensorFlowLite_ESP32`, `DHT sensor library`, `ArduinoJson`
- **Compilation Command:**
  ```bash
  pio run -e project_a1_ml
  ```

### Build B: `firmware/release/PROJECT_A1_BACKUP/`
- **Target Microcontroller:** ESP32 DevKit V1 (ESP32-WROOM-32)
- **Source Files:** `main.cpp`, `adc_manager.h`, `dht_manager.h`, `baseline_manager.h`, `signal_processor.h`, `feature_extractor.h`, `rule_engine.h`, `relay_manager.h`, `telemetry_manager.h`
- **Dependencies Removed:** **Zero TensorFlow Lite Micro dependency, zero model header dependency**
- **Build Flag:** `-DPROJECT_A1_ML_ENABLED=0`
- **Libraries Required:** `DHT sensor library`, `ArduinoJson`
- **Compilation Command:**
  ```bash
  pio run -e project_a1_backup
  ```

---

## 2. Test Verification Matrix (13 / 13 Passed)

| Suite Name | Target Module | Scope | Status |
| :--- | :--- | :--- | :--- |
| `test_m5_0_feature_parity.py` | C++ Feature Extractor | Bit-exact feature math & normalization ($< 10^{-7}$) | ✅ PASSED |
| `test_esp32_firmware_logic.py` | Firmware Core Logic | Rule engine, sensor fault decoupling, JSON schema | ✅ PASSED |
| `test_serial_communication.py` | Serial Acquisition | Line buffer, partial chunk assembly, malformed JSON | ✅ PASSED |
| `test_m4_system_validation.py` | Full Software Stack | 16 API endpoints, SQLite DB, simulation, models | ✅ PASSED |
| `test_m4_api_integration.py` | FastAPI Routing | Telemetry ingestion, safety interlocks, replay | ✅ PASSED |
| `test_m3_quantization.py` | TFLite INT8 Model | Quantization manifest, 100% test parity | ✅ PASSED |
| `test_m3_5_hardware.py` | Baseline Schema | Model input compatibility, baseline statistics | ✅ PASSED |
| `test_m2_7_generalization.py` | Synthetic Generalization | Cross-device generalization on M2.7 corpus | ✅ PASSED |
| `test_m2_5_validation.py` | Baseline-Relative Features | 5-window purge-gap validation | ✅ PASSED |
| `test_m2_baseline.py` | Baseline Models | Random Forest, XGBoost, Compact MLP | ✅ PASSED |
| `test_industrial_intelligence.py`| Hazard Engine | 8 zones, 8 scenarios, incident workflow | ✅ PASSED |
| `test_dataset_intelligence.py` | Dataset Inventory | CSV adapters, label registry, feature schemas | ✅ PASSED |
| `test_backend.py` | Backend Bridge | Status and WebSocket endpoints | ✅ PASSED |

---

## 3. Milestone 5.0 Exit Gate Verification

- [x] **Relay Safety Behavior Corrected:** Contactor command forced to disabled (`relayCommand = false`) in all automated threshold crossings and sensor faults.
- [x] **Dual Builds Prepared:** Both `PROJECT_A1_ML` and `PROJECT_A1_BACKUP` packaged. Backup build confirmed free of TensorFlow dependencies.
- [x] **C++ vs. Python Feature Parity:** 33 / 33 test comparisons verified with 0.00000000 max discrepancy.
- [x] **Serial Telemetry Protocol Aligned:** Verified JSON formatting with `null` fields for missing readings.
- [x] **Flashing Restriction Strictly Preserved:** Zero firmware uploads performed. Ready for M5.1 physical hardware inspection.
