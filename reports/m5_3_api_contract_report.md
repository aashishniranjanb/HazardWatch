# Project_A1 — Milestone 5.3: API Contract & Route Registry

**Date:** 2026-11-11  
**Protocol:** REST HTTP + WebSocket JSON  
**Base URL:** `http://127.0.0.1:8000`

---

## 1. Verified Route Registry

| Method | Route | Description | Response Schema | Frontend Component |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | System health, database status, loaded models | `{status, timestamp, database, models_loaded, live_hardware_connected}` | `SystemDiagnostics.tsx`, `Header.tsx` |
| `GET` | `/api/v1/serial/status` | Serial connection status and metrics | `{connected, port, baud_rate, last_frame_timestamp, last_error, frames_received, status}` | `SerialManager.tsx`, `SystemDiagnostics.tsx` |
| `GET` | `/api/v1/serial/ports` | Enumerate available host COM ports | `{count, ports: [{port, description, hwid, is_usb_uart}], hardware_verified}` | `SerialManager.tsx`, `SystemDiagnostics.tsx` |
| `POST` | `/api/v1/serial/connect` | Connect backend serial reader | Body: `{port, baud_rate}` $\rightarrow$ `{status: "CONNECTED", port, baud_rate}` | `SerialManager.tsx` |
| `POST` | `/api/v1/serial/disconnect`| Close backend serial reader | `{status: "DISCONNECTED"}` | `SerialManager.tsx` |
| `GET` | `/api/v1/telemetry/live` | Retrieve latest real-time frame | `{status: "LIVE", source: "ESP32_HARDWARE", data: {...}, timestamp}` | `page.tsx` (Live polling loop) |
| `GET` | `/api/v1/telemetry` | Query persisted telemetry history | `{count, records: [...]}` | `HistoricalAnalytics.tsx`, `SensorCharts.tsx` |
| `POST` | `/api/v1/telemetry` | Ingest synthetic or client telemetry | TelemetryPayload $\rightarrow$ Incident assessment | Client integrations |
| `POST` | `/api/v1/inference/predict` | Multi-model ML inference (RF, XGB, MLP) | `{predictions: {...}, primary_prediction, confidence, is_ood}` | `ModelLaboratory.tsx` |
| `GET` | `/api/v1/factory/zones` | List 8 factory zones configuration | Array of Zone objects | `FactoryZoneMonitor.tsx` |
| `GET` | `/api/v1/industrial/incidents` | List persistent industrial incidents | Array of Incident objects | `IncidentIntelligenceCard.tsx` |
| `POST` | `/api/v1/industrial/incidents/{id}/acknowledge` | Acknowledge active incident | `{status: "ACKNOWLEDGED", incident_id}` | `IncidentIntelligenceCard.tsx` |
| `POST` | `/api/v1/industrial/incidents/{id}/resolve` | Resolve active incident | `{status: "RESOLVED", incident_id}` | `IncidentIntelligenceCard.tsx` |
| `GET` | `/api/v1/analytics` | Persistent SCADA summary metrics | `{total_telemetry_records, active_incidents, severity_distribution}` | `HistoricalAnalytics.tsx` |
| `GET` | `/api/v1/events` | Audit trail of hazard and system events| Array of Event objects | `EventLogTable.tsx` |
| `WS` | `/ws/telemetry` | High-frequency telemetry push stream | Real-time JSON frames | `websocket.ts` |
| `WS` | `/ws/sensors` | Companion sensor WebSocket endpoint | Real-time JSON frames | `websocket.ts` |
