# ==============================================================================
# Project_A1 — Environment & Hardware Portability Checker
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Project_A1 Environment & Hardware Diagnostic Check    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$allPassed = $true

# 1. Check Python
Write-Host "`n[1/5] Checking Python..." -NoNewline
try {
    $pyVer = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [FOUND: $pyVer]" -ForegroundColor Green
    } else {
        Write-Host " [MISSING]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " [NOT FOUND]" -ForegroundColor Red
    $allPassed = $false
}

# 2. Check Node.js
Write-Host "[2/5] Checking Node.js..." -NoNewline
try {
    $nodeVer = & node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [FOUND: $nodeVer]" -ForegroundColor Green
    } else {
        Write-Host " [MISSING]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " [NOT FOUND]" -ForegroundColor Red
    $allPassed = $false
}

# 3. Check npm
Write-Host "[3/5] Checking npm..." -NoNewline
try {
    $npmVer = & npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [FOUND: v$npmVer]" -ForegroundColor Green
    } else {
        Write-Host " [MISSING]" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host " [NOT FOUND]" -ForegroundColor Red
    $allPassed = $false
}

# 4. Check Git
Write-Host "[4/5] Checking Git..." -NoNewline
try {
    $gitVer = & git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [FOUND: $gitVer]" -ForegroundColor Green
    } else {
        Write-Host " [OPTIONAL / NOT IN PATH]" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [OPTIONAL / NOT IN PATH]" -ForegroundColor Yellow
}

# 5. Check Physical COM Ports & USB-UART Drivers (CP210x, CH340, FTDI)
Write-Host "[5/5] Scanning Available Serial Ports & USB-UART Drivers..." -ForegroundColor Cyan

$detectedHardware = @()
try {
    $pnpDevices = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.Caption -match "\(COM(\d+)\)" }
    foreach ($dev in $pnpDevices) {
        $dev.Caption -match "\(COM(\d+)\)" | Out-Null
        $portNum = "COM" + $Matches[1]
        $isUsb = ($dev.Caption -match "CP210|CH340|FTDI|USB|UART|Silicon Labs")
        $detectedHardware += [PSCustomObject]@{
            Port = $portNum
            Name = $dev.Caption
            IsUsbUart = $isUsb
        }
    }
} catch {}

if ($detectedHardware.Count -eq 0) {
    # Fallback to basic port scanner if CIM fails
    try {
        $rawPorts = [System.IO.Ports.SerialPort]::GetPortNames()
        foreach ($p in $rawPorts) {
            $detectedHardware += [PSCustomObject]@{
                Port = $p
                Name = "Generic Serial Port ($p)"
                IsUsbUart = ($p -ne "COM1")
            }
        }
    } catch {}
}

if ($detectedHardware.Count -gt 0) {
    Write-Host "       Detected COM Ports:" -ForegroundColor Green
    $foundUsbDevice = $false
    foreach ($d in $detectedHardware) {
        if ($d.IsUsbUart) {
            Write-Host "       - $($d.Port): $($d.Name) [TARGET USB-UART]" -ForegroundColor Green
            $foundUsbDevice = $true
        } else {
            Write-Host "       - $($d.Port): $($d.Name) [Internal/Virtual]" -ForegroundColor Gray
        }
    }

    if (-not $foundUsbDevice) {
        Write-Host "`n       [NOTICE] Only internal/virtual COM ports detected." -ForegroundColor Yellow
        Write-Host "       If using an ESP32 with Silicon Labs CP210x or CH340 chip:" -ForegroundColor Yellow
        Write-Host "       Please install the driver (e.g., CP210xVCPInstaller_x64.exe or CH341SER.EXE)." -ForegroundColor Yellow
    }
} else {
    Write-Host "       No active COM ports detected. Plug in your ESP32." -ForegroundColor Yellow
    Write-Host "       If device is plugged in but not showing:" -ForegroundColor Yellow
    Write-Host "       Install Silicon Labs CP210x (CP210xVCPInstaller_x64.exe) or CH340 driver." -ForegroundColor Yellow
}

Write-Host "`n----------------------------------------------------------"
if ($allPassed) {
    Write-Host "All primary software prerequisites are SATISFIED." -ForegroundColor Green
} else {
    Write-Host "Some prerequisites are MISSING. Run scripts\setup.ps1 to install." -ForegroundColor Red
}
Write-Host "----------------------------------------------------------`n"
