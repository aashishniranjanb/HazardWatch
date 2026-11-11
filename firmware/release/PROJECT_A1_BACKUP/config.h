#pragma once

// =========================================================================
// PROJECT_A1 FIRMWARE CONFIGURATION & TIMINGS
// =========================================================================

#define DEVICE_ID               "PROJECT_A1_ESP32_01"
#define FIRMWARE_VERSION        "4.7.0"

// Sampling and Timing
#define SAMPLE_INTERVAL_MS      500     // 2.0 Hz nominal acquisition
#define WARMUP_DURATION_MS      60000   // 60-second baseline warm-up
#define SLIDING_WINDOW_SIZE     10      // 10 samples (5.0s window)
#define WINDOW_STEP_SAMPLES     2       // Stride = 2 samples (1.0s step)

// Default Clean-Air Prototype Calibration References
#define DEFAULT_BASELINE_MQ2    338.0f
#define DEFAULT_BASELINE_MQ135  1523.0f

// Sensor Fault Electrical Boundaries
#define SENSOR_FAULT_ADC_MIN    5       // Shorted to GND or disconnected pin
#define SENSOR_FAULT_ADC_MAX    4090    // Shorted to rail or blown sensor

// Rule-Based Hazard Thresholds (ADC Delta from Baseline)
#define DELTA_ADVISORY_ADC      120.0f
#define DELTA_WARNING_ADC       250.0f
#define DELTA_CRITICAL_ADC      500.0f

// Safety Actuation Thresholds (Confirmed Gas Leak Only)
#define RELAY_ACTUATE_MQ2_ADC   600
#define RELAY_ACTUATE_MQ135_ADC 1800
