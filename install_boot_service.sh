#!/bin/bash
# WaveAlert360 Boot Setup Script
# Installs systemd service to auto-start WaveAlert360 on boot

set -e

echo "🔧 Installing WaveAlert360 Boot Service..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo: sudo ./install_boot_service.sh"
    exit 1
fi

# Get the actual user (not root)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
else
    ACTUAL_USER="pi"
fi

echo "Installing service for user: $ACTUAL_USER"

# Copy service file to systemd
echo "📋 Copying service file..."
cp wavealert360-startup.service /etc/systemd/system/

# Update WorkingDirectory and ExecStart paths if not default
SERVICE_FILE="/etc/systemd/system/wavealert360-startup.service"
INSTALL_PATH="$(pwd)"

if [ "$INSTALL_PATH" != "/home/pi/WaveAlert360" ]; then
    echo "📝 Updating paths for installation at: $INSTALL_PATH"
    sed -i "s|/home/pi/WaveAlert360|$INSTALL_PATH|g" "$SERVICE_FILE"
fi

# Update user if not pi
if [ "$ACTUAL_USER" != "pi" ]; then
    echo "📝 Updating user to: $ACTUAL_USER"
    sed -i "s|User=pi|User=$ACTUAL_USER|g" "$SERVICE_FILE"
    sed -i "s|Group=pi|Group=$ACTUAL_USER|g" "$SERVICE_FILE"
fi

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "✅ Enabling service to start on boot..."
systemctl enable wavealert360-startup.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start wavealert360-startup"
echo "  Stop:    sudo systemctl stop wavealert360-startup"
echo "  Status:  sudo systemctl status wavealert360-startup"
echo "  Logs:    sudo journalctl -u wavealert360-startup -f"
echo "  Disable: sudo systemctl disable wavealert360-startup"
echo ""
echo "The service will now automatically start on system boot."
