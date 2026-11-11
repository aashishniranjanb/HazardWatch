/*
  Project_A1 — Unified ESP32 Firmware for Arduino IDE 2.x
  Target Board: ESP32 Dev Module (ESP32-WROOM-32)
  Build Modes (selectable in config.h):
    - PROJECT_A1_ML_ENABLED = 0 : Non-ML Deterministic Rule Engine (Backup)
    - PROJECT_A1_ML_ENABLED = 1 : TinyML TFLite Micro INT8 Inference + Rule Fallback

  CRITICAL SAFETY MANDATES:
  - Relay output is hardcoded safe-OFF by default.
  - Sensor faults, OOD inputs, and automated threshold crossings NEVER energize the relay.
  - Unavailable sensor readings emit null rather than fabricated zeros or stale numbers.
*/

#include <Arduino.h>
#include "config.h"
#include "pin_config.h"
#include "protocol.h"
#include "feature_schema.h"

// Subsystem Modules
#include "sensor_manager.h"
#include "baseline_manager.h"
#include "feature_extractor.h"
#include "rule_engine.h"
#include "relay_manager.h"
#include "telemetry_manager.h"

#if PROJECT_A1_ML_ENABLED
#include "ml_engine.h"
#endif

// System Instances
static SensorManager sensorMgr;
static BaselineManager baseMgr;
static RelayManager relayMgr;

#if PROJECT_A1_ML_ENABLED
static MLEngine mlEngine;
#endif

// Sliding Window Buffer
static SensorData windowBuffer[WINDOW_SIZE];
static size_t windowCount = 0;
static size_t windowHead = 0;

static uint32_t lastSampleMs = 0;
static uint32_t sequenceNum = 0;
static MonitorState currentMonitorState = INITIALIZING;

static float rawFeatures[FEATURE_COUNT];
static float normFeatures[FEATURE_COUNT];

void addSampleToWindow(const SensorData& s) {
    windowBuffer[windowHead] = s;
    windowHead = (windowHead + 1) % WINDOW_SIZE;
    if (windowCount < WINDOW_SIZE) windowCount++;
}

void getOrderedWindow(SensorData* outWindow) {
    size_t startIdx = (windowCount < WINDOW_SIZE) ? 0 : windowHead;
    for (size_t i = 0; i < windowCount; i++) {
        outWindow[i] = windowBuffer[(startIdx + i) % WINDOW_SIZE];
    }
}

void setup() {
    relayMgr.begin();
    relayMgr.setSafeOff();

    Serial.begin(SERIAL_BAUD);
    delay(500);

    sensorMgr.begin();
    baseMgr.begin();

#if PROJECT_A1_ML_ENABLED
    bool mlOk = mlEngine.begin();
    TelemetryManager::publishBoot("ML_ENABLED", mlOk ? "TFLM_READY" : "TFLM_INIT_FAILED_FALLBACK_RULE");
#else
    TelemetryManager::publishBoot("BACKUP_RULES", "RULE_ENGINE_READY");
#endif

    lastSampleMs = millis();
}

void loop() {
    uint32_t now = millis();
    if (now - lastSampleMs >= SAMPLE_PERIOD_MS) {
        lastSampleMs += SAMPLE_PERIOD_MS;
        sequenceNum++;

        // 1. Read Physical Sensor Signals
        SensorData sample = sensorMgr.readAll();
        bool sensorFault = (!sample.mq2Valid || !sample.mq135Valid);

        // 2. Update Calibration Baseline
        if (!sensorFault) {
            baseMgr.update(sample);
        }

        // 3. Update Monitor State
        if (sensorFault) {
            currentMonitorState = SENSOR_FAULT;
        } else if (!baseMgr.isReady()) {
            currentMonitorState = BASELINE_MODE;
        } else {
            currentMonitorState = LIVE_MONITORING;
        }

        // 4. Circular Window Accumulation
        if (!sensorFault) {
            addSampleToWindow(sample);
        }

        // 5. Evaluate Rule-Based Baseline Engine
        RuleResult ruleRes = RuleEngine::evaluate(
            sample.mq2,
            sample.mq135,
            baseMgr.getMQ2Baseline(),
            baseMgr.getMQ135Baseline(),
            sensorFault
        );

        // 6. Dual Inference Logic
        const char* inferenceEngine = PROJECT_A1_ML_ENABLED ? "TFLITE_INT8" : "RULE_ENGINE";
        const char* inferenceStatus = "WAITING_WARMUP";
        const char* inferenceClass = "UNKNOWN";
        float confidence = 0.0f;
        bool hasConfidence = false;
        HazardState hazState = HAZARD_UNKNOWN;
        bool relayCommand = false; // Intentionally disabled safe-OFF

        if (currentMonitorState == SENSOR_FAULT) {
            hazState = HAZARD_SENSOR_FAULT;
            inferenceStatus = "SENSOR_FAULT";
            inferenceClass = "UNKNOWN";
        } else if (currentMonitorState == BASELINE_MODE) {
            hazState = HAZARD_NORMAL_BASELINE;
            inferenceStatus = "WARMUP_BASELINE";
            inferenceClass = "NORMAL_BASELINE";
        } else {
            // Live monitoring
            bool windowReady = (windowCount >= WINDOW_SIZE);
            bool featExtracted = false;

            if (windowReady) {
                SensorData ordered[WINDOW_SIZE];
                getOrderedWindow(ordered);
                featExtracted = FeatureExtractor::extract(
                    ordered,
                    WINDOW_SIZE,
                    baseMgr.getMQ2Baseline(),
                    baseMgr.getMQ135Baseline(),
                    rawFeatures
                );
                if (featExtracted) {
                    FeatureExtractor::standardize(rawFeatures, normFeatures);
                }
            }

#if PROJECT_A1_ML_ENABLED
            if (mlEngine.isReady() && featExtracted) {
                MLPrediction pred = mlEngine.predict(normFeatures);
                inferenceStatus = pred.status;
                inferenceClass = pred.label;
                confidence = pred.confidence;
                hasConfidence = (pred.confidence > 0.0f);

                if (pred.ok) {
                    if (strcmp(pred.label, "NORMAL_BASELINE") == 0) hazState = HAZARD_NORMAL_BASELINE;
                    else if (strcmp(pred.label, "SMOKE") == 0) hazState = HAZARD_CRITICAL;
                    else hazState = HAZARD_WARNING;
                } else {
                    // Fallback to rule engine on OOD or failure
                    inferenceEngine = "FALLBACK_RULE_ENGINE";
                    hazState = ruleRes.state;
                }
            } else {
                inferenceEngine = "FALLBACK_RULE_ENGINE";
                inferenceStatus = featExtracted ? "RULE_EVALUATED" : "WINDOW_ACCUMULATING";
                inferenceClass = ruleRes.pattern;
                hazState = ruleRes.state;
            }
#else
            inferenceEngine = "RULE_ENGINE";
            inferenceStatus = featExtracted ? "VALID" : "WINDOW_ACCUMULATING";
            inferenceClass = ruleRes.pattern;
            hazState = ruleRes.state;
#endif
        }

        // Enforce Relay Safe-OFF
        relayMgr.setSafeOff();

        // 7. Publish Common JSON Telemetry Protocol
        TelemetryManager::publish(
            sequenceNum,
            sample,
            baseMgr.isReady(),
            baseMgr.getMQ2Baseline(),
            baseMgr.getMQ135Baseline(),
            currentMonitorState,
            hazState,
            windowCount,
            inferenceEngine,
            inferenceStatus,
            inferenceClass,
            confidence,
            hasConfidence,
            relayCommand,
            relayMgr.getFeedback()
        );
    }
}
