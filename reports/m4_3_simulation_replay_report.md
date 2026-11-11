# Milestone 4.3 Simulation & Replay Engine Report

**Subsystem:** Factory Atmospheric Simulation & Historical Data Replay  
**Status:** Operational (Deterministic & Verified)  

---

## 1. Ten Deterministic Factory Scenarios

The simulation engine (`backend/app/services/simulation_engine.py`) provides 10 reproducible industrial scenarios for end-to-end software testing without physical hardware:

1. `NORMAL_PRODUCTION` (Clean room ambient, nominal baseline)
2. `COMBUSTIBLE_RESPONSE_PATTERN` (MQ-2 surge, MQ-135 moderate)
3. `VOC_RESPONSE` (MQ-135 surge, MQ-2 low-to-moderate)
4. `SMOKE_RESPONSE` (MQ-2 & MQ-135 rapid concurrent increase)
5. `MIXTURE` (Volatile solvent + combustion traces)
6. `SENSOR_DRIFT_WARNING` (Monotonic baseline climb over time)
7. `SENSOR_FAULT` (Disconnected/shorted pin with null ADC counts)
8. `VENTILATION_FEEDBACK_UNAVAILABLE` (Relay command active, contactor feedback false)
9. `OFFLINE_MODE` (Edge gateway disconnection)
10. `UNKNOWN_OOD` (Extreme out-of-distribution voltage influx $z > 4.0\sigma$)

### Provenance Guarantee
Every simulated record strictly carries:
```json
{
  "mode": "SYNTHETIC_SIMULATION",
  "provenance": "SYNTHETIC_GENERATED"
}
```

---

## 2. Historical Replay Engine

- Serves `multi_sensor_data.csv` (812 rows), `multi_sensor_data_baseline.csv` (12,175 rows), and `Gas_Sensors_Measurements.csv` (6,400 rows).
- Preserves original sensor readings, units, timestamps, and sampling rates ($500\text{ ms} / 1000\text{ ms}$).
- Strictly stamped with provenance `VERIFIED_RESEARCH_DATASET`.
