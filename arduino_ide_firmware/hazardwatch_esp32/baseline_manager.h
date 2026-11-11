#pragma once

#include <Arduino.h>
#include "config.h"
#include "sensor_manager.h"

class BaselineManager {
private:
    uint32_t baselineCount = 0;
    double baselineMq2Sum = 0.0;
    double baselineMq135Sum = 0.0;
    float baselineMq2 = DEFAULT_BASELINE_MQ2;
    float baselineMq135 = DEFAULT_BASELINE_MQ135;
    bool baselineReady = false;

public:
    void begin() {
        baselineCount = 0;
        baselineMq2Sum = 0.0;
        baselineMq135Sum = 0.0;
        baselineMq2 = DEFAULT_BASELINE_MQ2;
        baselineMq135 = DEFAULT_BASELINE_MQ135;
        baselineReady = false;
    }

    void update(const SensorData& s) {
        if (baselineReady || !s.mq2Valid || !s.mq135Valid) return;

        baselineMq2Sum += s.mq2;
        baselineMq135Sum += s.mq135;
        baselineCount++;

        if (baselineCount >= BASELINE_SAMPLES) {
            baselineMq2 = (float)(baselineMq2Sum / baselineCount);
            baselineMq135 = (float)(baselineMq135Sum / baselineCount);
            baselineReady = true;
        }
    }

    bool isReady() const { return baselineReady; }
    float getMQ2Baseline() const { return baselineMq2; }
    float getMQ135Baseline() const { return baselineMq135; }
    uint32_t getSampleCount() const { return baselineCount; }
};
