"""
Recorded Serial Fixtures & Mock Serial Stream for Unit & Integration Testing:
Provides:
- Valid ESP32 JSON lines
- Partial line chunks to test line-buffer assembly
- Split lines across chunks
- Malformed / corrupted JSON lines
- Human-readable banner text (non-JSON)
- Sensor fault streams (null ADC)
- Rapid burst frames
"""

VALID_FRAME_1 = '{"device":"ESP32_GAS_MONITOR","timestamp":10500,"mq2_adc":342,"mq135_adc":1518,"temperature":24.5,"humidity":52.1,"relay":false,"pump":false,"fault":false}\n'
VALID_FRAME_2 = '{"device":"ESP32_GAS_MONITOR","timestamp":11000,"mq2_adc":345,"mq135_adc":1522,"temperature":24.6,"humidity":52.0,"relay":false,"pump":false,"fault":false}\n'
FAULT_FRAME = '{"device":"ESP32_GAS_MONITOR","timestamp":11500,"mq2_adc":null,"mq135_adc":null,"temperature":null,"humidity":null,"relay":false,"pump":false,"fault":true}\n'
BANNER_TEXT = '=================================\n     INDUSTRIAL GAS MONITOR      \n=================================\n'
MALFORMED_FRAME = '{"device":"ESP32_GAS_MONITOR","timestamp":12000,"mq2_adc":340,"mq135_adc":\n'

class MockSerialStream:
    """Simulates a physical UART port streaming chunks without hardware."""
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.is_open = True
        self.in_waiting_val = 0

    @property
    def in_waiting(self):
        return len(self.chunks[0].encode("utf-8")) if self.chunks else 0

    def read(self, size):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        return chunk.encode("utf-8")

    def close(self):
        self.is_open = False

    def setDTR(self, val):
        pass

    def setRTS(self, val):
        pass
