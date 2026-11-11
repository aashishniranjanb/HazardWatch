"""
Baseline & Reference Registry Service (M5.3.1):
Persistent registry for sensor baselines and reference profiles.
Supported Baseline Types:
- MEASURED_CALIBRATION: Genuine physical clean-air calibration session on hardware.
- CONFIGURED_REFERENCE: Factory engineering default from dataset/lab benchmark.
- DEMO_REFERENCE: Simulated or test demonstration reference.

CRITICAL CONSTRAINTS:
- Only MEASURED_CALIBRATION may be used for actual baseline-relative signal processing.
- CONFIGURED_REFERENCE and DEMO_REFERENCE must never be treated as physical sensor inputs.
- Uncalibrated channels preserve NOT_CALIBRATED calibration_status.
- Missing live values must remain null.
"""

import os
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(PROJECT_ROOT, "backend", "industrial_scada.db")

class BaselineRegistryService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_registry()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_registry(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_baselines (
                    sensor_id TEXT PRIMARY KEY,
                    sensor_name TEXT NOT NULL,
                    gpio_pin INTEGER NOT NULL,
                    baseline_value REAL,
                    baseline_type TEXT NOT NULL,
                    calibration_status TEXT NOT NULL,
                    reference_source TEXT NOT NULL,
                    reference_timestamp INTEGER NOT NULL,
                    device_id TEXT NOT NULL,
                    conditions_json TEXT,
                    unit TEXT NOT NULL
                )
            """)
            conn.commit()
            
            # Seed default configured references if empty
            cursor.execute("SELECT COUNT(*) FROM sensor_baselines")
            if cursor.fetchone()[0] == 0:
                now = int(time.time() * 1000)
                defaults = [
                    (
                        "mq2", "MQ-2 Combustible/Smoke", 34, 338.0,
                        "CONFIGURED_REFERENCE", "CALIBRATED_BENCHMARK",
                        "M2.7 Factory Benchmark", now, "PROJECT_A1_ESP32_01",
                        json.dumps({"ambient_temp_c": 25.0, "ambient_hum_pct": 50.0}), "ADC"
                    ),
                    (
                        "mq135", "MQ-135 Hazardous/Air Quality", 35, 1523.0,
                        "CONFIGURED_REFERENCE", "NOT_CALIBRATED",
                        "M2.7 Factory Benchmark", now, "PROJECT_A1_ESP32_01",
                        json.dumps({"ambient_temp_c": 25.0, "ambient_hum_pct": 50.0}), "ADC"
                    ),
                    (
                        "temperature", "DHT11 Ambient Temperature", 4, 25.0,
                        "CONFIGURED_REFERENCE", "FACTORY_NOMINAL",
                        "Standard Industrial Ambient", now, "PROJECT_A1_ESP32_01",
                        json.dumps({"zone": "General Manufacturing"}), "°C"
                    ),
                    (
                        "humidity", "DHT11 Relative Humidity", 4, 50.0,
                        "CONFIGURED_REFERENCE", "FACTORY_NOMINAL",
                        "Standard Industrial Ambient", now, "PROJECT_A1_ESP32_01",
                        json.dumps({"zone": "General Manufacturing"}), "%RH"
                    )
                ]
                cursor.executemany("""
                    INSERT INTO sensor_baselines (
                        sensor_id, sensor_name, gpio_pin, baseline_value, baseline_type,
                        calibration_status, reference_source, reference_timestamp, device_id,
                        conditions_json, unit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, defaults)
                conn.commit()

    def get_baseline(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sensor_baselines WHERE sensor_id = ?", (sensor_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("conditions_json"):
                    try:
                        d["conditions"] = json.loads(d["conditions_json"])
                    except Exception:
                        d["conditions"] = {}
                return d
            return None

    def get_all_baselines(self) -> Dict[str, Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sensor_baselines")
            result = {}
            for row in cursor.fetchall():
                d = dict(row)
                if d.get("conditions_json"):
                    try:
                        d["conditions"] = json.loads(d["conditions_json"])
                    except Exception:
                        d["conditions"] = {}
                result[d["sensor_id"]] = d
            return result

    def is_calibrated(self, sensor_id: str) -> bool:
        b = self.get_baseline(sensor_id)
        if not b:
            return False
        return b.get("calibration_status") in {"MEASURED_CALIBRATION", "CALIBRATED_BENCHMARK"}

    def register_or_update_baseline(
        self,
        sensor_id: str,
        sensor_name: str,
        gpio_pin: int,
        baseline_value: Optional[float],
        baseline_type: str,
        calibration_status: str,
        reference_source: str,
        device_id: str = "PROJECT_A1_ESP32_01",
        conditions: Optional[Dict[str, Any]] = None,
        unit: str = "ADC"
    ) -> Dict[str, Any]:
        valid_types = {"MEASURED_CALIBRATION", "CONFIGURED_REFERENCE", "DEMO_REFERENCE"}
        if baseline_type not in valid_types:
            raise ValueError(f"Invalid baseline_type '{baseline_type}'. Must be one of {valid_types}")

        now = int(time.time() * 1000)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_baselines (
                    sensor_id, sensor_name, gpio_pin, baseline_value, baseline_type,
                    calibration_status, reference_source, reference_timestamp, device_id,
                    conditions_json, unit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sensor_id) DO UPDATE SET
                    baseline_value=excluded.baseline_value,
                    baseline_type=excluded.baseline_type,
                    calibration_status=excluded.calibration_status,
                    reference_source=excluded.reference_source,
                    reference_timestamp=excluded.reference_timestamp,
                    device_id=excluded.device_id,
                    conditions_json=excluded.conditions_json,
                    unit=excluded.unit
            """, (
                sensor_id, sensor_name, gpio_pin, baseline_value, baseline_type,
                calibration_status, reference_source, now, device_id,
                json.dumps(conditions or {}), unit
            ))
            conn.commit()
        return self.get_baseline(sensor_id)
