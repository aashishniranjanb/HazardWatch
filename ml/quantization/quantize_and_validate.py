"""
M3 Full Integer int8 Quantization & Validation Pipeline
Converts compact_mlp_m2_7.keras to:
- ml/artifacts/v3/compact_mlp_int8.tflite
Evaluates float32 vs int8 numerical parity:
- Agreement percentage
- Max absolute probability error
- Confusion matrices
- Latency and model size reduction
"""

import os
import glob
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

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

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

def load_training_and_test_data():
    from ml.training.train_m2_7 import load_all_trials_and_partition
    train_df, val_df, test_a_df, held_out_b_df = load_all_trials_and_partition()

    scaler = joblib.load("ml/artifacts/v2_7/scaler_m2_7.joblib")
    le = joblib.load("ml/artifacts/v2_7/label_encoder_m2_7.joblib")

    X_train = scaler.transform(train_df[FEATURE_COLS_V2].to_numpy())
    X_test_b = scaler.transform(held_out_b_df[FEATURE_COLS_V2].to_numpy())
    y_test_b = le.transform(held_out_b_df["condition"].to_numpy())

    return X_train, X_test_b, y_test_b, le.classes_

def convert_to_full_int8(model, X_train):
    """
    Applies TFLite full-integer quantization using representative dataset.
    """
    def representative_dataset():
        # Sample 300 instances across training distribution
        for i in range(min(300, len(X_train))):
            yield [X_train[i:i+1].astype(np.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    
    # Enforce full integer quantization for all operations
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_quant_model = converter.convert()
    output_path = "ml/artifacts/v3/compact_mlp_int8.tflite"
    with open(output_path, "wb") as f:
        f.write(tflite_quant_model)

    print(f"Full integer int8 TFLite model saved to {output_path} ({len(tflite_quant_model)} bytes)")
    return output_path, tflite_quant_model

def evaluate_parity(keras_model, tflite_path, X_test, y_test, classes):
    """
    Compares prediction agreement and numerical difference between float32 Keras and int8 TFLite.
    """
    # 1. Keras Float32 Predictions
    t0 = time.time()
    keras_probs = keras_model.predict(X_test, verbose=0)
    keras_latency = ((time.time() - t0) / len(X_test)) * 1000
    keras_preds = np.argmax(keras_probs, axis=1)

    # 2. TFLite int8 Interpreter
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    input_scale, input_zero_point = input_details["quantization"]
    output_scale, output_zero_point = output_details["quantization"]

    print("\nQuantization Metadata:")
    print(f"  Input: scale={input_scale}, zero_point={input_zero_point}, dtype={input_details['dtype']}")
    print(f"  Output: scale={output_scale}, zero_point={output_zero_point}, dtype={output_details['dtype']}")

    tflite_preds = []
    tflite_probs = []

    t0 = time.time()
    for i in range(len(X_test)):
        # Quantize float32 input to int8
        x_val = X_test[i:i+1].astype(np.float32)
        x_quant = np.round(x_val / input_scale + input_zero_point).astype(np.int8)

        interpreter.set_tensor(input_details["index"], x_quant)
        interpreter.invoke()
        y_quant = interpreter.get_tensor(output_details["index"])

        # Dequantize int8 output to float32 probability space
        y_dequant = (y_quant.astype(np.float32) - output_zero_point) * output_scale
        tflite_probs.append(y_dequant[0])
        tflite_preds.append(np.argmax(y_dequant[0]))

    tflite_latency = ((time.time() - t0) / len(X_test)) * 1000
    tflite_preds = np.array(tflite_preds)
    tflite_probs = np.array(tflite_probs)

    # Parity Metrics
    agreement = (keras_preds == tflite_preds).mean() * 100.0
    max_prob_diff = np.max(np.abs(keras_probs - tflite_probs))
    mean_prob_diff = np.mean(np.abs(keras_probs - tflite_probs))

    acc_keras = accuracy_score(y_test, keras_preds)
    acc_tflite = accuracy_score(y_test, tflite_preds)

    _, _, f1_keras, _ = precision_recall_fscore_support(y_test, keras_preds, average="macro", zero_division=0)
    _, _, f1_tflite, _ = precision_recall_fscore_support(y_test, tflite_preds, average="macro", zero_division=0)

    p_per_k, r_per_k, _, _ = precision_recall_fscore_support(y_test, keras_preds, average=None, zero_division=0)
    p_per_t, r_per_t, _, _ = precision_recall_fscore_support(y_test, tflite_preds, average=None, zero_division=0)

    cm_k = confusion_matrix(y_test, keras_preds)
    cm_t = confusion_matrix(y_test, tflite_preds)

    size_keras_kb = os.path.getsize("ml/artifacts/v2_7/compact_mlp_m2_7.keras") / 1024.0
    size_tflite_kb = os.path.getsize(tflite_path) / 1024.0

    report = {
        "agreement_percentage": round(agreement, 2),
        "max_probability_divergence": round(float(max_prob_diff), 4),
        "mean_probability_divergence": round(float(mean_prob_diff), 4),
        "keras_float32": {
            "accuracy": round(acc_keras, 4),
            "macro_f1": round(f1_keras, 4),
            "artifact_size_kb": round(size_keras_kb, 2),
            "latency_ms": round(keras_latency, 3),
            "per_class_recall": {classes[i]: round(float(r_per_k[i]), 4) for i in range(len(classes))}
        },
        "tflite_int8": {
            "accuracy": round(acc_tflite, 4),
            "macro_f1": round(f1_tflite, 4),
            "artifact_size_kb": round(size_tflite_kb, 2),
            "latency_ms": round(tflite_latency, 3),
            "per_class_recall": {classes[i]: round(float(r_per_t[i]), 4) for i in range(len(classes))}
        },
        "quantization_metadata": {
            "input_scale": float(input_scale),
            "input_zero_point": int(input_zero_point),
            "output_scale": float(output_scale),
            "output_zero_point": int(output_zero_point),
        }
    }

    # Save comparison CSV
    df_parity = pd.DataFrame([
        {
            "format": "Keras Float32",
            "accuracy": round(acc_keras, 4),
            "macro_f1": round(f1_keras, 4),
            "normal_recall": round(float(r_per_k[classes.tolist().index("NORMAL_BASELINE")]), 4),
            "smoke_recall": round(float(r_per_k[classes.tolist().index("SMOKE")]), 4),
            "voc_recall": round(float(r_per_k[classes.tolist().index("VOC_RESPONSE")]), 4),
            "mixture_recall": round(float(r_per_k[classes.tolist().index("MIXTURE")]), 4),
            "model_size_kb": round(size_keras_kb, 2),
            "latency_ms": round(keras_latency, 3)
        },
        {
            "format": "TFLite Full-Integer int8",
            "accuracy": round(acc_tflite, 4),
            "macro_f1": round(f1_tflite, 4),
            "normal_recall": round(float(r_per_t[classes.tolist().index("NORMAL_BASELINE")]), 4),
            "smoke_recall": round(float(r_per_t[classes.tolist().index("SMOKE")]), 4),
            "voc_recall": round(float(r_per_t[classes.tolist().index("VOC_RESPONSE")]), 4),
            "mixture_recall": round(float(r_per_t[classes.tolist().index("MIXTURE")]), 4),
            "model_size_kb": round(size_tflite_kb, 2),
            "latency_ms": round(tflite_latency, 3)
        }
    ])
    df_parity.to_csv("reports/int8_float_parity.csv", index=False)
    print("\n=== Parity Evaluation Table ===")
    print(df_parity.to_string())

    with open("ml/artifacts/v3/quantization_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    X_train, X_test, y_test, classes = load_training_and_test_data()
    keras_model = keras.models.load_model("ml/artifacts/v2_7/compact_mlp_m2_7.keras")
    tflite_path, tflite_bytes = convert_to_full_int8(keras_model, X_train)
    report = evaluate_parity(keras_model, tflite_path, X_test, y_test, classes)
