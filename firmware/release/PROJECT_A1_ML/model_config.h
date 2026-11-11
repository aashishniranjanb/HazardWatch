#pragma once

// =========================================================================
// TINYML MODEL CONFIGURATION & OPERATING CONSTRAINTS
// =========================================================================

#define MODEL_NAME              "compact_mlp_int8_ops"
#define MODEL_VERSION           "3.0.0"

#define MODEL_INPUT_CHANNELS    11
#define MODEL_OUTPUT_CLASSES    4
#define TFLM_TENSOR_ARENA_SIZE  8192    // 8 KB internal SRAM buffer

// Model Class Registry (Canonical mapping)
static const char* MODEL_CLASSES[MODEL_OUTPUT_CLASSES] = {
    "MIXTURE",
    "NORMAL_BASELINE",
    "SMOKE",
    "VOC_RESPONSE"
};

// Experimental Out-of-Distribution Distance Boundary
#define OOD_Z_SCORE_THRESHOLD   4.0f    // Max normalized distance
#define MIN_CONFIDENCE_THRESHOLD 0.60f   // Minimum acceptable softmax probability
