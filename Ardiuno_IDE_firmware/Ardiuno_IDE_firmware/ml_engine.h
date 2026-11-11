#pragma once

#include <Arduino.h>
#include "config.h"

#if PROJECT_A1_ML_ENABLED

#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"
#include "models/model_data.h"

struct MLPrediction {
    bool ok;
    const char* label;
    float confidence;
    bool isOOD;
    float maxZ;
    const char* status;
};

class MLEngine {
private:
    static constexpr size_t ARENA_SIZE = 8192;
    uint8_t arena[ARENA_SIZE];
    tflite::MicroErrorReporter errorReporter;
    const tflite::Model* model = nullptr;
    tflite::MicroInterpreter* interpreter = nullptr;
    TfLiteTensor* inputTensor = nullptr;
    TfLiteTensor* outputTensor = nullptr;
    bool ready = false;

    static constexpr const char* CLASSES[4] = {
        "MIXTURE",
        "NORMAL_BASELINE",
        "SMOKE",
        "VOC_RESPONSE"
    };

public:
    bool begin() {
        model = tflite::GetModel(g_model_data);
        if (model->version() != TFLITE_SCHEMA_VERSION) {
            ready = false;
            return false;
        }

        static tflite::AllOpsResolver resolver;
        static tflite::MicroInterpreter static_interpreter(
            model, resolver, arena, ARENA_SIZE, &errorReporter
        );
        interpreter = &static_interpreter;

        if (interpreter->AllocateTensors() != kTfLiteOk) {
            ready = false;
            return false;
        }

        inputTensor = interpreter->input(0);
        outputTensor = interpreter->output(0);
        ready = true;
        return true;
    }

    bool isReady() const { return ready; }

    MLPrediction predict(const float* normalizedFeatures) {
        MLPrediction p{};
        p.ok = false;
        p.label = "UNKNOWN";
        p.confidence = 0.0f;
        p.isOOD = false;
        p.maxZ = 0.0f;
        p.status = "NOT_READY";

        if (!ready) return p;

        // OOD check
        float maxZ = 0.0f;
        for (size_t i = 0; i < 11; i++) {
            float az = fabsf(normalizedFeatures[i]);
            if (az > maxZ) maxZ = az;
        }
        p.maxZ = maxZ;

        if (maxZ > OOD_Z_SCORE_THRESHOLD) {
            p.isOOD = true;
            p.label = "UNKNOWN";
            p.status = "OUT_OF_DISTRIBUTION";
            return p;
        }

        for (size_t i = 0; i < 11; i++) {
            inputTensor->data.f[i] = normalizedFeatures[i];
        }

        if (interpreter->Invoke() != kTfLiteOk) {
            p.status = "INFERENCE_FAILED";
            return p;
        }

        int bestIdx = -1;
        float bestProb = -1.0f;
        for (int i = 0; i < 4; i++) {
            float prob = outputTensor->data.f[i];
            if (prob > bestProb) {
                bestProb = prob;
                bestIdx = i;
            }
        }

        if (bestProb < MIN_CONFIDENCE_THRESHOLD) {
            p.isOOD = true;
            p.label = "UNKNOWN";
            p.status = "LOW_CONFIDENCE";
            p.confidence = bestProb;
            return p;
        }

        p.ok = true;
        p.label = CLASSES[bestIdx];
        p.confidence = bestProb;
        p.status = "VALID";
        return p;
    }
};

#else

// Non-ML Backup Stub
struct MLPrediction {
    bool ok = false;
    const char* label = "UNKNOWN";
    float confidence = 0.0f;
    bool isOOD = false;
    float maxZ = 0.0f;
    const char* status = "DISABLED_IN_BACKUP";
};

class MLEngine {
public:
    bool begin() { return false; }
    bool isReady() const { return false; }
    MLPrediction predict(const float*) {
        MLPrediction p{};
        return p;
    }
};

#endif
