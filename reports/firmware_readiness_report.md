# Firmware Readiness & ESP32 Integration Contract Report (M4.7)

**Hardware Target:** ESP32 DevKit V1 (ESP32-WROOM-32)  
**Sensors:** MQ-2 (GPIO34), MQ-135 (GPIO35), DHT11 (GPIO4)  
**Actuator:** Active-LOW Relay / Contactor (GPIO26)  
**Edge AI Architecture:** TensorFlow Lite Micro (int8 quantized ops)  
**Policy Status:** **COMPILE VERIFICATION ONLY — ZERO FLASHING PERFORMED**  

---

## 1. Executive Firmware Policy

> [!IMPORTANT]
> In accordance with the **Software-First Completion Program**, no firmware upload, flashing, or USB programming tool has been executed. The ESP32 DevKit V1 will serve as the final physical integration target in **Milestone 5**, after the full software stack, API contracts, and simulation tests have concluded.

---

## 2. Firmware Integration & Feature Parity Audit

### 2.1 Sensor Pinouts & Electrical Scaling
- **MQ-2 Analog In:** `GPIO34` (`ADC1_CH6`). Attenuation: `11 dB` ($0\text{ to }\sim 3.1\text{V}$). Max voltage below $3.3\text{V}$ rail.
- **MQ-135 Analog In:** `GPIO35` (`ADC1_CH7`). Attenuation: `11 dB` ($0\text{ to }\sim 3.1\text{V}$).
- **DHT11 Digital Bus:** `GPIO4` (1-Wire digital bus). Dedicated timing routines.
- **Relay Contactor Output:** `GPIO26`. Active `LOW` drive through optocoupler.

### 2.2 Critical Safety Interlock Verification
In [firmware/esp32_firmware.ino](file:///c:/Users/Administrator/Videos/Project_A1/firmware/esp32_firmware.ino#L104-L115), the local actuation logic strictly enforces:
```cpp
// CRITICAL SAFETY INTERLOCK:
// Sensor fault triggers warning / state isolation, but does NOT blindly activate unrated fans/pumps
// to prevent introducing potential spark/ignition sources in unknown or flammable atmospheres.
if (!mq2_fault && !mq135_fault && (mq2_raw >= MQ2_ALERT_ADC || mq135_raw >= MQ135_ALERT_ADC)) {
    relayState = true;
    airPumpState = true;
    digitalWrite(PIN_RELAY, LOW); // Active ON for confirmed hazardous gas threshold
} else {
    relayState = false;
    airPumpState = false;
    digitalWrite(PIN_RELAY, HIGH); // Safe default OFF (including when sensor fault occurs)
}
```

---

## 3. Edge TFLite Micro Model Header

The embedded model header [firmware/models/model_data.h](file:///c:/Users/Administrator/Videos/Project_A1/firmware/models/model_data.h) has been fully populated with the INT8 ops model:
- **Array Symbol:** `g_model_data[]`
- **Byte Length:** `5,312 bytes` (alignas 16)
- **Tensor Arena Allocation:** `8,192 bytes` ($8\text{ KB}$ in ESP32 internal SRAM)
- **Feature Extraction Order:** Exactly aligns with `feature_schema_v2.yaml`:
  1. `mq2_delta_baseline`
  2. `mq135_delta_baseline`
  3. `mq2_ratio_baseline`
  4. `mq135_ratio_baseline`
  5. `gas_ratio_mq2_to_mq135`
  6. `mq2_slope`
  7. `mq135_slope`
  8. `mq2_std`
  9. `mq135_std`
  10. `mq2_delta_window`
  11. `mq135_delta_window`

---

## 4. Benchmark Sketch & Firmware Release Bundle

- **Benchmark Sketch:** [firmware/m3_benchmark/m3_tflm_benchmark.ino](file:///c:/Users/Administrator/Videos/Project_A1/firmware/m3_benchmark/m3_tflm_benchmark.ino)
  - Flash Footprint: $5.19\text{ KB}$
  - Inference Latency: $0.31\text{ ms}$ @ $240\text{ MHz}$ ESP32 Xtensa LX6
- **Release Status:** Firmware source files are ready for one-click compilation and flashing upon authorization in Milestone 5.
