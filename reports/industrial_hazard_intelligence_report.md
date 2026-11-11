# Industrial Gas Hazard Intelligence System — General Factory Specification Report

**Date:** 2026-11-11  
**Project:** Industrial Gas-Response Monitoring and Hazard Intelligence System  
**Target Environment:** General Industrial Manufacturing Factory  
**Status:** M2.5 & Industrial Intelligence Engine Complete  

---

## 1. Physical Hardware Capabilities & Boundary Constraints

In compliance with the project charter and OSHA / Winsen technical references:
- **MQ-2**: Broad combustible-gas and aerosol smoke pattern screening. It does **not** provide chemical differentiation between LPG and Methane, nor quantitative %LEL concentration without certified multi-point calibration.
- **MQ-135**: Broad volatile contaminant and solvent response monitoring. It does **not** provide certified quantification or speciation for Ammonia (NH3), Hydrogen Sulfide (H2S), Benzene, or Toluene.
- **DHT11**: Temperature and humidity context only. It has **no** gas detection capability.
- **ESP32 DevKit V1**: Feature extraction, baseline-first state machine, local risk thresholds, and deterministic fail-safe relay actuation. It operates completely autonomously if the network or server drops.
- **Relay & Air Pump**: Electrical switching and experimental airflow demonstration only. It is **not** an explosion-proof industrial extraction system, and relay closure does not verify atmospheric clearance.

---

## 2. Eight Factory Zones (Z01 to Z08) Configuration

The factory model is partitioned into 8 specific operational sectors ([`factory_zones.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/factory_zones.yaml)):
1. **Z01 — Gas Storage & Distribution**: Focus on combustible gas header supply (H01). Requires dedicated optical/catalytic LEL and O2 monitors.
2. **Z02 — Boiler & Furnace Room**: Combustible supply, flue smoke, and carbon monoxide (H01, H03, H04). Requires dedicated electrochemical CO monitors.
3. **Z03 — Painting & Coating Section**: Solvent vapor accumulation (H02) and extraction failure (H07). Downdraft booth filtration and active carbon scrubber context.
4. **Z04 — Chemical Storage & Decanting**: Solvent vapors (H02) and ammonia risks (H06). Requires certified NH3 electrochemical cells.
5. **Z05 — Electrical MCC & Switchgear**: Thermal decomposition smoke from insulation pyrolysis (H03). Clean-agent suppression context.
6. **Z06 — General Production Floor**: Mixed machine lubricant mists, volatile cleaners, and assembly line distribution (H01, H02, H03).
7. **Z07 — Wastewater & Drainage Sumps**: Confined space risks, H2S toxic hazard (H05), and methane (H01). Requires certified 4-gas monitor.
8. **Z08 — Ventilation & Exhaust Area**: Duct static pressure and extraction blower failure context (H07).

---

## 3. Eight Industrial Hazards (H01 to H08) Specification

Documented in [`industrial_scenarios.yaml`](file:///c:/Users/Administrator/Videos/Project_A1/ml/config/industrial_scenarios.yaml):
- **H01**: Combustible Gas Response (LPG, Propane, Methane) — Broad MQ-2 screening.
- **H02**: VOC & Solvent Vapor Accumulation (Toluene, Xylene) — Broad MQ-135 screening.
- **H03**: Smoke & Thermal Decomposition — MQ-2 aerosol particulate detection.
- **H04**: Carbon Monoxide Hazard Context — Marked as *NOT SUPPORTED* (Requires dedicated CO sensor).
- **H05**: Hydrogen Sulfide Hazard Context — Marked as *NOT SUPPORTED* (Requires dedicated H2S sensor).
- **H06**: Ammonia Hazard Context — Marked as *NOT SUPPORTED* (Requires dedicated NH3 sensor).
- **H07**: Ventilation & Extraction Failure — *INDIRECT ONLY* (Inferred from sustained elevated trends without clearance).
- **H08**: Oxygen Deficiency / Enrichment — Marked as *NOT SUPPORTED* (Requires dedicated O2 sensor).

---

## 4. Industrial Incident Intelligence Engine (`backend/app/services/industrial_hazard_engine.py`)

The engine separates **Measured Sensor Evidence** from **Industrial Context Interpretation**:
- Translates ML predictions (`NORMAL_BASELINE`, `SMOKE`, `VOC_RESPONSE`, `MIXTURE`) + sensor trends (slopes) + zone context into structured incident objects:
  ```json
  {
    "event_id": "EVT-1731302400",
    "operating_mode": "LIVE",
    "zone_id": "Z03",
    "zone_name": "Painting and Coating Section",
    "sensor_state": "VALID",
    "severity": "WARNING",
    "trend": "RISING",
    "pattern": "VOC_RESPONSE",
    "industrial_context": "SOLVENT_VAPOUR_ACCUMULATION_IN_SPRAY_BOOTH",
    "evidence": ["ML_CLASSIFIER_VOC_RESPONSE_PATTERN", "INFLUX_DETECTED_SLOPE: MQ135=8.2"],
    "gas_identity": "NOT_CONFIRMED (Broad screening only)",
    "ml_confidence": 0.94,
    "recommended_action": "INSPECT_LOCAL_EXTRACTION_AND_VERIFY_WITH_CALIBRATED_PID",
    "incident_state": "UNVERIFIED",
    "relay_command": "ON",
    "verification_steps": ["Check differential pressure across exhaust filtration banks"]
  }
  ```
- **Zero Fabrication**: If sensor readings are missing, severity is set to `CRITICAL` with `SENSOR_FAULT`. A disconnected pin is **never** interpreted as clean air.

---

## 5. UI Integration in Next.js

1. **Factory Zone Selector** ([`FactoryZoneMonitor.tsx`](file:///c:/Users/Administrator/Videos/Project_A1/frontend/src/components/FactoryZoneMonitor.tsx)):
   - Allows switching between all 8 zones (Z01 to Z08) with live process descriptions, hazard warnings, and required certified sensors displayed.
2. **Actionable Incident Intelligence Card** ([`IncidentIntelligenceCard.tsx`](file:///c:/Users/Administrator/Videos/Project_A1/frontend/src/components/IncidentIntelligenceCard.tsx)):
   - Highlights the zone incident interpretation, calibrated ML confidence, supporting mathematical evidence, and exact operator verification steps.
3. **Full Production Build Verified**:
   - `npm run build` compiled with 100% type safety and zero static page generation errors.
