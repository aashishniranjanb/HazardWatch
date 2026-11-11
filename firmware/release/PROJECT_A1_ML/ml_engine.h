#pragma once

#include <Arduino.h>
#include "model_config.h"
#include "feature_schema.h"

#if PROJECT_A1_ML_ENABLED

#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"
#include "models/model_data.h"

struct MLEvaluationResult {
    bool success;
    const char* predictedClass;
    float confidence;
    bool isOOD;
    float maxAbsZ;
    const char* status;
};

class MLEngine {
private:
    uint8_t tensor_arena[TFLM_TENSOR_ARENA_SIZE];
    tflite::MicroErrorReporter micro_error_reporter;
    tflite::ErrorReporter* error_reporter = nullptr;
    const tflite::Model* model = nullptr;
    tflite::MicroInterpreter* interpreter = nullptr;
    TfLiteTensor* input = nullptr;
    TfLiteTensor* output = nullptr;
    bool initialized = false;

public:
    bool begin() {
        error_reporter = &micro_error_reporter;
        model = tflite::GetModel(g_model_data);
        if (model->version() != TFLITE_SCHEMA_VERSION) {
            initialized = false;
            return false;
        }

        static tflite::AllOpsResolver resolver;
        static tflite::MicroInterpreter static_interpreter(
            model, resolver, tensor_arena, TFLM_TENSOR_ARENA_SIZE, error_reporter
        );
        interpreter = &static_interpreter;

        TfLiteStatus allocate_status = interpreter->AllocateTensors();
        if (allocate_status != kTfLiteOk) {
            initialized = false;
            return false;
        }

        input = interpreter->input(0);
        output = interpreter->output(0);
        initialized = true;
        return true;
    }

    bool isReady() const { return initialized; }

    MLEvaluationResult predict(const float* normalizedFeatures) {
        MLEvaluationResult res;
        res.success = false;
        res.predictedClass = "UNKNOWN";
        res.confidence = 0.0f;
        res.isOOD = false;
        res.maxAbsZ = 0.0f;
        res.status = "NOT_INITIALIZED";

        if (!initialized) return res;

        // 1. Check Out-of-Distribution boundary
        float max_z = 0.0f;
        for (int i = 0; i < FEATURE_COUNT; i++) {
            float az = fabsf(normalizedFeatures[i]);
            if (az > max_z) max_z = az;
        }
        res.maxAbsZ = max_z;
        if (max_z > OOD_Z_SCORE_THRESHOLD) {
            res.isOOD = true;
            res.predictedClass = "UNKNOWN";
            res.status = "OUT_OF_DISTRIBUTION";
            return res;
        }

        // 2. Populate Model Input Tensor
        for (int i = 0; i < FEATURE_COUNT; i++) {
            input->data.f[i] = normalizedFeatures[i];
        }

        // 3. Invoke Model
        TfLiteStatus invoke_status = interpreter->Invoke();
        if (invoke_status != kTfLiteOk) {
            res.status = "INFERENCE_FAILED";
            return res;
        }

        // 4. Softmax Evaluation
        int best_idx = -1;
        float best_prob = -1.0f;
        for (int i = 0; i < MODEL_OUTPUT_CLASSES; i++) {
            float p = output->data.f[i];
            if (p > best_prob) {
                best_prob = p;
                best_idx = i;
            }
        }

        if (best_prob < MIN_CONFIDENCE_THRESHOLD) {
            res.isOOD = true;
            res.predictedClass = "UNKNOWN";
            res.status = "LOW_CONFIDENCE";
            res.confidence = best_prob;
            return res;
        }

        res.success = true;
        res.predictedClass = MODEL_CLASSES[best_idx];
        res.confidence = best_prob;
        res.status = "VALID";
        return res;
    }
};

#else

// Dummy stub for Rule-Based Build B (Zero TensorFlow dependency)
struct MLEvaluationResult {
    bool success = false;
    const char* predictedClass = "UNKNOWN";
    float confidence = 0.0f;
    bool isOOD = false;
    float maxAbsZ = 0.0f;
    const char* status = "DISABLED_IN_BACKUP_BUILD";
};

class MLEngine {
public:
    bool begin() { return false; }
    bool isReady() const { return false; }
    MLEvaluationResult predict(const float*) {
        MLEvaluationResult res;
        return res;
    }
};

#endif
