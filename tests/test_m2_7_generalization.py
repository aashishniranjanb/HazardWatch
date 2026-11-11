import unittest
import os
import json
import pandas as pd

class TestM27IndependentValidation(unittest.TestCase):
    def test_trial_files_generated(self):
        trial_dir = "ml/collection/trials"
        self.assertTrue(os.path.exists(trial_dir))
        files = os.listdir(trial_dir)
        self.assertGreaterEqual(len(files), 8)
        # Check presence of both boards
        board_a_files = [f for f in files if "EXP_A" in f]
        board_b_files = [f for f in files if "EXP_B" in f]
        self.assertGreaterEqual(len(board_a_files), 4)
        self.assertGreaterEqual(len(board_b_files), 3)

    def test_trial_schema_columns(self):
        df = pd.read_parquet("ml/collection/trials/EXP_A_001_CLEAN_AIR_WARMUP.parquet")
        expected_cols = [
            "experiment_id", "sensor_board_id", "mq2_module_id", "mq135_module_id",
            "timestamp", "mq2_adc", "mq135_adc", "temperature", "humidity",
            "experiment_condition", "calibration_reference", "exposure_start",
            "exposure_end", "recovery_phase", "ground_truth_source"
        ]
        for col in expected_cols:
            self.assertIn(col, df.columns)

    def test_m2_7_artifacts_exist(self):
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/training_manifest_m2_7.json"))
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/scaler_m2_7.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/label_encoder_m2_7.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/random_forest_m2_7.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/xgboost_m2_7.joblib"))
        self.assertTrue(os.path.exists("ml/artifacts/v2_7/compact_mlp_m2_7.keras"))
        self.assertTrue(os.path.exists("reports/m2_7_generalization_comparison.csv"))

    def test_cross_device_normal_baseline_recall_solved(self):
        # In M2 it was 0%, in M2.5 it was 0-5%. In M2.7 with device-specific baselines, it should exceed 95%
        with open("ml/artifacts/v2_7/training_manifest_m2_7.json") as f:
            manifest = json.load(f)
        for model in ["Random Forest M2.7", "XGBoost M2.7", "Compact MLP M2.7"]:
            normal_recall = manifest["models_evaluated"][model]["per_class"]["NORMAL_BASELINE"]["recall"]
            self.assertGreater(normal_recall, 0.95)

if __name__ == '__main__':
    unittest.main()
