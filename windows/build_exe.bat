@echo off
cd /d "%~dp0.."
py -m pip install -r windows\requirements-build.txt
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "PresentationTimer" --add-data "assets\bell.mp3;assets" windows\udc_timer.py
pause
