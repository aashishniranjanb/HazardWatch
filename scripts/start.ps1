# ==============================================================================
# Project_A1 — Start System Services (Backend + Frontend Child Processes)
# ==============================================================================
param(
    [string]$ComPort = "AUTO",
    [int]$BaudRate = 115200,
    [switch]$DevMode = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        Project_A1 Industrial Monitoring Launcher         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PidsFile = Join-Path $ScriptDir ".active_pids.json"

# Auto-detect COM port if AUTO (Prioritize CP210x, CH340, FTDI, USB-UART)
if ($ComPort -eq "AUTO") {
    $selectedPort = $null
    $selectedName = "Generic"

    try {
        # Check Windows PnP entity for actual USB-UART hardware (CP210x / CH340 / FTDI)
        $pnpDevices = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.Caption -match "\(COM(\d+)\)" }
        foreach ($dev in $pnpDevices) {
            if ($dev.Caption -match "CP210|CH340|FTDI|USB-to-UART|Silicon Labs|UART|USB Serial") {
                $dev.Caption -match "\(COM(\d+)\)" | Out-Null
                $selectedPort = "COM" + $Matches[1]
                $selectedName = $dev.Caption
                break
            }
        }
    } catch {}

    # Fallback to standard Port scanner if CIM is unavailable or didn't match
    if (-not $selectedPort) {
        try {
            $ports = [System.IO.Ports.SerialPort]::GetPortNames() | Where-Object { $_ -ne "COM1" }
            if ($ports.Count -gt 0) {
                $selectedPort = $ports[0]
                $selectedName = "Detected Port ($selectedPort)"
            }
        } catch {}
    }

    if ($selectedPort) {
        $ComPort = $selectedPort
        Write-Host "Auto-discovered active ESP32 device on: $ComPort ($selectedName)" -ForegroundColor Green
    } else {
        $ComPort = "COM3"
        Write-Host "No external USB-UART COM port detected. Defaulting to $ComPort." -ForegroundColor Yellow
        Write-Host "Tip: If your ESP32 uses CP210x, make sure CP210xVCPInstaller_x64 has been run." -ForegroundColor Yellow
    }
} else {
    Write-Host "Target COM Port explicitly configured as: $ComPort" -ForegroundColor Cyan
}

# 1. Stop any currently recorded active child processes
if (Test-Path $PidsFile) {
    Write-Host "Stopping previous instances..." -ForegroundColor Yellow
    & (Join-Path $ScriptDir "stop.ps1")
}

# 2. Launch FastAPI Backend
Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan

$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

$backendScript = @"
`$env:PYTHONPATH = "$BackendDir;" + `$env:PYTHONPATH
& "$VenvPython" -m uvicorn main:app --host 127.0.0.1 --port 8000
"@

$backendProcess = Start-Process powershell.exe -ArgumentList "-NoProfile", "-Command", $backendScript -WorkingDirectory $BackendDir -PassThru -WindowStyle Minimized

Write-Host "FastAPI started (PID: $($backendProcess.Id))" -ForegroundColor Green

# Wait for backend health check
Write-Host "Waiting for backend initialization..." -NoNewline
$backendReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($res.status -eq "HEALTHY") {
            $backendReady = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline
    }
}

if ($backendReady) {
    Write-Host " Ready!" -ForegroundColor Green
} else {
    Write-Host " Backend started (health polling timed out, continuing)." -ForegroundColor Yellow
}

# 3. Connect Backend to Physical COM Port (FastAPI as Sole Serial Owner)
Write-Host "Attempting physical serial bridge to $ComPort ($BaudRate baud)..." -NoNewline
try {
    $body = @{ port = $ComPort; baud_rate = $BaudRate } | ConvertTo-Json
    $connRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/serial/connect" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($connRes.status -eq "CONNECTED") {
        Write-Host " CONNECTED!" -ForegroundColor Green
    } else {
        Write-Host " (Device on $ComPort not connected; connect manually from dashboard diagnostics if needed)." -ForegroundColor Yellow
    }
} catch {
    Write-Host " (Device offline or busy on $ComPort)." -ForegroundColor Yellow
}

# 4. Launch Next.js SCADA Frontend
Write-Host "`n[2/2] Starting Next.js SCADA Dashboard on http://localhost:3000..." -ForegroundColor Cyan

$frontendCmd = if ($DevMode) { "npm run dev" } else { "npm run start" }
$frontendScript = @"
cmd.exe /c "$frontendCmd"
"@

$frontendProcess = Start-Process powershell.exe -ArgumentList "-NoProfile", "-Command", $frontendScript -WorkingDirectory $FrontendDir -PassThru -WindowStyle Minimized

Write-Host "Next.js started (PID: $($frontendProcess.Id))" -ForegroundColor Green

# 5. Save PIDs for clean termination
$pidsData = @{
    backend_pid = $backendProcess.Id
    frontend_pid = $frontendProcess.Id
    start_time = (Get-Date).ToString("o")
    com_port = $ComPort
} | ConvertTo-Json

Set-Content -Path $PidsFile -Value $pidsData

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  Project_A1 Stack is LIVE & RUNNING                      " -ForegroundColor Green
Write-Host "  - SCADA UI:    http://localhost:3000                   " -ForegroundColor Cyan
Write-Host "  - API / Docs:  http://127.0.0.1:8000/docs              " -ForegroundColor Cyan
Write-Host "  - Serial Link: $ComPort ($BaudRate baud)               " -ForegroundColor Cyan
Write-Host "  To stop all services: .\scripts\stop.ps1                " -ForegroundColor Yellow
Write-Host "==========================================================`n" -ForegroundColor Green
