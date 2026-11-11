import unittest
import os
import json
import numpy as np
import pandas as pd
import joblib

class TestMilestone2Validation(unittest.TestCase):
    def test_artifacts_exist(self):
        self.assertTrue(os.path.exists("ml/artifacts/training_manifest.json"))
        self.assertTrue(os.path.exists("ml/artifacts/scaler.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/label_encoder.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/random_forest_baseline.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/xgboost_baseline.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/compact_mlp_baseline.keras"))
        self.assertTrue(os.path.exists("reports/baseline_model_comparison.csv"))

    def test_manifest_integrity(self):
        with open("ml/artifacts/training_manifest.json") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["milestone"], "M2_BASELINE_EXPERIMENT")
        self.assertEqual(manifest["random_seed"], 42)
        self.assertEqual(len(manifest["input_features"]), 15)
        self.assertIn("Random Forest", manifest["models_evaluated"])
        self.assertIn("XGBoost", manifest["models_evaluated"])
        self.assertIn("Compact MLP (Keras)", manifest["models_evaluated"])

    def test_domain_shift_reported(self):
        # Verify that domain incompatibility of external baseline is captured
        with open("ml/artifacts/training_manifest.json") as f:
            manifest = json.load(f)
        for model_name in ["Random Forest", "XGBoost", "Compact MLP (Keras)"]:
            base_eval = manifest["models_evaluated"][model_name]["external_baseline_evaluation"]
            self.assertEqual(base_eval["total_baseline_samples"], 6083)
            # Crucial check: external baseline classified as normal is 0% due to sensor rig shift
            self.assertEqual(base_eval["classified_as_normal_baseline_percentage"], 0.0)

    def test_compact_mlp_size_for_embedded(self):
        # Compact Keras MLP must be small enough for ESP32 SRAM
        size_kb = os.path.getsize("ml/artifacts/compact_mlp_baseline.keras") / 1024
        self.assertLess(size_kb, 100.0) # Well under 100KB

    def test_baseline_registry_exists(self):
        self.assertTrue(os.path.exists("ml/config/baseline_registry.yaml"))

if __name__ == '__main__':
    unittest.main()
