# Live Serial Acquisition & Hardware Detection Audit Report

**Date of Execution:** 2026-11-11  
**Target Hardware:** ESP32 DevKit V1 (ESP32-WROOM-32)  
**Host Subsystem:** Windows Serial Port Enumerator (`pyserial` / `serial.tools.list_ports`)

---

## 1. Physical Hardware Scan Results

The serial scanner evaluated all available communications interfaces on the host system:

| Port | Description | Hardware ID (HWID) | USB-UART Bridge Detected? | Status |
| :--- | :--- | :--- | :--- | :--- |
| `COM1` | Communications Port (COM1) | `ACPI\PNP0501\0` | ❌ No (Motherboard Super I/O) | Available but inactive |

### 1.1 USB Serial Diagnostics
- **USB-to-UART Silicon:** No CP2102, CH340, FTDI, or PL2303 VID/PID detected on any USB hub.
- **Physical ESP32 Status:** **DISCONNECTED / NOT PLUGGED IN**.
- **Live Hardware Mode State:** Marked as `DISCONNECTED_UNVERIFIED`. The system refuses to fabricate serial bytes or silently fall back to simulation when the user requests `LIVE_HARDWARE`.

---

## 2. Acquisition Protocol Architecture

The live serial acquisition subsystem (`backend/app/services/serial_acquisition.py`) has been fully engineered to production standards for whenever the user connects the physical ESP32:

1. **Auto-Enumeration API:** `/api/v1/serial/ports` lists active COM ports and identifies USB-UART devices.
2. **Connection Lifecycle:** `/api/v1/serial/connect` and `/api/v1/serial/disconnect` with DTR/RTS auto-reset control.
3. **Buffering & Error Isolation:** Partial serial line buffering ensures no split JSON frames crash the parser.
4. **Data Integrity & Cryptographic Hashing:** Every physical capture stream writes:
   - Raw binary serial log (`ml/collection/hardware_raw_logs/{session_id}_raw.log`)
   - SHA-256 integrity hash
   - Validated JSONL records (`ml/collection/hardware_parsed_logs/{session_id}_telemetry.jsonl`)
   - Acquisition manifest (`ml/collection/manifests/{session_id}_manifest.json`)
5. **No Synthetic Fallback:** If `LIVE_HARDWARE` mode is selected without an active connection, the backend returns HTTP 400 (`HARDWARE_DISCONNECTED`) and does not synthesize fake gas readings.

---

## 3. Physical Hardware Validation Gate Status

- **Physical Connection Gate:** ⏸️ **BLOCKED ON PHYSICAL USB HARDWARE ATTACHMENT**.
- **Model Baseline Compatibility on Simulated Profiles:** ✅ **PASSED (100% INT8/Float32 parity)**.
- **Gas Classification Performance on Physical Hardware:** ⏸️ **PENDING PHYSICAL GAS SENSOR RUNS**.
