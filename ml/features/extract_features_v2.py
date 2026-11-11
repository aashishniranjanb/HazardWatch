import numpy as np
import pandas as pd
import yaml

def extract_window_features_v2(
    series_mq2: np.ndarray,
    series_mq135: np.ndarray,
    baseline_mq2: float,
    baseline_mq135: float
) -> dict:
    """
    Extracts M2.5 baseline-relative and temporal dynamics features according to feature_schema_v2.yaml.
    """
    assert len(series_mq2) == len(series_mq135), "Window lengths must match"
    n = len(series_mq2)
    x = np.arange(n)

    mq2_mean = float(np.mean(series_mq2))
    mq2_std = float(np.std(series_mq2))
    mq2_min = float(np.min(series_mq2))
    mq2_max = float(np.max(series_mq2))
    mq2_delta_window = mq2_max - mq2_min
    mq2_slope = float(np.polyfit(x, series_mq2, 1)[0]) if n > 1 else 0.0

    mq135_mean = float(np.mean(series_mq135))
    mq135_std = float(np.std(series_mq135))
    mq135_min = float(np.min(series_mq135))
    mq135_max = float(np.max(series_mq135))
    mq135_delta_window = mq135_max - mq135_min
    mq135_slope = float(np.polyfit(x, series_mq135, 1)[0]) if n > 1 else 0.0

    # Baseline-Relative Features
    mq2_delta_baseline = mq2_mean - baseline_mq2
    mq135_delta_baseline = mq135_mean - baseline_mq135
    mq2_ratio_baseline = mq2_mean / (baseline_mq2 + 1e-4)
    mq135_ratio_baseline = mq135_mean / (baseline_mq135 + 1e-4)

    # Interaction Feature
    ratio_inter = mq2_mean / (mq135_mean + 1e-4)

    return {
        "mq2_delta_baseline": mq2_delta_baseline,
        "mq135_delta_baseline": mq135_delta_baseline,
        "mq2_ratio_baseline": mq2_ratio_baseline,
        "mq135_ratio_baseline": mq135_ratio_baseline,
        "gas_ratio_mq2_to_mq135": ratio_inter,
        "mq2_slope": mq2_slope,
        "mq135_slope": mq135_slope,
        "mq2_std": mq2_std,
        "mq135_std": mq135_std,
        "mq2_delta_window": mq2_delta_window,
        "mq135_delta_window": mq135_delta_window,
    }

def generate_baseline_relative_dataset(
    df: pd.DataFrame,
    source_baselines: dict,
    window_size: int = 10,
    step_size: int = 2
) -> pd.DataFrame:
    records = []
    for session_id, group in df.groupby("session_id", sort=False):
        group = group.reset_index(drop=True)
        source = group["source_dataset"].iloc[0]
        base_mq2 = source_baselines[source]["mq2"]
        base_mq135 = source_baselines[source]["mq135"]

        mq2_arr = group["mq2_adc"].to_numpy()
        mq135_arr = group["mq135_adc"].to_numpy()
        labels = group["canonical_label"].to_numpy()

        for start_idx in range(0, len(group) - window_size + 1, step_size):
            end_idx = start_idx + window_size
            w_mq2 = mq2_arr[start_idx:end_idx]
            w_mq135 = mq135_arr[start_idx:end_idx]

            instance_label = labels[end_idx - 1]
            feats = extract_window_features_v2(w_mq2, w_mq135, base_mq2, base_mq135)
            feats["canonical_label"] = instance_label
            feats["source_dataset"] = source
            feats["session_id"] = session_id
            feats["window_start_idx"] = start_idx
            feats["window_end_idx"] = end_idx
            records.append(feats)

    return pd.DataFrame(records)

if __name__ == "__main__":
    df_unified = pd.read_parquet("ml/datasets/processed/unified_dataset.parquet")
    
    # Baselines determined strictly from reference/clean-air distributions of each source
    # For Gas_Sensors_Measurements: clean air NoGas mean from training
    # For multi_sensor_data_baseline: verified baseline rig mean
    # For multi_sensor_data: baseline trial 0 mean
    source_baselines = {
        "Gas_Sensors_Measurements": {"mq2": 735.7, "mq135": 462.6}, # Calculated on train partition of NoGas!
        "multi_sensor_data_baseline": {"mq2": 337.94, "mq135": 1522.83},
        "multi_sensor_data": {"mq2": 337.94, "mq135": 1522.83},
    }

    df_feats_v2 = generate_baseline_relative_dataset(df_unified, source_baselines)
    df_feats_v2.to_parquet("ml/datasets/processed/windowed_features_v2.parquet", index=False)
    print(f"Generated {len(df_feats_v2)} baseline-relative feature instances.")
    print("Columns:", [c for c in df_feats_v2.columns if c not in ["canonical_label", "source_dataset", "session_id", "window_start_idx", "window_end_idx"]])
