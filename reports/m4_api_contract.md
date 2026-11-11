# Milestone 4 API Contract & Telemetry Schema Specification

**System:** Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Version:** 4.0.0  
**Backend Framework:** FastAPI (Python 3.11) with ASGI WebSocket Support  

---

## 1. Tri-Mode Operational Contract

The platform explicitly isolates data provenance into three operating modes:

```
+------------------------------------------------------------------------------------------------+
| OPERATING MODE         | PROVENANCE TAG                | INPUT SOURCE                          |
+------------------------+-------------------------------+---------------------------------------+
| LIVE_HARDWARE          | PHYSICAL_ESP32                | USB Serial COM Port (115200 Baud)     |
|                        | (or PENDING_VERIFICATION)     | (Disabled / Unverified if unplugged)  |
| HISTORICAL_REPLAY      | VERIFIED_RESEARCH_DATASET     | Research CSVs (Multi-Sensor, GasMOS)  |
| SYNTHETIC_SIMULATION   | SYNTHETIC_SIMULATION          | Hazard Engine Scenarios (H01 - H08)   |
+------------------------------------------------------------------------------------------------+
```

---

## 2. REST Endpoints Specification

### 2.1 System & Mode Diagnostics
- `GET /`
  - Response:
    ```json
    {
      "system": "Industrial Gas Hazard Intelligence Platform",
      "version": "4.0.0",
      "status": "OPERATIONAL",
      "supported_modes": ["LIVE_HARDWARE", "HISTORICAL_REPLAY", "SYNTHETIC_SIMULATION"],
      "primary_environment": "General Industrial Manufacturing Factory",
      "live_hardware_connected": false
    }
    ```

### 2.2 Serial Hardware Acquisition
- `GET /api/v1/serial/ports`
  - Enumerates host COM ports and identifies physical USB-UART silicon.
- `POST /api/v1/serial/connect`
  - Body: `{"port": "COM3", "baud_rate": 115200}`
- `POST /api/v1/serial/disconnect`
  - Safely stops background receiver, computes raw stream SHA-256 hash, and writes manifest.

### 2.3 Historical Dataset Replay
- `GET /api/v1/replay/datasets`
  - Returns catalog of available verified research CSVs with row counts and sampling rates.
- `POST /api/v1/replay/load/{dataset_id}`
  - Loads dataset into server memory pointer.
- `GET /api/v1/replay/step?index={optional_index}`
  - Steps through time-series, returning raw records and running server ML inference.

### 2.4 Factory Knowledge Base
- `GET /api/v1/factory/zones`: Returns 8 factory zones (`Z01` through `Z08`).
- `GET /api/v1/industrial/scenarios`: Returns 8 hazard scenarios (`H01` through `H08`).
- `GET /api/v1/industrial/capabilities`: Returns sensor capability bounds.

### 2.5 Real-Time Telemetry Ingestion
- `POST /api/v1/telemetry`
  - Body schema:
    ```json
    {
      "device": "ESP32_GAS_MONITOR",
      "zone_id": "Z03",
      "operating_mode": "HISTORICAL_REPLAY",
      "provenance": "VERIFIED_RESEARCH_DATASET",
      "mq2_adc": 340.0,
      "mq135_adc": 1520.0,
      "temperature": 25.1,
      "humidity": 53.5,
      "mq2_baseline": 338.0,
      "mq135_baseline": 1523.0,
      "edge_prediction": "NORMAL_BASELINE",
      "edge_confidence": 0.99,
      "mq2_slope": 0.0,
      "mq135_slope": 0.0,
      "relay_state": false,
      "fault": false
    }
    ```
  - Evaluates dual inference:
    - Compares `edge_prediction` (ESP32 int8) with `server_prediction` (FastAPI XGBoost).
    - Checks out-of-distribution distance ($z > 4.0\sigma$).
    - Applies Safety Interlock: if `fault == true`, sets `relay_command = false` and `severity = WARNING`.

---

## 3. WebSocket Real-Time Channel

- `WS /ws/telemetry`
  - Connects frontend clients to instant telemetry and incident notification feed.
  - Broadcast payload structure:
    ```json
    {
      "type": "TELEMETRY_UPDATE",
      "data": {
        "event_id": "EVT-1794376000000",
        "severity": "NORMAL",
        "zone_id": "Z03",
        "edge_prediction": "NORMAL_BASELINE",
        "server_prediction": "NORMAL_BASELINE",
        "is_ood": false,
        "relay_command": false,
        "actual_relay_state": false,
        "fault_detected": false,
        "provenance": "VERIFIED_RESEARCH_DATASET"
      }
    }
    ```
