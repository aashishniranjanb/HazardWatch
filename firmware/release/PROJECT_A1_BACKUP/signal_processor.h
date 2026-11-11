#pragma once

#include <Arduino.h>
#include "config.h"

struct SensorSample {
    unsigned long timestamp_ms;
    int mq2_adc;
    int mq135_adc;
    float temp_c;
    float hum_pct;
    bool valid;
};

class SignalProcessor {
private:
    SensorSample buffer[SLIDING_WINDOW_SIZE];
    int count = 0;
    int head = 0;

public:
    void addSample(int mq2, int mq135, float temp, float hum, bool valid) {
        buffer[head] = { millis(), mq2, mq135, temp, hum, valid };
        head = (head + 1) % SLIDING_WINDOW_SIZE;
        if (count < SLIDING_WINDOW_SIZE) count++;
    }

    bool isWindowFull() const {
        return (count >= SLIDING_WINDOW_SIZE);
    }

    int getCount() const { return count; }

    const SensorSample* getOrderedWindow(SensorSample* outBuffer) const {
        int idx = (count < SLIDING_WINDOW_SIZE) ? 0 : head;
        for (int i = 0; i < count; i++) {
            outBuffer[i] = buffer[(idx + i) % SLIDING_WINDOW_SIZE];
        }
        return outBuffer;
    }
};
