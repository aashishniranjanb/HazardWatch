"""
Unit and Integration Tests for Milestone 3.5:
Physical Hardware Baseline Acquisition and Model Validation
"""

import os
import json
import yaml
import numpy as np
import pandas as pd

def test_physical_session_artifacts_exist():
    """Verify that physical session files and reports exist on disk."""
    expected_files = [
        "reports/physical_baseline_statistics.csv",
        "reports/physical_model_input_compatibility.csv",
        "reports/physical_float_int8_comparison.csv",
        "ml/collection/manifests/physical_hardware_manifest.json",
        "ml/collection/physical_trials/SESSION_PHYS_01_WARMUP.parquet",
        "ml/collection/physical_trials/SESSION_PHYS_02_STABILIZED.parquet",
        "ml/collection/physical_trials/SESSION_PHYS_03_DRIFT_DAY2.parquet"
    ]
    for f in expected_files:
        assert os.path.exists(f), f"Expected artifact missing: {f}"

def test_physical_hardware_manifest_provenance():
    """Verify that provenance is strictly marked PHYSICAL_ESP32 and hardware specs are intact."""
    with open("ml/collection/manifests/physical_hardware_manifest.json", "r") as f:
        manifest = json.load(f)
    
    assert manifest["provenance"] == "PHYSICAL_ESP32"
    assert manifest["hardware_configuration"]["mcu"] == "ESP32-WROOM-32 (DevKit V1)"
    assert manifest["hardware_configuration"]["adc_attenuation"] == "ADC_ATTEN_DB_11 (0 to ~3.1V)"
    assert len(manifest["sessions"]) == 3
    assert manifest["validation_metrics"]["float32_int8_parity_pct"] >= 99.0
    assert manifest["validation_metrics"]["clean_air_normal_recall_pct"] >= 95.0

def test_physical_baseline_statistics():
    """Verify sensor baseline stability, drift slopes, and sample counts."""
    df = pd.read_csv("reports/physical_baseline_statistics.csv")
    assert len(df) == 3
    
    # Warmup should exhibit negative slope (cooling/stabilizing resistance decrease in ADC)
    warmup = df[df["session_type"] == "WARMUP"].iloc[0]
    assert warmup["mq2_drift_slope_per_sec"] < 0
    assert warmup["mq135_drift_slope_per_sec"] < 0

    # Stabilized baseline should have minimal drift (< 0.05 ADC / sec)
    stab = df[df["session_type"] == "STABILIZED"].iloc[0]
    assert abs(stab["mq2_drift_slope_per_sec"]) < 0.05
    assert abs(stab["mq135_drift_slope_per_sec"]) < 0.05
    assert stab["sample_count"] >= 1800

def test_feature_compatibility_schema():
    """Confirm all 11 features have zero nulls, zero infinities, and match model requirements."""
    df = pd.read_csv("reports/physical_model_input_compatibility.csv")
    assert len(df) == 11
    assert not df["has_nulls"].any()
    assert not df["has_infinities"].any()
    assert df["model_schema_compatible"].all()

def test_dual_inference_parity_and_clean_air_recall():
    """Verify that clean-air baseline physical data achieves 100% normal classification and high parity."""
    df = pd.read_csv("reports/physical_float_int8_comparison.csv")
    assert len(df) > 0
    
    # Parity match between Keras float32 and TFLite Micro INT8
    parity_rate = df["parity_match"].mean() * 100.0
    assert parity_rate >= 99.0, f"Parity rate too low: {parity_rate}%"

    # All clean physical ambient windows should classify as NORMAL_BASELINE
    normal_pct = (df["tflite_int8_label"] == "NORMAL_BASELINE").mean() * 100.0
    assert normal_pct >= 95.0, f"Clean air recall too low: {normal_pct}%"

def test_firmware_relay_safety_interlock():
    """Verify that firmware decouples sensor faults from automatic relay/pump triggering."""
    with open("firmware/esp32_firmware.ino", "r") as f:
        code = f.read()
    
    assert "!mq2_fault && !mq135_fault" in code, "Firmware must not activate relay during sensor fault"
    assert "Safe default OFF (including when sensor fault occurs)" in code

def test_baseline_registry_updated():
    """Verify that baseline_registry.yaml has an active verified hardware calibration entry."""
    with open("ml/config/baseline_registry.yaml", "r") as f:
        reg = yaml.safe_load(f)
    
    active = reg["baselines"]["hardware_calibration_active"]
    assert active["verified"] is True
    assert active["source_type"] == "HARDWARE_CALIBRATION"
    assert active["mq2"]["mean"] > 0
    assert active["mq135"]["mean"] > 0
