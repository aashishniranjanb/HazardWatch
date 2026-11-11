"""
Project_A1 — Milestone 5.3.1 Regression & Validation Suite
Tests the 10 Mandatory System Invariants for Baseline-Aware Dashboard and Missing-Sensor Display:
1. Live MQ-2 and missing MQ-135.
2. Both MQ sensors disconnected.
3. DHT11 unavailable (null readings).
4. Previously measured baseline available.
5. No baseline configured (NOT_CALIBRATED status).
6. Demo reference displayed correctly.
7. Reference value never overwrites live value.
8. Missing sensor never becomes zero (must remain null).
9. Hazard state remains UNKNOWN / SENSOR_FAULT when required physical sensors are absent.
10. Actuator / Relay remains disabled (safe-OFF, GPIO26 HIGH).
"""

import unittest
import json
import time
from backend.app.services.baseline_registry import BaselineRegistryService
from backend.app.services.unified_sensor_service import (
    build_unified_sensor_record,
    get_all_unified_sensors,
    LAST_KNOWN_CACHE
)
from backend.app.services.industrial_hazard_engine import IndustrialHazardEngine

class TestM531BaselineDisplay(unittest.TestCase):
    def setUp(self):
        # Reset cache
        for k in LAST_KNOWN_CACHE:
            LAST_KNOWN_CACHE[k] = {"value": None, "timestamp": None}
        self.hazard_engine = IndustrialHazardEngine()
        self.registry = BaselineRegistryService()

    def test_01_live_mq2_and_missing_mq135(self):
        """1. Live MQ-2 produces LIVE state; missing MQ-135 produces FAULT state."""
        live_frame = {
            "device_id": "PROJECT_A1_ESP32_01",
            "sensors": {
                "mq2_adc": 245.0,
                "mq135_adc": None,
                "temperature_c": None,
                "humidity_percent": None
            },
            "monitoring_state": "SENSOR_FAULT",
            "hazard_state": "SENSOR_FAULT"
        }
        baselines = self.registry.get_all_baselines()
        unified = get_all_unified_sensors(live_frame, baselines)

        # MQ-2 must be LIVE with exact value
        self.assertEqual(unified["mq2"]["availability"], "LIVE")
        self.assertEqual(unified["mq2"]["live_value"], 245.0)
        self.assertEqual(unified["mq2"]["gpio_pin"], 34)

        # MQ-135 must be FAULT, live_value must remain null
        self.assertEqual(unified["mq135"]["availability"], "FAULT")
        self.assertIsNone(unified["mq135"]["live_value"])
        self.assertEqual(unified["mq135"]["gpio_pin"], 35)

    def test_02_both_mq_sensors_disconnected(self):
        """2. When both MQ sensors are disconnected, both have availability FAULT and null live_value."""
        live_frame = {
            "device_id": "PROJECT_A1_ESP32_01",
            "sensors": {
                "mq2_adc": None,
                "mq135_adc": None,
                "temperature_c": None,
                "humidity_percent": None
            },
            "monitoring_state": "SENSOR_FAULT",
            "hazard_state": "SENSOR_FAULT"
        }
        baselines = self.registry.get_all_baselines()
        unified = get_all_unified_sensors(live_frame, baselines)

        self.assertEqual(unified["mq2"]["availability"], "FAULT")
        self.assertIsNone(unified["mq2"]["live_value"])
        self.assertEqual(unified["mq135"]["availability"], "FAULT")
        self.assertIsNone(unified["mq135"]["live_value"])

    def test_03_dht11_unavailable(self):
        """3. DHT11 unavailable produces null temperature and humidity, availability FAULT."""
        live_frame = {
            "device_id": "PROJECT_A1_ESP32_01",
            "sensors": {
                "mq2_adc": 250.0,
                "mq135_adc": None,
                "temperature_c": None,
                "humidity_percent": None
            },
            "monitoring_state": "SENSOR_FAULT",
            "hazard_state": "SENSOR_FAULT"
        }
        baselines = self.registry.get_all_baselines()
        unified = get_all_unified_sensors(live_frame, baselines)

        self.assertIsNone(unified["temperature"]["live_value"])
        self.assertEqual(unified["temperature"]["availability"], "FAULT")
        self.assertEqual(unified["temperature"]["unit"], "°C")

        self.assertIsNone(unified["humidity"]["live_value"])
        self.assertEqual(unified["humidity"]["availability"], "FAULT")
        self.assertEqual(unified["humidity"]["unit"], "%RH")

    def test_04_previously_measured_baseline_available(self):
        """4. Stored calibration baseline is loaded and accessible."""
        base_mq2 = self.registry.get_baseline("mq2")
        self.assertIsNotNone(base_mq2)
        self.assertEqual(base_mq2["baseline_value"], 338.0)
        self.assertEqual(base_mq2["calibration_status"], "CALIBRATED_BENCHMARK")

    def test_05_no_baseline_configured_not_calibrated(self):
        """5. Uncalibrated sensor preserves NOT_CALIBRATED status and cannot be used as valid measured input."""
        base_mq135 = self.registry.get_baseline("mq135")
        self.assertEqual(base_mq135["calibration_status"], "NOT_CALIBRATED")
        self.assertFalse(self.registry.is_calibrated("mq135"))

    def test_06_demo_reference_displayed_correctly(self):
        """6. Configured reference values are preserved with reference_source metadata."""
        baselines = self.registry.get_all_baselines()
        self.assertEqual(baselines["temperature"]["baseline_value"], 25.0)
        self.assertEqual(baselines["temperature"]["reference_source"], "Standard Industrial Ambient")
        self.assertEqual(baselines["humidity"]["baseline_value"], 50.0)
        self.assertEqual(baselines["humidity"]["reference_source"], "Standard Industrial Ambient")

    def test_07_reference_value_never_overwrites_live_value(self):
        """7. Reference value must never populate the live_value field."""
        live_frame = {
            "device_id": "PROJECT_A1_ESP32_01",
            "sensors": {
                "mq2_adc": 260.0,
                "mq135_adc": None,
                "temperature_c": None,
                "humidity_percent": None
            },
            "monitoring_state": "SENSOR_FAULT"
        }
        baselines = self.registry.get_all_baselines()
        unified = get_all_unified_sensors(live_frame, baselines)

        # Reference is 1523.0, but live_value must be None (never 1523.0)
        self.assertEqual(unified["mq135"]["reference_value"], 1523.0)
        self.assertIsNone(unified["mq135"]["live_value"])

    def test_08_missing_sensor_never_becomes_zero(self):
        """8. Missing physical sensors must remain null, NEVER 0."""
        live_frame = {
            "device_id": "PROJECT_A1_ESP32_01",
            "sensors": {
                "mq2_adc": 255.0,
                "mq135_adc": None,
                "temperature_c": None,
                "humidity_percent": None
            }
        }
        baselines = self.registry.get_all_baselines()
        unified = get_all_unified_sensors(live_frame, baselines)

        self.assertNotEqual(unified["mq135"]["live_value"], 0)
        self.assertIsNone(unified["mq135"]["live_value"])
        self.assertNotEqual(unified["temperature"]["live_value"], 0)
        self.assertIsNone(unified["temperature"]["live_value"])
        self.assertNotEqual(unified["humidity"]["live_value"], 0)
        self.assertIsNone(unified["humidity"]["live_value"])

    def test_09_hazard_state_remains_sensor_fault_unknown(self):
        """9. When required physical sensors are missing/faulted, hazard state remains SENSOR_FAULT / UNKNOWN."""
        incident = self.hazard_engine.evaluate_incident(
            event_id="EVT-TEST-001",
            operating_mode="LIVE_HARDWARE",
            zone_id="Z03",
            mq2_adc=260.0,
            mq135_adc=None,
            temperature=None,
            humidity=None,
            mq2_baseline=338.0,
            mq135_baseline=1523.0,
            ml_prediction="UNKNOWN",
            ml_confidence=0.0
        )
        self.assertEqual(incident["pattern"], "UNKNOWN")
        self.assertEqual(incident["sensor_state"], "SENSOR_FAULT")
        self.assertEqual(incident["industrial_context"], "SENSOR_FAULT_DISCONNECTED")

    def test_10_relay_remains_disabled_safe_off(self):
        """10. CRITICAL SAFETY INTERLOCK: Actuator/relay remains disabled when sensor fault is detected."""
        # Test simulated/evaluated incident fault safety
        from backend.main import app, process_telemetry, TelemetryPayload
        import asyncio

        payload = TelemetryPayload(
            operating_mode="LIVE_HARDWARE",
            provenance="PHYSICAL_ESP32",
            zone_id="Z03",
            mq2_adc=250.0,
            mq135_adc=None,
            fault=True
        )
        loop = asyncio.new_event_loop()
        incident = loop.run_until_complete(process_telemetry(payload))
        loop.close()

        self.assertFalse(incident["relay_command"])
        self.assertEqual(incident["gas_hazard_state"], "UNKNOWN")

if __name__ == "__main__":
    unittest.main()
