@echo off
cd /d "%~dp0.."
if exist ".venv-audio\Scripts\python.exe" (
    ".venv-audio\Scripts\python.exe" "DEMO\visual_reference_demo.py"
) else (
    python "DEMO\visual_reference_demo.py"
)
