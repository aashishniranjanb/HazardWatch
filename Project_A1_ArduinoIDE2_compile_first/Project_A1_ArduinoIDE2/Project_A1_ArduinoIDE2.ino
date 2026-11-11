/*
  Project_A1 — Arduino IDE 2.x starter firmware
  Target: ESP32 Dev Module (ESP32-WROOM-32)
  Build mode: set PROJECT_A1_BUILD_ML to 0 (backup) or 1 (ML integration scaffold).

  IMPORTANT:
  - This is a compile-first integration baseline, not certified safety equipment.
  - Relay output is intentionally hard-disabled. Do not connect an unrated pump/fan
    for automatic operation in a potentially flammable atmosphere.
  - ML mode currently reports ML_ADAPTER_NOT_LINKED; it does NOT fabricate predictions.
*/

#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>

#define PROJECT_A1_BUILD_ML 0   // 0 = BACKUP_RULES, 1 = ML integration scaffold

#if PROJECT_A1_BUILD_ML != 0 && PROJECT_A1_BUILD_ML != 1
#error "PROJECT_A1_BUILD_ML must be 0 or 1"
#endif

static constexpr uint8_t PIN_MQ2 = 34;
static constexpr uint8_t PIN_MQ135 = 35;
static constexpr uint8_t PIN_DHT = 4;
static constexpr uint8_t PIN_RELAY = 26;
static constexpr uint8_t DHT_TYPE = DHT11;

static constexpr uint32_t SERIAL_BAUD = 115200;
static constexpr uint32_t SAMPLE_PERIOD_MS = 500; // provisional 2 Hz
static constexpr size_t WINDOW_SIZE = 10;
static constexpr size_t BASELINE_SAMPLES = 40;

// ADC full-scale/attenuation varies by ESP32 variant and Arduino-ESP32 core.
// Validate actual analog voltage with a meter; GPIOs are NOT 5-V tolerant.
static constexpr uint16_t ADC_MIN_VALID = 5;
static constexpr uint16_t ADC_MAX_VALID = 4090;

// Actuation is deliberately disabled for this prototype.
static constexpr bool RELAY_ACTUATION_ENABLED = false;
static constexpr bool RELAY_ACTIVE_LOW = true;

DHT dht(PIN_DHT, DHT_TYPE);

struct Sample {
  uint32_t ts;
  uint16_t mq2;
  uint16_t mq135;
  float temperature;
  float humidity;
  bool dhtValid;
  bool mq2Valid;
  bool mq135Valid;
};

Sample windowBuf[WINDOW_SIZE];
size_t windowCount = 0;
size_t windowHead = 0;

uint32_t lastSampleMs = 0;
uint32_t sampleSequence = 0;
uint32_t baselineCount = 0;
double baselineMq2Sum = 0.0;
double baselineMq135Sum = 0.0;
float baselineMq2 = NAN;
float baselineMq135 = NAN;
bool baselineReady = false;

enum MonitorState { INITIALIZING, BASELINE_MODE, LIVE_MONITORING, SENSOR_FAULT };
MonitorState monitorState = INITIALIZING;

const char* stateName(MonitorState s) {
  switch (s) {
    case INITIALIZING: return "INITIALIZING";
    case BASELINE_MODE: return "BASELINE_MODE";
    case LIVE_MONITORING: return "LIVE_MONITORING";
    case SENSOR_FAULT: return "SENSOR_FAULT";
    default: return "UNKNOWN";
  }
}

void relaySafeOff() {
  // Active-LOW relay: HIGH means OFF. Never energize from sensor/ML output.
  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, RELAY_ACTIVE_LOW ? HIGH : LOW);
}

void emitBootRecord() {
  StaticJsonDocument<256> doc;
  doc["type"] = "firmware_status";
  doc["project"] = "Project_A1";
  doc["build_mode"] = PROJECT_A1_BUILD_ML ? "ML_SCAFFOLD" : "BACKUP_RULES";
  doc["state"] = stateName(monitorState);
  doc["relay_policy"] = "DISABLED_SAFE_OFF";
  doc["ml_status"] = PROJECT_A1_BUILD_ML ? "ML_ADAPTER_NOT_LINKED" : "NOT_USED";
  serializeJson(doc, Serial);
  Serial.println();
}

void emitTelemetry(const Sample& s) {
  StaticJsonDocument<512> doc;
  doc["type"] = "telemetry";
  doc["sequence"] = sampleSequence;
  doc["timestamp_ms"] = s.ts;
  doc["build_mode"] = PROJECT_A1_BUILD_ML ? "ML_SCAFFOLD" : "BACKUP_RULES";
  doc["monitoring_state"] = stateName(monitorState);

  JsonObject sensors = doc.createNestedObject("sensors");
  if (s.mq2Valid) sensors["mq2_adc"] = s.mq2; else sensors["mq2_adc"] = nullptr;
  if (s.mq135Valid) sensors["mq135_adc"] = s.mq135; else sensors["mq135_adc"] = nullptr;
  if (s.dhtValid) {
    sensors["temperature_c"] = s.temperature;
    sensors["humidity_pct"] = s.humidity;
  } else {
    sensors["temperature_c"] = nullptr;
    sensors["humidity_pct"] = nullptr;
  }

  JsonObject baseline = doc.createNestedObject("baseline");
  baseline["ready"] = baselineReady;
  if (baselineReady) {
    baseline["mq2_adc"] = baselineMq2;
    baseline["mq135_adc"] = baselineMq135;
  } else {
    baseline["mq2_adc"] = nullptr;
    baseline["mq135_adc"] = nullptr;
  }

  doc["window_samples"] = windowCount;
  doc["window_required"] = WINDOW_SIZE;
  doc["gas_hazard_state"] = "UNKNOWN_UNCALIBRATED";
  doc["prediction"] = nullptr;
  doc["prediction_status"] = PROJECT_A1_BUILD_ML ? "ML_ADAPTER_NOT_LINKED" : "NOT_USED";
  doc["relay_command"] = "DISABLED";
  doc["actuation_feedback"] = "UNAVAILABLE";
  serializeJson(doc, Serial);
  Serial.println();
}

bool validAdc(uint16_t v) {
  return v >= ADC_MIN_VALID && v <= ADC_MAX_VALID;
}

void addWindow(const Sample& s) {
  windowBuf[windowHead] = s;
  windowHead = (windowHead + 1) % WINDOW_SIZE;
  if (windowCount < WINDOW_SIZE) windowCount++;
}

void updateBaseline(const Sample& s) {
  if (baselineReady || !s.mq2Valid || !s.mq135Valid) return;

  // Baseline capture is provisional and must be done only in a known clean-air
  // supervised environment. No automatic declaration of atmospheric safety.
  baselineMq2Sum += s.mq2;
  baselineMq135Sum += s.mq135;
  baselineCount++;

  if (baselineCount >= BASELINE_SAMPLES) {
    baselineMq2 = baselineMq2Sum / baselineCount;
    baselineMq135 = baselineMq135Sum / baselineCount;
    baselineReady = true;
    monitorState = BASELINE_MODE;
  }
}

Sample readSample() {
  Sample s{};
  s.ts = millis();
  s.mq2 = analogRead(PIN_MQ2);
  s.mq135 = analogRead(PIN_MQ135);
  s.mq2Valid = validAdc(s.mq2);
  s.mq135Valid = validAdc(s.mq135);

  s.humidity = dht.readHumidity();
  s.temperature = dht.readTemperature();
  s.dhtValid = !isnan(s.humidity) && !isnan(s.temperature)
               && s.humidity >= 0.0f && s.humidity <= 100.0f
               && s.temperature >= -20.0f && s.temperature <= 80.0f;
  return s;
}

void processSample() {
  Sample s = readSample();
  sampleSequence++;

  if (!s.mq2Valid || !s.mq135Valid) {
    monitorState = SENSOR_FAULT;
    relaySafeOff();
    emitTelemetry(s);
    return;
  }

  updateBaseline(s);
  addWindow(s);

  if (baselineReady && windowCount >= WINDOW_SIZE) {
    monitorState = LIVE_MONITORING;
  } else if (!baselineReady) {
    monitorState = BASELINE_MODE;
  }

  // The 11-feature order is reserved for later parity integration:
  // 1 mq2_delta_baseline
  // 2 mq135_delta_baseline
  // 3 mq2_ratio_baseline
  // 4 mq135_ratio_baseline
  // 5 gas_ratio_mq2_to_mq135
  // 6 mq2_slope
  // 7 mq135_slope
  // 8 mq2_std
  // 9 mq135_std
  // 10 mq2_delta_window
  // 11 mq135_delta_window
  //
  // Do not emit an ML class until the original scaler, quantization parameters,
  // tensor layout, labels, and model header have been checked against source files.

  relaySafeOff();
  emitTelemetry(s);
}

void setup() {
  relaySafeOff();
  Serial.begin(SERIAL_BAUD);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_MQ2, ADC_11db);
  analogSetPinAttenuation(PIN_MQ135, ADC_11db);
  dht.begin();

  delay(300);
  emitBootRecord();
  lastSampleMs = millis();
}

void loop() {
  const uint32_t now = millis();
  if (now - lastSampleMs >= SAMPLE_PERIOD_MS) {
    lastSampleMs += SAMPLE_PERIOD_MS;
    processSample();
  }
}
