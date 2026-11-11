#pragma once

#include <Arduino.h>

// =========================================================================
// PROJECT_A1 FIRMWARE CONFIGURATION & BUILD SELECTION
// =========================================================================

// Build Selection:
// 0 = PROJECT_A1_BACKUP (Deterministic rule engine, zero TensorFlow Lite dependency)
// 1 = PROJECT_A1_ML     (TensorFlow Lite Micro INT8 ops model with rule fallback)
#define PROJECT_A1_ML_ENABLED 0

#define DEVICE_ID           "PROJECT_A1_ESP32_01"
#define FIRMWARE_VERSION    "5.0.0-ARDUINO"

// Sampling and Sliding Window
static constexpr uint32_t SERIAL_BAUD = 115200;
static constexpr uint32_t SAMPLE_PERIOD_MS = 500;   // 2.0 Hz nominal rate
static constexpr size_t WINDOW_SIZE = 10;           // 10 samples (5.0s temporal window)
static constexpr size_t BASELINE_SAMPLES = 40;       // Initial calibration sample count

// ADC Boundaries (Clamped to prevent reading invalid open/short pins)
static constexpr uint16_t ADC_MIN_VALID = 5;        // Open circuit or shorted to GND
static constexpr uint16_t ADC_MAX_VALID = 4090;     // Rail short to 3.3V / saturation

// Prototype Default Clean-Air Calibration References
static constexpr float DEFAULT_BASELINE_MQ2 = 338.0f;
static constexpr float DEFAULT_BASELINE_MQ135 = 1523.0f;

// Rule-Based Hazard Boundaries (Delta ADC above baseline)
static constexpr float DELTA_ADVISORY_ADC = 120.0f;
static constexpr float DELTA_WARNING_ADC = 250.0f;
static constexpr float DELTA_CRITICAL_ADC = 500.0f;

// Out-of-Distribution Gating
static constexpr float OOD_Z_SCORE_THRESHOLD = 4.0f;
static constexpr float MIN_CONFIDENCE_THRESHOLD = 0.60f;
