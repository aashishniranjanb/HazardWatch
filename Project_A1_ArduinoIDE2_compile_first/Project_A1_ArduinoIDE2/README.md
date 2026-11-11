# Project_A1 — Arduino IDE 2.x starter

## Included
- ESP32 DevKit V1 / ESP32-WROOM-32 sketch
- MQ-2 ADC input: GPIO34
- MQ-135 ADC input: GPIO35
- DHT11: GPIO4
- Active-LOW relay output: GPIO26, held OFF
- JSON telemetry at 115200 baud
- Baseline-first sampling and 10-sample rolling-window scaffold
- Two compile modes: `BACKUP_RULES` and `ML_SCAFFOLD`

## Important limitation
The supplied project reports that `firmware/models/model_data.h` exists and is 5,312 bytes, but the actual header, model metadata, scaler constants, and original firmware source were not present in the files available for this implementation pass. Therefore this package does **not** pretend to run TFLite Micro inference. The ML build compiles as a clearly labelled scaffold and reports `ML_ADAPTER_NOT_LINKED`. The real model adapter must be integrated and validated before the ML build can be called functional.

## Arduino IDE 2.x setup
1. Install Arduino IDE 2.x.
2. Open **File → Preferences** and add this Boards Manager URL:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Open Boards Manager; install **esp32 by Espressif Systems**.
4. Select **Tools → Board → esp32 → ESP32 Dev Module**.
5. Install these libraries using Library Manager:
   - DHT sensor library by Adafruit
   - Adafruit Unified Sensor
   - ArduinoJson (v6 or v7)
6. Open `Project_A1_ArduinoIDE2.ino`.

## Build A — backup first
In the sketch, set:
`#define PROJECT_A1_BUILD_ML 0`

Select the ESP32 Dev Module and the correct upload speed/port if available. Use **Sketch → Verify/Compile** only. Do not click Upload.

## Build B — ML scaffold
Set:
`#define PROJECT_A1_BUILD_ML 1`

Run **Verify/Compile** again. This currently verifies the alternate build configuration and telemetry identity only; it does not perform ML inference. Do not report it as a working AI model build.

## Serial output
- Baud: 115200
- One JSON object per line
- `type=firmware_status` at startup
- `type=telemetry` for each sample
- Missing sensor readings are emitted as JSON `null`, not zero or stale values.

## Electrical checks before any future flash
- MQ module AO outputs must be divided/scaled so ESP32 GPIO input never exceeds its permitted voltage. ESP32 GPIO is not 5-V tolerant.
- Verify each AO voltage with a multimeter before connecting GPIO34/GPIO35.
- Confirm a stable 5-V supply for MQ heater loads and common ground.
- Verify relay module polarity and isolation. Firmware defaults the active-LOW relay OFF.
- This firmware intentionally disables automatic relay actuation. Do not connect an ordinary pump/fan for automatic activation in a potentially flammable atmosphere.
- MQ-2/MQ-135 are broad-response MOS sensors, not selective or certified gas concentration instruments.

## Compile evidence to record
For each mode, save:
- Arduino IDE version
- esp32 board package version
- library versions
- selected board
- complete Verify output
- final `Sketch uses ... bytes` and `Global variables use ... bytes` lines

No hardware flashing is authorized by this workflow until the compile logs and code are reviewed.
