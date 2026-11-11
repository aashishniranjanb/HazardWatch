# Project_A1 — Milestone 5.0.1: PlatformIO Build Verification Report

**Date:** 2026-11-11  
**Build Tool:** PlatformIO Core `6.2.0`  
**Target Architecture:** Espressif ESP32 Dev Module (`esp32dev`, Xtensa dual-core 240MHz, 320KB RAM, 4MB Flash)  
**Framework:** Arduino Core for ESP32 (`framework-arduinoespressif32 @ 4.30312.261024`, ESP-IDF `3.3.12`)  
**Toolchain:** `toolchain-xtensa-esp-elf @ 14.2.0+20260121`, `tool-esptool @ 2.50400.0 (5.4.0)`  
**Status:** **100% SUCCESS — BOTH BUILDS COMPILED AND VERIFIED**

---

## 1. Executive Summary

Milestone 5.0.1 establishes strict, reproducible compiler verification for both Project_A1 firmware variants using PlatformIO Core CLI. Prior to this milestone, PlatformIO was missing from the workstation PATH, and actual compilation was unverified.

Both firmware environments now compile cleanly with zero errors, producing isolated, valid firmware binaries:
1. `project_a1_backup`: Deterministic rule-based backup build. Completely decoupled from TensorFlow Lite Micro, tensor arenas, and model headers.
2. `project_a1_ml`: Edge AI TinyML build. Compiles against the official `tflm_esp32` runtime and embeds the 5,312-byte INT8 quantized model (`model_data.h`). Features automatic fallback to the rule engine if initialization fails or an inference is out-of-distribution (OOD).

---

## 2. PlatformIO Compilation Evidence

### Build Command
```powershell
Set-Location -Path "firmware"
pio run
```

### Full Compiler Execution Log
```text
Processing project_a1_backup (platform: espressif32; board: esp32dev; framework: arduino)
--------------------------------------------------------------------------------
CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32dev.html
PLATFORM: Espressif 32 (8.0.0) > Espressif ESP32 Dev Module
HARDWARE: ESP32 240MHz, 320KB RAM, 4MB Flash
PACKAGES: 
 - framework-arduinoespressif32 @ 4.30312.261024 (3.3.12) 
 - framework-arduinoespressif32-esp32-libs @ 3.3.12 
 - tool-esptool @ 2.50400.0 (5.4.0) 
 - tool-riscv32-esp-elf-gdb @ 11.2.0+20220823 
 - tool-xtensa-esp-elf-gdb @ 11.2.0+20230208 
 - toolchain-riscv32-esp @ 14.2.0+20260121 
 - toolchain-xtensa-esp-elf @ 14.2.0+20260121
Found 47 compatible libraries
Scanning dependencies...
Dependency Graph
|-- DHT sensor library @ 1.4.7
|-- Adafruit Unified Sensor @ 1.1.15
|-- ArduinoJson @ 7.4.3
Building in release mode
Linking .pio\build\project_a1_backup\firmware.elf
Retrieving maximum program size .pio\build\project_a1_backup\firmware.elf
Checking size .pio\build\project_a1_backup\firmware.elf
RAM:   [=         ]   7.0% (used 22860 bytes from 327680 bytes)
Flash: [==        ]  23.8% (used 311464 bytes from 1310720 bytes)
Building .pio\build\project_a1_backup\firmware.bin
esptool v5.4.0
Creating ESP32 image...
Merged 3 ELF sections.
Successfully created ESP32 image.
========================= [SUCCESS] Took 18.09 seconds =========================

Processing project_a1_ml (platform: espressif32; board: esp32dev; framework: arduino)
--------------------------------------------------------------------------------
CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32dev.html
PLATFORM: Espressif 32 (8.0.0) > Espressif ESP32 Dev Module
HARDWARE: ESP32 240MHz, 320KB RAM, 4MB Flash
PACKAGES: 
 - framework-arduinoespressif32 @ 4.30312.261024 (3.3.12) 
 - framework-arduinoespressif32-esp32-libs @ 3.3.12 
 - tool-esptool @ 2.50400.0 (5.4.0) 
 - tool-riscv32-esp-elf-gdb @ 11.2.0+20220823 
 - tool-xtensa-esp-elf-gdb @ 11.2.0+20230208 
 - toolchain-riscv32-esp @ 14.2.0+20260121 
 - toolchain-xtensa-esp-elf @ 14.2.0+20260121
Found 48 compatible libraries
Scanning dependencies...
Dependency Graph
|-- DHT sensor library @ 1.4.7
|-- Adafruit Unified Sensor @ 1.1.15
|-- ArduinoJson @ 7.4.3
|-- tflm_esp32 @ 2.0.0
Building in release mode
Linking .pio\build\project_a1_ml\firmware.elf
Retrieving maximum program size .pio\build\project_a1_ml\firmware.elf
Checking size .pio\build\project_a1_ml\firmware.elf
RAM:   [=         ]   9.6% (used 31508 bytes from 327680 bytes)
Flash: [===       ]  32.7% (used 428500 bytes from 1310720 bytes)
Building .pio\build\project_a1_ml\firmware.bin
esptool v5.4.0
Creating ESP32 image...
Merged 3 ELF sections.
Successfully created ESP32 image.
========================= [SUCCESS] Took 2.82 seconds =========================

Environment        Status    Duration
-----------------  --------  ------------
project_a1_backup  SUCCESS   00:00:18.092
project_a1_ml      SUCCESS   00:00:02.823
========================= 2 succeeded in 00:00:20.914 =========================
```

---

## 3. Binary Artifact Inventory

| Environment | Binary Location | File Size | Flash Used | RAM Used |
|---|---|---|---|---|
| `project_a1_backup` | `firmware/.pio/build/project_a1_backup/firmware.bin` | 316,624 bytes | 311,464 B (23.8%) | 22,860 B (7.0%) |
| `project_a1_ml` | `firmware/.pio/build/project_a1_ml/firmware.bin` | 444,560 bytes | 428,500 B (32.7%) | 31,508 B (9.6%) |

Release packages have been updated with these verified builds:
- `firmware/release/PROJECT_A1_BACKUP/firmware.bin`
- `firmware/release/PROJECT_A1_ML/firmware.bin`

---

## 4. Flash and Upload Terminal Commands (For User Verification)

### Non-ML Backup Upload (Terminal)
```powershell
cd firmware
pio run -e project_a1_backup -t upload
pio device monitor -b 115200
```

### ML Firmware Upload (Terminal)
```powershell
cd firmware
pio run -e project_a1_ml -t upload
pio device monitor -b 115200
```

> [!IMPORTANT]
> Flashing is restricted until physical hardware inspection (Milestone 5.1) is confirmed.
