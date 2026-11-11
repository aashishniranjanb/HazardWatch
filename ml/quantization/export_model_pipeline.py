"""
M3 Complete Quantization Parity & Export Script
Exports:
1. ml/artifacts/v3/compact_mlp_int8.tflite (Full Integer Quantized, int8 I/O)
2. ml/artifacts/v3/compact_mlp_quant_ops.tflite (INT8 Ops with Float32 I/O for direct microcontroller ingestion)
3. firmware/models/model_data.h (C++ byte array for ESP32 TFLite Micro runtime)
4. reports/int8_float_parity.csv
"""

import os
import time
import json
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

FEATURE_COLS_V2 = [
    "mq2_delta_baseline",
    "mq135_delta_baseline",
    "mq2_ratio_baseline",
    "mq135_ratio_baseline",
    "gas_ratio_mq2_to_mq135",
    "mq2_slope",
    "mq135_slope",
    "mq2_std",
    "mq135_std",
    "mq2_delta_window",
    "mq135_delta_window"
]

def generate_cpp_header(tflite_bytes: bytes, output_path: str, scaler_mean, scaler_scale):
    """
    Generates a production C++ header containing the model byte array and exact preprocessing constants.
    """
    hex_lines = []
    for i, byte in enumerate(tflite_bytes):
        if i % 12 == 0:
            hex_lines.append("\n  ")
        hex_lines.append(f"0x{byte:02x}, ")

    c_array_content = "".join(hex_lines)

    mean_str = ", ".join([f"{v:.6f}f" for v in scaler_mean])
    scale_str = ", ".join([f"{v:.6f}f" for v in scaler_scale])

    header = f"""// =========================================================================
// AUTOMATICALLY GENERATED TENSORFLOW LITE MICRO EMBEDDED MODEL HEADER
// Target: ESP32 DevKit V1 (Xtensa dual-core 240MHz)
// Model: Compact Keras MLP (M2.7 Architecture)
// Model Size: {len(tflite_bytes)} bytes
// Quantization: INT8 Quantized Ops with Float32 Ingestion
// Feature Dimensions: 11
// Output Classes: 4 (0: MIXTURE, 1: NORMAL_BASELINE, 2: SMOKE, 3: VOC_RESPONSE)
// =========================================================================

#ifndef MODEL_DATA_H_
#define MODEL_DATA_H_

#include <stdint.h>

#ifdef __has_attribute
#define TFLM_ALIGNED(x) __attribute__((aligned(x)))
#else
#define TFLM_ALIGNED(x)
#endif

// Model binary byte array
const unsigned int g_compact_mlp_model_data_len = {len(tflite_bytes)};
const unsigned char g_compact_mlp_model_data[] TFLM_ALIGNED(16) = {{{c_array_content}
}};

// Preprocessing Constants (Fitted strictly on Training partition)
const int G_NUM_FEATURES = 11;

const float G_FEATURE_MEANS[11] = {{
  {mean_str}
}};

const float G_FEATURE_SCALES[11] = {{
  {scale_str}
}};

// Classification Taxonomy Labels
const char* const G_CLASS_LABELS[4] = {{
  "MIXTURE",
  "NORMAL_BASELINE",
  "SMOKE",
  "VOC_RESPONSE"
}};

#endif // MODEL_DATA_H_
"""
    with open(output_path, "w") as f:
        f.write(header)
    print(f"Generated C++ embedded model header: {output_path} ({len(tflite_bytes)} bytes)")

def run_quantization_and_export():
    from ml.training.train_m2_7 import load_all_trials_and_partition

    train_df, val_df, test_a_df, held_out_b_df = load_all_trials_and_partition()
    scaler = joblib.load("ml/artifacts/v2_7/scaler_m2_7.joblib")
    le = joblib.load("ml/artifacts/v2_7/label_encoder_m2_7.joblib")
    classes = list(le.classes_)

    X_train = scaler.transform(train_df[FEATURE_COLS_V2].to_numpy())
    X_test_b = scaler.transform(held_out_b_df[FEATURE_COLS_V2].to_numpy())
    y_test_b = le.transform(held_out_b_df["condition"].to_numpy())

    model = keras.models.load_model("ml/artifacts/v2_7/compact_mlp_m2_7.keras")

    def rep_dataset():
        for i in range(len(X_train)):
            yield [X_train[i:i+1].astype(np.float32)]

    # 1. Full INT8 conversion with float IO for numerical stability
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = rep_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    tflite_ops_int8 = converter.convert()

    tflite_path = "ml/artifacts/v3/compact_mlp_int8_ops.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_ops_int8)

    # 2. Benchmark Keras Float32 vs TFLite INT8 on Held-Out Board B
    t0 = time.time()
    keras_probs = model.predict(X_test_b, verbose=0)
    keras_latency = ((time.time() - t0) / len(X_test_b)) * 1000
    keras_preds = np.argmax(keras_probs, axis=1)

    interp = tf.lite.Interpreter(model_content=tflite_ops_int8)
    interp.allocate_tensors()
    in_d = interp.get_input_details()[0]
    out_d = interp.get_output_details()[0]

    t0 = time.time()
    tflite_preds = []
    tflite_probs = []
    for i in range(len(X_test_b)):
        interp.set_tensor(in_d["index"], X_test_b[i:i+1].astype(np.float32))
        interp.invoke()
        out = interp.get_tensor(out_d["index"])[0]
        tflite_probs.append(out)
        tflite_preds.append(np.argmax(out))
    tflite_latency = ((time.time() - t0) / len(X_test_b)) * 1000
    tflite_preds = np.array(tflite_preds)
    tflite_probs = np.array(tflite_probs)

    acc_k = accuracy_score(y_test_b, keras_preds)
    acc_t = accuracy_score(y_test_b, tflite_preds)

    _, _, f1_k, _ = precision_recall_fscore_support(y_test_b, keras_preds, average="macro", zero_division=0)
    _, _, f1_t, _ = precision_recall_fscore_support(y_test_b, tflite_preds, average="macro", zero_division=0)

    p_k, r_k, _, _ = precision_recall_fscore_support(y_test_b, keras_preds, average=None, zero_division=0)
    p_t, r_t, _, _ = precision_recall_fscore_support(y_test_b, tflite_preds, average=None, zero_division=0)

    size_keras_kb = os.path.getsize("ml/artifacts/v2_7/compact_mlp_m2_7.keras") / 1024.0
    size_tflite_kb = len(tflite_ops_int8) / 1024.0

    agreement = (keras_preds == tflite_preds).mean() * 100.0

    df_parity = pd.DataFrame([
        {
            "format": "Keras Float32 (Original)",
            "accuracy": round(acc_k, 4),
            "macro_f1": round(f1_k, 4),
            "normal_recall": round(float(r_k[classes.index("NORMAL_BASELINE")]), 4),
            "smoke_recall": round(float(r_k[classes.index("SMOKE")]), 4),
            "voc_recall": round(float(r_k[classes.index("VOC_RESPONSE")]), 4),
            "mixture_recall": round(float(r_k[classes.index("MIXTURE")]), 4),
            "model_size_kb": round(size_keras_kb, 2),
            "latency_ms": round(keras_latency, 3),
            "agreement_pct": 100.0
        },
        {
            "format": "TFLite INT8 Ops (Quantized)",
            "accuracy": round(acc_t, 4),
            "macro_f1": round(f1_t, 4),
            "normal_recall": round(float(r_t[classes.index("NORMAL_BASELINE")]), 4),
            "smoke_recall": round(float(r_t[classes.index("SMOKE")]), 4),
            "voc_recall": round(float(r_t[classes.index("VOC_RESPONSE")]), 4),
            "mixture_recall": round(float(r_t[classes.index("MIXTURE")]), 4),
            "model_size_kb": round(size_tflite_kb, 2),
            "latency_ms": round(tflite_latency, 3),
            "agreement_pct": round(agreement, 2)
        }
    ])
    df_parity.to_csv("reports/int8_float_parity.csv", index=False)
    print("\n=== Final Parity Comparison Table ===")
    print(df_parity.to_string())

    # 3. Export C++ Header
    generate_cpp_header(
        tflite_ops_int8,
        "firmware/models/model_data.h",
        scaler.mean_,
        scaler.scale_
    )

    manifest_v3 = {
        "milestone": "M3_INT8_EDGE_AI_OPTIMIZATION",
        "experiment_id": "M3-QUANTIZATION-PARITY-001",
        "data_provenance": "SYNTHETIC_GENERATED_M2_7_CORPUS",
        "tflite_size_bytes": len(tflite_ops_int8),
        "size_reduction_ratio": round(size_keras_kb / size_tflite_kb, 2),
        "agreement_percentage": agreement,
        "keras_float32": {
            "accuracy": acc_k,
            "macro_f1": f1_k
        },
        "tflite_int8": {
            "accuracy": acc_t,
            "macro_f1": f1_t
        },
        "features": FEATURE_COLS_V2,
        "classes": classes
    }

    with open("ml/artifacts/v3/quantization_manifest.json", "w") as f:
        json.dump(manifest_v3, f, indent=2)

if __name__ == "__main__":
    run_quantization_and_export()
