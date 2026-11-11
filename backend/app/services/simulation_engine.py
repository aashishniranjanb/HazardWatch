"""
Deterministic Factory Simulation Engine (M4.3):
Generates 10 reproducible industrial atmospheric response scenarios:
1. NORMAL_PRODUCTION -> Steady baseline readings
2. COMBUSTIBLE_RESPONSE_PATTERN -> High MQ-2 response, low MQ-135
3. VOC_RESPONSE -> High MQ-135 response, moderate MQ-2
4. SMOKE_RESPONSE -> High MQ-2 and high MQ-135, rapid rate of change
5. MIXTURE -> Simultaneous volatile solvent & combustion traces
6. SENSOR_DRIFT_WARNING -> Slow monotonic baseline elevation over time
7. SENSOR_FAULT -> Disconnected pin (0 or null counts)
8. VENTILATION_FEEDBACK_UNAVAILABLE -> Relay command requested but actual feedback false
9. OFFLINE_MODE -> Network disconnection simulation
10. UNKNOWN_OOD -> Extreme out-of-distribution voltage spike

Every generated record is strictly stamped:
- mode = "SYNTHETIC_SIMULATION"
- provenance = "SYNTHETIC_GENERATED"
"""

import os
import time
import math
import random
import numpy as np
from typing import Dict, Any, List, Optional

class SimulationEngine:
    SCENARIOS = {
        "NORMAL_PRODUCTION": {
            "name": "Normal Factory Production",
            "zone": "Z01",
            "description": "Controlled clean atmospheric air with normal ambient fluctuations",
            "duration_sec": 60,
            "expected_state": "NORMAL_BASELINE"
        },
        "COMBUSTIBLE_RESPONSE_PATTERN": {
            "name": "Combustible Fuel Gas Surge",
            "zone": "Z04",
            "description": "Fuel gas supply line flare pattern (MQ-2 surge, MQ-135 moderate)",
            "duration_sec": 60,
            "expected_state": "COMBUSTIBLE_RESPONSE_PATTERN"
        },
        "VOC_RESPONSE": {
            "name": "Volatile Solvent Evaporation",
            "zone": "Z02",
            "description": "Chemical solvent vapor response (MQ-135 surge, MQ-2 low-to-moderate)",
            "duration_sec": 60,
            "expected_state": "VOC_RESPONSE"
        },
        "SMOKE_RESPONSE": {
            "name": "Electrical Overheating Smolder",
            "zone": "Z03",
            "description": "Conduit cable overheating with rapid smoke particle release",
            "duration_sec": 60,
            "expected_state": "SMOKE_RESPONSE"
        },
        "MIXTURE": {
            "name": "Co-located Solvent & Smoke Mixture",
            "zone": "Z05",
            "description": "Combined chemical handling evaporation and exhaust vapor",
            "duration_sec": 60,
            "expected_state": "MIXTURE"
        },
        "SENSOR_DRIFT_WARNING": {
            "name": "Gradual Environmental Thermal Drift",
            "zone": "Z07",
            "description": "Gradual sensor baseline climb due to ambient heat/humidity accumulation",
            "duration_sec": 60,
            "expected_state": "SENSOR_DRIFT_WARNING"
        },
        "SENSOR_FAULT": {
            "name": "Physical Sensor Wiring Fault",
            "zone": "Z01",
            "description": "Disconnected analog wire causing floating pin or ground rail short",
            "duration_sec": 30,
            "expected_state": "SENSOR_FAULT"
        },
        "VENTILATION_FEEDBACK_UNAVAILABLE": {
            "name": "Ventilation Contactor Feedback Failure",
            "zone": "Z03",
            "description": "Relay commanded active but electrical pump feedback contactor remains open",
            "duration_sec": 45,
            "expected_state": "VENTILATION_FEEDBACK_UNAVAILABLE"
        },
        "OFFLINE_MODE": {
            "name": "Edge Gateway Communication Dropout",
            "zone": "Z06",
            "description": "Loss of network link between factory floor edge gateway and cloud server",
            "duration_sec": 30,
            "expected_state": "OFFLINE_MODE"
        },
        "UNKNOWN_OOD": {
            "name": "Extreme Out-of-Distribution Voltage Influx",
            "zone": "Z08",
            "description": "Atmospheric interference or non-model chemical outside calibration space",
            "duration_sec": 45,
            "expected_state": "UNKNOWN_OOD"
        }
    }

    def __init__(self):
        self.active_scenario_id: Optional[str] = None
        self.seed: int = 42
        self.speed: float = 1.0
        self.is_running: bool = False
        self.start_timestamp: Optional[float] = None
        self.elapsed_sec: float = 0.0
        self.sample_index: int = 0

    def start_simulation(self, scenario_id: str, seed: int = 42, speed: float = 1.0) -> Dict[str, Any]:
        if scenario_id not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")
        self.active_scenario_id = scenario_id
        self.seed = seed
        self.speed = max(0.1, min(10.0, speed))
        self.is_running = True
        self.start_timestamp = time.time()
        self.elapsed_sec = 0.0
        self.sample_index = 0
        random.seed(seed)
        np.random.seed(seed)
        return self.get_status()

    def stop_simulation(self) -> Dict[str, Any]:
        self.is_running = False
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        scenario = self.SCENARIOS.get(self.active_scenario_id) if self.active_scenario_id else None
        return {
            "is_running": self.is_running,
            "scenario_id": self.active_scenario_id,
            "scenario_name": scenario["name"] if scenario else None,
            "zone_id": scenario["zone"] if scenario else None,
            "speed": self.speed,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "samples_generated": self.sample_index,
            "expected_state": scenario["expected_state"] if scenario else None
        }

    def step(self, dt: float = 0.5) -> Dict[str, Any]:
        """Generates a deterministic synthetic sample according to scenario timeline."""
        if not self.is_running or not self.active_scenario_id:
            # Return baseline idle
            return self._generate_normal_sample(0.0)

        self.elapsed_sec += dt * self.speed
        self.sample_index += 1
        t = self.elapsed_sec

        sc = self.active_scenario_id
        if sc == "NORMAL_PRODUCTION":
            return self._generate_normal_sample(t)
        elif sc == "COMBUSTIBLE_RESPONSE_PATTERN":
            return self._generate_combustible_sample(t)
        elif sc == "VOC_RESPONSE":
            return self._generate_voc_sample(t)
        elif sc == "SMOKE_RESPONSE":
            return self._generate_smoke_sample(t)
        elif sc == "MIXTURE":
            return self._generate_mixture_sample(t)
        elif sc == "SENSOR_DRIFT_WARNING":
            return self._generate_drift_sample(t)
        elif sc == "SENSOR_FAULT":
            return self._generate_fault_sample(t)
        elif sc == "VENTILATION_FEEDBACK_UNAVAILABLE":
            return self._generate_vent_fail_sample(t)
        elif sc == "OFFLINE_MODE":
            return self._generate_offline_sample(t)
        elif sc == "UNKNOWN_OOD":
            return self._generate_ood_sample(t)
        else:
            return self._generate_normal_sample(t)

    def _generate_normal_sample(self, t: float) -> Dict[str, Any]:
        mq2 = 338.0 + 3.0 * math.sin(2 * math.pi * t / 20.0) + random.gauss(0, 1.5)
        mq135 = 1523.0 + 6.0 * math.sin(2 * math.pi * t / 25.0) + random.gauss(0, 3.0)
        return self._format_record(mq2, mq135, temp=24.5, hum=52.0, state="NORMAL_BASELINE")

    def _generate_combustible_sample(self, t: float) -> Dict[str, Any]:
        # Fuel surge profile: reaches peak at t=20s
        surge = 450.0 / (1.0 + math.exp(-(t - 15.0) / 3.0))
        mq2 = 338.0 + surge + random.gauss(0, 4.0)
        mq135 = 1523.0 + (surge * 0.15) + random.gauss(0, 3.0)
        state = "COMBUSTIBLE_RESPONSE_PATTERN" if t > 12.0 else "NORMAL_BASELINE"
        return self._format_record(mq2, mq135, temp=25.8, hum=51.0, state=state)

    def _generate_voc_sample(self, t: float) -> Dict[str, Any]:
        # VOC evaporation: MQ-135 climbs sharply
        surge = 650.0 / (1.0 + math.exp(-(t - 15.0) / 4.0))
        mq2 = 338.0 + (surge * 0.1) + random.gauss(0, 2.0)
        mq135 = 1523.0 + surge + random.gauss(0, 5.0)
        state = "VOC_RESPONSE" if t > 12.0 else "NORMAL_BASELINE"
        return self._format_record(mq2, mq135, temp=26.2, hum=54.0, state=state)

    def _generate_smoke_sample(self, t: float) -> Dict[str, Any]:
        # Rapid smoke influx
        surge_mq2 = 800.0 / (1.0 + math.exp(-(t - 10.0) / 2.5))
        surge_mq135 = 550.0 / (1.0 + math.exp(-(t - 10.0) / 2.5))
        mq2 = 338.0 + surge_mq2 + random.gauss(0, 8.0)
        mq135 = 1523.0 + surge_mq135 + random.gauss(0, 7.0)
        state = "SMOKE_RESPONSE" if t > 8.0 else "NORMAL_BASELINE"
        return self._format_record(mq2, mq135, temp=27.5, hum=49.0, state=state)

    def _generate_mixture_sample(self, t: float) -> Dict[str, Any]:
        surge_mq2 = 600.0 / (1.0 + math.exp(-(t - 12.0) / 3.0))
        surge_mq135 = 700.0 / (1.0 + math.exp(-(t - 12.0) / 3.0))
        mq2 = 338.0 + surge_mq2 + random.gauss(0, 5.0)
        mq135 = 1523.0 + surge_mq135 + random.gauss(0, 6.0)
        state = "MIXTURE" if t > 10.0 else "NORMAL_BASELINE"
        return self._format_record(mq2, mq135, temp=26.0, hum=53.0, state=state)

    def _generate_drift_sample(self, t: float) -> Dict[str, Any]:
        drift = t * 3.5  # Constant climb
        mq2 = 338.0 + drift + random.gauss(0, 2.0)
        mq135 = 1523.0 + (drift * 2.0) + random.gauss(0, 3.0)
        state = "SENSOR_DRIFT_WARNING" if t > 25.0 else "NORMAL_BASELINE"
        return self._format_record(mq2, mq135, temp=28.0, hum=60.0, state=state)

    def _generate_fault_sample(self, t: float) -> Dict[str, Any]:
        if t > 8.0:
            # Wire disconnected!
            return self._format_record(None, None, temp=None, hum=None, state="SENSOR_FAULT", fault=True)
        return self._generate_normal_sample(t)

    def _generate_vent_fail_sample(self, t: float) -> Dict[str, Any]:
        # Gas present, relay command requested, but contactor feedback stays false
        rec = self._generate_combustible_sample(t)
        if t > 15.0:
            rec["relay_command"] = True
            rec["actual_relay_state"] = False  # Contactor stuck open!
            rec["monitoring_state"] = "VENTILATION_FEEDBACK_UNAVAILABLE"
        return rec

    def _generate_offline_sample(self, t: float) -> Dict[str, Any]:
        rec = self._generate_normal_sample(t)
        rec["monitoring_state"] = "OFFLINE_MODE"
        rec["network_connected"] = False
        return rec

    def _generate_ood_sample(self, t: float) -> Dict[str, Any]:
        # Out-of-distribution spike: MQ-2 reaches 3800, MQ-135 reaches 3950
        if t > 10.0:
            mq2 = 3800.0 + random.gauss(0, 20.0)
            mq135 = 3950.0 + random.gauss(0, 20.0)
            return self._format_record(mq2, mq135, temp=35.0, hum=85.0, state="UNKNOWN_OOD", is_ood=True)
        return self._generate_normal_sample(t)

    def _format_record(
        self,
        mq2: Optional[float],
        mq135: Optional[float],
        temp: Optional[float],
        hum: Optional[float],
        state: str,
        fault: bool = False,
        is_ood: bool = False
    ) -> Dict[str, Any]:
        return {
            "mode": "SYNTHETIC_SIMULATION",
            "provenance": "SYNTHETIC_GENERATED",
            "scenario_id": self.active_scenario_id,
            "timestamp": int(time.time() * 1000),
            "elapsed_sec": round(self.elapsed_sec, 2),
            "mq2_adc": round(mq2, 1) if mq2 is not None else None,
            "mq135_adc": round(mq135, 1) if mq135 is not None else None,
            "temperature": round(temp, 1) if temp is not None else None,
            "humidity": round(hum, 1) if hum is not None else None,
            "mq2_baseline": 338.0,
            "mq135_baseline": 1523.0,
            "monitoring_state": state,
            "is_ood": is_ood,
            "fault": fault,
            "relay_command": False,
            "actual_relay_state": False,
            "network_connected": True
        }
