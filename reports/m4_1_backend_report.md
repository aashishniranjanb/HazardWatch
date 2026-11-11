# Milestone 4.1 Backend Architecture Report

**Version:** 4.5.0  
**Framework:** FastAPI + Uvicorn + SQLite3  
**Scope:** Complete implementation and verification of all 16 specified REST and WebSocket endpoints, SQLite database persistence, telemetry ingestion, multi-model AI inference, deterministic simulation, and incident management.

---

## 1. Endpoints Implemented & Verified

| HTTP Method | Route | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Comprehensive health check (DB, models, modes, simulation) | ✅ 200 OK |
| `GET` | `/api/v1/factory/zones` | Industrial factory zones (`Z01` through `Z08`) | ✅ 200 OK |
| `GET` | `/api/v1/industrial/scenarios` | Hazard scenarios (`H01` through `H08`) | ✅ 200 OK |
| `GET` | `/api/v1/industrial/capabilities` | Sensor capability boundaries | ✅ 200 OK |
| `POST` | `/api/v1/telemetry` | Telemetry ingestion with server ML & safety interlock | ✅ 200 OK |
| `POST` | `/api/v1/inference/predict` | Multi-model live prediction comparison | ✅ 200 OK |
| `GET` | `/api/v1/models` | Metadata catalog of 4 models | ✅ 200 OK |
| `GET` | `/api/v1/models/active` | Active server (XGBoost) and edge (TFLite Micro) models | ✅ 200 OK |
| `GET` | `/api/v1/industrial/incidents` | Active and historical incidents (`INC-xxxx`) | ✅ 200 OK |
| `POST` | `/api/v1/industrial/incidents/{id}/acknowledge` | Operator acknowledgment with audit logging | ✅ 200 OK |
| `POST` | `/api/v1/industrial/incidents/{id}/resolve` | Incident resolution with audit logging | ✅ 200 OK |
| `GET` | `/api/v1/analytics` | Persistent telemetry and incident metrics | ✅ 200 OK |
| `GET` | `/api/v1/events` | Persistent system audit log | ✅ 200 OK |
| `POST` | `/api/v1/simulation/start` | Start deterministic scenario with seed and speed | ✅ 200 OK |
| `POST` | `/api/v1/simulation/stop` | Stop deterministic simulation | ✅ 200 OK |
| `GET` | `/api/v1/simulation/status` | Current simulation timeline and status | ✅ 200 OK |
| `WS` | `/ws/telemetry` | Real-time WebSocket telemetry and incident broadcaster | ✅ Active |

---

## 2. Database Persistence Architecture (`database.py`)

Persistent SQLite database initialized at `backend/industrial_scada.db`:
- **`telemetry` table:** Stores timestamped readings, provenance tag, operating mode, zone ID, sensor raw ADC, server/edge predictions, confidence, OOD flag, severity, and relay commands.
- **`incidents` table:** Tracks `INC-xxxx` lifecycle (`UNVERIFIED`, `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`), gas hazard state, and operator verification notes.
- **`system_events` table:** Audit trail capturing state transitions, threshold crossings, manual overrides, and mode shifts.
- **`simulation_sessions` table:** Audit of deterministic simulation runs.

---

## 3. Safety Interlock Decoupling

In accordance with industrial safety mandates, `POST /api/v1/telemetry` strictly enforces:
```python
if payload.fault:
    incident["relay_command"] = False
    incident["severity"] = "WARNING"
    incident["gas_hazard_state"] = "UNKNOWN"
    incident["recommended_action"] = "Sensor hardware fault detected. Disconnect zone and inspect physical wiring."
```
Sensor faults never activate unrated ventilation fans automatically.
