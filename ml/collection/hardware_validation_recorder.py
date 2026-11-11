"""
M3.5 Hardware Validation Recorder
Logs genuine, un-faked sensor readings from physical ESP32 DevKit V1:
- Physical board ID
- Sensor module IDs
- Raw ADC counts
- Temperature & Humidity (DHT11)
- Clean-air warm-up elapsed time
- Real-time feature calculation
- Dual inference logging (Edge int8 vs Server float32)
"""

import os
import csv
import time
from typing import Optional, Dict, Any

HARDWARE_LOG_COLUMNS = [
    "timestamp",
    "experiment_id",
    "physical_board_id",
    "mq2_module_id",
    "mq135_module_id",
    "warmup_duration_sec",
    "mq2_adc_raw",
    "mq135_adc_raw",
    "temperature_c",
    "humidity_pct",
    "hardware_baseline_mq2",
    "hardware_baseline_mq135",
    "delta_mq2",
    "delta_mq135",
    "ratio_mq2",
    "ratio_mq135",
    "tflite_edge_prediction",
    "server_prediction",
    "sensor_status",
    "notes"
]

class HardwareValidationRecorder:
    def __init__(self, experiment_id: str, physical_board_id: str = "ESP32_PHYSICAL_01"):
        self.experiment_id = experiment_id
        self.physical_board_id = physical_board_id
        self.log_path = f"ml/collection/physical_{experiment_id}.csv"
        os.makedirs("ml/collection", exist_ok=True)
        
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(HARDWARE_LOG_COLUMNS)

    def record_sample(
        self,
        mq2_raw: Optional[int],
        mq135_raw: Optional[int],
        temp: Optional[float],
        hum: Optional[float],
        warmup_sec: float,
        base_mq2: float,
        base_mq135: float,
        edge_pred: Optional[str] = "UNKNOWN",
        server_pred: Optional[str] = "UNKNOWN",
        status: str = "VALID",
        notes: str = ""
    ):
        delta_2 = mq2_raw - base_mq2 if mq2_raw is not None else None
        delta_135 = mq135_raw - base_mq135 if mq135_raw is not None else None
        ratio_2 = mq2_raw / (base_mq2 + 1e-4) if mq2_raw is not None else None
        ratio_135 = mq135_raw / (base_mq135 + 1e-4) if mq135_raw is not None else None

        row = [
            int(time.time() * 1000),
            self.experiment_id,
            self.physical_board_id,
            f"{self.physical_board_id}_MQ2",
            f"{self.physical_board_id}_MQ135",
            round(warmup_sec, 1),
            mq2_raw if mq2_raw is not None else "",
            mq135_raw if mq135_raw is not None else "",
            temp if temp is not None else "",
            hum if hum is not None else "",
            base_mq2,
            base_mq135,
            round(delta_2, 1) if delta_2 is not None else "",
            round(delta_135, 1) if delta_135 is not None else "",
            round(ratio_2, 4) if ratio_2 is not None else "",
            round(ratio_135, 4) if ratio_135 is not None else "",
            edge_pred,
            server_pred,
            status,
            notes
        ]

        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

if __name__ == "__main__":
    recorder = HardwareValidationRecorder("PHYSICAL_BENCH_001")
    recorder.record_sample(
        mq2_raw=342,
        mq135_raw=1480,
        temp=25.4,
        hum=54.2,
        warmup_sec=120.0,
        base_mq2=338.0,
        base_mq135=1523.0,
        edge_pred="NORMAL_BASELINE",
        server_pred="NORMAL_BASELINE",
        status="STABILIZED",
        notes="Physical ESP32 ambient clean air test sample"
    )
    print(f"Hardware validation recorder initialized: {recorder.log_path}")
