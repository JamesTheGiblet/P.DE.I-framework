Write-Host "👻 Starting P.DE.I Daemon..."
python "$PSScriptRoot\pdei_core\setup.py" repair

# Detect Personality (Auto-select first non-template JSON)
$personalitiesPath = Join-Path $PSScriptRoot "personalities"
$persona = Get-ChildItem "$personalitiesPath\*.json" | Where-Object { $_.Name -ne "template.json" } | Select-Object -First 1
$personaArgs = @()
if ($persona) {
    Write-Host "🧠 Found Personality: $($persona.Name)" -ForegroundColor Cyan
    $personaArgs = @("--personality", $persona.FullName)
}

Write-Host "🌍 Opening Web Interface..."
Start-Process "http://localhost:8000/web"
python "$PSScriptRoot\main.py" --server $personaArgs
Read-Host -Prompt "Press Enter to exit"