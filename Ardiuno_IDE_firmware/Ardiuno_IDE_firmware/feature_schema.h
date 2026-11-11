#pragma once

#include <Arduino.h>

// =========================================================================
// EXACT 11-FEATURE SCHEMA & NORMALIZATION SCALING CONSTANTS
// Conforms directly to feature_schema_v2.yaml & scaler_m2_7.joblib
// =========================================================================

static constexpr size_t FEATURE_COUNT = 11;

enum FeatureIndex {
    FEAT_MQ2_DELTA_BASELINE = 0,
    FEAT_MQ135_DELTA_BASELINE,
    FEAT_MQ2_RATIO_BASELINE,
    FEAT_MQ135_RATIO_BASELINE,
    FEAT_GAS_RATIO_MQ2_TO_MQ135,
    FEAT_MQ2_SLOPE,
    FEAT_MQ135_SLOPE,
    FEAT_MQ2_STD,
    FEAT_MQ135_STD,
    FEAT_MQ2_DELTA_WINDOW,
    FEAT_MQ135_DELTA_WINDOW
};

// Trained StandardScaler Mean vector
static const float SCALER_MEAN[FEATURE_COUNT] = {
    194.755155f,   // mq2_delta_baseline
    189.242228f,   // mq135_delta_baseline
    1.556443f,     // mq2_ratio_baseline
    1.130512f,     // mq135_ratio_baseline
    0.328509f,     // gas_ratio_mq2_to_mq135
    -0.106840f,    // mq2_slope
    -0.063746f,    // mq135_slope
    16.656122f,    // mq2_std
    21.972149f,    // mq135_std
    51.571433f,    // mq2_delta_window
    69.947020f     // mq135_delta_window
};

// Trained StandardScaler Scale vector
static const float SCALER_SCALE[FEATURE_COUNT] = {
    332.701391f,   // mq2_delta_baseline
    314.119626f,   // mq135_delta_baseline
    0.950575f,     // mq2_ratio_baseline
    0.216634f,     // mq135_ratio_baseline
    0.182731f,     // gas_ratio_mq2_to_mq135
    11.335395f,    // mq2_slope
    10.898889f,    // mq135_slope
    40.754281f,    // mq2_std
    38.787090f,    // mq135_std
    101.551394f,   // mq2_delta_window
    98.909952f     // mq135_delta_window
};
