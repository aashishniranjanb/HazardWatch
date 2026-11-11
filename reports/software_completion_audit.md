# Software Completion Audit & Gap Analysis Report

**Project:** Project_A1 — Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Phase:** Software-First Completion Program (M4.1 through M4.7)  
**Rule in Effect:** **NO FLASHING OR UPLOADING TO ESP32 DURING THIS PHASE**. Physical integration is strictly deferred to Milestone 5.

---

## 1. Repository Inventory & Maturity Assessment

| Subsystem / Path | Key Files / Modules | Maturity Status | Gap / Required Expansion |
| :--- | :--- | :--- | :--- |
| **Backend** (`backend/`) | `main.py`<br>`app/services/industrial_hazard_engine.py`<br>`incident_manager.py`<br>`server_inference_service.py`<br>`historical_replay_service.py`<br>`serial_acquisition.py` | 🟡 Functional prototype (v4.0.0) | Needs: SQLite DB persistence (`database.py`), full API contract (`/api/v1/health`, `/models`, `/models/active`, `/analytics`, `/events`, `/simulation/*`, `/inference/predict`), deterministic simulation engine service. |
| **Frontend** (`frontend/`) | Next.js 14 App Router, 12 SCADA components (`SensorCards`, `FactoryZoneMonitor`, `EventLogTable`, `RiskAndVentilation`, etc.) | 🟡 Build passes, 6 screens active | Needs expansion into all **11 dedicated screens** (Plant Overview, Factory Zones, Live Monitoring, AI Intelligence, Incident Management, Ventilation, Analytics, Simulation Lab, Dataset Explorer, Model Lab, Diagnostics). |
| **Simulation & Replay** (`ml/` & `backend/`) | `synthetic-scenarios.ts`, `historical_replay_service.py`, `feature_schema_v2.yaml` | 🟡 Split logic | Backend needs a unified `simulation_engine.py` with 10 deterministic factory profiles (`NORMAL_BASELINE`, `COMBUSTIBLE_RESPONSE_PATTERN`, `VOC_RESPONSE`, `SMOKE_RESPONSE`, `MIXTURE`, `SENSOR_DRIFT_WARNING`, `SENSOR_FAULT`, `VENTILATION_FEEDBACK_UNAVAILABLE`, `OFFLINE_MODE`, `UNKNOWN_OOD`). |
| **Serial Communication** (`backend/app/services/serial_acquisition.py`, `frontend/src/lib/serial.ts`) | Port scanner, line buffering, Web Serial API client | 🟡 Logic implemented | Needs recorded serial fixtures and mock serial streams for automated testing without hardware. |
| **AI Software Integration** (`ml/artifacts/`) | XGBoost v2.7 (`xgboost_m2_7.joblib`), Compact MLP (`compact_mlp_m2_7.keras`), INT8 TFLite (`compact_mlp_int8_ops.tflite`), Scaler & Encoder | 🟢 High parity, multi-model loaded | Expose multi-model comparison endpoint (`/api/v1/inference/predict` comparing RF, XGBoost, Float32 MLP, INT8 TFLite Micro ops). |
| **Firmware Readiness** (`firmware/`) | `esp32_firmware.ino`<br>`m3_benchmark.ino`<br>`models/model_data.h` (5,312 bytes) | 🟢 Complete code, decoupled safety | Verify feature extraction order against `feature_schema_v2.yaml`, document C++ contract, and package for M5 release without flashing. |
| **Regression Tests** (`tests/`) | 10 existing Python test suites | 🟢 10 suites existing | Add M4 end-to-end regression tests covering DB persistence, simulation transitions, serial mock fixtures, and model lab. |

---

## 2. Operating Modes & Data Provenance Protocol

All modules strictly adhere to four distinct operating modes:

```
[ DATA ORIGIN MODES ]
  1. LIVE_HARDWARE         -> Provenance: PHYSICAL_ESP32 (or PENDING_VERIFICATION)
                              Explicitly unverified / disconnected until real USB-UART link established.
  2. HISTORICAL_REPLAY     -> Provenance: VERIFIED_RESEARCH_DATASET
                              Multi-sensor rig, clean-air baseline, MOS research bench.
  3. SYNTHETIC_SIMULATION  -> Provenance: SYNTHETIC_GENERATED
                              10 deterministic factory hazard response scenarios.
  4. OFFLINE_MODE          -> Provenance: LOCAL_CACHE_STORE
                              Standalone client operation without server connection.
```

---

## 3. Detailed Software Completion Roadmap (M4.1 – M4.7)

1. **M4.1 Backend Completion:** Implement SQLite database (`backend/app/services/database.py`), comprehensive telemetry schemas, model registry service (`model_registry_service.py`), deterministic simulation service (`simulation_service.py`), and all 16 required REST + WS endpoints.
2. **M4.2 Frontend Completion:** Expand Next.js dashboard to all 11 SCADA screens with responsive UI, live mode watermarks, historical trend analytics, and model laboratory.
3. **M4.3 Simulation & Historical Replay:** Backend + frontend deterministic simulation engine supporting 10 industrial profiles with configurable seed, speed, and event timelines.
4. **M4.4 Communication Layer:** Web Serial API parser, partial line buffering, mock serial streaming fixtures, and disconnection/reconnection state machines.
5. **M4.5 AI Software Integration:** Multi-model comparative inference service (`ServerInferenceService` comparing RF, XGBoost, Float32 MLP, and INT8 TFLite ops).
6. **M4.6 System-Wide Validation:** Comprehensive test suites across backend, database, simulation, serial fixtures, and Next.js production build.
7. **M4.7 Firmware Readiness:** Verification of ESP32 C++ firmware against exact 11-feature order and TFLite model data header; export firmware release bundle without flashing.
