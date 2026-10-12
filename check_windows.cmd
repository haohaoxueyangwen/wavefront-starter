@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if not exist "%~dp0runtime\python\python.exe" (
  echo Please download the windows-x64.zip complete release and extract all files.
  pause
  exit /b 1
)
"%~dp0runtime\python\python.exe" -B "%~dp0scripts\check_windows.py"
pause
