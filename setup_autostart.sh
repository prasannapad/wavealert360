#!/bin/bash
# WaveAlert360 Cron-based Auto-start Setup
# Simple and reliable alternative to systemd

set -e

echo "🔧 Setting up WaveAlert360 Auto-start with Cron..."

# Get the installation directory
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installation directory: $INSTALL_DIR"

# Create cron job entry
CRON_ENTRY="@reboot sleep 30 && cd $INSTALL_DIR && /bin/bash $INSTALL_DIR/restart_system.sh >> /tmp/wavealert_boot.log 2>&1"

# Check if entry already exists
if crontab -l 2>/dev/null | grep -q "restart_system.sh"; then
    echo "⚠️  Cron entry already exists, updating..."
    # Remove old entry and add new one
    (crontab -l 2>/dev/null | grep -v "restart_system.sh"; echo "$CRON_ENTRY") | crontab -
else
    echo "➕ Adding new cron entry..."
    # Add new entry to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
fi

echo ""
echo "✅ Auto-start configured successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep wavealert -i || echo "(No WaveAlert entries found)"
echo ""
echo "The system will automatically start 30 seconds after boot."
echo ""
echo "To view boot logs:    tail -f /tmp/wavealert_boot.log"
echo "To remove auto-start: crontab -e (then delete the WaveAlert360 line)"
