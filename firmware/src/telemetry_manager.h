#pragma once

#include <Arduino.h>
#include "protocol.h"
#include "config.h"

class TelemetryManager {
public:
    static void publish(
        const char* modeName,
        unsigned long timestamp_ms,
        int mq2_adc,
        int mq135_adc,
        float temp_c,
        float hum_pct,
        bool hasDHT,
        bool mq2_fault,
        bool mq135_fault,
        MonitoringState monState,
        HazardState hazState,
        const char* inferenceEngine,
        const char* inferenceStatus,
        const char* inferenceClass,
        float inferenceConf,
        bool hasConf,
        bool relayCommand,
        const char* relayFeedback
    ) {
        Serial.print("{\"device_id\":\"");
        Serial.print(DEVICE_ID);
        Serial.print("\",\"mode\":\"");
        Serial.print(modeName);
        Serial.print("\",\"provenance\":\"LIVE_HARDWARE\",");
        Serial.print("\"timestamp_ms\":");
        Serial.print(timestamp_ms);
        Serial.print(",\"sensors\":{");

        // MQ2
        if (!mq2_fault) {
            Serial.print("\"mq2_adc\":");
            Serial.print(mq2_adc);
        } else {
            Serial.print("\"mq2_adc\":null");
        }

        // MQ135
        if (!mq135_fault) {
            Serial.print(",\"mq135_adc\":");
            Serial.print(mq135_adc);
        } else {
            Serial.print(",\"mq135_adc\":null");
        }

        // Temp & Hum
        if (hasDHT) {
            Serial.print(",\"temperature_c\":");
            Serial.print(temp_c, 1);
            Serial.print(",\"humidity_percent\":");
            Serial.print(hum_pct, 1);
        } else {
            Serial.print(",\"temperature_c\":null,\"humidity_percent\":null");
        }
        Serial.print("},");

        // Monitoring and Hazard States
        Serial.print("\"monitoring_state\":\"");
        Serial.print(monitoringStateToString(monState));
        Serial.print("\",\"hazard_state\":\"");
        Serial.print(hazardStateToString(hazState));
        Serial.print("\",\"inference\":{");

        // Inference block
        Serial.print("\"engine\":\"");
        Serial.print(inferenceEngine);
        Serial.print("\",\"status\":\"");
        Serial.print(inferenceStatus);
        Serial.print("\",\"class\":\"");
        Serial.print(inferenceClass);
        Serial.print("\",\"confidence\":");
        if (hasConf) {
            Serial.print(inferenceConf, 4);
        } else {
            Serial.print("null");
        }
        Serial.print("},");

        // Relay block
        Serial.print("\"relay\":{");
        Serial.print("\"command\":\"");
        Serial.print(relayCommand ? "ENABLED" : "DISABLED");
        Serial.print("\",\"feedback\":\"");
        Serial.print(relayFeedback);
        Serial.print("\"}}\n");
    }
};
