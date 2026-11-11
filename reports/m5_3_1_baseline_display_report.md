# Project_A1 — Milestone 5.3.1: Baseline-Aware Dashboard & Missing-Sensor Display Report

**Timestamp:** 2026-11-11  
**Target Hardware:** ESP32 DevKit V1 (COM4, 115200 baud)  
**Status:** VALIDATED & COMPLIANT  

---

## 1. Executive Summary

Milestone 5.3.1 resolves the critical SCADA dashboard presentation and telemetry contract requirements for degraded hardware environments where one or more physical sensors are disconnected or faulted.

During hardware validation on `COM4`, the physical prototype streams valid ADC counts from **MQ-2 (GPIO34)** (~226–279 ADC), while **MQ-135 (GPIO35)** and **DHT11 (GPIO4)** are physically unwired, returning `null` frames from the ESP32.

### Strict Safety & Integrity Enforcements
1. **Zero Fabricated Physical Values:** Missing physical channels remain strictly `null` (`None`). Under no circumstance are missing readings coerced to `0` or filled with synthetic live data.
2. **Unified 5-State Sensor Value Architecture:** Every sensor is modeled across `LIVE`, `LAST_KNOWN`, `REFERENCE`, `UNAVAILABLE`, and `FAULT`.
3. **Calibrated Baseline Isolation:** Only genuine physical calibrations (`MEASURED_CALIBRATION`) may be used for baseline-relative math. Stored factory benchmarks and demo references (`CONFIGURED_REFERENCE`, `DEMO_REFERENCE`) are explicitly flagged, and uncalibrated channels preserve `NOT_CALIBRATED`.
4. **Protective Fail-Safe Invariance:** The industrial hazard engine maintains `SENSOR_FAULT` / `UNKNOWN` hazard status when required physical channels are missing, and the ventilation actuator/relay remains safely locked `OFF` (`DISABLED`, GPIO26 driven HIGH).

---

## 2. Sensor Channel Audit

| Sensor | GPIO Pin | Physical State | Availability State | Live Value | Displayed Reference | Calibration Status | Action Taken |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MQ-2** | 34 | Connected (ADC stream) | `LIVE` | 226–279 ADC | 338.0 ADC | `CALIBRATED_BENCHMARK` | Render live count, real-time baseline deviation (-112 ADC) |
| **MQ-135** | 35 | Unwired (Open circuit) | `FAULT` | `null` (never 0) | 1523.0 ADC | `NOT_CALIBRATED` | Explicit `SENSOR FAULT` banner, dashed benchmark reference, zero fabrication |
| **DHT11 Temp** | 4 | Unwired (Open bus) | `FAULT` | `null` (never 0) | 25.0 °C | `FACTORY_NOMINAL` | Display `-- °C` with ambient reference footnote (25.0 °C) |
| **DHT11 Hum** | 4 | Unwired (Open bus) | `FAULT` | `null` (never 0) | 50.0 %RH | `FACTORY_NOMINAL` | Display `-- %RH` with ambient reference footnote (50.0 %) |

---

## 3. Architecture & Implementation Deliverables

### Backend Implementation
- `backend/app/services/baseline_registry.py`: Persistent SQLite registry table `sensor_baselines` with schema columns:
  - `sensor_id`, `sensor_name`, `gpio_pin`, `baseline_value`, `baseline_type`, `calibration_status`, `reference_source`, `reference_timestamp`, `device_id`, `conditions_json`, `unit`.
  - Distinguishes `MEASURED_CALIBRATION`, `CONFIGURED_REFERENCE`, and `DEMO_REFERENCE`.
  - Exposes `get_baseline()`, `get_all_baselines()`, `is_calibrated()`, `register_or_update_baseline()`.
- `backend/app/services/unified_sensor_service.py`: Computes 5-state records with in-memory last-known cache and TTL checking (`build_unified_sensor_record`, `get_all_unified_sensors`).
- `backend/main.py`:
  - `GET /api/v1/sensors/unified`: Exposes the complete 5-state payload for SCADA consumption.
  - `GET /api/v1/baselines`: Lists registered calibration records and status.
  - Telemetry pipeline integrates `unified_sensors` in both REST and WebSocket broadcast streams.

### Frontend Implementation
- `frontend/src/lib/types.ts`: Added `SensorAvailabilityState` (`'LIVE' | 'LAST_KNOWN' | 'REFERENCE' | 'UNAVAILABLE' | 'FAULT'`) and `UnifiedSensorRecord`.
- `frontend/src/components/SensorCards.tsx`:
  - Visual badges for all 5 states with distinctive color semantics:
    - `LIVE`: Green border, glowing pulse indicator.
    - `LAST_KNOWN`: Amber warning with timestamp of last physical frame.
    - `REFERENCE`: Cyan dashed border with reference source annotation.
    - `FAULT`: Red border with Alert icon and fail-safe confirmation.
    - `UNAVAILABLE`: Muted neutral dash.
  - Displays `NOT CALIBRATED` badge for MQ-135.
  - Renders `--` for missing live values; never converts null to 0.
- `frontend/src/components/SensorCharts.tsx`:
  - Recharts component updated with `<ReferenceLine>` dashed horizontal benchmarks for baseline references.
  - Live lines configure `connectNulls={false}` so disconnected channels break cleanly rather than plotting fake zero or interpolated data.
  - Distinct chart legend separates live measurements from reference lines.
- `frontend/src/app/page.tsx`:
  - Parallel polling for `/api/v1/telemetry/live` and `/api/v1/sensors/unified`.
  - Supplies `unifiedSensors` across Overview, Live Monitor, and Diagnostics tabs.

---

## 4. Safety Interlock Verification

- **Relay Command:** In backup firmware on ESP32, GPIO26 is explicitly set to `HIGH` (active-LOW relay OFF).
- **Hazard Classification:** With MQ-135 reporting `null`, the ML classifier cannot construct the 11-feature vector; hazard state is clamped to `UNKNOWN`, and `sensor_state` is set to `SENSOR_FAULT`.
- **Ventilation Invariant:** Under `SENSOR_FAULT`, emergency extraction fans remain disabled to avoid triggering uncertified electrical components during unverified atmospheric conditions.
