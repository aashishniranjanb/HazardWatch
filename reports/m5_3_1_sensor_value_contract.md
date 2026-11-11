# Project_A1 — Milestone 5.3.1: Unified Sensor Value & Baseline Contract

**Document Version:** 1.0.0  
**Effective Date:** 2026-11-11  

---

## 1. Unified 5-State Sensor Schema

Every sensor channel emitted by the backend or consumed by the SCADA frontend adheres to the following JSON schema:

```json
{
  "sensor_id": "mq135",
  "sensor_name": "MQ-135 Hazardous/Air Quality",
  "gpio_pin": 35,
  "live_value": null,
  "last_known_value": null,
  "last_known_timestamp": null,
  "reference_value": 1523.0,
  "reference_source": "M2.7 Factory Benchmark",
  "reference_timestamp": 1794380782573,
  "availability": "FAULT",
  "calibration_status": "NOT_CALIBRATED",
  "unit": "ADC"
}
```

### State Definitions
- **`LIVE`**: A valid physical reading was acquired on active hardware within the live TTL window (3.5 seconds).
- **`LAST_KNOWN`**: The physical connection dropped or went temporarily quiet, but a valid historical reading was observed within the past 120 seconds.
- **`REFERENCE`**: Live and last-known readings are unavailable, but an official reference baseline is configured.
- **`FAULT`**: Sensor hardware error, open circuit, CRC failure, or null payload received from physical microcontroller.
- **`UNAVAILABLE`**: Channel is not present in hardware or software profile.

---

## 2. Baseline Registry Contract

The baseline registry (`sensor_baselines` in SQLite) supports three baseline types:

1. **`MEASURED_CALIBRATION`**: Genuine baseline established during clean-air physical sensor calibration.
   - **Math Eligibility:** Permitted for baseline-deviation (`reading - baseline`), slope, and ratio features.
2. **`CONFIGURED_REFERENCE`**: Engineering benchmark defined from factory dataset distributions (e.g. M2.7 synthetic/historical benchmark).
   - **Math Eligibility:** FORBIDDEN for live inference or mathematical feature derivation; for human visual context only.
3. **`DEMO_REFERENCE`**: Demonstration / simulation baseline.
   - **Math Eligibility:** FORBIDDEN for live physical validation.

### Calibration Status Enum
- `MEASURED_CALIBRATION`: Verified clean air test on physical device.
- `CALIBRATED_BENCHMARK`: Factory lab benchmark (e.g. MQ-2 clean air ADC 338).
- `FACTORY_NOMINAL`: Manufacturer datasheet standard (e.g. 25°C / 50% RH).
- `NOT_CALIBRATED`: Uncalibrated channel (e.g. MQ-135 prototype channel without clean-air chamber testing).

---

## 3. Physical Channel Allocations

| Sensor ID | Sensor Name | ESP32 GPIO | Native Unit | Benchmark Reference | Reference Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mq2` | MQ-2 Combustible/Smoke | 34 | ADC | 338.0 | M2.7 Factory Benchmark |
| `mq135` | MQ-135 Hazardous/Air Quality | 35 | ADC | 1523.0 | M2.7 Factory Benchmark |
| `temperature` | DHT11 Temperature | 4 | °C | 25.0 | Standard Industrial Ambient |
| `humidity` | DHT11 Humidity | 4 | %RH | 50.0 | Standard Industrial Ambient |

---

## 4. API Endpoints

- `GET /api/v1/sensors/unified`: Returns current 5-state payload for all 4 channels.
- `GET /api/v1/baselines`: Returns all baseline registry records with calibration metadata.
- `GET /api/v1/telemetry/live`: Returns raw ESP32 frame with `unified_sensors` mapping.
