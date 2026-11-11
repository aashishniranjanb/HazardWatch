# ==============================================================================
# HazardWatch — System Architecture & Physical Interconnects
# ==============================================================================

This document provides system topology diagrams and hardware wiring specifications for HazardWatch.

---

## 1. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph EdgeHardware["1. Edge Microcontroller Layer (ESP32 DevKit V1)"]
        MQ2["MQ-2 Gas Sensor\n(Combustible Gas / Smoke)\n[Pin GPIO34 / ADC1_CH6]"]
        MQ135["MQ-135 Air Quality Sensor\n(Hazardous VOCs / CO2)\n[Pin GPIO35 / ADC1_CH7]"]
        DHT11["DHT11 Sensor\n(Temperature & Humidity)\n[Pin GPIO4 / Digital Bus]"]
        Relay["Relay Module & Fan\n(Ventilation Interlock)\n[Pin GPIO26 / Active-LOW]"]
        
        ESP32Core["ESP32 Dual-Core 240MHz\n(FreeRTOS Firmware)"]
        
        MQ2 -->|Analog ADC| ESP32Core
        MQ135 -->|Analog ADC| ESP32Core
        DHT11 -->|Digital Stream| ESP32Core
        ESP32Core -.->|Safety Interlock Locked OFF| Relay
    end

    subgraph TransportLayer["2. Hardware Communications Layer"]
        USBSerial["USB-UART Serial Bus\n(CH340 / CP2102 @ 115,200 baud)\n[Exclusive Host Bridge]"]
        ESP32Core ==>|1 Hz Telemetry JSON Frame| USBSerial
    end

    subgraph HostBackend["3. Host Server & Analytical Backend (FastAPI Python)"]
        SerialService["Serial Acquisition Service\n(Sole OS COM Port Owner)"]
        HazardEngine["Industrial Hazard Engine\n(Zone Logic & Safety Interlock)"]
        UnifiedSensor["Unified 5-State Sensor Service\n(LIVE / LAST_KNOWN / REFERENCE / FAULT)"]
        ModelInference["Multi-Model Inference Engine\n(XGBoost / Random Forest / TFLite)"]
        SQLiteDB[("SQLite Database\n(telemetry, incidents, baselines)")]

        USBSerial ==>|Physical Stream| SerialService
        SerialService --> HazardEngine
        SerialService --> UnifiedSensor
        HazardEngine --> ModelInference
        HazardEngine --> SQLiteDB
    end

    subgraph HostFrontend["4. SCADA Operator Dashboard (Next.js 14)"]
        WebSockets["WebSocket Feed\n(/ws/telemetry)"]
        RestAPI["REST API\n(/api/v1/*)"]
        SCADAUI["Industrial SCADA Dashboard\n- Plant Overview & Zone Monitor\n- 5-State Sensor Cards\n- Real-Time Trend Charts\n- Incident Management Console"]

        HostBackend -->|Real-Time Broadcast| WebSockets
        HostBackend -->|Query / Control| RestAPI
        WebSockets ==> SCADAUI
        RestAPI ==> SCADAUI
    end
```

---

## 2. Hardware Pinout & Wiring Table

| Peripheral | Board Pin / Channel | ESP32 GPIO | Operating Voltage | Signal Type | Role in HazardWatch |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MQ-2** | Analog Out (AO) | `GPIO34` | 5.0 V VCC (Heater), 3.3 V ADC | Analog (0–3.3V) | Indicative combustible gas & smoke response |
| **MQ-135** | Analog Out (AO) | `GPIO35` | 5.0 V VCC (Heater), 3.3 V ADC | Analog (0–3.3V) | Indicative air contaminants & VOC response |
| **DHT11** | Data (OUT) | `GPIO4` | 3.3 V VCC | 1-Wire Digital Bus | Ambient climatic temperature & humidity |
| **Relay** | Control (IN) | `GPIO26` | 5.0 V VCC, 3.3 V Logic | Active-LOW Digital | Ventilation interlock (Held HIGH / Safe-OFF) |
| **Status LED**| Onboard LED | `GPIO2` | 3.3 V | Digital Output | Acquisition heartbeat (toggles on valid sample) |
| **UART TX** | TX0 | `GPIO1` | 3.3 V Logic | Serial (115200 baud)| Downlink telemetry transmission to host PC |
| **UART RX** | RX0 | `GPIO3` | 3.3 V Logic | Serial (115200 baud)| Uplink command link from host PC |

---

## 3. Physical Safety Interlock Topology

```
                  +--------------------------------+
                  |      ESP32 DevKit V1 Boot      |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |  GPIO26 Mode: OUTPUT           |
                  |  GPIO26 State: HIGH (Safe-OFF) |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  | Any Sensor Missing or Faulted? |
                  +-------+----------------+-------+
                          |                |
                     YES  |                |  NO
                          v                v
      +-----------------------------+    +-----------------------------+
      | FORCE RELAY COMMAND = OFF   |    | Normal Monitoring State     |
      | State remains DISABLED      |    | Manual Control Permitted    |
      | Pump strictly powered down  |    | Continuous Safety Checks    |
      +-----------------------------+    +-----------------------------+
```
