# ==============================================================================
# Project_A1 — Stop System Services Cleanly
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         Project_A1 Service Shutdown Tool                 " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidsFile = Join-Path $ScriptDir ".active_pids.json"

if (Test-Path $PidsFile) {
    try {
        $pids = Get-Content $PidsFile -Raw | ConvertFrom-Json
        
        # Disconnect serial gracefully via API if backend is still reachable
        try {
            Write-Host "Disconnecting serial port via backend API..." -NoNewline
            $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/serial/disconnect" -Method Post -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host " OK." -ForegroundColor Green
        } catch {
            Write-Host " (API already offline)" -ForegroundColor Gray
        }

        if ($pids.backend_pid) {
            Write-Host "Stopping FastAPI backend (PID: $($pids.backend_pid))..." -NoNewline
            try {
                Stop-Process -Id $pids.backend_pid -Force -ErrorAction SilentlyContinue
                Write-Host " Stopped." -ForegroundColor Green
            } catch {
                Write-Host " (Not running)." -ForegroundColor Gray
            }
        }

        if ($pids.frontend_pid) {
            Write-Host "Stopping Next.js frontend (PID: $($pids.frontend_pid))..." -NoNewline
            try {
                Stop-Process -Id $pids.frontend_pid -Force -ErrorAction SilentlyContinue
                Write-Host " Stopped." -ForegroundColor Green
            } catch {
                Write-Host " (Not running)." -ForegroundColor Gray
            }
        }

        Remove-Item -Path $PidsFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "Warning: Could not read .active_pids.json properly." -ForegroundColor Yellow
    }
} else {
    Write-Host "No active PID file found. Checking for lingering uvicorn/node processes..." -ForegroundColor Gray
}

# Cleanup any orphan uvicorn or next processes running on default ports
try {
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($port8000) {
        foreach ($conn in $port8000) {
            Write-Host "Terminating process on port 8000 (PID: $($conn.OwningProcess))..." -ForegroundColor Yellow
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
} catch {}

try {
    $port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    if ($port3000) {
        foreach ($conn in $port3000) {
            Write-Host "Terminating process on port 3000 (PID: $($conn.OwningProcess))..." -ForegroundColor Yellow
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
} catch {}

Write-Host "All Project_A1 services have been stopped cleanly.`n" -ForegroundColor Green
