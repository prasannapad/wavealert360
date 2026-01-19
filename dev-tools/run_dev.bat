@echo off
echo 🖥️  WaveAlert360 - Development Mode
echo ====================================
echo Running main device logic without auto-updater
echo Press Ctrl+C to stop
echo.

cd device
..\\.venv\\Scripts\\python.exe main.py

echo.
echo Development session ended.
pause
