"""
Industrial Hazard Intelligence Engine
Combines:
- Verified ML response pattern (NORMAL_BASELINE, SMOKE, VOC_RESPONSE, MIXTURE)
- Mathematical sensor trends (STABLE, RISING, FALLING)
- Physical baseline deviations
- Configured factory zone context (Z01 to Z08)
Produces structured, standardized industrial incident records.
"""

import os
import yaml
import time
from typing import Dict, Any, List, Optional

class IndustrialHazardEngine:
    def __init__(
        self,
        zones_config_path: str = "ml/config/factory_zones.yaml",
        scenarios_config_path: str = "ml/config/industrial_scenarios.yaml",
        capabilities_config_path: str = "ml/config/sensor_capabilities.yaml"
    ):
        with open(zones_config_path, "r") as f:
            self.zones_cfg = yaml.safe_load(f)["zones"]
        with open(scenarios_config_path, "r") as f:
            self.scenarios_cfg = yaml.safe_load(f)["hazards"]
        with open(capabilities_config_path, "r") as f:
            self.capabilities_cfg = yaml.safe_load(f)

    def evaluate_incident(
        self,
        event_id: str,
        operating_mode: str, # "LIVE" | "SIMULATED" | "HISTORICAL_REPLAY"
        zone_id: str,
        mq2_adc: Optional[float],
        mq135_adc: Optional[float],
        temperature: Optional[float],
        humidity: Optional[float],
        mq2_baseline: float,
        mq135_baseline: float,
        ml_prediction: Optional[str] = None, # "NORMAL_BASELINE" | "SMOKE" | "VOC_RESPONSE" | "MIXTURE"
        ml_confidence: Optional[float] = None,
        mq2_slope: float = 0.0,
        mq135_slope: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Synthesizes raw telemetry, ML classification, and zone context into an actionable industrial incident.
        """
        zone = self.zones_cfg.get(zone_id, self.zones_cfg["Z06"])
        evidence = []

        # 1. Check Sensor Health & Availability
        if mq2_adc is None or mq135_adc is None:
            return {
                "event_id": event_id,
                "timestamp": int(time.time() * 1000),
                "operating_mode": operating_mode,
                "zone_id": zone_id,
                "zone_name": zone["name"],
                "sensor_state": "SENSOR_FAULT",
                "severity": "CRITICAL",
                "trend": "UNKNOWN",
                "pattern": "UNKNOWN",
                "industrial_context": "SENSOR_FAULT_DISCONNECTED",
                "evidence": ["ONE_OR_MORE_REQUIRED_ADC_CHANNELS_MISSING"],
                "gas_identity": "NOT_CONFIRMED",
                "ml_confidence": None,
                "recommended_action": "INSPECT_SENSOR_BUS_WIRING_DO_NOT_ASSUME_CLEAN_AIR",
                "incident_state": "UNVERIFIED",
                "relay_recommendation": "FAIL_SAFE_VENTILATION_ACTIVE"
            }

        # 2. Mathematical Trend Detection
        trend = "STABLE"
        if mq2_slope > 5.0 or mq135_slope > 5.0:
            trend = "RISING"
            evidence.append(f"INFLUX_DETECTED_SLOPE: MQ2={round(mq2_slope,1)}, MQ135={round(mq135_slope,1)}")
        elif mq2_slope < -5.0 or mq135_slope < -5.0:
            trend = "FALLING"
            evidence.append("VENTING_DECAY_OBSERVED")

        # 3. Baseline Deviations
        mq2_dev = mq2_adc - mq2_baseline
        mq135_dev = mq135_adc - mq135_baseline

        if mq2_dev > 100:
            evidence.append(f"MQ2_ELEVATED_ABOVE_BASELINE: +{round(mq2_dev, 1)} ADC")
        if mq135_dev > 100:
            evidence.append(f"MQ135_ELEVATED_ABOVE_BASELINE: +{round(mq135_dev, 1)} ADC")

        # 4. Pattern & Context Synthesis
        severity = "NORMAL"
        context = "ATMOSPHERE_NOMINAL"
        recommended_action = "CONTINUE_ROUTINE_MONITORING"
        relay_action = "OFF"

        pred = ml_prediction or "NORMAL_BASELINE"

        if pred == "SMOKE":
            severity = "CRITICAL"
            context = f"POTENTIAL_SMOKE_OR_COMBUSTION_IN_{zone['name'].upper()}"
            evidence.append("ML_CLASSIFIER_SMOKE_SIGNATURE_CONFIRMED")
            recommended_action = "DISPATCH_SAFETY_OFFICER_VERIFY_FIRE_AND_OVERHEATING"
            relay_action = "FORCE_ON"

        elif pred == "VOC_RESPONSE":
            if zone_id == "Z03": # Painting
                severity = "WARNING"
                context = "SOLVENT_VAPOUR_ACCUMULATION_IN_SPRAY_BOOTH"
            elif zone_id == "Z04": # Chemical storage
                severity = "WARNING"
                context = "ABNORMAL_VOLATILE_CHEMICAL_FUME_CONCENTRATION"
            else:
                severity = "ADVISORY"
                context = f"ELEVATED_VOLATILE_CONTAMINANTS_IN_{zone['name'].upper()}"
            evidence.append("ML_CLASSIFIER_VOC_RESPONSE_PATTERN")
            recommended_action = "INSPECT_LOCAL_EXTRACTION_AND_VERIFY_WITH_CALIBRATED_PID"
            relay_action = "ON" if severity in ["WARNING", "CRITICAL"] else "OFF"

        elif pred == "MIXTURE":
            severity = "WARNING"
            context = f"COMPLEX_MULTI_SPECIES_ATMOSPHERIC_DISTURBANCE_IN_{zone['name'].upper()}"
            evidence.append("ML_CLASSIFIER_MIXTURE_SIGNATURE")
            recommended_action = "VERIFY_PROCESS_AREA_AND_INSPECT_VENTILATION_DAMPER"
            relay_action = "ON"

        else: # NORMAL_BASELINE
            if mq2_dev > 250 or mq135_dev > 250:
                severity = "ADVISORY"
                context = "THRESHOLD_ELEVATION_EXCEEDING_NOMINAL_BASELINE"
                evidence.append("SENSORS_ABOVE_CALIBRATED_RESTING_BAND")
                recommended_action = "OBSERVE_TREND_FOR_PERSISTENT_DRIFT"

        return {
            "event_id": event_id,
            "timestamp": int(time.time() * 1000),
            "operating_mode": operating_mode,
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "sensor_state": "VALID",
            "mq2_adc": mq2_adc,
            "mq135_adc": mq135_adc,
            "temperature": temperature,
            "humidity": humidity,
            "mq2_baseline": mq2_baseline,
            "mq135_baseline": mq135_baseline,
            "pattern": pred,
            "ml_confidence": ml_confidence,
            "severity": severity,
            "trend": trend,
            "industrial_context": context,
            "evidence": evidence,
            "gas_identity": "NOT_CONFIRMED (Broad screening only)",
            "recommended_action": recommended_action,
            "incident_state": "UNVERIFIED" if severity != "NORMAL" else "RESOLVED",
            "relay_command": relay_action,
            "verification_steps": zone.get("operator_verification_steps", []),
            "emergency_procedure": zone.get("emergency_response_procedure", "")
        }
