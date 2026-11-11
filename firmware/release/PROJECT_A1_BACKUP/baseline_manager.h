#pragma once

#include <Arduino.h>
#include "config.h"

class BaselineManager {
private:
    float baselineMQ2 = DEFAULT_BASELINE_MQ2;
    float baselineMQ135 = DEFAULT_BASELINE_MQ135;
    bool isCalibrated = false;
    unsigned long warmupStartTime = 0;
    
    // Accumulators during warm-up
    double sumMQ2 = 0;
    double sumMQ135 = 0;
    unsigned long sampleCount = 0;

public:
    void begin() {
        warmupStartTime = millis();
        baselineMQ2 = DEFAULT_BASELINE_MQ2;
        baselineMQ135 = DEFAULT_BASELINE_MQ135;
        isCalibrated = false;
        sumMQ2 = 0;
        sumMQ135 = 0;
        sampleCount = 0;
    }

    void update(int mq2_adc, int mq135_adc) {
        if (!isCalibrated) {
            sumMQ2 += mq2_adc;
            sumMQ135 += mq135_adc;
            sampleCount++;

            if (millis() - warmupStartTime >= WARMUP_DURATION_MS && sampleCount > 20) {
                baselineMQ2 = (float)(sumMQ2 / sampleCount);
                baselineMQ135 = (float)(sumMQ135 / sampleCount);
                isCalibrated = true;
            }
        }
    }

    float getBaselineMQ2() const { return baselineMQ2; }
    float getBaselineMQ135() const { return baselineMQ135; }
    bool isWarmupComplete() const { return isCalibrated; }
    float getWarmupProgressPct() const {
        if (isCalibrated) return 100.0f;
        unsigned long elapsed = millis() - warmupStartTime;
        return min(100.0f, ((float)elapsed / WARMUP_DURATION_MS) * 100.0f);
    }
};
