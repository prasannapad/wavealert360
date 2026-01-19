#!/bin/bash
# WaveAlert360 Boot Startup Script - Non-interactive for cron/systemd
# This version is optimized for automated startup without user interaction

# Absolute paths
INSTALL_DIR="/home/pi/WaveAlert360"
VENV_PYTHON="$INSTALL_DIR/.venv/bin/python3"
LOG_FILE="/tmp/wavealert_boot.log"

# Redirect all output to log file
exec >> "$LOG_FILE" 2>&1

echo "=================================="
echo "WaveAlert360 Boot Startup"
echo "$(date)"
echo "=================================="

# Change to installation directory
cd "$INSTALL_DIR" || exit 1

# Kill any existing processes
echo "Cleaning up any existing processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*auto_updater.py" 2>/dev/null || true
pkill -f "python.*watchdog.py" 2>/dev/null || true
sleep 2

# Clean lock files
rm -f .*.lock device/.main.pid updater/.updater.pid /tmp/led_service.lock 2>/dev/null || true

# Pull latest code
echo "Pulling latest code from GitHub..."
git pull origin main || echo "Warning: git pull failed, using local code"

# Start watchdog in background (which starts everything else)
echo "Starting WaveAlert360 system via watchdog..."
cd "$INSTALL_DIR/updater"

# Start watchdog in background with nohup
nohup "$VENV_PYTHON" watchdog.py >> "$LOG_FILE" 2>&1 &
WATCHDOG_PID=$!

echo "Started watchdog with PID: $WATCHDOG_PID"
echo "Boot startup complete at $(date)"
echo "=================================="

# Give it a moment to start
sleep 5

# Verify processes started
echo "Checking processes..."
ps aux | grep -E 'main.py|watchdog|auto_updater' | grep -v grep || echo "Warning: No processes found yet"

exit 0
