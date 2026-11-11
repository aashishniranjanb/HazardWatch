import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import yaml
import pandas as pd
import numpy as np

from ml.adapters.dataset_adapters import GasSensorAdapter
from ml.features.extract_features import extract_window_features, generate_windowed_dataset

class TestDatasetIntelligence(unittest.TestCase):
    def setUp(self):
        self.adapter = GasSensorAdapter()

    def test_config_files_exist(self):
        self.assertTrue(os.path.exists("ml/config/label_registry.yaml"))
        self.assertTrue(os.path.exists("ml/config/sensor_compatibility.yaml"))
        self.assertTrue(os.path.exists("ml/config/feature_schema.yaml"))
        self.assertTrue(os.path.exists("ml/config/dataset_inventory.csv"))
        self.assertTrue(os.path.exists("ml/config/dataset_audit.json"))

    def test_label_registry_integrity(self):
        with open("ml/config/label_registry.yaml", "r") as f:
            registry = yaml.safe_load(f)
        self.assertIn("canonical_classes", registry)
        self.assertIn("NORMAL_BASELINE", registry["canonical_classes"])
        self.assertIn("SMOKE", registry["canonical_classes"])
        self.assertIn("VOC_RESPONSE", registry["canonical_classes"])
        self.assertIn("UNKNOWN_UNMAPPED", registry["canonical_classes"])

    def test_gas_sensors_measurements_adapter(self):
        df = self.adapter.load_gas_sensors_measurements()
        self.assertEqual(len(df), 6400)
        self.assertIn("canonical_label", df.columns)
        self.assertTrue((df["canonical_label"] == "NORMAL_BASELINE").sum() == 1600)
        self.assertTrue((df["canonical_label"] == "SMOKE").sum() == 1600)
        self.assertTrue((df["canonical_label"] == "VOC_RESPONSE").sum() == 1600)
        self.assertTrue((df["canonical_label"] == "MIXTURE").sum() == 1600)

    def test_multisensor_adapter_preserves_unmapped_labels(self):
        df = self.adapter.load_multi_sensor_data()
        self.assertEqual(len(df), 812)
        # Class 0 mapped to NORMAL_BASELINE, 1-4 mapped to UNKNOWN_UNMAPPED
        self.assertTrue((df["canonical_label"] == "NORMAL_BASELINE").sum() == 76)
        self.assertTrue((df["canonical_label"] == "UNKNOWN_UNMAPPED").sum() == (812 - 76))

    def test_baseline_dataset_adapter(self):
        df = self.adapter.load_baseline_data()
        self.assertEqual(len(df), 12175)
        self.assertTrue((df["canonical_label"] == "NORMAL_BASELINE").all())

    def test_mq2_data_malformed_handling(self):
        df = self.adapter.load_mq2_data()
        # Exactly 15,994 valid rows imported, skipping the 46 malformed rows
        self.assertEqual(len(df), 15994)
        self.assertTrue((df["canonical_label"] == "UNKNOWN_UNMAPPED").all())

    def test_unified_dataset_generation(self):
        df = pd.read_parquet("ml/datasets/processed/unified_dataset.parquet")
        self.assertEqual(len(df), 19387)
        self.assertFalse(df["mq2_adc"].isna().any())
        self.assertFalse(df["mq135_adc"].isna().any())

    def test_feature_extraction_properties(self):
        sample_mq2 = np.array([300, 310, 320, 330, 340, 350, 360, 370, 380, 390], dtype=float)
        sample_mq135 = np.array([1500, 1505, 1510, 1515, 1520, 1525, 1530, 1535, 1540, 1545], dtype=float)
        feats = extract_window_features(sample_mq2, sample_mq135)
        
        self.assertEqual(feats["mq2_raw_current"], 390.0)
        self.assertEqual(feats["mq2_min"], 300.0)
        self.assertEqual(feats["mq2_max"], 390.0)
        self.assertEqual(feats["mq2_delta"], 90.0)
        self.assertAlmostEqual(feats["mq2_mean"], 345.0)
        self.assertGreater(feats["mq2_slope"], 0.0) # Rising slope
        self.assertGreater(feats["gas_ratio_mq2_to_mq135"], 0.0)

    def test_no_data_leakage_in_session_windowing(self):
        # Ensure instances from session_0 do not bridge with session_1
        test_df = pd.DataFrame({
            "mq2_adc": [100] * 12 + [200] * 12,
            "mq135_adc": [1000] * 12 + [2000] * 12,
            "canonical_label": ["NORMAL_BASELINE"] * 12 + ["SMOKE"] * 12,
            "source_dataset": ["test"] * 24,
            "session_id": ["sess_A"] * 12 + ["sess_B"] * 12
        })
        feats = generate_windowed_dataset(test_df, window_size=10, step_size=2)
        # For sess_A: (12 - 10)/2 + 1 = 2 instances
        # For sess_B: (12 - 10)/2 + 1 = 2 instances => Total 4 instances
        self.assertEqual(len(feats), 4)
        self.assertEqual((feats["session_id"] == "sess_A").sum(), 2)
        self.assertEqual((feats["session_id"] == "sess_B").sum(), 2)

if __name__ == '__main__':
    unittest.main()
