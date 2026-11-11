"""
Historical CSV Replay Service for Factory Gas Monitoring:
- Loads research datasets with full provenance tagging
- Standardizes columns to internal telemetry schema
- Supports step-by-step or timed replay streaming
- Preserves original sensor values and sampling intervals
"""

import os
import glob
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DATASET_CONFIGS = {
    "multi_sensor_data": {
        "file": "multi_sensor_data.csv",
        "name": "Multi-Sensor Combustion & VOC Rig",
        "provenance": "VERIFIED_RESEARCH_DATASET",
        "mq2_col": "mq2_adc",
        "mq135_col": "mq135_adc",
        "temp_col": None,
        "hum_col": None,
        "label_col": "label",
        "sample_interval_ms": 500
    },
    "multi_sensor_data_baseline": {
        "file": "multi_sensor_data_baseline.csv",
        "name": "Multi-Sensor Clean Air Continuous Baseline",
        "provenance": "VERIFIED_RESEARCH_DATASET",
        "mq2_col": "mq2_adc",
        "mq135_col": "mq135_adc",
        "temp_col": None,
        "hum_col": None,
        "label_col": None,
        "sample_interval_ms": 500
    },
    "gas_sensors_measurements": {
        "file": "Gas_Sensors_Measurements.csv",
        "name": "6,400-Sample MOS Research Bench",
        "provenance": "VERIFIED_RESEARCH_DATASET",
        "mq2_col": "MQ2",
        "mq135_col": "MQ135",
        "temp_col": None,
        "hum_col": None,
        "label_col": "Gas",
        "sample_interval_ms": 1000
    }
}

class HistoricalReplayService:
    def __init__(self):
        self.active_dataset_id: Optional[str] = None
        self.df: Optional[pd.DataFrame] = None
        self.current_index = 0

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        result = []
        for d_id, cfg in DATASET_CONFIGS.items():
            path = os.path.join(PROJECT_ROOT, cfg["file"])
            exists = os.path.exists(path)
            row_count = 0
            if exists:
                try:
                    row_count = sum(1 for _ in open(path, "r", encoding="utf-8", errors="ignore")) - 1
                except Exception:
                    pass
            result.append({
                "dataset_id": d_id,
                "name": cfg["name"],
                "file": cfg["file"],
                "provenance": cfg["provenance"],
                "exists": exists,
                "row_count": row_count,
                "sample_interval_ms": cfg["sample_interval_ms"]
            })
        return result

    def load_dataset(self, dataset_id: str) -> bool:
        if dataset_id not in DATASET_CONFIGS:
            return False
        cfg = DATASET_CONFIGS[dataset_id]
        path = os.path.join(PROJECT_ROOT, cfg["file"])
        if not os.path.exists(path):
            return False
        
        self.df = pd.read_csv(path)
        self.active_dataset_id = dataset_id
        self.current_index = 0
        return True

    def get_sample(self, index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if self.df is None or self.active_dataset_id is None:
            return None
        
        if index is not None:
            self.current_index = index % len(self.df)
        
        row = self.df.iloc[self.current_index]
        cfg = DATASET_CONFIGS[self.active_dataset_id]
        
        mq2 = float(row[cfg["mq2_col"]]) if cfg["mq2_col"] and cfg["mq2_col"] in row and pd.notnull(row[cfg["mq2_col"]]) else None
        mq135 = float(row[cfg["mq135_col"]]) if cfg["mq135_col"] and cfg["mq135_col"] in row and pd.notnull(row[cfg["mq135_col"]]) else None
        label = str(row[cfg["label_col"]]) if cfg["label_col"] and cfg["label_col"] in row and pd.notnull(row[cfg["label_col"]]) else "NORMAL_BASELINE"
        
        # Advance index
        idx_ret = self.current_index
        self.current_index = (self.current_index + 1) % len(self.df)

        return {
            "index": idx_ret,
            "total_rows": len(self.df),
            "dataset_id": self.active_dataset_id,
            "provenance": cfg["provenance"],
            "mq2_adc": mq2,
            "mq135_adc": mq135,
            "temperature": 25.0,  # Ambient default for research datasets lacking DHT
            "humidity": 50.0,
            "original_label": label,
            "operating_mode": "HISTORICAL_REPLAY"
        }
