# expert_sync.ps1
# P.DDE.I Framework - Master Synchronization & Deployment Utility
# Purpose: Packages the VS Code extension and restarts the Exocortex Daemon.

$ErrorActionPreference = "Stop"

Write-Host "Starting Master Sync: VS Code Extension -> Exocortex Core" -ForegroundColor Cyan

# --- Phase I: VS Code Extension Packaging ---
$extPath = "integrations\vscode-pdei"
Write-Host "Phase I: Packaging Extension..." -ForegroundColor Yellow

# Ensure media assets are in the correct location
if (-not (Test-Path "$extPath\media")) {
    New-Item -ItemType Directory -Path "$extPath\media" -Force | Out-Null
}

# 1. Generate SVG (Best for Sidebar UI)
if (-not (Test-Path "$extPath\media\icon.svg")) {
    Write-Host "🎨 Generating default SVG icon..."
    Set-Content -Path "$extPath\media\icon.svg" -Value '<svg width="200" height="200" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="45" stroke="#cccccc" stroke-width="5" fill="none" /><circle cx="50" cy="50" r="20" fill="#007acc" /></svg>'
}

# 2. Generate PNG (Required for .vsix Package)
if (-not (Test-Path "$extPath\media\icon.png")) {
    Write-Host "🎨 Generating default PNG icon..."
    try {
        Add-Type -AssemblyName System.Drawing
        $bmp = New-Object System.Drawing.Bitmap 512, 512
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.Clear([System.Drawing.Color]::Transparent)
        $brush = [System.Drawing.Brushes]::CornflowerBlue
        $g.FillEllipse($brush, 40, 40, 432, 432)
        $bmp.Save("$extPath\media\icon.png", [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose(); $bmp.Dispose()
    } catch {
        Write-Warning "⚠️ Failed to auto-generate PNG. Please add 'media/icon.png' manually."
    }
}

# --- Sync Icon to Core Server ---
$coreIconsPath = "pdei_core\icons"
if (-not (Test-Path $coreIconsPath)) {
    New-Item -ItemType Directory -Path $coreIconsPath -Force | Out-Null
}
if (Test-Path "$extPath\media\icon.png") {
    Copy-Item "$extPath\media\icon.png" "$coreIconsPath\icon.png" -Force
}

if (Test-Path "$extPath\*.vsix") {
    Remove-Item "$extPath\*.vsix" -Force
}

Set-Location $extPath
# Ensure dependencies are present for the build
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing extension dependencies..."
    npm install
}

# Package the extension (Requires 'vsce' installed: npm install -g @vscode/vsce)
vsce package --out pdei-latest.vsix

# Install natively to your local VS Code instance
Write-Host "Installing extension to VS Code..."
code --install-extension pdei-latest.vsix --force
Set-Location ..\..

# --- Phase II: Server Reset & Neural Link Refresh ---
Write-Host "Phase II: Resetting Exocortex Daemon..." -ForegroundColor Yellow

# Safely terminate existing processes to prevent Port 8000 collisions
$pdeiProcesses = Get-CimInstance Win32_Process | Where-Object { $_.Name -match "python|uvicorn" -and $_.CommandLine -match "main.py" }
if ($pdeiProcesses) {
    Write-Host "Stopping active Exocortex instances..."
    $pdeiProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Start-Sleep -Seconds 2
}

# --- Phase III: Deployment ---
Write-Host "Initializing Neural Link..." -ForegroundColor Green
Write-Host "⚠️  Ensure Ollama is running! (main.py will exit if it's offline)" -ForegroundColor Yellow

# Detect Personality (Auto-select first non-template JSON)
$persona = Get-ChildItem "personalities\*.json" | Where-Object { $_.Name -ne "template.json" } | Select-Object -First 1
$personaArg = ""
if ($persona) {
    Write-Host "🧠 Found Personality: $($persona.Name)" -ForegroundColor Cyan
    $personaArg = "--personality `"$($persona.FullName)`""
}

# Launch the server with Tailscale detection enabled
# The --server flag triggers the FastAPI/Uvicorn runtime in main.py
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py --server $personaArg"

# Launch the CLI Interface in a separate window
Write-Host "Launching CLI Interface..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py $personaArg"

Write-Host "Master Sync Complete." -ForegroundColor Cyan
Write-Host "Monitor the new terminal for your Tailscale IP and QR code."