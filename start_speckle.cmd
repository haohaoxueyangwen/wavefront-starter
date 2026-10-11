@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_frontend.ps1" -App speckle
if errorlevel 1 pause
