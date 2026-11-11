"""
Milestone 5.0 C++ vs Python Feature Parity Harness
Directly executes identical sliding-window test vectors across:
1. Python reference feature extractor (extract_window_features / feature_schema_v2)
2. C++ simulated feature extractor (FeatureExtractor::extractFeatures)
Verifies exact 11-feature alignment, numerical tolerances (< 1e-4), and scaler math.
"""

import math
import numpy as np
import pandas as pd
import joblib

# Feature Names in exact canonical order
CANONICAL_FEATURES = [
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

SCALER_MEAN = np.array([
    194.755155, 189.242228, 1.556443, 1.130512, 0.328509,
    -0.106840, -0.063746, 16.656122, 21.972149, 51.571433, 69.947020
], dtype=np.float32)

SCALER_SCALE = np.array([
    332.701391, 314.119626, 0.950575, 0.216634, 0.182731,
    11.335395, 10.898889, 40.754281, 38.787090, 101.551394, 98.909952
], dtype=np.float32)

def python_feature_extractor(window_mq2, window_mq135, base_mq2=338.0, base_mq135=1523.0):
    """Python implementation conforming to feature_schema_v2.yaml."""
    w2 = np.array(window_mq2, dtype=float)
    w135 = np.array(window_mq135, dtype=float)
    n = len(w2)

    mean_2 = np.mean(w2)
    mean_135 = np.mean(w135)

    delta_2 = mean_2 - base_mq2
    delta_135 = mean_135 - base_mq135
    ratio_2 = mean_2 / (base_mq2 + 1e-4)
    ratio_135 = mean_135 / (base_mq135 + 1e-4)
    cross_ratio = mean_2 / (mean_135 + 1e-4)

    t_axis = np.arange(n) * 0.5
    slope_2, _ = np.polyfit(t_axis, w2, 1)
    slope_135, _ = np.polyfit(t_axis, w135, 1)

    std_2 = np.std(w2, ddof=1)
    std_135 = np.std(w135, ddof=1)

    range_2 = np.ptp(w2)
    range_135 = np.ptp(w135)

    return np.array([
        delta_2, delta_135, ratio_2, ratio_135, cross_ratio,
        slope_2, slope_135, std_2, std_135, range_2, range_135
    ], dtype=np.float32)

def cpp_simulated_feature_extractor(window_mq2, window_mq135, base_mq2=338.0, base_mq135=1523.0):
    """Exact C++ math implementation replicating FeatureExtractor::extractFeatures."""
    windowSize = len(window_mq2)
    sum_mq2 = 0.0
    sum_mq135 = 0.0
    min_mq2 = 4096
    max_mq2 = -1
    min_mq135 = 4096
    max_mq135 = -1

    for i in range(windowSize):
        q2 = window_mq2[i]
        q135 = window_mq135[i]
        sum_mq2 += q2
        sum_mq135 += q135
        if q2 < min_mq2: min_mq2 = q2
        if q2 > max_mq2: max_mq2 = q2
        if q135 < min_mq135: min_mq135 = q135
        if q135 > max_mq135: max_mq135 = q135

    mean_mq2 = sum_mq2 / windowSize
    mean_mq135 = sum_mq135 / windowSize

    mq2_delta_base = mean_mq2 - base_mq2
    mq135_delta_base = mean_mq135 - base_mq135
    mq2_ratio_base = mean_mq2 / (base_mq2 + 1e-4)
    mq135_ratio_base = mean_mq135 / (base_mq135 + 1e-4)
    cross_ratio = mean_mq2 / (mean_mq135 + 1e-4)

    t_mean = (windowSize - 1) * 0.5 / 2.0
    num_mq2 = 0.0
    num_mq135 = 0.0
    denom = 0.0
    for i in range(windowSize):
        t = i * 0.5
        dt = t - t_mean
        num_mq2 += dt * (window_mq2[i] - mean_mq2)
        num_mq135 += dt * (window_mq135[i] - mean_mq135)
        denom += dt * dt

    slope_mq2 = num_mq2 / denom if denom > 1e-5 else 0.0
    slope_mq135 = num_mq135 / denom if denom > 1e-5 else 0.0

    var_mq2 = 0.0
    var_mq135 = 0.0
    for i in range(windowSize):
        d2 = window_mq2[i] - mean_mq2
        d135 = window_mq135[i] - mean_mq135
        var_mq2 += d2 * d2
        var_mq135 += d135 * d135

    std_mq2 = math.sqrt(var_mq2 / (windowSize - 1))
    std_mq135 = math.sqrt(var_mq135 / (windowSize - 1))

    range_mq2 = float(max_mq2 - min_mq2)
    range_mq135 = float(max_mq135 - min_mq135)

    return np.array([
        mq2_delta_base, mq135_delta_base, mq2_ratio_base, mq135_ratio_base, cross_ratio,
        slope_mq2, slope_mq135, std_mq2, std_mq135, range_mq2, range_mq135
    ], dtype=np.float32)

def run_parity_comparison():
    print("=== M5.0 C++ VS PYTHON FEATURE PARITY AUDIT ===")

    # Test Vector 1: Nominal Clean Baseline
    v1_mq2 = [339, 341, 338, 340, 342, 339, 340, 341, 338, 340]
    v1_mq135 = [1522, 1525, 1520, 1524, 1521, 1523, 1526, 1522, 1524, 1521]

    # Test Vector 2: Transient Combustible Influx (Steep MQ-2 slope)
    v2_mq2 = [340, 360, 395, 440, 500, 570, 650, 740, 835, 940]
    v2_mq135 = [1520, 1530, 1545, 1560, 1580, 1605, 1630, 1660, 1690, 1725]

    # Test Vector 3: VOC Solvent Response (High MQ-135 std & range)
    v3_mq2 = [345, 342, 348, 344, 350, 346, 352, 348, 355, 350]
    v3_mq135 = [1530, 1620, 1710, 1820, 1950, 2080, 2210, 2350, 2480, 2600]

    vectors = [
        ("NOMINAL_BASELINE", v1_mq2, v1_mq135),
        ("COMBUSTIBLE_TRANSIENT", v2_mq2, v2_mq135),
        ("VOC_SOLVENT_RESPONSE", v3_mq2, v3_mq135)
    ]

    parity_rows = []

    for name, w2, w135 in vectors:
        py_feats = python_feature_extractor(w2, w135)
        cpp_feats = cpp_simulated_feature_extractor(w2, w135)

        # Standardize
        py_norm = (py_feats - SCALER_MEAN) / SCALER_SCALE
        cpp_norm = (cpp_feats - SCALER_MEAN) / SCALER_SCALE

        for idx, feat_name in enumerate(CANONICAL_FEATURES):
            py_val = float(py_feats[idx])
            cpp_val = float(cpp_feats[idx])
            abs_diff = abs(py_val - cpp_val)
            rel_diff = (abs_diff / (abs(py_val) + 1e-5)) * 100.0

            py_z = float(py_norm[idx])
            cpp_z = float(cpp_norm[idx])
            z_diff = abs(py_z - cpp_z)

            passed = (abs_diff < 1e-4) and (z_diff < 1e-4)

            parity_rows.append({
                "test_vector": name,
                "feature_index": idx,
                "feature_name": feat_name,
                "python_val": round(py_val, 5),
                "cpp_val": round(cpp_val, 5),
                "abs_diff": round(abs_diff, 7),
                "python_z": round(py_z, 5),
                "cpp_z": round(cpp_z, 5),
                "z_diff": round(z_diff, 7),
                "parity_pass": passed
            })

    df = pd.DataFrame(parity_rows)
    all_passed = df["parity_pass"].all()
    max_diff = df["abs_diff"].max()

    print(f"Evaluated {len(df)} feature comparisons across 3 test vectors.")
    print(f"Max absolute discrepancy: {max_diff:.8f}")
    print(f"All features matched with < 1e-4 tolerance: {all_passed}")

    # Save to CSV
    csv_path = "reports/m5_0_feature_parity_table.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved parity audit table to {csv_path}")

    assert all_passed, "Feature parity check failed!"

if __name__ == "__main__":
    run_parity_comparison()
