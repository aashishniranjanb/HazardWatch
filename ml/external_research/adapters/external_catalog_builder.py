"""
Adapter and Manifest Builder for External Research Datasets:
- Zenodo Long-Term Drift (E-Nose 40 days)
- UCI Gas Sensor Array Drift (16 chemical sensors, 36 months, 6 gases)
- UCI Twin Gas Sensor Arrays (dynamic mixtures)
- ESP32 MP-135 Indoor Air Quality (Zenodo, 2026)

All external datasets are strictly partitioned into ml/external_research/
and kept isolated from ESP32 training data to prevent domain corruption.
"""

import os
import json
import yaml
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXT_DIR = os.path.join(PROJECT_ROOT, "ml", "external_research")
MANIFEST_DIR = os.path.join(EXT_DIR, "manifests")
PROCESSED_DIR = os.path.join(EXT_DIR, "processed")

os.makedirs(MANIFEST_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def catalog_external_datasets():
    catalog = {
        "external_datasets": [
            {
                "id": "ZENODO_LONG_TERM_DRIFT_2025",
                "name": "Long-Term Drift Behavior of Electronic Nose Dataset",
                "doi": "10.5281/zenodo.15681119",
                "provenance": "EXTERNAL_RESEARCH",
                "description": "62 metal-oxide sensors across 40 days, baseline/exposure/recovery cycles.",
                "analytes": ["diacetyl", "2-phenylethanol", "ethanol"],
                "path": "Long-Term Drift Behavior of Electronic Nose Dataset",
                "sampling_days": 40,
                "role": "Reference benchmark for long-term MOS baseline drift and thermal recovery"
            },
            {
                "id": "UCI_GAS_SENSOR_ARRAY_DRIFT",
                "name": "Gas Sensor Array Drift Dataset at Different Concentrations",
                "doi": "10.24432/C5RP6W",
                "provenance": "EXTERNAL_RESEARCH",
                "description": "16 chemical sensors over 36 months under 6 volatile organic compounds.",
                "analytes": ["Ethanol", "Ethylene", "Ammonia", "Acetaldehyde", "Acetone", "Toluene"],
                "path": "gas+sensor+array+drift+dataset+at+different+concentrations",
                "batches": 10,
                "role": "Cross-device multi-year sensor aging and drift reference"
            },
            {
                "id": "UCI_TWIN_GAS_SENSOR_ARRAYS",
                "name": "Twin Gas Sensor Arrays Dataset",
                "doi": "10.24432/C5MW3K",
                "provenance": "EXTERNAL_RESEARCH",
                "description": "Two identical 8-sensor arrays in turbulent wind tunnel under dynamic mixtures.",
                "analytes": ["CO", "Methane", "Ethylene"],
                "path": "twin+gas+sensor+arrays",
                "role": "Turbulence and multi-sensor correlation benchmark"
            },
            {
                "id": "ZENODO_ESP32_INDOOR_AIR_QUALITY_2026",
                "name": "Indoor Air Quality ESP32 MP-135 Dataset v1.0.0",
                "doi": "10.5281/zenodo.13944645",
                "provenance": "EXTERNAL_RESEARCH",
                "description": "ESP32 real-time continuous indoor monitoring using MP-135 (MQ135 equivalent) with temperature & humidity.",
                "path": "indoor-air-quality-esp32-dataset-v1.0.0/masumkawsar99-indoor-air-quality-esp32-dataset-ea3d364/data",
                "role": "Direct ESP32 ADC and DHT environmental reference under domestic/indoor ambient conditions"
            }
        ]
    }
    
    out_path = os.path.join(MANIFEST_DIR, "external_research_inventory.json")
    with open(out_path, "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"Saved external research inventory to {out_path}")

    # Process ESP32 MP-135 baseline reference summary
    esp32_csv = os.path.join(PROJECT_ROOT, "indoor-air-quality-esp32-dataset-v1.0.0", "masumkawsar99-indoor-air-quality-esp32-dataset-ea3d364", "data", "indoor_air_quality_esp32.csv")
    if os.path.exists(esp32_csv):
        df_esp = pd.read_csv(esp32_csv)
        summary = {
            "dataset_id": "ZENODO_ESP32_INDOOR_AIR_QUALITY_2026",
            "total_records": len(df_esp),
            "gas_adc_mean": round(float(df_esp["gas_adc"].mean()), 2),
            "gas_adc_std": round(float(df_esp["gas_adc"].std()), 2),
            "gas_adc_min": int(df_esp["gas_adc"].min()),
            "gas_adc_max": int(df_esp["gas_adc"].max()),
            "temp_mean": round(float(df_esp["Temp C"].mean()), 2),
            "humidity_mean": round(float(df_esp["Humidity %"].mean()), 2),
            "splits": df_esp["split"].value_counts().to_dict()
        }
        sum_path = os.path.join(PROCESSED_DIR, "esp32_external_summary.json")
        with open(sum_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Saved external ESP32 summary to {sum_path}: {summary['total_records']} samples")

if __name__ == "__main__":
    catalog_external_datasets()
