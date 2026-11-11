// =========================================================================
// ESP32 INDUSTRIAL HAZARDOUS GAS LEAKAGE MONITORING FIRMWARE
// Sensors: MQ-2 (GPIO34), MQ-135 (GPIO35), DHT11 (GPIO4)
// Actuation: Relay / DC Air Pump (GPIO26)
// Architecture: Baseline-First Initial Boot Telemetry & Local Risk Protection
// Baud Rate: 115200
// =========================================================================

#include <DHT.h>

// Pin Definitions
#define PIN_MQ2         34    // ADC1_CH6 (Analog in)
#define PIN_MQ135       35    // ADC1_CH7 (Analog in)
#define PIN_DHT         4     // Digital pin for DHT11
#define PIN_RELAY       26    // Relay trigger (Air Pump)

#define DHTTYPE         DHT11
DHT dht(PIN_DHT, DHTTYPE);

const char* DEVICE_ID = "ESP32_GAS_MONITOR";

// Verified Baseline References (Calibrated clean-air prototypes)
const int BASELINE_MQ2_REF   = 338;
const int BASELINE_MQ135_REF = 1523;

// Configurable Prototype Safety Alert Thresholds
const int MQ2_ALERT_ADC   = 600;
const int MQ135_ALERT_ADC = 1600;

// Internal State
bool relayState = false;
bool airPumpState = false;
bool sensorsOnline = false;
unsigned long lastSampleTime = 0;
const unsigned long SAMPLE_INTERVAL_MS = 500;

void printSerialMonitorBanner() {
  Serial.println("\n=================================");
  Serial.println("     INDUSTRIAL GAS MONITOR      ");
  Serial.println("=================================");
  Serial.println("STATUS       : CONNECTED");
  Serial.println("BASELINE MODE: ACTIVE REFERENCE\n");

  Serial.println("MQ-2");
  Serial.print("Baseline ADC : ");
  Serial.println(BASELINE_MQ2_REF);
  Serial.println("Current ADC  : WAITING");
  Serial.println("Status       : NO LIVE DATA\n");

  Serial.println("MQ-135");
  Serial.print("Baseline ADC : ");
  Serial.println(BASELINE_MQ135_REF);
  Serial.println("Current ADC  : WAITING");
  Serial.println("Status       : NO LIVE DATA\n");

  Serial.println("DHT11");
  Serial.println("Temperature  : --");
  Serial.println("Humidity     : --");
  Serial.println("Status       : WAITING\n");

  Serial.println("=================================");
  Serial.println("SYSTEM STATUS : BASELINE MODE");
  Serial.println("AI PREDICTION : NOT AVAILABLE");
  Serial.println("RELAY         : OFF");
  Serial.println("PUMP          : OFF");
  Serial.println("=================================\n");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PIN_MQ2, INPUT);
  pinMode(PIN_MQ135, INPUT);
  pinMode(PIN_RELAY, OUTPUT);

  // Relay default OFF (Active LOW relay module)
  digitalWrite(PIN_RELAY, HIGH);

  dht.begin();

  // Print startup human-readable baseline banner
  printSerialMonitorBanner();

  // Initial machine JSON announcement
  Serial.println("{\"device\":\"ESP32_GAS_MONITOR\",\"state\":\"BASELINE_MODE\",\"mq2_baseline\":338,\"mq135_baseline\":1523}");
}

void loop() {
  unsigned long now = millis();

  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;

    int mq2_raw = analogRead(PIN_MQ2);
    int mq135_raw = analogRead(PIN_MQ135);
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    // Fault detection: zero or float disconnected pin checking
    bool mq2_fault = (mq2_raw <= 5 || mq2_raw >= 4090);
    bool mq135_fault = (mq135_raw <= 5 || mq135_raw >= 4090);

    // Local Fail-Safe Relay Actuation Policy (M5.0 Safety Fix):
    // CRITICAL SAFETY INTERLOCK:
    // Neither the MQ-2 / MQ-135 sensors nor the prototype air pump are explosion-proof or certified.
    // Relay must remain disabled (OFF) by default in all automated conditions to eliminate ignition risk.
    relayState = false;
    airPumpState = false;
    digitalWrite(PIN_RELAY, HIGH); // Safe default OFF (Active LOW relay -> HIGH = OFF)

    // JSON Stream for Web Serial Dashboard
    Serial.print("{\"device\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",\"timestamp\":");
    Serial.print(now);
    
    // Send null if fault, never fake zero or clean air
    if (!mq2_fault) {
      Serial.print(",\"mq2_adc\":");
      Serial.print(mq2_raw);
    } else {
      Serial.print(",\"mq2_adc\":null");
    }

    if (!mq135_fault) {
      Serial.print(",\"mq135_adc\":");
      Serial.print(mq135_raw);
    } else {
      Serial.print(",\"mq135_adc\":null");
    }

    if (!isnan(temp)) {
      Serial.print(",\"temperature\":");
      Serial.print(temp, 1);
    } else {
      Serial.print(",\"temperature\":null");
    }

    if (!isnan(hum)) {
      Serial.print(",\"humidity\":");
      Serial.print(hum, 1);
    } else {
      Serial.print(",\"humidity\":null");
    }

    Serial.print(",\"relay\":");
    Serial.print(relayState ? "true" : "false");
    Serial.print(",\"pump\":");
    Serial.print(airPumpState ? "true" : "false");

    if (mq2_fault || mq135_fault) {
      Serial.print(",\"fault\":true");
    } else {
      Serial.print(",\"fault\":false");
    }

    Serial.println("}");
  }
}
