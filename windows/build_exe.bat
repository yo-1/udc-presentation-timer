@echo off
cd /d "%~dp0.."
powershell.exe -NoProfile -File windows\build_comparison.ps1 -Mode onedir
exit /b %errorlevel%
