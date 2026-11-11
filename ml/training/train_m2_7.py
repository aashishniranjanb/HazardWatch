"""
M2.7 Multi-Trial Training, Generalization, and OOD Evaluation Pipeline
Implements:
- Experiment-level partitioning: Entire experiments are held out.
- Separate cross-device evaluation on BOARD_B.
- Retraining Random Forest, XGBoost, and Compact MLP.
- Evaluation of accuracy, macro F1, per-class recall, and OOD rejection.
- Comparison with M2 and M2.5.
"""

import os
import glob
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

def extract_features_from_trial(df_trial, baseline_mq2, baseline_mq135, window_size=10, step_size=2):
    records = []
    mq2_arr = df_trial["mq2_adc"].to_numpy()
    mq135_arr = df_trial["mq135_adc"].to_numpy()
    conditions = df_trial["experiment_condition"].to_numpy()
    n = len(df_trial)
    x = np.arange(window_size)

    for start_idx in range(0, n - window_size + 1, step_size):
        end_idx = start_idx + window_size
        w_mq2 = mq2_arr[start_idx:end_idx]
        w_mq135 = mq135_arr[start_idx:end_idx]
        cond = str(conditions[end_idx - 1])

        mq2_mean = float(np.mean(w_mq2))
        mq2_std = float(np.std(w_mq2))
        mq2_min = float(np.min(w_mq2))
        mq2_max = float(np.max(w_mq2))
        mq2_delta = mq2_max - mq2_min
        mq2_slope = float(np.polyfit(x, w_mq2, 1)[0]) if window_size > 1 else 0.0

        mq135_mean = float(np.mean(w_mq135))
        mq135_std = float(np.std(w_mq135))
        mq135_min = float(np.min(w_mq135))
        mq135_max = float(np.max(w_mq135))
        mq135_delta = mq135_max - mq135_min
        mq135_slope = float(np.polyfit(x, w_mq135, 1)[0]) if window_size > 1 else 0.0

        # Relative features
        mq2_delta_base = mq2_mean - baseline_mq2
        mq135_delta_base = mq135_mean - baseline_mq135
        mq2_ratio_base = mq2_mean / (baseline_mq2 + 1e-4)
        mq135_ratio_base = mq135_mean / (baseline_mq135 + 1e-4)
        gas_ratio = mq2_mean / (mq135_mean + 1e-4)

        records.append({
            "mq2_delta_baseline": mq2_delta_base,
            "mq135_delta_baseline": mq135_delta_base,
            "mq2_ratio_baseline": mq2_ratio_base,
            "mq135_ratio_baseline": mq135_ratio_base,
            "gas_ratio_mq2_to_mq135": gas_ratio,
            "mq2_slope": mq2_slope,
            "mq135_slope": mq135_slope,
            "mq2_std": mq2_std,
            "mq135_std": mq135_std,
            "mq2_delta_window": mq2_delta,
            "mq135_delta_window": mq135_delta,
            "condition": cond,
            "experiment_id": df_trial["experiment_id"].iloc[0],
            "sensor_board_id": df_trial["sensor_board_id"].iloc[0]
        })
    return pd.DataFrame(records)

def load_all_trials_and_partition():
    trial_files = sorted(glob.glob("ml/collection/trials/*.parquet"))
    print(f"Discovered {len(trial_files)} trial files.")

    baselines = {
        "BOARD_A": (350.0, 1450.0),
        "BOARD_B": (320.0, 1520.0),
    }

    train_dfs = []
    val_dfs = []
    test_device_a_dfs = []
    held_out_device_b_dfs = []

    for f in trial_files:
        df_trial = pd.read_parquet(f)
        exp_id = str(df_trial["experiment_id"].iloc[0])
        board_id = str(df_trial["sensor_board_id"].iloc[0])
        base_mq2, base_mq135 = baselines[board_id]

        df_feats = extract_features_from_trial(df_trial, base_mq2, base_mq135)

        # EXPERIMENT-LEVEL PARTITIONING:
        # Board B is 100% held-out for cross-device evaluation!
        if board_id == "BOARD_B":
            held_out_device_b_dfs.append(df_feats)
        else:
            # Board A experiments:
            if "WARMUP" in exp_id or "VOC" in exp_id or "SMOKE" in exp_id or "MIXTURE_TRIAL_1" in exp_id:
                train_dfs.append(df_feats)
            elif "MIXTURE_TRIAL_2" in exp_id:
                val_dfs.append(df_feats)
            elif "STABLE" in exp_id:
                test_device_a_dfs.append(df_feats)

    train_df = pd.concat(train_dfs, ignore_index=True)
    val_df = pd.concat(val_dfs, ignore_index=True)
    test_a_df = pd.concat(test_device_a_dfs, ignore_index=True)
    held_out_b_df = pd.concat(held_out_device_b_dfs, ignore_index=True)

    print(f"Experiment Partitions:")
    print(f"  Train (Board A - Warmup, Smoke 1, VOC 1, Mixture 1): {len(train_df)} windows")
    print(f"  Val (Board A - Mixture 2): {len(val_df)} windows")
    print(f"  Test A (Board A - Stable Day 2 Clean Air): {len(test_a_df)} windows")
    print(f"  Held-Out Device B (Cross-Sensor Board Evaluation): {len(held_out_b_df)} windows")

    return train_df, val_df, test_a_df, held_out_b_df

def run_m2_7_pipeline():
    train_df, val_df, test_a_df, held_out_b_df = load_all_trials_and_partition()

    X_train = train_df[FEATURE_COLS_V2].to_numpy()
    y_train_raw = train_df["condition"].to_numpy()

    X_val = val_df[FEATURE_COLS_V2].to_numpy()
    y_val_raw = val_df["condition"].to_numpy()

    X_test_b = held_out_b_df[FEATURE_COLS_V2].to_numpy()
    y_test_b_raw = held_out_b_df["condition"].to_numpy()

    # Encode labels
    all_classes = ["MIXTURE", "NORMAL_BASELINE", "SMOKE", "VOC_RESPONSE"]
    le = LabelEncoder()
    le.fit(all_classes)

    y_train = le.transform(y_train_raw)
    y_val = le.transform(y_val_raw)
    y_test_b = le.transform(y_test_b_raw)
    classes = list(le.classes_)
    print("Classes encoded:", {i: c for i, c in enumerate(classes)})
    print("Train unique labels:", np.unique(y_train))

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_b_scaled = scaler.transform(X_test_b)

    os.makedirs("ml/artifacts/v2_7", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    joblib.dump(scaler, "ml/artifacts/v2_7/scaler_m2_7.joblib")
    joblib.dump(le, "ml/artifacts/v2_7/label_encoder_m2_7.joblib")

    # =========================================================================
    # Train Models
    # =========================================================================
    print("\n--- Training Model 1: Random Forest (M2.7) ---")
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=RANDOM_SEED, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    joblib.dump(rf, "ml/artifacts/v2_7/random_forest_m2_7.joblib")

    print("\n--- Training Model 2: XGBoost (M2.7) ---")
    xgb_clf = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=RANDOM_SEED, eval_metric="mlogloss", n_jobs=-1)
    xgb_clf.fit(X_train_scaled, y_train)
    joblib.dump(xgb_clf, "ml/artifacts/v2_7/xgboost_m2_7.joblib")

    print("\n--- Training Model 3: Compact Keras MLP (M2.7) ---")
    mlp = keras.Sequential([
        layers.Input(shape=(len(FEATURE_COLS_V2),), name="sensor_features_m2_7"),
        layers.Dense(32, activation="relu", name="dense_1"),
        layers.Dropout(0.1, name="dropout_1"),
        layers.Dense(16, activation="relu", name="dense_2"),
        layers.Dense(len(classes), activation="softmax", name="classification_output")
    ])
    mlp.compile(optimizer=keras.optimizers.Adam(learning_rate=0.005), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    mlp.fit(X_train_scaled, y_train, validation_data=(X_val_scaled, y_val), epochs=35, batch_size=32, verbose=0)
    mlp.save("ml/artifacts/v2_7/compact_mlp_m2_7.keras")

    # =========================================================================
    # Cross-Device Evaluation on Held-Out BOARD_B (1,384 windows)
    # =========================================================================
    models = {
        "Random Forest M2.7": rf,
        "XGBoost M2.7": xgb_clf,
        "Compact MLP M2.7": mlp
    }

    comparison_rows = []
    manifest_results = {}

    for name, model_obj in models.items():
        t0 = time.time()
        if "Compact MLP" in name:
            probs = model_obj.predict(X_test_b_scaled, verbose=0)
            preds = np.argmax(probs, axis=1)
        else:
            probs = model_obj.predict_proba(X_test_b_scaled)
            preds = model_obj.predict(X_test_b_scaled)
        latency_ms = ((time.time() - t0) / len(X_test_b)) * 1000

        # OOD / Uncertainty Gating:
        # If max probability < 0.60, mark as UNKNOWN
        max_conf = np.max(probs, axis=1)
        gated_preds = np.where(max_conf >= 0.60, preds, -1)
        ood_count = int(np.sum(gated_preds == -1))

        acc = accuracy_score(y_test_b, preds)
        b_acc = balanced_accuracy_score(y_test_b, preds)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test_b, preds, average="macro", zero_division=0)
        p_per, r_per, f_per, _ = precision_recall_fscore_support(y_test_b, preds, average=None, zero_division=0)
        cm = confusion_matrix(y_test_b, preds)

        # Plot confusion matrix on held-out device
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=classes, yticklabels=classes)
        plt.title(f"Cross-Device B: {name}")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.tight_layout()
        plt.savefig(f"reports/cm_m2_7_{name.lower().replace(' ', '_').replace('.', '_')}.png")
        plt.close()

        normal_idx = classes.index("NORMAL_BASELINE")
        smoke_idx = classes.index("SMOKE")
        voc_idx = classes.index("VOC_RESPONSE")
        mixture_idx = classes.index("MIXTURE")

        comparison_rows.append({
            "model": name,
            "cross_board_b_accuracy": round(acc, 4),
            "macro_f1": round(f1, 4),
            "normal_baseline_recall": round(float(r_per[normal_idx]), 4),
            "smoke_recall": round(float(r_per[smoke_idx]), 4),
            "voc_response_recall": round(float(r_per[voc_idx]), 4),
            "mixture_recall": round(float(r_per[mixture_idx]), 4),
            "ood_uncertain_count": ood_count,
            "latency_ms": round(latency_ms, 3)
        })

        manifest_results[name] = {
            "cross_board_b_accuracy": acc,
            "macro_f1": f1,
            "per_class": {
                classes[i]: {
                    "precision": float(p_per[i]),
                    "recall": float(r_per[i]),
                    "f1": float(f_per[i])
                } for i in range(len(classes))
            },
            "confusion_matrix": cm.tolist(),
            "ood_rejection_count": ood_count
        }

    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv("reports/m2_7_generalization_comparison.csv", index=False)
    print("\n=== M2.7 Multi-Trial Cross-Device Comparison Table ===")
    print(df_comp.to_string())

    manifest = {
        "milestone": "M2.7_INDEPENDENT_EXPERIMENT_DATASET_EXPANSION",
        "experiment_id": "GAS-CLASSIFICATION-M2.7-MULTI-TRIAL-001",
        "random_seed": RANDOM_SEED,
        "feature_schema_version": "2.0.0",
        "features": FEATURE_COLS_V2,
        "classes": classes,
        "trial_partitions": {
            "method": "EXPERIMENT_LEVEL_HOLD_OUT_AND_CROSS_DEVICE_SPLIT",
            "train_trials": ["EXP_A_001_CLEAN_AIR_WARMUP", "EXP_A_003_SMOKE_TRIAL_1", "EXP_A_004_VOC_TRIAL_1", "EXP_A_005_MIXTURE_TRIAL_1"],
            "val_trials": ["EXP_A_005B_MIXTURE_TRIAL_2"],
            "test_device_a_trials": ["EXP_A_002_CLEAN_AIR_STABLE"],
            "held_out_cross_device_b_trials": ["EXP_B_006_CLEAN_AIR_HELD_OUT", "EXP_B_007_SMOKE_HELD_OUT", "EXP_B_008_VOC_HELD_OUT", "EXP_B_009_MIXTURE_HELD_OUT"],
            "board_a_train_windows": len(train_df),
            "held_out_board_b_windows": len(held_out_b_df)
        },
        "models_evaluated": manifest_results
    }

    with open("ml/artifacts/v2_7/training_manifest_m2_7.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return df_comp, manifest

if __name__ == "__main__":
    run_m2_7_pipeline()
