#pragma once

#include <Arduino.h>
#include "config.h"
#include "protocol.h"
#include "sensor_manager.h"

class TelemetryManager {
public:
    static void publish(
        uint32_t sequence,
        const SensorData& s,
        bool baselineReady,
        float baseMq2,
        float baseMq135,
        MonitorState monState,
        HazardState hazState,
        size_t windowCount,
        const char* inferenceEngine,
        const char* inferenceStatus,
        const char* inferenceClass,
        float confidence,
        bool hasConfidence,
        bool relayCmd,
        const char* relayFeedback
    ) {
        Serial.print("{\"type\":\"telemetry\",\"device_id\":\"");
        Serial.print(DEVICE_ID);
        Serial.print("\",\"sequence\":");
        Serial.print(sequence);
        Serial.print(",\"timestamp_ms\":");
        Serial.print(s.ts);
        Serial.print(",\"build_mode\":\"");
        Serial.print(PROJECT_A1_ML_ENABLED ? "ML_ENABLED" : "BACKUP_RULES");
        Serial.print("\",\"monitoring_state\":\"");
        Serial.print(stateName(monState));
        Serial.print("\",\"hazard_state\":\"");
        Serial.print(hazardName(hazState));
        Serial.print("\",\"sensors\":{");

        if (s.mq2Valid) {
            Serial.print("\"mq2_adc\":");
            Serial.print(s.mq2);
        } else {
            Serial.print("\"mq2_adc\":null");
        }

        if (s.mq135Valid) {
            Serial.print(",\"mq135_adc\":");
            Serial.print(s.mq135);
        } else {
            Serial.print(",\"mq135_adc\":null");
        }

        if (s.dhtValid) {
            Serial.print(",\"temperature_c\":");
            Serial.print(s.temperature, 1);
            Serial.print(",\"humidity_percent\":");
            Serial.print(s.humidity, 1);
        } else {
            Serial.print(",\"temperature_c\":null,\"humidity_percent\":null");
        }
        Serial.print("},\"baseline\":{");
        Serial.print("\"ready\":");
        Serial.print(baselineReady ? "true" : "false");
        if (baselineReady) {
            Serial.print(",\"mq2_adc\":");
            Serial.print(baseMq2, 1);
            Serial.print(",\"mq135_adc\":");
            Serial.print(baseMq135, 1);
        } else {
            Serial.print(",\"mq2_adc\":null,\"mq135_adc\":null");
        }
        Serial.print("},\"window\":{");
        Serial.print("\"samples\":");
        Serial.print(windowCount);
        Serial.print(",\"required\":");
        Serial.print(WINDOW_SIZE);
        Serial.print("},\"inference\":{");
        Serial.print("\"engine\":\"");
        Serial.print(inferenceEngine);
        Serial.print("\",\"status\":\"");
        Serial.print(inferenceStatus);
        Serial.print("\",\"class\":\"");
        Serial.print(inferenceClass);
        Serial.print("\",\"confidence\":");
        if (hasConfidence) {
            Serial.print(confidence, 4);
        } else {
            Serial.print("null");
        }
        Serial.print("},\"relay\":{");
        Serial.print("\"command\":\"");
        Serial.print(relayCmd ? "ENABLED" : "DISABLED");
        Serial.print("\",\"feedback\":\"");
        Serial.print(relayFeedback);
        Serial.print("\"}}\n");
    }

    static void publishBoot(const char* buildName, const char* status) {
        Serial.print("{\"type\":\"firmware_status\",\"device_id\":\"");
        Serial.print(DEVICE_ID);
        Serial.print("\",\"build\":\"");
        Serial.print(buildName);
        Serial.print("\",\"version\":\"");
        Serial.print(FIRMWARE_VERSION);
        Serial.print("\",\"status\":\"");
        Serial.print(status);
        Serial.print("\",\"relay_policy\":\"SAFE_OFF_DISABLED\"}\n");
    }
};
