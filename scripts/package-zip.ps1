# Project_A1 — Portable Distribution Packaging Script
# Creates a clean, reproducible ZIP archive excluding build caches, node_modules, and secrets.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$Timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$ZipDestination = Join-Path (Split-Path -Parent $ProjectRoot) "Project_A1_Portable_$Timestamp.zip"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Project_A1 Portable ZIP Archive Generator          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Directories and files to exclude from ZIP
$excludePatterns = @(
    "*\.venv*",
    "*\node_modules*",
    "*\.next*",
    "*\.pio*",
    "*\__pycache__*",
    "*\.git*",
    "*\.env",
    "*\scripts\.active_pids.json",
    "*\*.zip"
)

Write-Host "Target ZIP Path: $ZipDestination" -ForegroundColor Green
Write-Host "Filtering out virtualenvs, node_modules, build artifacts, and secrets..." -ForegroundColor Yellow

# Use .NET System.IO.Compression with exclusion filter
Add-Type -AssemblyName System.IO.Compression.FileSystem

$tempStaging = Join-Path $env:TEMP "Project_A1_Staging_$Timestamp"
if (Test-Path $tempStaging) { Remove-Item -Path $tempStaging -Recurse -Force }
New-Item -ItemType Directory -Path $tempStaging | Out-Null

$itemsToCopy = @(
    "backend",
    "frontend",
    "firmware",
    "firmware_builds",
    "Ardiuno_IDE_firmware",
    "ml",
    "reports",
    "tests",
    "scripts",
    ".env.example",
    "README.md",
    ".gitignore"
)

foreach ($item in $itemsToCopy) {
    $srcPath = Join-Path $ProjectRoot $item
    if (Test-Path $srcPath) {
        $destPath = Join-Path $tempStaging $item
        Write-Host "Copying $item..."
        if (Test-Path $srcPath -PathType Container) {
            # Use robocopy to mirror with exclusions
            & robocopy $srcPath $destPath /E /XD .venv node_modules .next .pio __pycache__ .git /XF .env .active_pids.json *.zip *.log /NFL /NDL /NJH /NJS | Out-Null
        } else {
            Copy-Item -Path $srcPath -Destination $destPath -Force
        }
    }
}

Write-Host "`nCompressing staging directory into ZIP..." -ForegroundColor Cyan
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempStaging, $ZipDestination, [System.IO.Compression.CompressionLevel]::Optimal, $false)

# Clean up staging
Remove-Item -Path $tempStaging -Recurse -Force

$zipFileInfo = Get-Item $ZipDestination
$zipSizeMb = [Math]::Round($zipFileInfo.Length / 1MB, 2)

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Portable ZIP successfully generated!                    " -ForegroundColor Green
Write-Host " - File: $ZipDestination ($zipSizeMb MB)                  " -ForegroundColor Green
Write-Host "==========================================================`n" -ForegroundColor Green
