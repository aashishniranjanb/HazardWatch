#pragma once

// =========================================================================
// PROJECT_A1 ESP32 PIN CONFIGURATION
// Target: ESP32 DevKit V1 (ESP32-WROOM-32)
// =========================================================================

// ADC1 Analog Inputs (free from Wi-Fi conflict)
static constexpr uint8_t PIN_MQ2 = 34;    // ADC1_CH6 via voltage divider (<= 3.1V)
static constexpr uint8_t PIN_MQ135 = 35;  // ADC1_CH7 via voltage divider (<= 3.1V)

// Digital Buses
static constexpr uint8_t PIN_DHT = 4;     // DHT11 / DHT22 1-Wire Single Bus
static constexpr uint8_t DHT_TYPE = 11;   // DHT11

// Actuation Outputs
static constexpr uint8_t PIN_RELAY = 26;  // Optocoupled Active-LOW Relay Input
static constexpr bool RELAY_ACTIVE_LOW = true;
static constexpr bool RELAY_ACTUATION_ENABLED = false; // Intentionally disabled safe-OFF
