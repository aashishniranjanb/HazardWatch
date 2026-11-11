# Project_A1 — Industrial Gas-Response Monitoring & Hazard Intelligence System

**Project_A1** is a dual-tier Edge AI & SCADA monitoring solution designed for factory environmental safety:
- **Microcontroller:** ESP32 DevKit V1 (MQ-2 combustible gas, MQ-135 air quality, DHT11 climatic ambient).
- **Backend:** FastAPI (Python 3.10/3.11 64-bit) providing exclusive COM-port serial acquisition, multi-model inference (XGBoost, Random Forest, Compact MLP), and SQLite persistence.
- **Frontend:** Next.js 14 SCADA operator dashboard with real-time WebSockets, 11 industrial views, and baseline-aware telemetry presentation.

---

## 1. Quick Transfer to Another Laptop

Transferring this project to another Windows machine is completely automated via PowerShell scripts.

### What is Included in the Distribution Archive:
```text
Project_A1/
├── backend/                  # FastAPI server, SQLite db, ML inference models
│   ├── app/
│   ├── requirements.txt      # Python dependencies
│   └── main.py
├── frontend/                 # Next.js 14 SCADA Dashboard
│   ├── src/
│   ├── package.json
│   └── package-lock.json     # Node.js pinned dependencies
├── firmware/                 # PlatformIO dual-firmware source (Backup & ML)
├── Ardiuno_IDE_firmware/     # Standalone Arduino IDE firmware sketch
├── scripts/                  # Automated management scripts
│   ├── check-environment.ps1 # Diagnoses Python, Node.js, COM ports
│   ├── setup.ps1             # Automatically builds .venv & installs npm
│   ├── start.ps1             # Launches backend & frontend child processes
│   ├── stop.ps1              # Cleanly terminates all child processes
│   └── package-zip.ps1       # Generates clean portable ZIP archive
├── reports/                  # Validation audits and verification logs
├── .env.example              # Safe environment variable template
└── README.md
```

*(Note: Virtual environments `.venv`, `node_modules`, `.next` build caches, and private `.env` secrets are excluded from distribution archives to keep the package lightweight, portable, and secure).*

---

## 2. Setup on New Laptop (Step-by-Step)

### Step 1: Unzip Archive
Extract `Project_A1_Portable_*.zip` to any folder on the new laptop (e.g., `C:\Projects\Project_A1` or `C:\Users\<User>\Videos\Project_A1`).

### Step 2: Open PowerShell as Administrator
Open PowerShell in the unzipped folder:
```powershell
Set-Location -Path "C:\path\to\Project_A1"
```

### Step 3: Run Diagnostic Check
Verify system prerequisites and available USB serial devices:
```powershell
.\scripts\check-environment.ps1
```

### Step 4: Run Automated Setup
This script creates the Python `.venv`, installs all backend libraries, copies `.env.example` to `.env`, and installs frontend packages:
```powershell
.\scripts\setup.ps1
```
> **Tip:** If the new laptop does not have Python 3.11 or Node.js installed, pass `-AutoInstallPrereqs`:
> ```powershell
> .\scripts\setup.ps1 -AutoInstallPrereqs
> ```

---

## 3. Running the System

### Start Both Services
Run the launcher script:
```powershell
.\scripts\start.ps1
```
- Automatically auto-discovers your ESP32 COM port (e.g. `COM3`, `COM4`, `COM5`).
- Spawns the **FastAPI backend** on `http://127.0.0.1:8000` as a background child process.
- Connects FastAPI as the **sole physical reader** of the ESP32 USB port.
- Spawns the **Next.js SCADA frontend** on `http://localhost:3000` as a background child process.
- Records process IDs in `.active_pids.json` for deterministic process management.

### Access the Interfaces:
- **SCADA Web Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Live Health Endpoint:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Stop All Services Cleanly
To shut down both servers and release the serial COM port:
```powershell
.\scripts\stop.ps1
```

---

## 4. Hardware Portability & COM Ports (CP210x, CH340, COM3 / COM6)

Different laptops assign different COM ports (e.g. `COM3`, `COM5`, `COM6`) depending on the USB port used and whether the ESP32 board uses a **Silicon Labs CP2102/CP2104** chip or a **WCH CH340** chip.

### 1. USB-UART Driver Requirement
If the ESP32 is not recognized when plugged in, run the appropriate USB VCP driver installer on the new laptop:
- **Silicon Labs CP210x:** Run `CP210xVCPInstaller_x64.exe` (Official Silicon Labs VCP driver).
- **WCH CH340/CH341:** Run `CH341SER.EXE`.

### 2. Intelligent Auto-Discovery
`scripts\start.ps1` and `scripts\check-environment.ps1` automatically scan Windows PnP hardware to identify which port the CP210x or CH340 chip is assigned to (e.g. `COM3`, `COM4`, `COM6`), ignoring internal legacy motherboard ports like `COM1`.

### 3. Manual COM Port Override
If you want to explicitly pin to a specific COM port on the new laptop:
```powershell
.\scripts\start.ps1 -ComPort COM3 -BaudRate 115200
# or
.\scripts\start.ps1 -ComPort COM6 -BaudRate 115200
```

### 4. Firmware Status
The ESP32 is **already flashed** with the deterministic backup firmware (`project_a1_backup`). Simply plug the USB cable into the new laptop. You do **not** need to reflash the firmware on the new laptop. Active-LOW relay logic remains locked `DISABLED` (GPIO26 driven HIGH on boot).


---

## 5. Security & Secret Configuration

1. **Zero Secret Leakage:** Real credentials, passwords, and `.env` files are excluded from the distribution archive.
2. **Local Configuration:** Modify `.env` on the new laptop to adjust origins, ports, and secret keys.
3. For enterprise Windows deployments, sensitive API tokens should be stored using Windows Data Protection API (DPAPI) or Windows Credential Manager.
