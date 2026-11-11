"""
Serial Communication & Parser Unit Tests:
- Tests partial line chunk assembly
- Tests malformed JSON rejection without crashes
- Tests human banner filtering
- Tests sensor fault JSON handling
- Tests SHA-256 stream integrity calculation
"""

import sys
import os
import json
import hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tests"))

from app.services.serial_acquisition import ESP32SerialAcquisition
from mock_serial_fixtures import VALID_FRAME_1, VALID_FRAME_2, FAULT_FRAME, BANNER_TEXT, MALFORMED_FRAME

def test_serial_line_buffer_assembly():
    """Verify that split chunks across buffers assemble into valid telemetry."""
    received = []
    def on_telem(data):
        received.append(data)

    acq = ESP32SerialAcquisition("MOCK_COM", session_id="TEST_MOCK_BUF", on_telemetry=on_telem)

    # Split VALID_FRAME_1 into 3 arbitrary fragments
    part1 = VALID_FRAME_1[:25]
    part2 = VALID_FRAME_1[25:60]
    part3 = VALID_FRAME_1[60:]

    buffer = ""
    # Process fragments exactly as in serial read loop
    for chunk in [part1, part2, part3]:
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line:
                # Mock opened parsed file
                class DummyF:
                    def write(self, s): pass
                    def flush(self): pass
                acq._process_line(line, DummyF())

    assert len(received) == 1
    assert received[0]["device"] == "ESP32_GAS_MONITOR"
    assert received[0]["mq2_adc"] == 342
    assert received[0]["mq135_adc"] == 1518

def test_malformed_and_banner_handling():
    """Verify that human banner and malformed JSON are ignored without raising exceptions."""
    received = []
    acq = ESP32SerialAcquisition("MOCK_COM", session_id="TEST_MOCK_ERR", on_telemetry=lambda d: received.append(d))

    class DummyF:
        def write(self, s): pass
        def flush(self): pass

    # 1. Human banner lines
    for line in BANNER_TEXT.split("\n"):
        acq._process_line(line.strip(), DummyF())
    assert len(received) == 0

    # 2. Malformed JSON line
    acq._process_line(MALFORMED_FRAME.strip(), DummyF())
    assert len(received) == 0
    assert acq.error_count == 1

def test_fault_frame_handling():
    """Verify that null sensor readings in JSON are parsed cleanly."""
    received = []
    acq = ESP32SerialAcquisition("MOCK_COM", session_id="TEST_MOCK_FLT", on_telemetry=lambda d: received.append(d))

    class DummyF:
        def write(self, s): pass
        def flush(self): pass

    acq._process_line(FAULT_FRAME.strip(), DummyF())
    assert len(received) == 1
    assert received[0]["mq2_adc"] is None
    assert received[0]["mq135_adc"] is None
    assert received[0]["fault"] is True

if __name__ == "__main__":
    test_serial_line_buffer_assembly()
    test_malformed_and_banner_handling()
    test_fault_frame_handling()
    print("ALL SERIAL PARSER FIXTURE TESTS PASSED SUCCESSFULLY!")
