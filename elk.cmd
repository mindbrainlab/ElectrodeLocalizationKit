@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
uv run python src/main.py
