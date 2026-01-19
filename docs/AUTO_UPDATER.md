# WaveAlert360 Auto-Updater System

## 🔄 Overview

The WaveAlert360 Auto-Updater is an evergreen deployment system that automatically keeps your beach safety device up-to-date with the latest code from GitHub. It ensures your coastal hazard detection system always has the newest features and security updates.

## ✨ Features

- **🕒 Continuous Monitoring**: Checks GitHub every 2 minutes for updates
- **🔄 Automatic Deployment**: Pulls and deploys updates automatically
- **🛡️ Safe Updates**: Creates backups before updating
- **🔄 Process Management**: Gracefully stops and restarts the main application
- **📊 Health Monitoring**: Monitors system health and process status
- **📝 Comprehensive Logging**: Detailed logs of all update activities
- **⚡ Zero-Downtime**: Minimizes service interruption during updates
- **🎯 Smart Detection**: Only updates when actual changes are detected

## 🏗️ Architecture

### Complete 3-Layer Process Hierarchy

```
┌─────────────────────┐    ┌─────────────────────────────────────────────┐
│   GitHub Repository │    │           Raspberry Pi Device               │
│  (prasannapad/      │    │                                             │
│   wavealert360)     │    │  ┌─────────────────────────────────────────┐ │
└──────────┬──────────┘    │  │        🐕 Watchdog Process             │ │
           │                │  │        (Layer 1 - Guardian)            │ │
           │ API calls      │  │  - Monitors auto-updater health         │ │
           ▼                │  │  - Restarts failed processes            │ │
┌─────────────────────┐    │  │  - 5-minute health checks               │ │
│   GitHub API        │◀───┼──│  - Process lock management              │ │
│   Commits Endpoint  │    │  └─────────────┬───────────────────────────┘ │
└─────────────────────┘    │                │ monitors & restarts          │
                           │                ▼                              │
                           │  ┌─────────────────────────────────────────┐ │
                           │  │      🔄 Auto-Updater Service           │ │
                           │  │      (Layer 2 - Deployment)            │ │
                           │  │  - Monitors GitHub every 2 minutes      │ │
                           │  │  - Pulls and deploys updates            │ │
                           │  │  - Manages main process lifecycle       │ │
                           │  │  - Creates backups and health files     │ │
                           │  └─────────────┬───────────────────────────┘ │
                           │                │ manages & restarts           │
                           │                ▼                              │
                           │  ┌─────────────────────────────────────────┐ │
                           │  │      🌊 WaveAlert360 Main Process      │ │
                           │  │      (Layer 3 - Core Function)         │ │
                           │  │  - NWS API monitoring                   │ │
                           │  │  - LED control and visual alerts        │ │
                           │  │  - Audio alert generation               │ │
                           │  │  - Coastal hazard detection             │ │
                           │  └─────────────────────────────────────────┘ │
                           └─────────────────────────────────────────────┘
```

### Process Relationships
- **🐕 Watchdog** monitors **🔄 Auto-Updater**, **🌊 Main Process**, **🌐 Web Dashboard**, and **💡 LED Service** (every 60 seconds)
- **🔄 Auto-Updater** manages **🌐 Web Dashboard** process
- **🔄 Auto-Updater** polls **GitHub** for updates (every 2 minutes)
- **🐕 Watchdog** restarts **🌊 Main Process** when new code is deployed

## 📦 Installation

### Prerequisites
- Raspberry Pi with Raspbian/Ubuntu
- Python 3.7+
- Git installed
- Internet connectivity
- sudo access

### Quick Install
```bash
# Download and run the installation script
curl -sSL https://raw.githubusercontent.com/prasannapad/wavealert360/main/scripts/install_auto_updater.sh | sudo bash
```

### Manual Installation
```bash
# 1. Clone the repository
cd ~
git clone https://github.com/prasannapad/wavealert360.git WaveAlert360

# 2. Install dependencies
cd ~/WaveAlert360
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 4. Set up watchdog to start on boot
# Add to /etc/rc.local or create systemd service as needed
```

## 🎛️ Configuration

### Auto-Updater Settings
Edit `auto_updater_config.py` to customize behavior:

```python
# Update frequency (seconds)
CHECK_INTERVAL = 120

# Enable/disable auto-updates
UPDATE_ENABLED = True

# Repository settings
REPO_OWNER = "prasannapad"
REPO_NAME = "wavealert360"
BRANCH = "main"
```

### Emergency Controls
Create these files to control the updater:

```bash
# Stop all automatic updates
touch ~/WaveAlert360/.emergency_stop

# Enable manual-only mode
touch ~/WaveAlert360/.manual_mode

# Remove files to resume automatic updates
rm ~/WaveAlert360/.emergency_stop
rm ~/WaveAlert360/.manual_mode
```

## 🔧 Management Commands

### Process Control
```bash
# Start the watchdog (which starts all processes)
cd ~/WaveAlert360/updater
python3 watchdog.py &

# Check running processes
ps aux | grep python

# View watchdog logs
tail -f ~/WaveAlert360/updater/logs/watchdog.log

# View auto-updater logs  
tail -f ~/WaveAlert360/updater/logs/auto_updater.log
```

### Monitoring
```bash
# Check system health
cd ~/WaveAlert360
python3 scripts/monitor_updater.py

# Get JSON status report
python3 scripts/monitor_updater.py --json

# View watchdog logs
tail -f ~/WaveAlert360/updater/logs/watchdog.log
```

## 📊 Monitoring & Logs

### Log Locations
- **Auto-updater logs**: `~/WaveAlert360/updater/logs/auto_updater.log`
- **Watchdog logs**: `~/WaveAlert360/updater/logs/watchdog.log`
- **Main process logs**: Check device/ directory output

### Health Monitoring
The system provides comprehensive health monitoring:

```bash
# Run health check
./scripts/monitor_updater.py

# Sample output:
🌊 WaveAlert360 Auto-Updater Status Report
==================================================
Generated: 2025-07-26 23:45:30

🔧 Service Status:
   ✅ Auto-updater service: running

🚀 Main Process Status:
   ✅ WaveAlert360 main: Running (1 processes)
   📊 PIDs: 1234

🔄 Update Status:
   ✅ Last update: 0.5 hours ago
   📝 Commit SHA: a1b2c3d4
   📅 Date: 2025-07-26T23:15:00

🌐 GitHub Connectivity:
   ✅ GitHub API: Accessible
   📝 Latest commit: a1b2c3d4
   📅 Commit date: 2025-07-26T23:15:00Z

🏥 Overall Health:
   ✅ System Health: Excellent (100%)
```

## 🔄 Update Process Flow

1. **📡 GitHub Check**: Auto-updater checks for new commits every 2 minutes
2. **🔍 Change Detection**: Compare local commit SHA with remote
3. **🛑 Process Stop**: Auto-updater stops web_status.py dashboard
4. **💾 Backup**: Create backup of current version using git archive
5. **📥 Pull Update**: Git pull latest changes from main branch (sparse checkout on Pi)
6. **📦 Dependencies**: Install any new Python dependencies
7. **💾 Save State**: Record new commit SHA in device/.last_commit
8. **🚀 Restart Dashboard**: Auto-updater restarts web_status.py with new code
9. **🔄 Watchdog Detects**: Watchdog detects code change and restarts main.py automatically
10. **✅ Verify**: All processes running with updated code

## 🛡️ Safety Features

### Backup System
- Automatic backups before each update
- Timestamped backup archives
- Quick rollback capability

### Error Handling
- Graceful failure recovery
- Automatic restart on process crashes
- Comprehensive error logging

### Update Validation
- Verify GitHub connectivity before updating
- Validate repository integrity
- Confirm successful process restart

## 🚨 Troubleshooting

### Common Issues

**Processes not starting:**
```bash
# Check if watchdog is running
ps aux | grep watchdog

# Check logs
tail -50 ~/WaveAlert360/updater/logs/watchdog.log
```

**Updates not working:**
```bash
# Check GitHub connectivity
curl -I https://api.github.com/repos/prasannapad/wavealert360

# Verify Git repository
cd ~/WaveAlert360
git status
git remote -v
```

**Main process not starting:**
```bash
# Check if script exists
ls -la ~/WaveAlert360/device/main.py

# Test manual start
cd ~/WaveAlert360/device
python3 main.py
```

### Emergency Procedures

**Stop everything immediately:**
```bash
# Kill watchdog (will stop monitoring)
pkill -f "watchdog.py"

# Kill all WaveAlert360 processes
pkill -f "auto_updater.py"
pkill -f "main.py"
pkill -f "web_status.py"
```

**Manual update:**
```bash
cd ~/WaveAlert360
git pull origin main
# Watchdog will auto-restart processes
```

**Reset to fresh state:**
```bash
cd ~/WaveAlert360
git reset --hard origin/main
# Kill and restart watchdog to reload everything
```

## 📈 Performance Impact

- **CPU Usage**: Minimal (~1-2% during checks)
- **Memory Usage**: ~50MB for auto-updater process
- **Network Usage**: ~10KB per check (every 2 minutes)
- **Storage**: Log rotation keeps disk usage minimal

## 🔒 Security Considerations

- Repository access via HTTPS (no SSH keys needed)
- Read-only access to GitHub repository
- Secure process management
- Log sanitization (no sensitive data in logs)

## 🎯 Future Enhancements

- [ ] Blue-green deployment support
- [ ] Staged rollout capabilities
- [ ] Health check integration
- [ ] Slack/email notifications
- [ ] Update scheduling windows
- [ ] A/B testing support

---

## 📞 Support

For issues with the auto-updater system:

1. Check the logs: `journalctl -u wavealert360-updater`
2. Run health check: `./scripts/monitor_updater.py`
3. Review troubleshooting section above
4. Create an issue on GitHub

The auto-updater ensures your WaveAlert360 system stays current with the latest safety features and improvements! 🌊✨
