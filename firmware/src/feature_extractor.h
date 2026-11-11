#pragma once

#include <Arduino.h>
#include <math.h>
#include "signal_processor.h"
#include "feature_schema.h"

class FeatureExtractor {
public:
    static bool extractFeatures(
        const SensorSample* window,
        int windowSize,
        float base_mq2,
        float base_mq135,
        float* outFeatures
    ) {
        if (windowSize < 2) return false;

        float sum_mq2 = 0;
        float sum_mq135 = 0;
        int min_mq2 = 4096, max_mq2 = -1;
        int min_mq135 = 4096, max_mq135 = -1;

        for (int i = 0; i < windowSize; i++) {
            int q2 = window[i].mq2_adc;
            int q135 = window[i].mq135_adc;

            sum_mq2 += q2;
            sum_mq135 += q135;

            if (q2 < min_mq2) min_mq2 = q2;
            if (q2 > max_mq2) max_mq2 = q2;

            if (q135 < min_mq135) min_mq135 = q135;
            if (q135 > max_mq135) max_mq135 = q135;
        }

        float mean_mq2 = sum_mq2 / windowSize;
        float mean_mq135 = sum_mq135 / windowSize;

        // 1-4. Baseline-Relative Features
        float mq2_delta_base = mean_mq2 - base_mq2;
        float mq135_delta_base = mean_mq135 - base_mq135;
        float mq2_ratio_base = mean_mq2 / (base_mq2 + 1e-4f);
        float mq135_ratio_base = mean_mq135 / (base_mq135 + 1e-4f);

        // 5. Cross-Sensor Interaction Feature
        float cross_ratio = mean_mq2 / (mean_mq135 + 1e-4f);

        // 6-7. Slopes (ADC/sec with dt = 0.5s)
        float t_mean = (windowSize - 1) * 0.5f / 2.0f;
        float num_mq2 = 0, num_mq135 = 0, denom = 0;

        for (int i = 0; i < windowSize; i++) {
            float t = i * 0.5f;
            float dt = t - t_mean;
            num_mq2 += dt * (window[i].mq2_adc - mean_mq2);
            num_mq135 += dt * (window[i].mq135_adc - mean_mq135);
            denom += dt * dt;
        }
        float slope_mq2 = (denom > 1e-5f) ? (num_mq2 / denom) : 0.0f;
        float slope_mq135 = (denom > 1e-5f) ? (num_mq135 / denom) : 0.0f;

        // 8-9. Standard Deviation
        float var_mq2 = 0, var_mq135 = 0;
        for (int i = 0; i < windowSize; i++) {
            float d2 = window[i].mq2_adc - mean_mq2;
            float d135 = window[i].mq135_adc - mean_mq135;
            var_mq2 += d2 * d2;
            var_mq135 += d135 * d135;
        }
        float std_mq2 = sqrtf(var_mq2 / (windowSize - 1));
        float std_mq135 = sqrtf(var_mq135 / (windowSize - 1));

        // 10-11. Delta Range in Window
        float range_mq2 = (float)(max_mq2 - min_mq2);
        float range_mq135 = (float)(max_mq135 - min_mq135);

        // Populate in EXACT order of FeatureIndex
        outFeatures[FEAT_MQ2_DELTA_BASELINE] = mq2_delta_base;
        outFeatures[FEAT_MQ135_DELTA_BASELINE] = mq135_delta_base;
        outFeatures[FEAT_MQ2_RATIO_BASELINE] = mq2_ratio_base;
        outFeatures[FEAT_MQ135_RATIO_BASELINE] = mq135_ratio_base;
        outFeatures[FEAT_GAS_RATIO_MQ2_TO_MQ135] = cross_ratio;
        outFeatures[FEAT_MQ2_SLOPE] = slope_mq2;
        outFeatures[FEAT_MQ135_SLOPE] = slope_mq135;
        outFeatures[FEAT_MQ2_STD] = std_mq2;
        outFeatures[FEAT_MQ135_STD] = std_mq135;
        outFeatures[FEAT_MQ2_DELTA_WINDOW] = range_mq2;
        outFeatures[FEAT_MQ135_DELTA_WINDOW] = range_mq135;

        return true;
    }

    static void standardizeFeatures(const float* rawFeatures, float* outNormalized) {
        for (int i = 0; i < FEATURE_COUNT; i++) {
            outNormalized[i] = (rawFeatures[i] - SCALER_MEAN[i]) / SCALER_SCALE[i];
        }
    }
};
