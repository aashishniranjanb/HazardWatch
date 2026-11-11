import unittest
import os
import json
import pandas as pd

class TestM3QuantizationAndExport(unittest.TestCase):
    def test_artifacts_exist(self):
        self.assertTrue(os.path.exists("ml/artifacts/v3/compact_mlp_int8_ops.tflite"))
        self.assertTrue(os.path.exists("firmware/models/model_data.h"))
        self.assertTrue(os.path.exists("reports/int8_float_parity.csv"))
        self.assertTrue(os.path.exists("ml/artifacts/v3/quantization_manifest.json"))
        self.assertTrue(os.path.exists("firmware/m3_benchmark/m3_tflm_benchmark.ino"))
        self.assertTrue(os.path.exists("ml/collection/hardware_validation_recorder.py"))

    def test_parity_metrics(self):
        df_p = pd.read_csv("reports/int8_float_parity.csv")
        self.assertEqual(len(df_p), 2)
        # Check that TFLite INT8 ops model achieves 100% agreement on the evaluated test set
        tflite_row = df_p[df_p["format"].str.contains("TFLite")].iloc[0]
        self.assertEqual(tflite_row["agreement_pct"], 100.0)
        self.assertEqual(tflite_row["normal_recall"], 1.0)
        self.assertEqual(tflite_row["smoke_recall"], 1.0)

    def test_model_size_reduction(self):
        # Keras float32: ~38.7 KB -> TFLite INT8: ~5.2 KB (~7.4x compression)
        df_p = pd.read_csv("reports/int8_float_parity.csv")
        keras_sz = df_p[df_p["format"].str.contains("Keras")].iloc[0]["model_size_kb"]
        tflite_sz = df_p[df_p["format"].str.contains("TFLite")].iloc[0]["model_size_kb"]
        self.assertLess(tflite_sz, 10.0)
        self.assertGreater(keras_sz / tflite_sz, 5.0)

    def test_header_file_integrity(self):
        with open("firmware/models/model_data.h", "r") as f:
            content = f.read()
        self.assertIn("g_compact_mlp_model_data", content)
        self.assertIn("G_FEATURE_MEANS", content)
        self.assertIn("G_FEATURE_SCALES", content)
        self.assertIn("G_CLASS_LABELS", content)
        self.assertIn("NORMAL_BASELINE", content)

if __name__ == '__main__':
    unittest.main()
