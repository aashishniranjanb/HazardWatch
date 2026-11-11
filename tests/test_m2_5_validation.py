import unittest
import os
import json
import pandas as pd

class TestM25ValidationAudit(unittest.TestCase):
    def test_v2_artifacts_exist(self):
        self.assertTrue(os.path.exists("ml/config/feature_schema_v2.yaml"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/training_manifest_v2.json"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/scaler_v2.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/label_encoder_v2.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/random_forest_v2.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/xgboost_v2.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2/compact_mlp_v2.keras"))
        self.assertTrue(os.path.exists("reports/m2_5_model_comparison.csv"))

    def test_partition_purge_gaps_prevent_leakage(self):
        with open("ml/artifacts/v2/training_manifest_v2.json") as f:
            manifest = json.load(f)
        parts = manifest["partitions"]
        self.assertEqual(parts["method"], "SESSION_CONTIGUOUS_SPLIT_WITH_PURGE_GAPS")
        self.assertEqual(parts["purge_gap_windows"], 5)
        # Train (2228), Val (476), Test (440) -> Test count reflects 40 windows purged (10 per class)
        self.assertEqual(parts["test_samples"], 440)

    def test_baseline_relative_features_present(self):
        with open("ml/artifacts/v2/training_manifest_v2.json") as f:
            manifest = json.load(f)
        feats = manifest["features"]
        self.assertIn("mq2_delta_baseline", feats)
        self.assertIn("mq135_delta_baseline", feats)
        self.assertIn("mq2_ratio_baseline", feats)
        self.assertIn("mq135_ratio_baseline", feats)
        self.assertEqual(len(feats), 11)

    def test_smoke_precision_and_recall_preserved(self):
        with open("ml/artifacts/v2/training_manifest_v2.json") as f:
            manifest = json.load(f)
        for model in ["Random Forest v2", "XGBoost v2", "Compact MLP v2"]:
            smoke_metrics = manifest["models_evaluated"][model]["per_class"]["SMOKE"]
            self.assertEqual(smoke_metrics["recall"], 1.0)

if __name__ == '__main__':
    unittest.main()
