"""
M2 Baseline Training Pipeline
Enforces Gate 1, 2, 3, 4, and 5:
- Group/Session-separated 70/15/15 partitions.
- Random Forest, XGBoost, and Compact Keras MLP comparison.
- Full confusion matrices, classification metrics, false-negative analysis.
- External baseline evaluation on multi_sensor_data_baseline.csv.
- Reproducible artifact and manifest generation.
"""

import os
import json
import time
import yaml
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
    log_loss,
)
import xgboost as xgb
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

FEATURE_COLS = [
    "mq2_raw_current", "mq2_mean", "mq2_std", "mq2_min", "mq2_max", "mq2_delta", "mq2_slope",
    "mq135_raw_current", "mq135_mean", "mq135_std", "mq135_min", "mq135_max", "mq135_delta", "mq135_slope",
    "gas_ratio_mq2_to_mq135"
]

def load_and_partition_data():
    """
    Loads windowed features from Gas_Sensors_Measurements only (primary training source).
    Uses session/time contiguous blocks per class to avoid leakage (70% train, 15% val, 15% test).
    """
    df = pd.read_parquet("ml/datasets/processed/windowed_features.parquet")
    # Filter strictly for Gas_Sensors_Measurements
    df_gsm = df[df["source_dataset"] == "Gas_Sensors_Measurements"].copy()
    print(f"Total windowed instances in Gas_Sensors_Measurements: {len(df_gsm)}")

    train_indices = []
    val_indices = []
    test_indices = []

    # Partition each of the 4 classes (1600 raw records -> ~796 windows) chronologically
    for label, group in df_gsm.groupby("canonical_label", sort=False):
        n = len(group)
        idx = group.index.to_numpy()
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        
        train_indices.extend(idx[:n_train])
        val_indices.extend(idx[n_train:n_train + n_val])
        test_indices.extend(idx[n_train + n_val:])

    train_df = df_gsm.loc[train_indices].copy()
    val_df = df_gsm.loc[val_indices].copy()
    test_df = df_gsm.loc[test_indices].copy()

    print(f"Partition shapes -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # Load external baseline (multi_sensor_data_baseline)
    df_base = df[df["source_dataset"] == "multi_sensor_data_baseline"].copy()
    print(f"Isolated external baseline instances for evaluation: {len(df_base)}")

    return train_df, val_df, test_df, df_base

def train_and_evaluate():
    train_df, val_df, test_df, df_base = load_and_partition_data()

    X_train = train_df[FEATURE_COLS].to_numpy()
    y_train_raw = train_df["canonical_label"].to_numpy()

    X_val = val_df[FEATURE_COLS].to_numpy()
    y_val_raw = val_df["canonical_label"].to_numpy()

    X_test = test_df[FEATURE_COLS].to_numpy()
    y_test_raw = test_df["canonical_label"].to_numpy()

    X_base = df_base[FEATURE_COLS].to_numpy()
    y_base_raw = df_base["canonical_label"].to_numpy()

    # Encode labels
    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_val = le.transform(y_val_raw)
    y_test = le.transform(y_test_raw)
    classes = list(le.classes_)
    print("Classes encoded:", {i: c for i, c in enumerate(classes)})

    # Fit scaler strictly on Train
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    X_base_scaled = scaler.transform(X_base)

    os.makedirs("ml/artifacts", exist_ok=True)
    os.makedirs("ml/reports", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    joblib.dump(scaler, "ml/artifacts/scaler.joblib")
    joblib.dump(le, "ml/artifacts/label_encoder.joblib")

    results = {}

    # =========================================================================
    # Model 1: Random Forest
    # =========================================================================
    print("\n--- Training Model 1: Random Forest ---")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    t0 = time.time()
    rf.fit(X_train_scaled, y_train)
    rf_train_time = time.time() - t0

    t0 = time.time()
    rf_preds = rf.predict(X_test_scaled)
    rf_latency_ms = ((time.time() - t0) / len(X_test)) * 1000
    rf_probs = rf.predict_proba(X_test_scaled)

    joblib.dump(rf, "ml/artifacts/random_forest_baseline.joblib")

    # =========================================================================
    # Model 2: XGBoost
    # =========================================================================
    print("\n--- Training Model 2: XGBoost ---")
    xgb_clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=RANDOM_SEED,
        eval_metric="mlogloss",
        n_jobs=-1
    )
    t0 = time.time()
    xgb_clf.fit(X_train_scaled, y_train)
    xgb_train_time = time.time() - t0

    t0 = time.time()
    xgb_preds = xgb_clf.predict(X_test_scaled)
    xgb_latency_ms = ((time.time() - t0) / len(X_test)) * 1000
    xgb_probs = xgb_clf.predict_proba(X_test_scaled)

    joblib.dump(xgb_clf, "ml/artifacts/xgboost_baseline.joblib")

    # =========================================================================
    # Model 3: Compact Keras MLP (Targeted for TFLite Micro on ESP32)
    # =========================================================================
    print("\n--- Training Model 3: Compact Keras MLP ---")
    mlp = keras.Sequential([
        layers.Input(shape=(len(FEATURE_COLS),), name="sensor_features"),
        layers.Dense(32, activation="relu", name="dense_1"),
        layers.Dropout(0.1, name="dropout_1"),
        layers.Dense(16, activation="relu", name="dense_2"),
        layers.Dense(len(classes), activation="softmax", name="classification_output")
    ])
    mlp.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.005),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    mlp.summary()

    t0 = time.time()
    history = mlp.fit(
        X_train_scaled, y_train,
        validation_data=(X_val_scaled, y_val),
        epochs=40,
        batch_size=32,
        verbose=0
    )
    mlp_train_time = time.time() - t0

    t0 = time.time()
    mlp_probs = mlp.predict(X_test_scaled, verbose=0)
    mlp_latency_ms = ((time.time() - t0) / len(X_test)) * 1000
    mlp_preds = np.argmax(mlp_probs, axis=1)

    mlp.save("ml/artifacts/compact_mlp_baseline.keras")

    # =========================================================================
    # Metrics Compilation
    # =========================================================================
    models_dict = {
        "Random Forest": (rf_preds, rf_probs, rf_latency_ms, "ml/artifacts/random_forest_baseline.joblib"),
        "XGBoost": (xgb_preds, xgb_probs, xgb_latency_ms, "ml/artifacts/xgboost_baseline.joblib"),
        "Compact MLP (Keras)": (mlp_preds, mlp_probs, mlp_latency_ms, "ml/artifacts/compact_mlp_baseline.keras"),
    }

    comparison_rows = []

    for name, (preds, probs, lat_ms, art_path) in models_dict.items():
        acc = accuracy_score(y_test, preds)
        b_acc = balanced_accuracy_score(y_test, preds)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average="macro", zero_division=0)
        p_per, r_per, f_per, _ = precision_recall_fscore_support(y_test, preds, average=None, zero_division=0)
        ll = log_loss(y_test, probs)
        size_kb = os.path.getsize(art_path) / 1024

        cm = confusion_matrix(y_test, preds)

        # Plot confusion matrix
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
        plt.title(f"Confusion Matrix: {name}")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.tight_layout()
        plt.savefig(f"reports/cm_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.png")
        plt.close()

        # External Baseline Evaluation (Domain Compatibility check)
        if name == "Random Forest":
            base_preds = rf.predict(X_base_scaled)
        elif name == "XGBoost":
            base_preds = xgb_clf.predict(X_base_scaled)
        else:
            base_preds = np.argmax(mlp.predict(X_base_scaled, verbose=0), axis=1)

        normal_idx = classes.index("NORMAL_BASELINE")
        base_normal_pct = (base_preds == normal_idx).mean() * 100

        comparison_rows.append({
            "model": name,
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(b_acc, 4),
            "macro_precision": round(prec, 4),
            "macro_recall": round(rec, 4),
            "macro_f1": round(f1, 4),
            "log_loss": round(ll, 4),
            "test_latency_ms": round(lat_ms, 3),
            "artifact_size_kb": round(size_kb, 1),
            "external_baseline_classified_as_normal_pct": round(base_normal_pct, 2)
        })

        results[name] = {
            "overall": {
                "accuracy": acc,
                "balanced_accuracy": b_acc,
                "macro_precision": prec,
                "macro_recall": rec,
                "macro_f1": f1,
                "log_loss": ll,
                "latency_ms": lat_ms,
                "artifact_size_kb": size_kb,
            },
            "per_class": {
                classes[i]: {
                    "precision": float(p_per[i]),
                    "recall": float(r_per[i]),
                    "f1": float(f_per[i])
                } for i in range(len(classes))
            },
            "confusion_matrix": cm.tolist(),
            "external_baseline_evaluation": {
                "total_baseline_samples": len(X_base),
                "classified_as_normal_baseline_percentage": base_normal_pct,
                "prediction_distribution": pd.Series(le.inverse_transform(base_preds)).value_counts().to_dict()
            }
        }

    # Save comparison table
    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv("reports/baseline_model_comparison.csv", index=False)
    print("\n=== Baseline Model Comparison Table ===")
    print(df_comp.to_string())

    # Save metadata manifest
    manifest = {
        "milestone": "M2_BASELINE_EXPERIMENT",
        "experiment_id": "GAS-CLASSIFICATION-BASELINE-001",
        "random_seed": RANDOM_SEED,
        "feature_schema_version": "1.0.0",
        "label_registry_version": "1.0.0",
        "input_features": FEATURE_COLS,
        "classes": classes,
        "partitions": {
            "method": "SESSION_CONTIGUOUS_CHRONOLOGICAL_SPLIT",
            "train_ratio": 0.70,
            "val_ratio": 0.15,
            "test_ratio": 0.15,
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "external_baseline_samples": len(df_base)
        },
        "models_evaluated": results
    }

    with open("ml/artifacts/training_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return df_comp, manifest

if __name__ == "__main__":
    train_and_evaluate()
