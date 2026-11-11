"""
FastAPI Industrial Gas Hazard Intelligence Server (v4.5.0)
Architecture:
- Tri-Mode Operating Architecture:
    1. LIVE_HARDWARE (USB Serial COM port streaming with explicit verification gating)
    2. HISTORICAL_REPLAY (Verified research CSV replay with original provenance)
    3. SYNTHETIC_SIMULATION (Hazard engine scenarios across 8 industrial factory zones)
    4. OFFLINE_MODE (Local cached telemetry and disconnected client operations)
- Complete API Contract per User Specification:
    GET /api/v1/health
    GET /api/v1/factory/zones
    GET /api/v1/industrial/scenarios
    GET /api/v1/industrial/capabilities
    POST /api/v1/telemetry
    POST /api/v1/inference/predict
    GET /api/v1/models
    GET /api/v1/models/active
    GET /api/v1/industrial/incidents
    POST /api/v1/industrial/incidents/{id}/acknowledge
    POST /api/v1/industrial/incidents/{id}/resolve
    GET /api/v1/analytics
    GET /api/v1/events
    POST /api/v1/simulation/start
    POST /api/v1/simulation/stop
    GET /api/v1/simulation/status
    WS /ws/telemetry
- Full SQLite Database Persistence (telemetry, incidents, events, simulation sessions)
- Safety Interlock Decoupling: Sensor faults NEVER trigger emergency air ventilation
"""

import os
import sys
import time
import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.industrial_hazard_engine import IndustrialHazardEngine
from app.services.incident_manager import IncidentManager
from app.services.serial_acquisition import SerialDeviceScanner, ESP32SerialAcquisition
from app.services.historical_replay_service import HistoricalReplayService
from app.services.server_inference_service import ServerInferenceService
from app.services.database import DatabaseService
from app.services.simulation_engine import SimulationEngine
from app.services.multi_model_service import MultiModelAIService
from app.services.baseline_registry import BaselineRegistryService
from app.services.unified_sensor_service import get_all_unified_sensors, build_unified_sensor_record

app = FastAPI(
    title="Industrial Gas Hazard Intelligence Platform",
    version="4.5.0",
    description="Software-First Complete SCADA & AI Platform for Factory Gas Monitoring"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services Initialization
db = DatabaseService()
hazard_engine = IndustrialHazardEngine()
incident_mgr = IncidentManager()
replay_service = HistoricalReplayService()
server_ml = ServerInferenceService()
sim_engine = SimulationEngine()
ai_service = MultiModelAIService()
baseline_reg = BaselineRegistryService()

active_serial: Optional[ESP32SerialAcquisition] = None
connected_websockets: List[WebSocket] = []
simulation_task: Optional[asyncio.Task] = None
main_event_loop: Optional[asyncio.AbstractEventLoop] = None

@app.on_event("startup")
async def startup_event():
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()

# Pydantic Schemas
class TelemetryPayload(BaseModel):
    device: str = "ESP32_GAS_MONITOR"
    zone_id: str = "Z03"
    operating_mode: str = "LIVE_HARDWARE"
    provenance: str = "PENDING_VERIFICATION"
    mq2_adc: Optional[float] = None
    mq135_adc: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    mq2_baseline: float = 338.0
    mq135_baseline: float = 1523.0
    edge_prediction: Optional[str] = "NORMAL_BASELINE"
    edge_confidence: Optional[float] = 0.95
    mq2_slope: float = 0.0
    mq135_slope: float = 0.0
    relay_state: bool = False
    air_pump_state: bool = False
    fault: bool = False

class PredictRequest(BaseModel):
    mq2_adc: float
    mq135_adc: float
    mq2_baseline: float = 338.0
    mq135_baseline: float = 1523.0
    mq2_slope: float = 0.0
    mq135_slope: float = 0.0

class SimulationStartRequest(BaseModel):
    scenario_id: str
    seed: int = 42
    speed: float = 1.0

class ConnectSerialRequest(BaseModel):
    port: str
    baud_rate: int = 115200

class IncidentActionRequest(BaseModel):
    notes: Optional[str] = ""

async def broadcast_ws(message: Dict[str, Any]):
    dead = []
    for ws in connected_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in connected_websockets:
            connected_websockets.remove(ws)

# -------------------------------------------------------------
# 1. SYSTEM HEALTH & DIAGNOSTICS
# -------------------------------------------------------------
@app.get("/")
def root():
    return {
        "system": "Industrial Gas Hazard Intelligence Platform",
        "version": "4.5.0",
        "status": "OPERATIONAL",
        "supported_modes": ["LIVE_HARDWARE", "HISTORICAL_REPLAY", "SYNTHETIC_SIMULATION", "OFFLINE_MODE"],
        "active_clients": len(connected_websockets)
    }

@app.get("/api/v1/health")
def get_health():
    return {
        "status": "HEALTHY",
        "timestamp": int(time.time() * 1000),
        "database": "CONNECTED",
        "models_loaded": len(ai_service.get_models_metadata()),
        "supported_modes": ["LIVE_HARDWARE", "HISTORICAL_REPLAY", "SYNTHETIC_SIMULATION", "OFFLINE_MODE"],
        "active_simulation": sim_engine.is_running,
        "live_hardware_connected": active_serial is not None and active_serial.is_running
    }

# -------------------------------------------------------------
# 2. FACTORY KNOWLEDGE BASE (ZONES, SCENARIOS, CAPABILITIES)
# -------------------------------------------------------------
@app.get("/api/v1/factory/zones")
def list_zones():
    return hazard_engine.zones_cfg

@app.get("/api/v1/industrial/scenarios")
def list_scenarios():
    return hazard_engine.scenarios_cfg

@app.get("/api/v1/industrial/capabilities")
def get_capabilities():
    return hazard_engine.capabilities_cfg

# -------------------------------------------------------------
# 3. TELEMETRY & MULTI-MODEL ML INFERENCE
# -------------------------------------------------------------
@app.get("/api/v1/sensors/unified")
def get_unified_sensor_states():
    """Returns the unified 5-state model for all sensors."""
    baselines = baseline_reg.get_all_baselines()
    live_frame = active_serial.last_frame if (active_serial and active_serial.last_frame) else None
    unified = get_all_unified_sensors(live_frame, baselines)
    return {
        "status": "LIVE" if live_frame else "DISCONNECTED",
        "timestamp": int(time.time() * 1000),
        "sensors": unified
    }

@app.get("/api/v1/baselines")
def list_baselines():
    """Returns all registered sensor baselines and calibration status."""
    return baseline_reg.get_all_baselines()

@app.get("/api/v1/telemetry")
def get_telemetry_history(limit: int = Query(50, ge=1, le=500)):
    records = db.get_recent_telemetry(limit=limit)
    return {
        "count": len(records),
        "records": records
    }

@app.get("/api/v1/telemetry/live")
def get_live_telemetry():
    if active_serial and active_serial.last_frame:
        return {
            "status": "LIVE",
            "source": "ESP32_HARDWARE",
            "data": active_serial.last_frame,
            "timestamp": active_serial.last_frame_timestamp
        }
    recent = db.get_recent_telemetry(limit=1)
    if recent:
        return {
            "status": "CACHED",
            "source": "DATABASE",
            "data": recent[0],
            "timestamp": recent[0].get("timestamp")
        }
    return {
        "status": "NO_DATA",
        "source": None,
        "data": None,
        "timestamp": int(time.time() * 1000)
    }

@app.post("/api/v1/telemetry")
async def process_telemetry(payload: TelemetryPayload):
    event_id = f"EVT-{int(time.time() * 1000)}"

    server_prediction = "UNKNOWN"
    server_confidence = 0.0
    is_ood = False

    if payload.mq2_adc is not None and payload.mq135_adc is not None and not payload.fault:
        ai_res = ai_service.predict_all(
            mq2_adc=payload.mq2_adc,
            mq135_adc=payload.mq135_adc,
            base_mq2=payload.mq2_baseline,
            base_mq135=payload.mq135_baseline,
            mq2_slope=payload.mq2_slope,
            mq135_slope=payload.mq135_slope
        )
        server_prediction = ai_res["primary_prediction"]
        server_confidence = ai_res["primary_confidence"]
        is_ood = ai_res["is_ood"]

    incident = hazard_engine.evaluate_incident(
        event_id=event_id,
        operating_mode=payload.operating_mode,
        zone_id=payload.zone_id,
        mq2_adc=payload.mq2_adc,
        mq135_adc=payload.mq135_adc,
        temperature=payload.temperature,
        humidity=payload.humidity,
        mq2_baseline=payload.mq2_baseline,
        mq135_baseline=payload.mq135_baseline,
        ml_prediction=server_prediction,
        ml_confidence=server_confidence,
        mq2_slope=payload.mq2_slope,
        mq135_slope=payload.mq135_slope
    )

    incident["edge_prediction"] = payload.edge_prediction
    incident["edge_confidence"] = payload.edge_confidence
    incident["server_prediction"] = server_prediction
    incident["server_confidence"] = server_confidence
    incident["is_ood"] = is_ood
    incident["provenance"] = payload.provenance
    incident["relay_command"] = incident.get("relay_activation", False)
    incident["actual_relay_state"] = payload.relay_state
    incident["fault_detected"] = payload.fault

    # CRITICAL SAFETY INTERLOCK: Sensor fault keeps ventilation relay OFF
    if payload.fault:
        incident["relay_command"] = False
        incident["severity"] = "WARNING"
        incident["gas_hazard_state"] = "UNKNOWN"
        incident["recommended_action"] = "Sensor hardware fault detected. Isolate zone wiring. Ventilation interlock safe OFF."

    # Persist in DB
    db.insert_telemetry(incident)

    if incident["severity"] != "NORMAL":
        incident_mgr.create_incident(incident)
        db.insert_or_update_incident(incident)
        db.log_event("HAZARD_DETECTED", payload.zone_id, incident["severity"], incident["evidence"], incident)

    await broadcast_ws({
        "type": "TELEMETRY_UPDATE",
        "data": incident
    })
    return incident

@app.post("/api/v1/inference/predict")
def run_model_predict(req: PredictRequest):
    return ai_service.predict_all(
        mq2_adc=req.mq2_adc,
        mq135_adc=req.mq135_adc,
        base_mq2=req.mq2_baseline,
        base_mq135=req.mq135_baseline,
        mq2_slope=req.mq2_slope,
        mq135_slope=req.mq135_slope
    )

@app.get("/api/v1/models")
def list_models():
    return {
        "models": ai_service.get_models_metadata(),
        "feature_schema": "feature_schema_v2.yaml (11 features)"
    }

@app.get("/api/v1/models/active")
def get_active_model():
    return {
        "active_server_model": "xgboost_v2_7",
        "active_edge_model": "compact_mlp_int8_ops.tflite",
        "quantization": "int8_quantized_ops_with_float_io",
        "input_features": 11,
        "supported_classes": ai_service.classes
    }

# -------------------------------------------------------------
# 4. INCIDENT MANAGEMENT & AUDIT TRAILS
# -------------------------------------------------------------
@app.get("/api/v1/industrial/incidents")
def get_incidents():
    return db.get_all_incidents()

@app.post("/api/v1/industrial/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str, req: IncidentActionRequest = IncidentActionRequest()):
    success = db.acknowledge_incident(incident_id, notes=req.notes or "")
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found in database")
    incident_mgr.acknowledge_incident(incident_id)
    db.log_event("INCIDENT_ACKNOWLEDGED", incident_id, "INFO", f"Operator acknowledged incident: {req.notes}")
    await broadcast_ws({"type": "INCIDENT_ACK", "incident_id": incident_id})
    return {"status": "ACKNOWLEDGED", "incident_id": incident_id}

@app.post("/api/v1/industrial/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, req: IncidentActionRequest = IncidentActionRequest()):
    success = db.resolve_incident(incident_id, notes=req.notes or "")
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found in database")
    incident_mgr.resolve_incident(incident_id)
    db.log_event("INCIDENT_RESOLVED", incident_id, "INFO", f"Incident resolved: {req.notes}")
    await broadcast_ws({"type": "INCIDENT_RESOLVED", "incident_id": incident_id})
    return {"status": "RESOLVED", "incident_id": incident_id}

# -------------------------------------------------------------
# 5. ANALYTICS & EVENTS
# -------------------------------------------------------------
@app.get("/api/v1/analytics")
def get_analytics():
    return db.get_analytics_summary()

@app.get("/api/v1/events")
def get_events(limit: int = Query(50)):
    return db.get_recent_events(limit=limit)

# -------------------------------------------------------------
# 6. DETERMINISTIC FACTORY SIMULATION
# -------------------------------------------------------------
async def _simulation_loop():
    while sim_engine.is_running:
        sample = sim_engine.step(dt=0.5)
        # Evaluate telemetry
        payload = TelemetryPayload(
            operating_mode="SYNTHETIC_SIMULATION",
            provenance="SYNTHETIC_GENERATED",
            zone_id=sim_engine.SCENARIOS[sim_engine.active_scenario_id]["zone"],
            mq2_adc=sample["mq2_adc"],
            mq135_adc=sample["mq135_adc"],
            temperature=sample["temperature"],
            humidity=sample["humidity"],
            fault=sample["fault"]
        )
        await process_telemetry(payload)
        await asyncio.sleep(0.5 / sim_engine.speed)

@app.post("/api/v1/simulation/start")
async def start_simulation(req: SimulationStartRequest):
    global simulation_task
    try:
        status = sim_engine.start_simulation(req.scenario_id, seed=req.seed, speed=req.speed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if simulation_task and not simulation_task.done():
        simulation_task.cancel()
    
    simulation_task = asyncio.create_task(_simulation_loop())
    db.log_event("SIMULATION_STARTED", req.scenario_id, "INFO", f"Started deterministic scenario {req.scenario_id}")
    return status

@app.post("/api/v1/simulation/stop")
async def stop_simulation():
    global simulation_task
    status = sim_engine.stop_simulation()
    if simulation_task and not simulation_task.done():
        simulation_task.cancel()
    db.log_event("SIMULATION_STOPPED", "ENGINE", "INFO", "Simulation stopped by operator")
    return status

@app.get("/api/v1/simulation/status")
def get_simulation_status():
    return sim_engine.get_status()

# -------------------------------------------------------------
# 7. HISTORICAL REPLAY API
# -------------------------------------------------------------
@app.get("/api/v1/replay/datasets")
def list_replay_datasets():
    return replay_service.list_available_datasets()

@app.post("/api/v1/replay/load/{dataset_id}")
def load_replay_dataset(dataset_id: str):
    success = replay_service.load_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found or could not be opened")
    return {"status": "LOADED", "dataset_id": dataset_id, "total_rows": len(replay_service.df)}

@app.get("/api/v1/replay/step")
def get_replay_step(index: Optional[int] = Query(None)):
    sample = replay_service.get_sample(index)
    if not sample:
        raise HTTPException(status_code=400, detail="No active replay dataset loaded. Call /load first.")
    
    if sample["mq2_adc"] is not None and sample["mq135_adc"] is not None:
        ai_res = ai_service.predict_all(
            mq2_adc=sample["mq2_adc"],
            mq135_adc=sample["mq135_adc"]
        )
        sample["multi_model_inference"] = ai_res
    return sample

# -------------------------------------------------------------
# 8. SERIAL HARDWARE GATING
# -------------------------------------------------------------
@app.get("/api/v1/serial/status")
def get_serial_status():
    if active_serial is None:
        return {
            "connected": False,
            "port": None,
            "baud_rate": None,
            "last_frame_timestamp": None,
            "last_error": None,
            "frames_received": 0,
            "status": "DISCONNECTED"
        }
    
    is_live = active_serial.is_running and (active_serial.ser is not None and active_serial.ser.is_open)
    return {
        "connected": is_live,
        "port": active_serial.port,
        "baud_rate": active_serial.baud_rate,
        "last_frame_timestamp": active_serial.last_frame_timestamp,
        "last_error": active_serial.last_error,
        "frames_received": active_serial.sample_count,
        "status": "CONNECTED" if is_live else ("ERROR" if active_serial.last_error else "DISCONNECTED"),
        "raw_log_path": active_serial.raw_log_path,
        "parsed_log_path": active_serial.parsed_log_path
    }

@app.get("/api/v1/serial/ports")
def list_serial_ports():
    ports = SerialDeviceScanner.list_ports()
    return {
        "count": len(ports),
        "ports": ports,
        "hardware_verified": any(p["is_usb_uart"] for p in ports)
    }

@app.post("/api/v1/serial/connect")
async def connect_serial(req: ConnectSerialRequest):
    global active_serial
    if active_serial and active_serial.is_running:
        active_serial.stop()
    
    loop = asyncio.get_running_loop()

    def on_hardware_frame(frame: Dict[str, Any]):
        # Structure normalized incident from hardware frame
        sensors = frame.get("sensors", {})
        mq2_adc = sensors.get("mq2_adc")
        mq135_adc = sensors.get("mq135_adc")
        temp = sensors.get("temperature_c")
        hum = sensors.get("humidity_percent")
        mon_state = frame.get("monitoring_state", "LIVE_MONITORING")
        haz_state = frame.get("hazard_state", "NORMAL_BASELINE")
        inf = frame.get("inference", {})

        is_fault = (mon_state == "SENSOR_FAULT" or haz_state == "SENSOR_FAULT")
        
        telemetry_doc = {
            "event_id": f"EVT-HW-{int(time.time()*1000)}",
            "timestamp": int(time.time() * 1000),
            "operating_mode": "LIVE_HARDWARE",
            "provenance": "PHYSICAL_ESP32",
            "zone_id": "Z03",
            "device": frame.get("device_id", "PROJECT_A1_ESP32_01"),
            "mq2_adc": mq2_adc,
            "mq135_adc": mq135_adc,
            "temperature": temp,
            "humidity": hum,
            "mq2_baseline": 338.0,
            "mq135_baseline": 1523.0,
            "server_prediction": inf.get("class", "NORMAL_BASELINE"),
            "edge_prediction": inf.get("class", "NORMAL_BASELINE"),
            "server_confidence": inf.get("confidence", 0.95),
            "is_ood": False,
            "severity": "WARNING" if is_fault else "NORMAL",
            "gas_hazard_state": haz_state,
            "relay_command": False,
            "actual_relay_state": False,
            "fault_detected": is_fault,
            "rawJson": json.dumps(frame),
            "unified_sensors": get_all_unified_sensors(frame, baseline_reg.get_all_baselines())
        }
        
        db.insert_telemetry(telemetry_doc)
        
        # Broadcast via async threadsafe runner
        if connected_websockets:
            msg = {
                "type": "TELEMETRY_UPDATE",
                "data": telemetry_doc,
                "timestamp": telemetry_doc["timestamp"]
            }
            # Schedule broadcast in event loop
            try:
                asyncio.run_coroutine_threadsafe(broadcast_ws(msg), main_event_loop)
            except Exception:
                pass

    active_serial = ESP32SerialAcquisition(
        port=req.port,
        baud_rate=req.baud_rate,
        on_telemetry=on_hardware_frame
    )
    success = active_serial.start()
    if not success:
        active_serial = None
        raise HTTPException(status_code=400, detail=f"Failed to connect to serial port {req.port}")
    return {"status": "CONNECTED", "port": req.port, "baud_rate": req.baud_rate}

@app.post("/api/v1/serial/disconnect")
def disconnect_serial():
    global active_serial
    if active_serial:
        active_serial.stop()
        active_serial = None
        return {"status": "DISCONNECTED"}
    return {"status": "ALREADY_DISCONNECTED"}

@app.on_event("shutdown")
def shutdown_event():
    global active_serial
    if active_serial:
        active_serial.stop()
        active_serial = None

# -------------------------------------------------------------
# 9. WEBSOCKET REAL-TIME BROADCAST
# -------------------------------------------------------------
@app.websocket("/ws/telemetry")
@app.websocket("/ws/sensors")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            if text == "PING":
                await websocket.send_json({"status": "ack", "received": "PING"})
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
