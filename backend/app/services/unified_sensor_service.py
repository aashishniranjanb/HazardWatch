"""
Unified Sensor Model Builder (M5.3.1):
Transforms raw telemetry and baseline registry state into the unified sensor value schema:
States:
- LIVE: Valid physical reading received on active hardware within TTL.
- LAST_KNOWN: Previously observed live reading (stale / hardware temporarily quiet).
- REFERENCE: Fallback reference/baseline value when live reading is unavailable.
- FAULT: Sensor fault detected (pin open/short or CRC error).
- UNAVAILABLE: Completely absent reading without active live link.
"""

import time
from typing import Optional, Dict, Any

# Sensor memory cache for last-known values across acquisition frames
LAST_KNOWN_CACHE: Dict[str, Dict[str, Any]] = {
    "mq2": {"value": None, "timestamp": None},
    "mq135": {"value": None, "timestamp": None},
    "temperature": {"value": None, "timestamp": None},
    "humidity": {"value": None, "timestamp": None}
}

LIVE_TTL_SECONDS = 3.5

def build_unified_sensor_record(
    sensor_id: str,
    sensor_name: str,
    gpio_pin: int,
    live_raw_value: Optional[float],
    is_fault: bool,
    baseline_record: Optional[Dict[str, Any]],
    unit: str = "ADC",
    current_time_s: Optional[float] = None
) -> Dict[str, Any]:
    now_s = current_time_s or time.time()
    now_ms = int(now_s * 1000)
    
    cached = LAST_KNOWN_CACHE.get(sensor_id, {"value": None, "timestamp": None})
    
    # 1. Update last-known cache if we have a non-null, non-fault physical reading
    if live_raw_value is not None and not is_fault:
        cached["value"] = float(live_raw_value)
        cached["timestamp"] = now_ms
        LAST_KNOWN_CACHE[sensor_id] = cached

    # 2. Determine Availability
    live_val: Optional[float] = None
    if is_fault:
        availability = "FAULT"
    elif live_raw_value is not None:
        availability = "LIVE"
        live_val = float(live_raw_value)
    elif cached["value"] is not None and (now_ms - cached["timestamp"] < 120000): # within 2 mins
        availability = "LAST_KNOWN"
    elif baseline_record and baseline_record.get("baseline_value") is not None:
        availability = "REFERENCE"
    else:
        availability = "UNAVAILABLE"

    # 3. Reference Metadata
    ref_val = baseline_record.get("baseline_value") if baseline_record else None
    ref_src = baseline_record.get("reference_source") if baseline_record else "SYSTEM_DEFAULT"
    ref_ts = baseline_record.get("reference_timestamp") if baseline_record else None
    cal_status = baseline_record.get("calibration_status") if baseline_record else "NOT_CALIBRATED"

    return {
        "sensor_id": sensor_id,
        "sensor_name": sensor_name,
        "gpio_pin": gpio_pin,
        "live_value": live_val,
        "last_known_value": cached["value"],
        "last_known_timestamp": cached["timestamp"],
        "reference_value": ref_val,
        "reference_source": ref_src,
        "reference_timestamp": ref_ts,
        "availability": availability,
        "calibration_status": cal_status,
        "unit": unit
    }

def get_all_unified_sensors(
    live_frame: Optional[Dict[str, Any]],
    baselines: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    sensors_raw = live_frame.get("sensors", {}) if live_frame else {}
    mon_state = live_frame.get("monitoring_state") if live_frame else None
    haz_state = live_frame.get("hazard_state") if live_frame else None
    is_system_fault = (mon_state == "SENSOR_FAULT" or haz_state == "SENSOR_FAULT")

    # MQ-2 (GPIO34)
    mq2_raw = sensors_raw.get("mq2_adc")
    mq2_fault = (mq2_raw is None and is_system_fault)
    mq2_record = build_unified_sensor_record(
        sensor_id="mq2",
        sensor_name="MQ-2 Combustible/Smoke",
        gpio_pin=34,
        live_raw_value=mq2_raw,
        is_fault=mq2_fault,
        baseline_record=baselines.get("mq2"),
        unit="ADC"
    )

    # MQ-135 (GPIO35)
    mq135_raw = sensors_raw.get("mq135_adc")
    mq135_fault = (mq135_raw is None) # Reported as null on hardware
    mq135_record = build_unified_sensor_record(
        sensor_id="mq135",
        sensor_name="MQ-135 Hazardous/Air Quality",
        gpio_pin=35,
        live_raw_value=mq135_raw,
        is_fault=mq135_fault,
        baseline_record=baselines.get("mq135"),
        unit="ADC"
    )

    # Temperature (GPIO4)
    temp_raw = sensors_raw.get("temperature_c") or sensors_raw.get("temperature")
    temp_fault = (temp_raw is None)
    temp_record = build_unified_sensor_record(
        sensor_id="temperature",
        sensor_name="DHT11 Ambient Temperature",
        gpio_pin=4,
        live_raw_value=temp_raw,
        is_fault=temp_fault,
        baseline_record=baselines.get("temperature"),
        unit="°C"
    )

    # Humidity (GPIO4)
    hum_raw = sensors_raw.get("humidity_percent") or sensors_raw.get("humidity")
    hum_fault = (hum_raw is None)
    hum_record = build_unified_sensor_record(
        sensor_id="humidity",
        sensor_name="DHT11 Relative Humidity",
        gpio_pin=4,
        live_raw_value=hum_raw,
        is_fault=hum_fault,
        baseline_record=baselines.get("humidity"),
        unit="%RH"
    )

    return {
        "mq2": mq2_record,
        "mq135": mq135_record,
        "temperature": temp_record,
        "humidity": hum_record
    }
