"""
M2.7 Experiment Recording & Data Ingestion Schema
Defines the required metadata fields for multi-trial experiments:
- experiment_id
- sensor_board_id
- mq2_module_id
- mq135_module_id
- timestamp
- mq2_adc
- mq135_adc
- temperature
- humidity
- experiment_condition (NORMAL_BASELINE, SMOKE, VOC_RESPONSE, MIXTURE, RECOVERY, DRIFT)
- calibration_reference
- exposure_start
- exposure_end
- recovery_phase
- ground_truth_source
"""

import os
import time
import pandas as pd
import numpy as np

RECORDING_COLUMNS = [
    "experiment_id",
    "sensor_board_id",
    "mq2_module_id",
    "mq135_module_id",
    "timestamp",
    "mq2_adc",
    "mq135_adc",
    "temperature",
    "humidity",
    "experiment_condition",
    "calibration_reference",
    "exposure_start",
    "exposure_end",
    "recovery_phase",
    "ground_truth_source"
]

class ExperimentTrialRecorder:
    def __init__(self, experiment_id: str, sensor_board_id: str = "ESP32_DEV_A"):
        self.experiment_id = experiment_id
        self.sensor_board_id = sensor_board_id
        self.records = []

    def log_reading(
        self,
        mq2_adc: float,
        mq135_adc: float,
        temperature: float,
        humidity: float,
        condition: str,
        calibration_ref: str,
        is_exposure: bool = False,
        is_recovery: bool = False,
        source: str = "CONTROLLED_LAB_TRIAL"
    ):
        self.records.append({
            "experiment_id": self.experiment_id,
            "sensor_board_id": self.sensor_board_id,
            "mq2_module_id": f"{self.sensor_board_id}_MQ2",
            "mq135_module_id": f"{self.sensor_board_id}_MQ135",
            "timestamp": int(time.time() * 1000),
            "mq2_adc": float(mq2_adc),
            "mq135_adc": float(mq135_adc),
            "temperature": float(temperature) if temperature is not None else np.nan,
            "humidity": float(humidity) if humidity is not None else np.nan,
            "experiment_condition": condition,
            "calibration_reference": calibration_ref,
            "exposure_start": is_exposure,
            "exposure_end": not is_exposure and not is_recovery,
            "recovery_phase": is_recovery,
            "ground_truth_source": source
        })

    def save(self, output_dir: str = "ml/collection/trials") -> str:
        os.makedirs(output_dir, exist_ok=True)
        df = pd.DataFrame(self.records, columns=RECORDING_COLUMNS)
        filepath = os.path.join(output_dir, f"{self.experiment_id}.parquet")
        df.to_parquet(filepath, index=False)
        return filepath
