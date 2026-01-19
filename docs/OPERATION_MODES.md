# WaveAlert360 Operation Modes

The WaveAlert360 system now supports two distinct operation modes for different use cases.

## 🌐 Dashboard Mode (Default)
**Usage:** `./restart_system.sh`

**Features:**
- Web dashboard accessible at `http://localhost:5000`
- Background operation with watchdog monitoring
- System status, GitHub sync info, and alert history
- Automatic restarts and updates
- Perfect for remote monitoring

**What happens:**
- Web server starts on port 5000
- Watchdog system monitors main.py
- System runs in background
- LED patterns still work but output not visible in terminal

## 🖥️ Console Mode
**Usage:** `./restart_system.sh --console`

**Features:**
- LED patterns displayed directly in terminal
- Real-time status messages
- Audio playback status
- API call logs
- Perfect for testing and debugging

**What you'll see:**
```
🔴🟡🟢 Console Mode: LED patterns and status will appear below
You'll see: [LED] messages, [AUDIO] messages, and [API] calls
Press Ctrl+C to stop

🌊 WaveAlert360 started at 2024-01-15 14:30:25

⏰ [Monday 01/15/24 02:30:25 PM] Running WaveAlert360 check...
🌐 [API] Calling: https://api.weather.gov/alerts/active?area=CA&region=coast
📍 [LOCATION] Monitoring: Morro Bay, CA (35.3669, -120.8507)

🟢🟢🟢 [LED] NORMAL
[AUDIO] Playing: normal_alert.mp3 (using mpg123)
```

## Quick Testing
For a single run test (no continuous monitoring):
```bash
cd device
python3 main.py
```

## Mode Comparison

| Feature | Dashboard Mode | Console Mode |
|---------|---------------|-------------|
| Web Interface | ✅ Available | ❌ Not running |
| LED Visibility | ❌ Background only | ✅ Terminal output |
| Continuous Operation | ✅ Watchdog managed | ✅ Direct execution |
| Remote Access | ✅ Web dashboard | ❌ SSH terminal only |
| Debugging | ❌ Limited visibility | ✅ Full output |
| Background Operation | ✅ Yes | ❌ Foreground only |

## System Requirements
- System-wide Python 3.11.2+ with all packages installed globally
- All dependencies in `requirements.txt` (including Flask for dashboard)
- Bluetooth audio configured (Anker SoundCore speaker recommended)
- Internet connectivity for NWS API access
