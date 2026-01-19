#!/bin/bash
# WaveAlert360 System Restart Script for Raspberry Pi
# ===================================================
# Usage:
#   ./restart_system.sh           - Normal background mode (production)
#   ./restart_system.sh --console - Console mode with LED output (testing)

# Check for console mode parameter
CONSOLE_MODE=false
if [ "$1" = "--console" ] || [ "$1" = "-c" ]; then
    CONSOLE_MODE=true
    echo "🖥️  Console mode enabled - LED output will be visible"
    echo ""
fi

echo "🛑 Stopping WaveAlert360 System..."

# Stop processes by name and command line (more thorough cleanup with sudo)
echo "Stopping main.py processes..."
sudo pkill -f "python.*main.py" 2>/dev/null || echo "   No main.py processes found"
sudo pkill -f "main.py" 2>/dev/null || true  # Catch any remaining

echo "Stopping auto_updater.py processes..."
sudo pkill -f "python.*auto_updater.py" 2>/dev/null || echo "   No auto_updater.py processes found"
sudo pkill -f "auto_updater.py" 2>/dev/null || true

echo "Stopping watchdog.py processes..."
sudo pkill -f "python.*watchdog.py" 2>/dev/null || echo "   No watchdog.py processes found"
sudo pkill -f "watchdog.py" 2>/dev/null || true

echo "Stopping led_failsafe_manager.py processes..."
sudo pkill -f "python.*led_failsafe_manager.py" 2>/dev/null || echo "   No led_failsafe_manager.py processes found"
sudo pkill -f "led_failsafe_manager.py" 2>/dev/null || true

echo "Stopping web_status.py processes..."
sudo pkill -f "python.*web_status.py" 2>/dev/null || echo "   No web_status.py processes found"
sudo pkill -f "web_status.py" 2>/dev/null || true

# Force kill any stubborn WaveAlert360 processes
echo "🔨 Force stopping any remaining WaveAlert360 processes..."
sudo pkill -9 -f "WaveAlert360" 2>/dev/null || true
sudo pkill -9 -f "wavealert360" 2>/dev/null || true

# Wait for processes to stop
sleep 3

echo "🧹 Cleaning lock files..."
rm -f .*.lock 2>/dev/null || true
rm -f device/.main.pid 2>/dev/null || true  # Clean up main.py PID file
rm -f updater/.updater.pid 2>/dev/null || true  # Clean up auto-updater PID file
rm -f /tmp/led_service.lock 2>/dev/null || true  # Clean up LED service lock

echo ""
echo "🚀 Starting WaveAlert360 System..."
echo "This will show the enhanced GitHub information including:"
echo "   - Commit SHA and author"
echo "   - Commit date and message"
echo "   - Last sync time"
echo ""

# Change to the script directory
cd "$(dirname "$0")"

# Pull latest code from GitHub
echo "📥 Pulling latest code from GitHub..."
git pull origin main || echo "   Warning: Git pull failed, continuing with local code"
echo ""

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source .venv/bin/activate
elif [ -d "/opt/wavealert360/.venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source /opt/wavealert360/.venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Install/update dependencies
echo "📦 Using pre-installed system packages (no installation at startup for safety)"

# NOTE: LED and web services are started by watchdog, not here
# This prevents duplicate processes and lock file conflicts
echo "Services will be started by watchdog..."

if [ "$CONSOLE_MODE" = true ]; then
    echo "🖥️  Console Mode: Starting full system with visible output"
    echo "   LED output will be visible via watchdog → auto_updater → main.py chain"
    echo "   Press Ctrl+C to stop"
    echo ""
fi

echo "Starting watchdog system..."
echo "Press Ctrl+C to stop the system"
echo ""

cd updater
python3 watchdog.py

echo ""
echo "🛑 System stopped - cleaning up background processes..."

# Watchdog handles all service cleanup, just clean up any stragglers
sudo pkill -f led_failsafe_manager.py 2>/dev/null || true
sudo pkill -f web_status.py 2>/dev/null || true

echo "✅ Cleanup complete"
