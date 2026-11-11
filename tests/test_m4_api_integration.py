"""
Integration Tests for FastAPI Backend (v4.0.0):
- Tri-mode operation (LIVE_HARDWARE, HISTORICAL_REPLAY, SYNTHETIC_SIMULATION)
- Server ML XGBoost inference & OOD detection
- Serial port scanner & acquisition protocol
- Historical replay step & loading
- Factory zone & scenario endpoints
- Safety interlock: Sensor fault decouples relay activation
"""

import sys
import os
from fastapi.testclient import TestClient

# Add project root and backend to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = BACKEND_DIR
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import main
from main import app

client = TestClient(app)

def test_system_status():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "LIVE_HARDWARE" in data["supported_modes"]
    assert "HISTORICAL_REPLAY" in data["supported_modes"]
    assert "SYNTHETIC_SIMULATION" in data["supported_modes"]

def test_list_zones_and_scenarios():
    res_z = client.get("/api/v1/factory/zones")
    assert res_z.status_code == 200
    assert "Z01" in res_z.json()

    res_s = client.get("/api/v1/industrial/scenarios")
    assert res_s.status_code == 200
    assert "H01" in res_s.json()

def test_serial_port_scanner():
    res = client.get("/api/v1/serial/ports")
    assert res.status_code == 200
    data = res.json()
    assert "ports" in data
    assert isinstance(data["ports"], list)

def test_replay_lifecycle():
    # 1. List datasets
    res = client.get("/api/v1/replay/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 3

    # 2. Load dataset
    res_load = client.post("/api/v1/replay/load/multi_sensor_data")
    assert res_load.status_code == 200
    assert res_load.json()["status"] == "LOADED"

    # 3. Step dataset
    res_step = client.get("/api/v1/replay/step?index=0")
    assert res_step.status_code == 200
    sample = res_step.json()
    assert sample["provenance"] == "VERIFIED_RESEARCH_DATASET"
    assert "multi_model_inference" in sample or "server_inference" in sample

def test_telemetry_normal_baseline():
    payload = {
        "device": "ESP32_GAS_MONITOR",
        "zone_id": "Z03",
        "operating_mode": "HISTORICAL_REPLAY",
        "provenance": "VERIFIED_RESEARCH_DATASET",
        "mq2_adc": 340.0,
        "mq135_adc": 1520.0,
        "temperature": 25.1,
        "humidity": 53.5,
        "mq2_baseline": 338.0,
        "mq135_baseline": 1523.0,
        "edge_prediction": "NORMAL_BASELINE",
        "edge_confidence": 0.99,
        "fault": False
    }
    res = client.post("/api/v1/telemetry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["severity"] == "NORMAL"
    assert data["relay_command"] is False
    assert data["server_prediction"] == "NORMAL_BASELINE"

def test_safety_interlock_on_sensor_fault():
    """CRITICAL SAFETY TEST: Sensor fault must NOT activate ventilation relay."""
    payload = {
        "device": "ESP32_GAS_MONITOR",
        "zone_id": "Z03",
        "operating_mode": "LIVE_HARDWARE",
        "provenance": "PHYSICAL_ESP32",
        "mq2_adc": None,
        "mq135_adc": None,
        "temperature": None,
        "humidity": None,
        "edge_prediction": "UNKNOWN",
        "fault": True  # Disconnected or shorted pins
    }
    res = client.post("/api/v1/telemetry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["fault_detected"] is True
    assert data["relay_command"] is False  # Must remain false to prevent ignition
    assert data["severity"] == "WARNING"

if __name__ == "__main__":
    test_system_status()
    test_list_zones_and_scenarios()
    test_serial_port_scanner()
    test_replay_lifecycle()
    test_telemetry_normal_baseline()
    test_safety_interlock_on_sensor_fault()
    print("ALL M4 API INTEGRATION TESTS PASSED SUCCESSFULLY!")
