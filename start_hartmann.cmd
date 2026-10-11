@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_frontend.ps1" -App hartmann
if errorlevel 1 pause
