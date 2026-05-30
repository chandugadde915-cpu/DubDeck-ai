@echo off
cd /d "%~dp0"
echo Starting DubDeck AI...
where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON_CMD=py
) else (
  set PYTHON_CMD=python
)
if not exist ".venv" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
set TORCH_HOME=%cd%\temp\cache\torch
set XDG_CACHE_HOME=%cd%\temp\cache
set PYTHONPYCACHEPREFIX=%cd%\temp\cache\pycache
.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto error
pause
exit /b 0
:error
echo.
echo DubDeck AI could not start. Check Python, FFmpeg, and internet access for first-time package installation.
pause
exit /b 1
