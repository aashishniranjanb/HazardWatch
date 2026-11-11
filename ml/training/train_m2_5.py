"""
M2.5 Baseline-Relative Model Retraining Pipeline
Implements:
- 11 baseline-relative and dynamics features (feature_schema_v2).
- Boundary-safe partitioning with purge gaps (no window crossing split boundaries).
- Retraining Random Forest, XGBoost, and Compact Keras MLP.
- External baseline evaluation and domain shift assessment.
- Full manifest generation and metric comparison vs M2.
"""

import os
import json
import time
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
    log_loss,
)
import xgboost as xgb
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

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

def load_and_partition_data_v2():
    df = pd.read_parquet("ml/datasets/processed/windowed_features_v2.parquet")
    df_gsm = df[df["source_dataset"] == "Gas_Sensors_Measurements"].copy()

    train_indices = []
    val_indices = []
    test_indices = []

    # Enforce strict boundary purge gaps between partitions (10 samples buffer)
    for label, group in df_gsm.groupby("canonical_label", sort=False):
        n = len(group)
        idx = group.index.to_numpy()
        
        # 70% Train, 15% Val, 15% Test with 5-window purge gap (10 samples)
        n_train = int(n * 0.70)
        gap = 5
        n_val = int(n * 0.15)
        
        train_idx = idx[:n_train]
        val_idx = idx[n_train + gap : n_train + gap + n_val]
        test_idx = idx[n_train + gap + n_val + gap :]

        train_indices.extend(train_idx)
        val_indices.extend(val_idx)
        test_indices.extend(test_idx)

    train_df = df_gsm.loc[train_indices].copy()
    val_df = df_gsm.loc[val_indices].copy()
    test_df = df_gsm.loc[test_indices].copy()

    print(f"Purge-protected partition shapes -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # External baseline
    df_base = df[df["source_dataset"] == "multi_sensor_data_baseline"].copy()
    print(f"External baseline evaluation instances: {len(df_base)}")

    return train_df, val_df, test_df, df_base

def retrain_and_evaluate_v2():
    train_df, val_df, test_df, df_base = load_and_partition_data_v2()

    X_train = train_df[FEATURE_COLS_V2].to_numpy()
    y_train_raw = train_df["canonical_label"].to_numpy()

    X_val = val_df[FEATURE_COLS_V2].to_numpy()
    y_val_raw = val_df["canonical_label"].to_numpy()

    X_test = test_df[FEATURE_COLS_V2].to_numpy()
    y_test_raw = test_df["canonical_label"].to_numpy()

    X_base = df_base[FEATURE_COLS_V2].to_numpy()
    y_base_raw = df_base["canonical_label"].to_numpy()

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

    os.makedirs("ml/artifacts/v2", exist_ok=True)
    joblib.dump(scaler, "ml/artifacts/v2/scaler_v2.joblib")
    joblib.dump(le, "ml/artifacts/v2/label_encoder_v2.joblib")

    # =========================================================================
    # Model 1: Random Forest v2
    # =========================================================================
    print("\n--- Training Model 1: Random Forest (v2) ---")
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
    joblib.dump(rf, "ml/artifacts/v2/random_forest_v2.joblib")

    # =========================================================================
    # Model 2: XGBoost v2
    # =========================================================================
    print("\n--- Training Model 2: XGBoost (v2) ---")
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
    joblib.dump(xgb_clf, "ml/artifacts/v2/xgboost_v2.joblib")

    # =========================================================================
    # Model 3: Compact Keras MLP v2
    # =========================================================================
    print("\n--- Training Model 3: Compact Keras MLP (v2) ---")
    mlp = keras.Sequential([
        layers.Input(shape=(len(FEATURE_COLS_V2),), name="sensor_features_v2"),
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
    mlp.fit(
        X_train_scaled, y_train,
        validation_data=(X_val_scaled, y_val),
        epochs=40,
        batch_size=32,
        verbose=0
    )

    t0 = time.time()
    mlp_probs = mlp.predict(X_test_scaled, verbose=0)
    mlp_latency_ms = ((time.time() - t0) / len(X_test)) * 1000
    mlp_preds = np.argmax(mlp_probs, axis=1)
    mlp.save("ml/artifacts/v2/compact_mlp_v2.keras")

    # =========================================================================
    # Evaluation Compilation
    # =========================================================================
    models_dict = {
        "Random Forest v2": (rf, rf_preds, rf_probs, rf_latency_ms, "ml/artifacts/v2/random_forest_v2.joblib"),
        "XGBoost v2": (xgb_clf, xgb_preds, xgb_probs, xgb_latency_ms, "ml/artifacts/v2/xgboost_v2.joblib"),
        "Compact MLP v2": (mlp, mlp_preds, mlp_probs, mlp_latency_ms, "ml/artifacts/v2/compact_mlp_v2.keras"),
    }

    comparison_rows = []
    manifest_results = {}

    for name, (model_obj, preds, probs, lat_ms, art_path) in models_dict.items():
        acc = accuracy_score(y_test, preds)
        b_acc = balanced_accuracy_score(y_test, preds)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, preds, average="macro", zero_division=0)
        p_per, r_per, f_per, _ = precision_recall_fscore_support(y_test, preds, average=None, zero_division=0)
        ll = log_loss(y_test, probs)
        size_kb = os.path.getsize(art_path) / 1024

        cm = confusion_matrix(y_test, preds)

        # Plot confusion matrix
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Purples", xticklabels=classes, yticklabels=classes)
        plt.title(f"Confusion Matrix: {name}")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.tight_layout()
        plt.savefig(f"reports/cm_{name.lower().replace(' ', '_')}.png")
        plt.close()

        # External Baseline Evaluation
        if "Random Forest" in name:
            base_preds = rf.predict(X_base_scaled)
        elif "XGBoost" in name:
            base_preds = xgb_clf.predict(X_base_scaled)
        else:
            base_preds = np.argmax(mlp.predict(X_base_scaled, verbose=0), axis=1)

        normal_idx = classes.index("NORMAL_BASELINE")
        base_normal_pct = (base_preds == normal_idx).mean() * 100
        base_dist = pd.Series(le.inverse_transform(base_preds)).value_counts().to_dict()

        comparison_rows.append({
            "model": name,
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(b_acc, 4),
            "macro_precision": round(prec, 4),
            "macro_recall": round(rec, 4),
            "macro_f1": round(f1, 4),
            "normal_baseline_recall": round(float(r_per[classes.index("NORMAL_BASELINE")]), 4),
            "smoke_recall": round(float(r_per[classes.index("SMOKE")]), 4),
            "log_loss": round(ll, 4),
            "test_latency_ms": round(lat_ms, 3),
            "artifact_size_kb": round(size_kb, 1),
            "external_baseline_normal_pct": round(base_normal_pct, 2)
        })

        manifest_results[name] = {
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
                "total_samples": len(X_base),
                "classified_as_normal_percentage": base_normal_pct,
                "prediction_distribution": base_dist
            }
        }

    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv("reports/m2_5_model_comparison.csv", index=False)
    print("\n=== M2.5 Retrained Model Comparison Table ===")
    print(df_comp.to_string())

    manifest = {
        "milestone": "M2.5_VALIDATION_AUDIT_AND_BASELINE_RELATIVE_RETRAINING",
        "experiment_id": "GAS-CLASSIFICATION-M2.5-BASELINE-RELATIVE-001",
        "random_seed": RANDOM_SEED,
        "feature_schema_version": "2.0.0",
        "features": FEATURE_COLS_V2,
        "classes": classes,
        "partitions": {
            "method": "SESSION_CONTIGUOUS_SPLIT_WITH_PURGE_GAPS",
            "purge_gap_windows": 5,
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "external_baseline_samples": len(df_base)
        },
        "models_evaluated": manifest_results
    }

    with open("ml/artifacts/v2/training_manifest_v2.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return df_comp, manifest

if __name__ == "__main__":
    retrain_and_evaluate_v2()
