import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app.services.industrial_hazard_engine import IndustrialHazardEngine
from app.services.incident_manager import IncidentManager

class TestIndustrialHazardEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IndustrialHazardEngine()
        self.mgr = IncidentManager()

    def test_zone_definitions_loaded(self):
        self.assertEqual(len(self.engine.zones_cfg), 8)
        self.assertIn("Z01", self.engine.zones_cfg)
        self.assertIn("Z03", self.engine.zones_cfg)
        self.assertIn("Z07", self.engine.zones_cfg)

    def test_sensor_fault_evaluation(self):
        # Missing readings should trigger SENSOR_FAULT, never clean air!
        incident = self.engine.evaluate_incident(
            event_id="EVT-TEST-001",
            operating_mode="LIVE",
            zone_id="Z01",
            mq2_adc=None,
            mq135_adc=None,
            temperature=None,
            humidity=None,
            mq2_baseline=338.0,
            mq135_baseline=1523.0
        )
        self.assertEqual(incident["sensor_state"], "SENSOR_FAULT")
        self.assertEqual(incident["severity"], "CRITICAL")
        self.assertIn("ONE_OR_MORE_REQUIRED_ADC_CHANNELS_MISSING", incident["evidence"])

    def test_smoke_response_contextual_synthesis(self):
        incident = self.engine.evaluate_incident(
            event_id="EVT-TEST-002",
            operating_mode="LIVE",
            zone_id="Z05", # Electrical switchgear
            mq2_adc=1400.0,
            mq135_adc=450.0,
            temperature=32.0,
            humidity=45.0,
            mq2_baseline=338.0,
            mq135_baseline=1523.0,
            ml_prediction="SMOKE",
            ml_confidence=0.99,
            mq2_slope=15.0
        )
        self.assertEqual(incident["severity"], "CRITICAL")
        self.assertEqual(incident["pattern"], "SMOKE")
        self.assertIn("ELECTRICAL", incident["industrial_context"].upper())
        self.assertEqual(incident["relay_command"], "FORCE_ON")

    def test_voc_response_in_painting_booth(self):
        incident = self.engine.evaluate_incident(
            event_id="EVT-TEST-003",
            operating_mode="LIVE",
            zone_id="Z03", # Painting & Coating
            mq2_adc=350.0,
            mq135_adc=1850.0,
            temperature=28.0,
            humidity=55.0,
            mq2_baseline=338.0,
            mq135_baseline=1523.0,
            ml_prediction="VOC_RESPONSE",
            ml_confidence=0.92,
            mq135_slope=8.0
        )
        self.assertEqual(incident["severity"], "WARNING")
        self.assertEqual(incident["pattern"], "VOC_RESPONSE")
        self.assertIn("SOLVENT_VAPOUR", incident["industrial_context"])

    def test_incident_manager_lifecycle(self):
        inc = {
            "event_id": "EVT-TEST-004",
            "zone_id": "Z03",
            "severity": "WARNING",
            "industrial_context": "SOLVENT_VAPOUR_ACCUMULATION"
        }
        created = self.mgr.create_incident(inc)
        self.assertIn("INC-", created["id"])
        self.assertFalse(created["acknowledged"])
        
        # Acknowledge
        self.assertTrue(self.mgr.acknowledge_incident(created["id"], "Lead_Operator"))
        self.assertTrue(created["acknowledged"])
        
        # Resolve
        self.assertTrue(self.mgr.resolve_incident(created["id"], "Ventilation restored"))
        self.assertTrue(created["resolved"])

if __name__ == '__main__':
    unittest.main()
