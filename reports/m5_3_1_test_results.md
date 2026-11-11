# Project_A1 — Milestone 5.3.1: Test Results & Validation Verification

**Execution Date:** 2026-11-11  
**Test Suite:** `tests/test_m5_3_1_baseline_display.py` & Global Regression Suite  
**Test Runner:** `unittest` (Python 3.11.9)  

---

## 1. M5.3.1 Specific Invariant Test Results

All 10 mandatory system invariants were verified through `tests/test_m5_3_1_baseline_display.py`:

| # | Test Case | Target Invariant | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `test_01_live_mq2_and_missing_mq135` | Live MQ-2 streams `LIVE` state; missing MQ-135 produces `FAULT` | **PASSED** | MQ-2 `live_value` = 245.0, `availability` = LIVE. MQ-135 `live_value` = None, `availability` = FAULT. |
| **02** | `test_02_both_mq_sensors_disconnected` | Both MQ channels disconnected produce `FAULT` and null `live_value` | **PASSED** | Both sensors report `availability` = FAULT, live_value = None. |
| **03** | `test_03_dht11_unavailable` | DHT11 unavailable produces null temperature/humidity with `FAULT` | **PASSED** | Temperature and humidity live values remain null, unit annotations preserved. |
| **04** | `test_04_previously_measured_baseline_available` | Stored calibration baseline is loaded and accessible | **PASSED** | MQ-2 baseline loaded as 338.0 ADC with `CALIBRATED_BENCHMARK`. |
| **05** | `test_05_no_baseline_configured_not_calibrated` | Uncalibrated sensor preserves `NOT_CALIBRATED` status | **PASSED** | `is_calibrated('mq135')` returns False; status is `NOT_CALIBRATED`. |
| **06** | `test_06_demo_reference_displayed_correctly` | Reference values preserved with source metadata | **PASSED** | 25.0 °C / 50.0 %RH referenced to "Standard Industrial Ambient". |
| **07** | `test_07_reference_value_never_overwrites_live_value` | Reference value must never populate `live_value` field | **PASSED** | MQ-135 reference is 1523.0, but `live_value` strictly remains None. |
| **08** | `test_08_missing_sensor_never_becomes_zero` | Missing physical sensors must remain null, never coerced to 0 | **PASSED** | Asserts `live_value != 0` and `live_value is None` across all missing channels. |
| **09** | `test_09_hazard_state_remains_sensor_fault_unknown` | Hazard state remains `SENSOR_FAULT` / `UNKNOWN` on missing sensor | **PASSED** | Hazard engine returns `pattern` = UNKNOWN, `sensor_state` = SENSOR_FAULT. |
| **10** | `test_10_relay_remains_disabled_safe_off` | Actuator/relay remains disabled when sensor fault is detected | **PASSED** | Telemetry processing clamps `relay_command` = False under fault. |

---

## 2. Global Software Regression Suite

Execution command: `python -m unittest discover -s tests -p "test_*.py"`

```text
Ran 46 tests in 0.675s

OK
```

- Total Tests Executed: **46**
- Passed: **46**
- Failed: **0**
- Errors: **0**
- Test Coverage Breakdown:
  - M4.1–M4.6 Backend, Replay, Multi-Model ML, Hazard Engine: 24 tests
  - M5.0 Feature Parity & C++ Vector Alignment: 9 tests
  - M5.3 Live Serial Hardware Integration: 3 tests
  - M5.3.1 Unified 5-State Baseline & Missing Sensor Model: 10 tests

---

## 3. Frontend Static Verification & Build Audit

Execution command: `cmd.exe /c "cd frontend && npm run build"`

```text
Route (app)                              Size     First Load JS
┌ ○ /                                    148 kB          235 kB
└ ○ /_not-found                          873 B          88.2 kB
+ First Load JS shared by all            87.3 kB
  ├ chunks/117-5840e53afe153d68.js       31.7 kB
  ├ chunks/fd9d1056-7af6a7ccbdd77626.js  53.6 kB
  └ other shared chunks (total)          1.96 kB

○  (Static)  prerendered as static content
```

- Status: Built successfully with 0 TypeScript and 0 JSX compilation errors.
- Both Next.js production server (`http://localhost:3000`) and FastAPI backend (`http://127.0.0.1:8000`) are active and serving live hardware data from `COM4`.
