# Milestone 4.4 Serial Communication Layer Report

**Subsystem:** Hardware Serial Driver, Web Serial API Client & Stream Parser  
**Verification:** Tested via Mock Serial Fixtures & COM Port Scanner  

---

## 1. Serial Stream Processing Architecture

Implemented in `backend/app/services/serial_acquisition.py` and `frontend/src/lib/serial.ts`:
- **Port Enumeration:** Scans all system COM ports and identifies physical USB-UART bridges (`CP2102`, `CH340`, `FTDI`).
- **Partial-Line Buffer:** Buffers fragmented incoming byte packets and yields complete newline-delimited JSON strings.
- **Malformed & Banner Filtering:** Gracefully skips human startup banners and rejects truncated JSON without parser crashes.
- **Cryptographic Hashing:** Computes SHA-256 integrity hash of raw unparsed byte streams.
- **No Synthetic Fallback:** Does not fabricate live telemetry when hardware is disconnected.

---

## 2. Test Verification (`test_serial_communication.py`)

- **Split Chunk Assembly Test:** Verified 3-way split fragments reassemble into valid telemetry frames.
- **Malformed & Banner Test:** Verified human text banners and broken syntax are rejected with incremented error counters.
- **Fault Frame Test:** Verified null ADC readings in fault frames parse cleanly.
- **Result:** **100% Passed**.
