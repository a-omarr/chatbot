@echo off
setlocal

REM Simple dev script for Windows
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

endlocal
