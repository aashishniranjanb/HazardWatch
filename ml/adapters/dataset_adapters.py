"""
Dataset Adapters for Industrial Gas Monitoring
Normalizes candidate datasets into harmonized Parquet and features.
"""

import os
import csv
import pandas as pd
import numpy as np
import yaml

class GasSensorAdapter:
    def __init__(self, label_registry_path="ml/config/label_registry.yaml"):
        with open(label_registry_path, "r") as f:
            self.registry = yaml.safe_load(f)

    def load_gas_sensors_measurements(self, filepath="Gas_Sensors_Measurements.csv") -> pd.DataFrame:
        """
        Loads Gas_Sensors_Measurements.csv (6,400 rows).
        Features: Serial Number, MQ2, MQ3, MQ5, MQ6, MQ7, MQ8, MQ135, Gas
        Classes: NoGas, Perfume, Smoke, Mixture
        """
        df = pd.read_csv(filepath)
        source_meta = self.registry["sources"]["Gas_Sensors_Measurements"]["labels"]

        # Map labels to canonical
        df["canonical_label"] = df["Gas"].map(lambda x: source_meta.get(x, {}).get("canonical", "UNKNOWN_UNMAPPED"))
        df["label_confidence"] = df["Gas"].map(lambda x: source_meta.get(x, {}).get("confidence", 0.0))
        df["is_verified"] = df["Gas"].map(lambda x: source_meta.get(x, {}).get("verified", False))

        # Standardize columns
        harmonized = pd.DataFrame({
            "source_dataset": "Gas_Sensors_Measurements",
            "sample_index": df["Serial Number"],
            "mq2_adc": df["MQ2"].astype(float),
            "mq135_adc": df["MQ135"].astype(float),
            "mq7_adc": df["MQ7"].astype(float),
            "temperature": np.nan,
            "humidity": np.nan,
            "raw_label": df["Gas"],
            "canonical_label": df["canonical_label"],
            "label_confidence": df["label_confidence"],
            "is_verified": df["is_verified"],
            "session_id": df["Gas"] # 1600 rows per session
        })
        return harmonized

    def load_multi_sensor_data(self, filepath="multi_sensor_data.csv") -> pd.DataFrame:
        """
        Loads multi_sensor_data.csv (812 rows).
        Classes: 0, 1, 2, 3, 4
        """
        df = pd.read_csv(filepath)
        source_meta = self.registry["sources"]["multi_sensor_data"]["labels"]

        df["canonical_label"] = df["label"].astype(str).map(
            lambda x: source_meta.get(x, {}).get("canonical", "UNKNOWN_UNMAPPED")
        )
        df["label_confidence"] = df["label"].astype(str).map(
            lambda x: source_meta.get(x, {}).get("confidence", 0.0)
        )
        df["is_verified"] = df["label"].astype(str).map(
            lambda x: source_meta.get(x, {}).get("verified", False)
        )

        harmonized = pd.DataFrame({
            "source_dataset": "multi_sensor_data",
            "sample_index": np.arange(len(df)),
            "mq2_adc": pd.to_numeric(df["mq2_adc"], errors="coerce"),
            "mq135_adc": pd.to_numeric(df["mq135_adc"], errors="coerce"),
            "mq7_adc": pd.to_numeric(df["mq7_adc"], errors="coerce"),
            "temperature": np.nan,
            "humidity": np.nan,
            "raw_label": df["label"].astype(str),
            "canonical_label": df["canonical_label"],
            "label_confidence": df["label_confidence"],
            "is_verified": df["is_verified"],
            "session_id": "session_" + df["label"].astype(str)
        })
        return harmonized

    def load_baseline_data(self, filepath="multi_sensor_data_baseline.csv") -> pd.DataFrame:
        """
        Loads multi_sensor_data_baseline.csv (12,175 rows, class 0).
        """
        df = pd.read_csv(filepath)
        harmonized = pd.DataFrame({
            "source_dataset": "multi_sensor_data_baseline",
            "sample_index": np.arange(len(df)),
            "mq2_adc": pd.to_numeric(df["mq2_adc"], errors="coerce"),
            "mq135_adc": pd.to_numeric(df["mq135_adc"], errors="coerce"),
            "mq7_adc": pd.to_numeric(df["mq7_adc"], errors="coerce"),
            "temperature": np.nan,
            "humidity": np.nan,
            "raw_label": "0",
            "canonical_label": "NORMAL_BASELINE",
            "label_confidence": 1.0,
            "is_verified": True,
            "session_id": "baseline_run_continuous"
        })
        return harmonized

    def load_mq2_data(self, filepath="mq2_data.csv") -> pd.DataFrame:
        """
        Loads mq2_data.csv (15,994 valid rows, 46 malformed skipped).
        """
        valid_rows = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) == len(header):
                    valid_rows.append(row)

        df = pd.DataFrame(valid_rows, columns=header)
        harmonized = pd.DataFrame({
            "source_dataset": "mq2_data",
            "sample_index": np.arange(len(df)),
            "mq2_adc": pd.to_numeric(df["ADC"], errors="coerce"),
            "mq135_adc": np.nan,
            "mq7_adc": np.nan,
            "temperature": np.nan,
            "humidity": np.nan,
            "raw_label": "UNLABELED",
            "canonical_label": "UNKNOWN_UNMAPPED",
            "label_confidence": 0.0,
            "is_verified": False,
            "session_id": "mq2_drift_profile"
        })
        return harmonized

    def build_unified_dataset(self) -> pd.DataFrame:
        """
        Builds the unified dataset combining the verified dual-sensor datasets.
        """
        df_gsm = self.load_gas_sensors_measurements()
        df_ms = self.load_multi_sensor_data()
        df_base = self.load_baseline_data()

        # Concatenate dual-channel records
        unified = pd.concat([df_gsm, df_ms, df_base], ignore_index=True)
        return unified

if __name__ == "__main__":
    adapter = GasSensorAdapter()
    unified = adapter.build_unified_dataset()
    os.makedirs("ml/datasets/processed", exist_ok=True)
    unified.to_parquet("ml/datasets/processed/unified_dataset.parquet", index=False)
    print(f"Unified dataset created: {len(unified)} records saved to ml/datasets/processed/unified_dataset.parquet")
    print("Class breakdown:")
    print(unified["canonical_label"].value_counts())
    print("Dataset breakdown:")
    print(unified["source_dataset"].value_counts())
