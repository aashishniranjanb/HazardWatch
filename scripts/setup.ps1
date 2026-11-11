# ==============================================================================
# Project_A1 — Laptop Setup & Automated Dependency Installer
# ==============================================================================
param(
    [switch]$AutoInstallPrereqs = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         Project_A1 Laptop Setup & Initialization         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# 1. Environment Prerequisite Inspection
Write-Host "`n[Step 1/5] Verifying Core System Prerequisites..." -ForegroundColor Yellow

function Test-CommandAvailable ($cmd) {
    return [bool](Get-Command -Name $cmd -ErrorAction SilentlyContinue)
}

$hasPython = Test-CommandAvailable "python"
$hasNode = Test-CommandAvailable "node"
$hasNpm = Test-CommandAvailable "npm"

if (-not $hasPython -or -not $hasNode -or -not $hasNpm) {
    if ($AutoInstallPrereqs) {
        Write-Host "Missing tools detected. Attempting automated winget installation..." -ForegroundColor Cyan
        if (Test-CommandAvailable "winget") {
            if (-not $hasPython) {
                Write-Host "Installing Python 3.11 via winget..."
                & winget install Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
            }
            if (-not $hasNode) {
                Write-Host "Installing Node.js LTS via winget..."
                & winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
            }
            Write-Host "Prerequisites installed. Please restart your PowerShell session and rerun setup.ps1." -ForegroundColor Green
            exit 0
        } else {
            Write-Error "winget is not available on this machine. Please install Python 3.11 and Node.js LTS manually."
        }
    } else {
        Write-Host "`n[ERROR] Missing required tools:" -ForegroundColor Red
        if (-not $hasPython) { Write-Host " - Python (3.10+ 64-bit)" -ForegroundColor Red }
        if (-not $hasNode) { Write-Host " - Node.js (v18+ LTS)" -ForegroundColor Red }
        if (-not $hasNpm) { Write-Host " - npm" -ForegroundColor Red }
        Write-Host "`nTip: Run .\scripts\setup.ps1 -AutoInstallPrereqs to auto-install via winget, or install manually." -ForegroundColor Yellow
        exit 1
    }
}

# 2. Setup Environment Variables (.env)
Write-Host "`n[Step 2/5] Initializing Configuration..." -ForegroundColor Yellow
$EnvExample = Join-Path $ProjectRoot ".env.example"
$EnvTarget = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvTarget) -and (Test-Path $EnvExample)) {
    Copy-Item -Path $EnvExample -Destination $EnvTarget
    Write-Host "Created .env configuration from .env.example." -ForegroundColor Green
} else {
    Write-Host ".env configuration already exists." -ForegroundColor Gray
}

# 3. Setup Python Backend Virtual Environment
Write-Host "`n[Step 3/5] Setting up Python Virtual Environment & Requirements..." -ForegroundColor Yellow
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment in backend\.venv..."
    & python -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

Write-Host "Upgrading pip..."
& $VenvPython -m pip install --upgrade pip --quiet

$ReqFile = Join-Path $BackendDir "requirements.txt"
if (Test-Path $ReqFile) {
    Write-Host "Installing Python backend packages from requirements.txt..."
    & $VenvPython -m pip install -r $ReqFile
} else {
    Write-Host "Warning: backend\requirements.txt not found." -ForegroundColor Yellow
}

# 4. Setup Next.js Frontend Packages
Write-Host "`n[Step 4/5] Installing Frontend Node.js Dependencies..." -ForegroundColor Yellow
$FrontendDir = Join-Path $ProjectRoot "frontend"
Push-Location $FrontendDir
try {
    if (Test-Path "package-lock.json") {
        Write-Host "Running npm ci..."
        & cmd.exe /c "npm ci"
    } else {
        Write-Host "Running npm install..."
        & cmd.exe /c "npm install"
    }

    Write-Host "Building Next.js production bundle..."
    & cmd.exe /c "npm run build"
} finally {
    Pop-Location
}

# 5. Done
Write-Host "`n[Step 5/5] Setup Complete!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " You can now start the software stack by running:         " -ForegroundColor Cyan
Write-Host "   .\scripts\start.ps1                                    " -ForegroundColor Yellow
Write-Host " To stop all services:                                    " -ForegroundColor Cyan
Write-Host "   .\scripts\stop.ps1                                     " -ForegroundColor Yellow
Write-Host "==========================================================`n" -ForegroundColor Cyan
