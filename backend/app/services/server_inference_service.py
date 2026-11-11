"""
Full Python Server ML Inference Pipeline for FastAPI:
- Loads XGBoost v2.7 model and Label Encoder
- Performs feature extraction on sliding telemetry buffers
- Evaluates out-of-distribution (OOD) distance against standard scaling space
- Outputs structured inference payload with confidence and class probabilities
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "ml", "artifacts", "v2_7")

class ServerInferenceService:
    def __init__(self):
        self.scaler = joblib.load(os.path.join(ARTIFACTS_DIR, "scaler_m2_7.joblib"))
        self.le = joblib.load(os.path.join(ARTIFACTS_DIR, "label_encoder_m2_7.joblib"))
        self.xgb_model = joblib.load(os.path.join(ARTIFACTS_DIR, "xgboost_m2_7.joblib"))
        self.classes = list(self.le.classes_)

    def predict(
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
        mq135_delta_window: float = 12.0,
        ood_threshold_z: float = 4.0
    ) -> Dict[str, Any]:
        """Runs full 11-feature inference with XGBoost model and OOD checks."""
        # 1. Compute features
        mq2_delta = mq2_adc - base_mq2
        mq135_delta = mq135_adc - base_mq135
        mq2_ratio = mq2_adc / (base_mq2 + 1e-4)
        mq135_ratio = mq135_adc / (base_mq135 + 1e-4)
        cross_ratio = mq2_adc / (mq135_adc + 1e-4)

        feature_vector = np.array([[
            mq2_delta, mq135_delta, mq2_ratio, mq135_ratio,
            cross_ratio, mq2_slope, mq135_slope,
            mq2_std, mq135_std, mq2_delta_window, mq135_delta_window
        ]], dtype=np.float32)

        # 2. Standardize
        norm_features = self.scaler.transform(feature_vector)
        max_abs_z = float(np.max(np.abs(norm_features)))
        is_ood = max_abs_z > ood_threshold_z

        # 3. XGBoost Predict
        probs = self.xgb_model.predict_proba(norm_features)[0]
        pred_idx = int(np.argmax(probs))
        predicted_class = self.classes[pred_idx]
        confidence = float(probs[pred_idx])

        # If OOD, override classification to UNKNOWN / OUT_OF_DISTRIBUTION
        final_prediction = "UNKNOWN_OUT_OF_DISTRIBUTION" if is_ood else predicted_class

        prob_dict = {self.classes[i]: round(float(probs[i]), 4) for i in range(len(self.classes))}

        return {
            "prediction": final_prediction,
            "raw_class": predicted_class,
            "confidence": round(confidence, 4),
            "is_ood": is_ood,
            "max_abs_z": round(max_abs_z, 2),
            "probabilities": prob_dict,
            "features_used": {
                "mq2_delta_baseline": round(float(mq2_delta), 2),
                "mq135_delta_baseline": round(float(mq135_delta), 2),
                "mq2_ratio_baseline": round(float(mq2_ratio), 4),
                "mq135_ratio_baseline": round(float(mq135_ratio), 4),
                "cross_ratio": round(float(cross_ratio), 4)
            }
        }
