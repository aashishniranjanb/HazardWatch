import numpy as np
import pandas as pd
import yaml

def extract_window_features(series_mq2: np.ndarray, series_mq135: np.ndarray) -> dict:
    """
    Extracts statistical and temporal features over a window of readings according to feature_schema.yaml.
    """
    assert len(series_mq2) == len(series_mq135), "Sensor window lengths must match"
    n = len(series_mq2)
    x = np.arange(n)

    # MQ-2 statistics
    mq2_curr = float(series_mq2[-1])
    mq2_mean = float(np.mean(series_mq2))
    mq2_std = float(np.std(series_mq2))
    mq2_min = float(np.min(series_mq2))
    mq2_max = float(np.max(series_mq2))
    mq2_delta = mq2_max - mq2_min
    mq2_slope = float(np.polyfit(x, series_mq2, 1)[0]) if n > 1 else 0.0

    # MQ-135 statistics
    mq135_curr = float(series_mq135[-1])
    mq135_mean = float(np.mean(series_mq135))
    mq135_std = float(np.std(series_mq135))
    mq135_min = float(np.min(series_mq135))
    mq135_max = float(np.max(series_mq135))
    mq135_delta = mq135_max - mq135_min
    mq135_slope = float(np.polyfit(x, series_mq135, 1)[0]) if n > 1 else 0.0

    # Interaction feature
    ratio = float(mq2_mean / (mq135_mean + 1e-4))

    return {
        "mq2_raw_current": mq2_curr,
        "mq2_mean": mq2_mean,
        "mq2_std": mq2_std,
        "mq2_min": mq2_min,
        "mq2_max": mq2_max,
        "mq2_delta": mq2_delta,
        "mq2_slope": mq2_slope,
        "mq135_raw_current": mq135_curr,
        "mq135_mean": mq135_mean,
        "mq135_std": mq135_std,
        "mq135_min": mq135_min,
        "mq135_max": mq135_max,
        "mq135_delta": mq135_delta,
        "mq135_slope": mq135_slope,
        "gas_ratio_mq2_to_mq135": ratio,
    }

def generate_windowed_dataset(
    df: pd.DataFrame,
    window_size: int = 10,
    step_size: int = 2
) -> pd.DataFrame:
    """
    Applies sliding window extraction per session without leaking future records.
    """
    records = []
    # Group by session to prevent cross-session leakage during windowing
    for session_id, group in df.groupby("session_id", sort=False):
        group = group.reset_index(drop=True)
        mq2_arr = group["mq2_adc"].to_numpy()
        mq135_arr = group["mq135_adc"].to_numpy()
        labels = group["canonical_label"].to_numpy()
        sources = group["source_dataset"].to_numpy()

        for start_idx in range(0, len(group) - window_size + 1, step_size):
            end_idx = start_idx + window_size
            w_mq2 = mq2_arr[start_idx:end_idx]
            w_mq135 = mq135_arr[start_idx:end_idx]

            # Label of the current instance is the label of the last window sample
            instance_label = labels[end_idx - 1]
            instance_source = sources[end_idx - 1]

            feats = extract_window_features(w_mq2, w_mq135)
            feats["canonical_label"] = instance_label
            feats["source_dataset"] = instance_source
            feats["session_id"] = session_id
            records.append(feats)

    return pd.DataFrame(records)

if __name__ == "__main__":
    df_raw = pd.read_parquet("ml/datasets/processed/unified_dataset.parquet")
    print(f"Loaded {len(df_raw)} records for windowing feature extraction...")
    df_feats = generate_windowed_dataset(df_raw, window_size=10, step_size=2)
    df_feats.to_parquet("ml/datasets/processed/windowed_features.parquet", index=False)
    print(f"Generated {len(df_feats)} windowed feature vectors.")
    print("Columns:", df_feats.columns.tolist())
    print("Class distribution in feature instances:")
    print(df_feats["canonical_label"].value_counts())
