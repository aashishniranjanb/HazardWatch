# Project_A1 — Milestone 5.3: Live Integration Audit & Communications Repair

**Date:** 2026-11-11  
**Milestone:** M5.3 Live Hardware Integration & SCADA Communications Repair  
**Target Device:** ESP32 DevKit V1 (ESP32-D0WD-V3, MAC `b0:cb:d8:0f:a2:2c`)  
**Serial Link:** `COM4` (CH340 USB-UART, 115,200 baud)  
**Backend:** FastAPI `127.0.0.1:8000` (Process ID `17964`)  
**Frontend:** Next.js 14 SCADA Dashboard `http://localhost:3000`  
**Status:** **100% REPAIRED & OPERATIONAL**

---

## 1. Executive Summary

Milestone 5.3 resolves the port contention, serial ownership conflicts, and dashboard communication breakdowns identified during initial hardware bring-up:

1. **Sole Serial Ownership Enforced:** FastAPI is established as the **sole physical reader of `COM4`**. The frontend no longer attempts to independently open `COM4` via the browser Web Serial API, eliminating "Failed to open port" contention.
2. **Telemetry Pipeline Restored:** ESP32 telemetry frames are captured line-buffered by FastAPI, validated, persisted in SQLite (`telemetry` table), and broadcast live to the Next.js SCADA dashboard over REST and WebSocket.
3. **Sensor Fault Integrity Maintained:** The firmware correctly identifies that `MQ-2` is active (`mq2_adc: ~695` to `717`), while `MQ-135` (`GPIO35`) and `DHT11` (`GPIO4`) are absent/unwired. These missing readings are transmitted strictly as `null` and displayed as `SENSOR_FAULT` / `DISCONNECTED`, never falsified as clean air.
4. **Relay Safety Lock:** Relay output remains strictly `false` / `DISABLED` (GPIO26 HIGH). Sensor faults and threshold crosses never trigger emergency ventilation.

---

## 2. Root Cause Analysis & Corrections

| Issue | Root Cause | Implemented Correction | Verified Behavior |
|---|---|---|---|
| **Port Contention (`Failed to open port`)** | The browser's Web Serial API and FastAPI both attempted to open `COM4` simultaneously. Physical OS COM ports are mutually exclusive. | Rewrote `SerialManager.tsx` to interface exclusively with FastAPI's serial endpoints. Web Serial direct port opening was removed in backend-managed mode. | Zero port contention. FastAPI manages COM4 cleanly, and dashboard reflects backend link state. |
| **Backend Telemetry Polling 404/405** | `/api/v1/telemetry` was only registered as `POST`. `GET /api/v1/telemetry` and `GET /api/v1/telemetry/live` were missing. | Added `GET /api/v1/telemetry` (with `limit` query param) and `GET /api/v1/telemetry/live` in `backend/main.py`. | HTTP 200 OK. Dashboard and REST clients successfully retrieve recent and live records. |
| **Serial Status Endpoint Missing** | Frontend could not inspect backend serial connection health or frames received. | Added `GET /api/v1/serial/status` exposing `connected`, `port`, `baud_rate`, `frames_received`, `last_frame_timestamp`, and `last_error`. | Frontend updates connection badges every 3s with exact frame counters. |
| **Telemetry Parser Field Mismatch** | ESP32 firmware emits `"device_id": "PROJECT_A1_ESP32_01"`, but Python parser required `"device" in data`. | Updated `_process_line()` in `serial_acquisition.py` to accept both `"device"` and `"device_id"`. | 100% of incoming serial frames are parsed, logged to `.jsonl`, and forwarded to SQLite. |
| **Clipped SENSOR FAULT UI Text** | Flex child in `SensorCards.tsx` lacked wrapping and truncation controls on narrow viewports. | Added `flex-wrap`, `min-w-0`, and `truncate` classes to fault banners. | Responsive text rendering on mobile and desktop without clipping. |
