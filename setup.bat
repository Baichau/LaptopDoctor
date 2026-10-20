@echo off
set PY=py
where py >nul 2>nul || set PY=python
%PY% -m venv .venv || (echo Python not found. Install it from python.org with "Add to PATH" ticked. & pause & exit /b 1)
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
echo.
echo Setup done. Open this folder in VS Code and press F5, or run build.bat.
pause
