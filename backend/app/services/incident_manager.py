"""
Industrial Incident Lifecycle Manager
Handles active incidents, acknowledgments, resolutions, and event audit trails.
"""

import time
from typing import Dict, Any, List

class IncidentManager:
    def __init__(self):
        self.incidents: List[Dict[str, Any]] = []
        self.counter = 1

    def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        incident_data["id"] = f"INC-{self.counter:04d}"
        self.counter += 1
        incident_data["created_at"] = int(time.time() * 1000)
        incident_data["acknowledged"] = False
        incident_data["acknowledged_by"] = None
        incident_data["resolved"] = False
        incident_data["resolved_at"] = None

        self.incidents.insert(0, incident_data)
        self.incidents = self.incidents[:100] # Rolling buffer
        return incident_data

    def get_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.incidents[:limit]

    def acknowledge_incident(self, incident_id: str, operator_name: str = "Control_Room_Operator") -> bool:
        for inc in self.incidents:
            if inc.get("id") == incident_id or inc.get("event_id") == incident_id:
                inc["acknowledged"] = True
                inc["acknowledged_by"] = operator_name
                inc["acknowledged_at"] = int(time.time() * 1000)
                return True
        return False

    def resolve_incident(self, incident_id: str, resolution_notes: str = "Verified normal atmosphere") -> bool:
        for inc in self.incidents:
            if inc.get("id") == incident_id or inc.get("event_id") == incident_id:
                inc["resolved"] = True
                inc["resolved_at"] = int(time.time() * 1000)
                inc["resolution_notes"] = resolution_notes
                inc["incident_state"] = "RESOLVED"
                return True
        return False
