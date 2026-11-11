#pragma once

// =========================================================================
// PROJECT_A1 PIN DEFINITIONS & HARDWARE MAPPING
// Sensors: MQ-2 (GPIO34), MQ-135 (GPIO35), DHT11/22 (GPIO4)
// Actuators: Active-LOW Relay / Air Pump (GPIO26)
// =========================================================================

// ADC1 Pins (Free of Wi-Fi conflict)
#define PIN_MQ2_ADC         34    // ADC1_CH6 (Analog in via voltage divider)
#define PIN_MQ135_ADC       35    // ADC1_CH7 (Analog in via voltage divider)

// Digital Buses
#define PIN_DHT_DATA        4     // 1-Wire Single Bus for DHT11 / DHT22

// Actuator Outputs
#define PIN_RELAY_IN        26    // Optocoupled active-LOW Relay input

// ADC Configuration
#define ADC_RESOLUTION_BITS 12    // 0 - 4095
#define ADC_ATTEN_CONFIG    ADC_11db // 0 to ~3.1V input scale
