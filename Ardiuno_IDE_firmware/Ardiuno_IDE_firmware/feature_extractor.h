#pragma once

#include <Arduino.h>
#include <math.h>
#include "config.h"
#include "feature_schema.h"
#include "sensor_manager.h"

class FeatureExtractor {
public:
    static bool extract(
        const SensorData* window,
        size_t count,
        float baseMq2,
        float baseMq135,
        float* outFeatures
    ) {
        if (count < 2) return false;

        float sum2 = 0.0f;
        float sum135 = 0.0f;
        uint16_t min2 = 4096, max2 = 0;
        uint16_t min135 = 4096, max135 = 0;

        for (size_t i = 0; i < count; i++) {
            uint16_t q2 = window[i].mq2;
            uint16_t q135 = window[i].mq135;
            sum2 += q2;
            sum135 += q135;
            if (q2 < min2) min2 = q2;
            if (q2 > max2) max2 = q2;
            if (q135 < min135) min135 = q135;
            if (q135 > max135) max135 = q135;
        }

        float mean2 = sum2 / count;
        float mean135 = sum135 / count;

        float delta2 = mean2 - baseMq2;
        float delta135 = mean135 - baseMq135;
        float ratio2 = mean2 / (baseMq2 + 1e-4f);
        float ratio135 = mean135 / (baseMq135 + 1e-4f);
        float crossRatio = mean2 / (mean135 + 1e-4f);

        // Linear slope (dt = 0.5s)
        float t_mean = (count - 1) * 0.5f / 2.0f;
        float num2 = 0.0f, num135 = 0.0f, denom = 0.0f;
        for (size_t i = 0; i < count; i++) {
            float dt = (i * 0.5f) - t_mean;
            num2 += dt * (window[i].mq2 - mean2);
            num135 += dt * (window[i].mq135 - mean135);
            denom += dt * dt;
        }
        float slope2 = (denom > 1e-5f) ? (num2 / denom) : 0.0f;
        float slope135 = (denom > 1e-5f) ? (num135 / denom) : 0.0f;

        // Sample standard deviation
        float var2 = 0.0f, var135 = 0.0f;
        for (size_t i = 0; i < count; i++) {
            float d2 = window[i].mq2 - mean2;
            float d135 = window[i].mq135 - mean135;
            var2 += d2 * d2;
            var135 += d135 * d135;
        }
        float std2 = sqrtf(var2 / (count - 1));
        float std135 = sqrtf(var135 / (count - 1));

        float range2 = (float)(max2 - min2);
        float range135 = (float)(max135 - min135);

        outFeatures[FEAT_MQ2_DELTA_BASELINE] = delta2;
        outFeatures[FEAT_MQ135_DELTA_BASELINE] = delta135;
        outFeatures[FEAT_MQ2_RATIO_BASELINE] = ratio2;
        outFeatures[FEAT_MQ135_RATIO_BASELINE] = ratio135;
        outFeatures[FEAT_GAS_RATIO_MQ2_TO_MQ135] = crossRatio;
        outFeatures[FEAT_MQ2_SLOPE] = slope2;
        outFeatures[FEAT_MQ135_SLOPE] = slope135;
        outFeatures[FEAT_MQ2_STD] = std2;
        outFeatures[FEAT_MQ135_STD] = std135;
        outFeatures[FEAT_MQ2_DELTA_WINDOW] = range2;
        outFeatures[FEAT_MQ135_DELTA_WINDOW] = range135;

        return true;
    }

    static void standardize(const float* raw, float* outNorm) {
        for (size_t i = 0; i < FEATURE_COUNT; i++) {
            outNorm[i] = (raw[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];
        }
    }
};
