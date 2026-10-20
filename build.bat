@echo off
if not exist .venv\Scripts\python.exe (echo Run setup.bat first. & pause & exit /b 1)
set MODE=--onefile
if "%1"=="folder" set MODE=--onedir
.venv\Scripts\python -m PyInstaller --noconfirm --clean --noconsole %MODE% --name LaptopDoctor --add-data "laptop_doctor\web;laptop_doctor\web" --collect-all webview main.py
echo.
echo Built: dist\LaptopDoctor.exe   (or dist\LaptopDoctor\LaptopDoctor.exe when run as: build.bat folder)
pause
