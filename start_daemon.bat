@echo off
cd /d "%~dp0"
echo 👻 Starting P.DE.I Daemon...
python pdei_core/setup.py repair

set "PERSONA_ARGS="
for %%f in (personalities\*.json) do (
    if /I not "%%~nxf"=="template.json" (
        set "PERSONA_ARGS=--personality "%%~ff""
        echo 🧠 Found Personality: %%~nxf
        goto :found
    )
)
:found

echo 🌍 Opening Web Interface...
start http://localhost:8000/web
python main.py --server %PERSONA_ARGS%
pause