"""
Comprehensive Multi-Model AI Service (M4.5):
Loads and manages inference comparison across:
1. Random Forest (M2.7)
2. XGBoost (M2.7)
3. Compact MLP Keras Float32 (M2.7)
4. TFLite Micro INT8 ops Reference (v3)

Preprocesses raw sensor inputs using exact 11-feature schema (feature_schema_v2.yaml)
with strict Mahalanobis / StandardScaler Out-of-Distribution Gating ($z > 4.0\sigma$).
"""

import os
import time
import joblib
import numpy as np
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "ml", "artifacts", "v2_7")
V3_DIR = os.path.join(PROJECT_ROOT, "ml", "artifacts", "v3")

class MultiModelAIService:
    def __init__(self):
        # 1. Load Preprocessors
        self.scaler = joblib.load(os.path.join(ARTIFACTS_DIR, "scaler_m2_7.joblib"))
        self.le = joblib.load(os.path.join(ARTIFACTS_DIR, "label_encoder_m2_7.joblib"))
        self.classes = list(self.le.classes_)

        # 2. Load Scikit-Learn / XGBoost Models
        self.rf_model = joblib.load(os.path.join(ARTIFACTS_DIR, "random_forest_m2_7.joblib"))
        self.xgb_model = joblib.load(os.path.join(ARTIFACTS_DIR, "xgboost_m2_7.joblib"))

        # 3. Load Keras Float32 Model
        try:
            import tensorflow as tf
            self.mlp_model = tf.keras.models.load_model(os.path.join(ARTIFACTS_DIR, "compact_mlp_m2_7.keras"))
            
            # 4. Load TFLite INT8 Reference
            self.tflite_interpreter = tf.lite.Interpreter(model_path=os.path.join(V3_DIR, "compact_mlp_int8_ops.tflite"))
            self.tflite_interpreter.allocate_tensors()
            self.tflite_in_details = self.tflite_interpreter.get_input_details()
            self.tflite_out_details = self.tflite_interpreter.get_output_details()
            self.tf_available = True
        except Exception as e:
            print(f"[Warning] TensorFlow loading failed in MultiModelAIService: {e}")
            self.mlp_model = None
            self.tflite_interpreter = None
            self.tf_available = False

    def get_models_metadata(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "xgboost_v2_7",
                "name": "XGBoost Classifier (Primary Server Model)",
                "type": "Gradient Boosted Decision Trees",
                "framework": "XGBoost / Scikit-Learn",
                "status": "ACTIVE_PRIMARY",
                "features_count": 11,
                "classes": self.classes,
                "latency_ms_estimate": 0.85
            },
            {
                "id": "random_forest_v2_7",
                "name": "Random Forest Ensemble (M2.7)",
                "type": "Bagged Decision Trees",
                "framework": "Scikit-Learn",
                "status": "COMPARISON_BENCHMARK",
                "features_count": 11,
                "classes": self.classes,
                "latency_ms_estimate": 1.20
            },
            {
                "id": "compact_mlp_float32",
                "name": "Compact MLP Float32 (M2.7)",
                "type": "Deep Neural Network",
                "framework": "TensorFlow / Keras",
                "status": "COMPARISON_BENCHMARK",
                "features_count": 11,
                "classes": self.classes,
                "latency_ms_estimate": 1.45
            },
            {
                "id": "compact_mlp_int8_edge",
                "name": "TFLite Micro INT8 Reference (v3 Edge Model)",
                "type": "Quantized Neural Network (INT8 ops)",
                "framework": "TensorFlow Lite Micro",
                "status": "EDGE_TARGET",
                "features_count": 11,
                "classes": self.classes,
                "latency_ms_estimate": 0.31
            }
        ]

    def extract_features(
        self,
        mq2_adc: float,
        mq135_adc: float,
        base_mq2: float = 338.0,
        base_mq135: float = 1523.0,
        mq2_slope: float = 0.0,
        mq135_slope: float = 0.0,
        mq2_std: float = 2.5,
        mq135_std: float = 5.0,
        mq2_delta_window: float = 6.0,
        mq135_delta_window: float = 12.0
    ) -> np.ndarray:
        mq2_delta = mq2_adc - base_mq2
        mq135_delta = mq135_adc - base_mq135
        mq2_ratio = mq2_adc / (base_mq2 + 1e-4)
        mq135_ratio = mq135_adc / (base_mq135 + 1e-4)
        cross_ratio = mq2_adc / (mq135_adc + 1e-4)

        raw = np.array([[
            mq2_delta, mq135_delta, mq2_ratio, mq135_ratio,
            cross_ratio, mq2_slope, mq135_slope,
            mq2_std, mq135_std, mq2_delta_window, mq135_delta_window
        ]], dtype=np.float32)
        return raw

    def predict_all(
        self,
        mq2_adc: float,
        mq135_adc: float,
        base_mq2: float = 338.0,
        base_mq135: float = 1523.0,
        mq2_slope: float = 0.0,
        mq135_slope: float = 0.0,
        ood_threshold_z: float = 4.0
    ) -> Dict[str, Any]:
        raw_feats = self.extract_features(
            mq2_adc=mq2_adc,
            mq135_adc=mq135_adc,
            base_mq2=base_mq2,
            base_mq135=base_mq135,
            mq2_slope=mq2_slope,
            mq135_slope=mq135_slope
        )
        norm_feats = self.scaler.transform(raw_feats).astype(np.float32)
        max_abs_z = float(np.max(np.abs(norm_feats)))
        is_ood = max_abs_z > ood_threshold_z

        results = {}

        # 1. XGBoost Predict
        t0 = time.perf_counter()
        xgb_probs = self.xgb_model.predict_proba(norm_feats)[0]
        xgb_lat = (time.perf_counter() - t0) * 1000.0
        xgb_idx = int(np.argmax(xgb_probs))
        results["xgboost"] = {
            "prediction": "UNKNOWN_OOD" if is_ood else self.classes[xgb_idx],
            "confidence": round(float(xgb_probs[xgb_idx]), 4),
            "latency_ms": round(xgb_lat, 2),
            "probabilities": {self.classes[i]: round(float(xgb_probs[i]), 4) for i in range(len(self.classes))}
        }

        # 2. Random Forest Predict
        t0 = time.perf_counter()
        rf_probs = self.rf_model.predict_proba(norm_feats)[0]
        rf_lat = (time.perf_counter() - t0) * 1000.0
        rf_idx = int(np.argmax(rf_probs))
        results["random_forest"] = {
            "prediction": "UNKNOWN_OOD" if is_ood else self.classes[rf_idx],
            "confidence": round(float(rf_probs[rf_idx]), 4),
            "latency_ms": round(rf_lat, 2),
            "probabilities": {self.classes[i]: round(float(rf_probs[i]), 4) for i in range(len(self.classes))}
        }

        # 3. Keras Float32 Predict
        if self.mlp_model:
            t0 = time.perf_counter()
            mlp_probs = self.mlp_model.predict(norm_feats, verbose=0)[0]
            mlp_lat = (time.perf_counter() - t0) * 1000.0
            mlp_idx = int(np.argmax(mlp_probs))
            results["compact_mlp_float32"] = {
                "prediction": "UNKNOWN_OOD" if is_ood else self.classes[mlp_idx],
                "confidence": round(float(mlp_probs[mlp_idx]), 4),
                "latency_ms": round(mlp_lat, 2),
                "probabilities": {self.classes[i]: round(float(mlp_probs[i]), 4) for i in range(len(self.classes))}
            }

        # 4. TFLite INT8 ops Predict
        if self.tflite_interpreter:
            t0 = time.perf_counter()
            self.tflite_interpreter.set_tensor(self.tflite_in_details[0]['index'], norm_feats)
            self.tflite_interpreter.invoke()
            tflite_out = self.tflite_interpreter.get_tensor(self.tflite_out_details[0]['index'])[0]
            tfl_lat = (time.perf_counter() - t0) * 1000.0
            tfl_idx = int(np.argmax(tflite_out))
            results["compact_mlp_int8_edge"] = {
                "prediction": "UNKNOWN_OOD" if is_ood else self.classes[tfl_idx],
                "confidence": round(float(tflite_out[tfl_idx]), 4),
                "latency_ms": round(tfl_lat, 2),
                "probabilities": {self.classes[i]: round(float(tflite_out[i]), 4) for i in range(len(self.classes))}
            }

        # Consensus & Disagreement Audit
        preds = [v["prediction"] for v in results.values()]
        consensus = len(set(preds)) == 1

        return {
            "primary_prediction": results["xgboost"]["prediction"],
            "primary_confidence": results["xgboost"]["confidence"],
            "is_ood": is_ood,
            "max_abs_z": round(max_abs_z, 2),
            "consensus": consensus,
            "models": results
        }
