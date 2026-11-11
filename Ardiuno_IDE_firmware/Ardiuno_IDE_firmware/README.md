# Project_A1 — Arduino IDE 2.x Firmware Guide

**Location:** `Ardiuno_IDE_firmware/Ardiuno_IDE_firmware/`  
**Main Sketch:** `Ardiuno_IDE_firmware.ino`  
**Target Board:** ESP32 Dev Module (ESP32-WROOM-32)  
**Safety Protocol:** **RELAY HARD-DISABLED SAFE-OFF BY DEFAULT — ZERO FLASHING DURING PREPARATION**  

---

## 1. Quick Setup in Arduino IDE 2.x

1. **Install ESP32 Board Support:**
   - Go to `File -> Preferences`.
   - In "Additional Boards Manager URLs", add:
     ```
     https://espressif.github.io/arduino-esp32/package_esp32_index.json
     ```
   - Go to `Tools -> Board -> Boards Manager`, search for **`esp32`** by Espressif Systems and click **Install**.
   - Select board: `Tools -> Board -> esp32 -> ESP32 Dev Module`.

2. **Install Required Libraries:**
   - Go to `Tools -> Manage Libraries...` (or Ctrl+Shift+I).
   - Search and install:
     - **`DHT sensor library`** by Adafruit
     - **`Adafruit Unified Sensor`** by Adafruit
     - **`ArduinoJson`** by Benoît Blanchon (version 6.x or 7.x)
     - *(Optional for ML mode)*: Compatible **`TensorFlowLite_ESP32`** library

---

## 2. Selecting Build Mode (`config.h`)

Open `config.h` inside Arduino IDE 2.x:

### A. Non-ML Backup Firmware (Recommended First Build)
```cpp
#define PROJECT_A1_ML_ENABLED 0
```
- **Zero TensorFlow dependencies:** Compiles immediately with only DHT and ArduinoJson.
- Employs deterministic baseline tracking, 10-sample windowing, exact 11-feature extraction, and rule-based hazard classification.
- Relay remains hardcoded **OFF** to eliminate spark risks.

### B. TinyML Edge AI Firmware
```cpp
#define PROJECT_A1_ML_ENABLED 1
```
- Links `ml_engine.h` and the embedded INT8 ops model ([models/model_data.h](file:///c:/Users/Administrator/Videos/Project_A1/Ardiuno_IDE_firmware/Ardiuno_IDE_firmware/models/model_data.h)).
- Automatically falls back to the deterministic rule engine if tensor allocation fails or if normalized inputs are out-of-distribution ($z > 4.0\sigma$).

---

## 3. Verify & Compile Sequence (No Flashing)

1. Open `Ardiuno_IDE_firmware/Ardiuno_IDE_firmware/Ardiuno_IDE_firmware.ino` in Arduino IDE 2.x.
2. Ensure `PROJECT_A1_ML_ENABLED` is set to `0` in `config.h`.
3. Click the **Verify (Checkmark icon)** button to compile.
4. Verify compile log outputs success without errors.
5. Switch `PROJECT_A1_ML_ENABLED` to `1` in `config.h` and click **Verify** again to test ML compilation.
6. **Do NOT click Upload.** Hardware flashing remains strictly reserved for **Milestone 5.2** after electrical multimeter verification.
