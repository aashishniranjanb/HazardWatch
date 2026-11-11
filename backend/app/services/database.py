"""
SQLite Database Persistence Service for Industrial Gas Platform:
Stores:
- Telemetry records (with provenance, operating mode, zone, raw ADC, and ML outputs)
- System events and hazard transitions
- Industrial incidents (INC-xxxx) and operator audit actions (acknowledge, resolve)
- Simulation and replay session logs
"""

import os
import sqlite3
import json
import time
from typing import Optional, List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(PROJECT_ROOT, "backend", "industrial_scada.db")

class DatabaseService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Telemetry Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    operating_mode TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    zone_id TEXT NOT NULL,
                    device_id TEXT,
                    mq2_adc REAL,
                    mq135_adc REAL,
                    temperature REAL,
                    humidity REAL,
                    mq2_baseline REAL,
                    mq135_baseline REAL,
                    server_prediction TEXT,
                    edge_prediction TEXT,
                    confidence REAL,
                    is_ood INTEGER,
                    severity TEXT,
                    relay_command INTEGER,
                    actual_relay_state INTEGER,
                    fault_detected INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Incidents Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    operating_mode TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    zone_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    gas_hazard_state TEXT NOT NULL,
                    evidence TEXT,
                    recommended_action TEXT,
                    status TEXT NOT NULL,
                    acknowledged_at INTEGER,
                    resolved_at INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. System Events & Audit Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. Simulation Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_sessions (
                    session_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    speed REAL NOT NULL,
                    status TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER,
                    samples_generated INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def insert_telemetry(self, t: Dict[str, Any]) -> int:
        query = """
            INSERT INTO telemetry (
                event_id, timestamp, operating_mode, provenance, zone_id, device_id,
                mq2_adc, mq135_adc, temperature, humidity, mq2_baseline, mq135_baseline,
                server_prediction, edge_prediction, confidence, is_ood, severity,
                relay_command, actual_relay_state, fault_detected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                t.get("event_id", f"EVT-{int(time.time()*1000)}"),
                t.get("timestamp", int(time.time() * 1000)),
                t.get("operating_mode", "LIVE_HARDWARE"),
                t.get("provenance", "PENDING_VERIFICATION"),
                t.get("zone_id", "Z01"),
                t.get("device", "ESP32_GAS_MONITOR"),
                t.get("mq2_adc"),
                t.get("mq135_adc"),
                t.get("temperature"),
                t.get("humidity"),
                t.get("mq2_baseline", 338.0),
                t.get("mq135_baseline", 1523.0),
                t.get("server_prediction", "UNKNOWN"),
                t.get("edge_prediction", "UNKNOWN"),
                t.get("server_confidence", 0.0),
                1 if t.get("is_ood") else 0,
                t.get("severity", "NORMAL"),
                1 if t.get("relay_command") else 0,
                1 if t.get("actual_relay_state") else 0,
                1 if t.get("fault_detected") else 0
            ))
            conn.commit()
            return cursor.lastrowid

    def insert_or_update_incident(self, inc: Dict[str, Any]):
        query = """
            INSERT INTO incidents (
                incident_id, event_id, timestamp, operating_mode, provenance, zone_id,
                severity, pattern, gas_hazard_state, evidence, recommended_action, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(incident_id) DO UPDATE SET
                severity=excluded.severity,
                pattern=excluded.pattern,
                gas_hazard_state=excluded.gas_hazard_state,
                evidence=excluded.evidence,
                recommended_action=excluded.recommended_action
        """
        evidence_val = inc.get("evidence", "")
        if isinstance(evidence_val, list):
            evidence_val = json.dumps(evidence_val)
        else:
            evidence_val = str(evidence_val)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                inc.get("incident_id", f"INC-{int(time.time()*1000)}"),
                inc.get("event_id", ""),
                inc.get("timestamp", int(time.time() * 1000)),
                inc.get("operating_mode", "LIVE_HARDWARE"),
                inc.get("provenance", "PENDING_VERIFICATION"),
                inc.get("zone_id", "Z01"),
                inc.get("severity", "WARNING"),
                inc.get("pattern", "UNKNOWN"),
                inc.get("gas_hazard_state", "UNKNOWN"),
                evidence_val,
                str(inc.get("recommended_action", "")),
                inc.get("incident_state", "ACTIVE")
            ))
            conn.commit()

    def acknowledge_incident(self, incident_id: str, notes: str = "") -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE incidents 
                SET status='ACKNOWLEDGED', acknowledged_at=?, notes=? 
                WHERE incident_id=?
            """, (int(time.time() * 1000), notes, incident_id))
            conn.commit()
            return cursor.rowcount > 0

    def resolve_incident(self, incident_id: str, notes: str = "") -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE incidents 
                SET status='RESOLVED', resolved_at=?, notes=? 
                WHERE incident_id=?
            """, (int(time.time() * 1000), notes, incident_id))
            conn.commit()
            return cursor.rowcount > 0

    def log_event(self, event_type: str, source: str, severity: str, description: Any, metadata: Optional[Dict[str, Any]] = None):
        desc_str = json.dumps(description) if isinstance(description, (list, dict)) else str(description)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_events (timestamp, event_type, source, severity, description, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (int(time.time() * 1000), event_type, source, severity, desc_str, json.dumps(metadata or {})))
            conn.commit()

    def get_recent_telemetry(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_events ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_analytics_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry")
            total_telemetry = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM incidents WHERE status='ACTIVE'")
            active_incidents = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM incidents WHERE status='ACKNOWLEDGED'")
            ack_incidents = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM incidents WHERE status='RESOLVED'")
            resolved_incidents = cursor.fetchone()[0]

            cursor.execute("SELECT severity, COUNT(*) FROM telemetry GROUP BY severity")
            severity_dist = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute("SELECT server_prediction, COUNT(*) FROM telemetry GROUP BY server_prediction")
            pred_dist = {r[0]: r[1] for r in cursor.fetchall()}

            return {
                "total_telemetry_records": total_telemetry,
                "active_incidents": active_incidents,
                "acknowledged_incidents": ack_incidents,
                "resolved_incidents": resolved_incidents,
                "severity_distribution": severity_dist,
                "prediction_distribution": pred_dist
            }
