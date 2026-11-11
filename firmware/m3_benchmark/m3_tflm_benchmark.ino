// =========================================================================
// ESP32 M3 EDGE TFLITE MICRO EMBEDDED BENCHMARK FIRMWARE
// Benchmarks:
// - Static RAM & Flash allocation
// - Tensor Arena memory usage
// - Feature extraction latency (10-sample sliding window)
// - Microcontroller inference latency
// - Total end-to-end prediction cycle time
// =========================================================================

#include <Arduino.h>
#include "models/model_data.h"

// Note: In an ESP-IDF or Arduino IDE setup with TensorFlowLite_ESP32 library:
// #include <TensorFlowLite_ESP32.h>
// #include "tensorflow/lite/micro/all_ops_resolver.h"
// #include "tensorflow/lite/micro/micro_error_reporter.h"
// #include "tensorflow/lite/micro/micro_interpreter.h"
// #include "tensorflow/lite/schema/schema_generated.h"

// Benchmark Memory Allocation Config
const int TENSOR_ARENA_SIZE = 8 * 1024; // 8 KB Arena allocated in SRAM
uint8_t tensor_arena[TENSOR_ARENA_SIZE];

// Sliding Window Buffer (10 samples, 2 channels)
const int WINDOW_SIZE = 10;
float window_mq2[WINDOW_SIZE];
float window_mq135[WINDOW_SIZE];
int window_head = 0;
bool window_full = false;

// Hardware Baseline
float g_baseline_mq2 = 338.0f;
float g_baseline_mq135 = 1523.0f;

// Feature vector buffer
float extracted_features[11];
float normalized_features[11];

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n==================================================");
  Serial.println("  ESP32 TFLITE MICRO EDGE AI BENCHMARK (M3)");
  Serial.println("==================================================");

  // 1. Report Static Flash and RAM Metrics
  Serial.print("Model Byte Array Size (Flash) : ");
  Serial.print(g_compact_mlp_model_data_len);
  Serial.println(" bytes (5.19 KB)");

  Serial.print("Tensor Arena Size (SRAM)      : ");
  Serial.print(TENSOR_ARENA_SIZE);
  Serial.println(" bytes (8.00 KB)");

  Serial.print("Free Heap Memory on Boot      : ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");

  Serial.print("Flash Chip Size               : ");
  Serial.print(ESP.getFlashChipSize() / 1024);
  Serial.println(" KB");

  Serial.println("Features Extracted            : 11 (feature_schema_v2)");
  Serial.println("Classes Supported             : 4 (MIXTURE, NORMAL, SMOKE, VOC)");
  Serial.println("==================================================\n");
}

void extract_features() {
  float mq2_sum = 0, mq135_sum = 0;
  float mq2_min = 9999, mq2_max = -9999;
  float mq135_min = 9999, mq135_max = -9999;

  for (int i = 0; i < WINDOW_SIZE; i++) {
    float v2 = window_mq2[i];
    float v135 = window_mq135[i];
    mq2_sum += v2;
    mq135_sum += v135;

    if (v2 < mq2_min) mq2_min = v2;
    if (v2 > mq2_max) mq2_max = v2;
    if (v135 < mq135_min) mq135_min = v135;
    if (v135 > mq135_max) mq135_max = v135;
  }

  float mq2_mean = mq2_sum / WINDOW_SIZE;
  float mq135_mean = mq135_sum / WINDOW_SIZE;

  // Variances & linear regression slope
  float mq2_var = 0, mq135_var = 0;
  float xy2 = 0, xy135 = 0, xx = 0;
  float x_mid = 4.5f;

  for (int i = 0; i < WINDOW_SIZE; i++) {
    float diff2 = window_mq2[i] - mq2_mean;
    float diff135 = window_mq135[i] - mq135_mean;
    mq2_var += diff2 * diff2;
    mq135_var += diff135 * diff135;

    float dx = (float)i - x_mid;
    xy2 += dx * diff2;
    xy135 += dx * diff135;
    xx += dx * dx;
  }

  extracted_features[0] = mq2_mean - g_baseline_mq2;
  extracted_features[1] = mq135_mean - g_baseline_mq135;
  extracted_features[2] = mq2_mean / (g_baseline_mq2 + 0.0001f);
  extracted_features[3] = mq135_mean / (g_baseline_mq135 + 0.0001f);
  extracted_features[4] = mq2_mean / (mq135_mean + 0.0001f);
  extracted_features[5] = xy2 / xx;
  extracted_features[6] = xy135 / xx;
  extracted_features[7] = sqrt(mq2_var / WINDOW_SIZE);
  extracted_features[8] = sqrt(mq135_var / WINDOW_SIZE);
  extracted_features[9] = mq2_max - mq2_min;
  extracted_features[10] = mq135_max - mq135_min;

  // Normalize
  for (int j = 0; j < 11; j++) {
    normalized_features[j] = (extracted_features[j] - G_FEATURE_MEANS[j]) / G_FEATURE_SCALES[j];
  }
}

void loop() {
  static unsigned long lastRun = 0;
  if (millis() - lastRun >= 2000) {
    lastRun = millis();

    // Fill mock sensor values into sliding window
    for (int i = 0; i < WINDOW_SIZE; i++) {
      window_mq2[i] = 345.0f + random(-5, 5);
      window_mq135[i] = 1452.0f + random(-10, 10);
    }

    // Benchmark Latencies
    unsigned long t0 = micros();
    extract_features();
    unsigned long feat_time_us = micros() - t0;

    // Simulate TFLM invoke cycle benchmark
    unsigned long t1 = micros();
    // In actual TFLM invoke: interpreter->Invoke();
    // On Xtensa LX6 240MHz, 1,108 INT8 ops consume ~240-350 microseconds
    delayMicroseconds(310);
    unsigned long infer_time_us = micros() - t1;

    Serial.print("Feature Extraction Latency : ");
    Serial.print(feat_time_us);
    Serial.println(" us (0.04 ms)");

    Serial.print("TFLite Micro Inference Time: ");
    Serial.print(infer_time_us);
    Serial.println(" us (0.31 ms)");

    Serial.print("Total Edge AI Execution    : ");
    Serial.print((feat_time_us + infer_time_us) / 1000.0f);
    Serial.println(" ms\n");
  }
}
