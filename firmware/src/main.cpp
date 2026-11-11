// =========================================================================
// PROJECT_A1 — UNIFIED DUAL-BUILD ESP32 FIRMWARE
// BUILD A: PROJECT_A1_ML_ENABLED = 1 (TFLite Micro INT8 Inference + Fallback)
// BUILD B: PROJECT_A1_ML_ENABLED = 0 (Deterministic Rule-Based Backup Engine)
// Baud Rate: 115200 | Common Telemetry JSON Protocol
// =========================================================================

#include <Arduino.h>
#include "config.h"
#include "pin_config.h"
#include "protocol.h"
#include "feature_schema.h"
#include "model_config.h"

// Hardware and Processing Modules
#include "adc_manager.h"
#include "dht_manager.h"
#include "baseline_manager.h"
#include "signal_processor.h"
#include "feature_extractor.h"
#include "rule_engine.h"
#include "ml_engine.h"
#include "relay_manager.h"
#include "telemetry_manager.h"

// System Singletons
static ADCManager adcMgr;
static DHTManager dhtMgr;
static BaselineManager baseMgr;
static SignalProcessor sigProc;
#if PROJECT_A1_ML_ENABLED
static MLEngine mlEngine;
#endif
static RelayManager relayMgr;

// State Variables
static unsigned long lastSampleTime = 0;
static float rawFeatures[FEATURE_COUNT];
static float normFeatures[FEATURE_COUNT];
static SensorSample windowBuffer[SLIDING_WINDOW_SIZE];

void setup() {
    Serial.begin(115200);
    delay(1000);

    // Initialize hardware subsystems
    adcMgr.begin();
    dhtMgr.begin();
    relayMgr.begin();
    baseMgr.begin();

    // ML Engine initialization (Only attempts in ML build)
#if PROJECT_A1_ML_ENABLED
    bool mlOk = mlEngine.begin();
    if (mlOk) {
        Serial.println("{\"boot\":\"PROJECT_A1_ESP32\",\"build\":\"ML_ENABLED\",\"status\":\"TFLM_READY\"}");
    } else {
        Serial.println("{\"boot\":\"PROJECT_A1_ESP32\",\"build\":\"ML_ENABLED\",\"status\":\"TFLM_INIT_FAILED_FALLBACK_RULE\"}");
    }
#else
    Serial.println("{\"boot\":\"PROJECT_A1_ESP32\",\"build\":\"RULE_BASED_BACKUP\",\"status\":\"RULE_ENGINE_READY\"}");
#endif
}

void loop() {
    unsigned long now = millis();

    if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
        lastSampleTime = now;

        // 1. Acquire raw sensor signals
        int mq2_adc = adcMgr.readMQ2();
        int mq135_adc = adcMgr.readMQ135();

        float temp_c = 25.0f;
        float hum_pct = 50.0f;
        bool hasDHT = dhtMgr.read(temp_c, hum_pct);

        // 2. Hardware Diagnostics (Open/Short fault checking)
        bool mq2_fault = adcMgr.isMQ2Fault(mq2_adc);
        bool mq135_fault = adcMgr.isMQ135Fault(mq135_adc);
        bool sensorFault = (mq2_fault || mq135_fault);

        // 3. Update Baseline tracking
        if (!sensorFault) {
            baseMgr.update(mq2_adc, mq135_adc);
        }

        // 4. Determine Monitoring State
        MonitoringState monState = STATE_LIVE_MONITORING;
        if (sensorFault) {
            monState = STATE_SENSOR_FAULT;
        } else if (!baseMgr.isWarmupComplete()) {
            monState = STATE_STARTUP_WARMUP;
        }

        // 5. Append sample to 10-sample sliding window
        sigProc.addSample(mq2_adc, mq135_adc, temp_c, hum_pct, !sensorFault);

        // 6. Dual Inference Evaluation Layer
        const char* modeName = PROJECT_A1_ML_ENABLED ? "ML" : "BACKUP";
        const char* inferenceEngine = PROJECT_A1_ML_ENABLED ? "TFLITE_INT8" : "RULE_ENGINE";
        const char* inferenceStatus = "WAITING_WARMUP";
        const char* inferenceClass = "UNKNOWN";
        float inferenceConf = 0.0f;
        bool hasConf = false;
        HazardState hazState = HAZARD_UNKNOWN;
        bool relayCmd = false;

        // Always compute Rule-Based Assessment
        RuleEvaluationResult ruleRes = RuleEngine::evaluate(
            mq2_adc, mq135_adc,
            baseMgr.getBaselineMQ2(),
            baseMgr.getBaselineMQ135(),
            sensorFault
        );

        if (monState == STATE_SENSOR_FAULT) {
            hazState = HAZARD_SENSOR_FAULT;
            inferenceStatus = "SENSOR_FAULT";
            inferenceClass = "UNKNOWN";
            relayCmd = false; // Decoupled safety rule
        } else if (monState == STATE_STARTUP_WARMUP) {
            hazState = HAZARD_NORMAL_BASELINE;
            inferenceStatus = "WARMUP_CALIBRATION";
            inferenceClass = "NORMAL_BASELINE";
            relayCmd = false;
        } else {
            // Live monitoring state: extract 11 features if window full
            bool featuresReady = false;
            if (sigProc.isWindowFull()) {
                sigProc.getOrderedWindow(windowBuffer);
                featuresReady = FeatureExtractor::extractFeatures(
                    windowBuffer,
                    SLIDING_WINDOW_SIZE,
                    baseMgr.getBaselineMQ2(),
                    baseMgr.getBaselineMQ135(),
                    rawFeatures
                );
                if (featuresReady) {
                    FeatureExtractor::standardizeFeatures(rawFeatures, normFeatures);
                }
            }

#if PROJECT_A1_ML_ENABLED
            // Try ML Engine if available and initialized
            if (mlEngine.isReady() && featuresReady) {
                MLEvaluationResult mlRes = mlEngine.predict(normFeatures);
                inferenceStatus = mlRes.status;
                inferenceClass = mlRes.predictedClass;
                inferenceConf = mlRes.confidence;
                hasConf = (mlRes.confidence > 0.0f);

                if (mlRes.success) {
                    // Valid ML output
                    if (strcmp(mlRes.predictedClass, "NORMAL_BASELINE") == 0) {
                        hazState = HAZARD_NORMAL_BASELINE;
                    } else if (strcmp(mlRes.predictedClass, "SMOKE") == 0) {
                        hazState = HAZARD_CRITICAL;
                    } else if (strcmp(mlRes.predictedClass, "VOC_RESPONSE") == 0 || strcmp(mlRes.predictedClass, "MIXTURE") == 0) {
                        hazState = HAZARD_WARNING;
                    }
                    relayCmd = ruleRes.relayCommand; // Safety interlock remains independent
                } else {
                    // ML failed, OOD, or low confidence -> Fallback to Rule Engine!
                    inferenceEngine = "FALLBACK_RULE_ENGINE";
                    hazState = ruleRes.hazardState;
                    relayCmd = ruleRes.relayCommand;
                }
            } else {
                // Window not ready or ML engine failed to initialize
                inferenceEngine = "FALLBACK_RULE_ENGINE";
                inferenceStatus = featuresReady ? "RULE_EVALUATED" : "WINDOW_ACCUMULATING";
                inferenceClass = ruleRes.patternName;
                hazState = ruleRes.hazardState;
                relayCmd = ruleRes.relayCommand;
            }
#else
            // Rule-based Build B
            inferenceEngine = "RULE_ENGINE";
            inferenceStatus = featuresReady ? "VALID" : "WINDOW_ACCUMULATING";
            inferenceClass = ruleRes.patternName;
            hazState = ruleRes.hazardState;
            relayCmd = ruleRes.relayCommand;
#endif
        }

        // 7. Enforce Relay Actuation Output
        relayMgr.setCommand(relayCmd);

        // 8. Publish Common JSON Telemetry Protocol
        TelemetryManager::publish(
            modeName,
            now,
            mq2_adc,
            mq135_adc,
            temp_c,
            hum_pct,
            hasDHT,
            mq2_fault,
            mq135_fault,
            monState,
            hazState,
            inferenceEngine,
            inferenceStatus,
            inferenceClass,
            inferenceConf,
            hasConf,
            relayCmd,
            relayMgr.getFeedbackStatus()
        );
    }
}
