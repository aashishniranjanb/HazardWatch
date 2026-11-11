import unittest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from main import app

class TestBackendBridge(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data.get("status"), ["online", "OPERATIONAL"])
        self.assertIn("active_clients", data)

    def test_websocket_connection(self):
        with self.client.websocket_connect("/ws/sensors") as websocket:
            websocket.send_text("PING")
            data = websocket.receive_json()
            self.assertEqual(data.get("status"), "ack")
            self.assertEqual(data.get("received"), "PING")

if __name__ == '__main__':
    unittest.main()
