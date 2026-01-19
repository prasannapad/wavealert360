# WaveAlert360 Process Monitoring Architecture

## Overview

The WaveAlert360 system uses a **two-layer resilience architecture** for process monitoring and automatic recovery.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    WATCHDOG.PY                          │
│              (Process Health Monitor)                   │
│                                                         │
│  Monitors every 60 seconds:                            │
│  ├── 🔄 auto_updater.py  (Code updates)               │
│  ├── 🚨 main.py          (Alert monitoring)           │
│  ├── 🌐 web_status.py    (Dashboard)                  │
│  └── 💡 led_failsafe_manager.py (Hardware control)   │
│                                                         │
│  Restart Limits: 5 attempts per 10 minutes            │
└─────────────────────────────────────────────────────────┘
                           │
                           │ starts and monitors
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 AUTO_UPDATER.PY                         │
│              (GitHub Update Manager)                    │
│                                                         │
│  Checks GitHub every 120 seconds:                      │
│  ├── Detect new commits                               │
│  ├── Pull latest code                                 │
│  ├── Restart web dashboard during updates            │
│  └── Let watchdog handle main.py restart             │
└─────────────────────────────────────────────────────────┘
```

## Process Responsibilities

### Watchdog (watchdog.py)
**Primary Job:** Keep all critical processes alive

**Monitors:**
- ✅ `auto_updater.py` - Code update manager
- ✅ `main.py` - Core alert monitoring system
- ✅ `web_status.py` - Web dashboard (port 5000)
- ✅ `led_failsafe_manager.py` - GPIO LED controller

**Restart Policy:**
- Check interval: 60 seconds
- Max restarts: 5 per process
- Cooldown: 10 minutes between restart cycles
- Independent tracking per process

**Started by:** `restart_system.sh`

### Auto-Updater (auto_updater.py)
**Primary Job:** Keep code up-to-date with GitHub

**Responsibilities:**
- ✅ Monitor GitHub for new commits (every 120 seconds)
- ✅ Pull latest code when changes detected
- ✅ Manage web dashboard restarts during updates
- ❌ NO LONGER monitors main.py (delegated to watchdog)

**Restart Policy:**
- Automatically restarted by watchdog if it crashes
- Manages its own update cycle

**Started by:** Watchdog

### Main Process (main.py)
**Primary Job:** Alert monitoring and hardware control

**Responsibilities:**
- ✅ Query Azure service every 30 seconds
- ✅ Fallback to direct NWS API if Azure unavailable
- ✅ Control LEDs and play audio
- ✅ Maintain system state

**Restart Policy:**
- Automatically restarted by watchdog if it crashes
- No restart limit (watchdog handles this)

**Started by:** Watchdog

### Web Dashboard (web_status.py)
**Primary Job:** Provide web UI for system status

**Responsibilities:**
- ✅ Flask server on port 5000
- ✅ Display alert status and system info
- ✅ Show NWS data and reference alerts

**Restart Policy:**
- Automatically restarted by watchdog if it crashes
- Also restarted by auto_updater during code updates

**Started by:** Watchdog (and auto_updater during updates)

### LED Service (led_failsafe_manager.py)
**Primary Job:** Manage GPIO LED hardware

**Responsibilities:**
- ✅ Monitor `/tmp/led_control_signal` file
- ✅ Control GPIO pins (requires sudo)
- ✅ Implement LED patterns and failsafe

**Restart Policy:**
- Automatically restarted by watchdog if it crashes
- Runs with sudo privileges

**Started by:** Watchdog

## Separation of Concerns

### Before Refactoring (OLD - Incorrect)
```
watchdog.py → monitors auto_updater.py
auto_updater.py → monitors main.py ❌ WRONG LAYER
main.py, web_status.py, LED service → NO MONITORING ❌ GAP
```

### After Refactoring (NEW - Correct)
```
watchdog.py → monitors ALL processes ✅ CORRECT
  ├── auto_updater.py (focuses on updates only)
  ├── main.py (alert monitoring)
  ├── web_status.py (dashboard)
  └── led_failsafe_manager.py (hardware)
```

## Benefits of New Architecture

1. **Single Responsibility Principle**
   - Watchdog = Process health
   - Auto-updater = Code updates
   - Each component has one clear job

2. **Complete Coverage**
   - ALL critical processes monitored
   - No gaps in resilience
   - LED and web dashboard now auto-restart

3. **Better Resilience**
   - Independent restart tracking per process
   - One guardian watching everything
   - Simpler debugging (one place to check)

4. **Cleaner Code**
   - Auto-updater simplified
   - No dual responsibility
   - Easier to maintain

## Startup Sequence

1. User runs `./restart_system.sh`
2. Script starts `watchdog.py`
3. Watchdog starts (in order):
   - LED service (hardware layer)
   - Main.py (core logic)
   - Web dashboard (UI layer)
   - Auto-updater (management layer)
4. Watchdog enters monitoring loop (60s checks)
5. Auto-updater enters update loop (120s checks)

## Failure Recovery Examples

### Scenario 1: Main.py Crashes
```
1. Main.py crashes (e.g., unhandled exception)
2. Watchdog detects on next check (within 60s)
3. Watchdog logs: "❌ Main process has stopped!"
4. Watchdog calls restart_process('main', start_main)
5. Main.py restarted within 2-5 seconds
6. System resumes alert monitoring
7. Restart count incremented (max 5 per 10 min)
```

### Scenario 2: Web Dashboard Crashes
```
1. Web dashboard crashes (e.g., Flask error)
2. Watchdog detects on next check (within 60s)
3. Watchdog logs: "❌ Web dashboard has stopped!"
4. Watchdog restarts web_status.py
5. Dashboard available within seconds
6. No impact to alert monitoring (main.py unaffected)
```

### Scenario 3: LED Service Crashes
```
1. LED service crashes (e.g., GPIO permission error)
2. Watchdog detects on next check (within 60s)
3. Watchdog logs: "❌ LED service has stopped!"
4. Watchdog restarts with sudo privileges
5. LEDs resume normal operation
6. Hardware control restored
```

### Scenario 4: Auto-Updater Crashes
```
1. Auto-updater crashes (e.g., network error during update)
2. Watchdog detects on next check (within 60s)
3. Watchdog logs: "❌ Auto-updater has stopped!"
4. Watchdog restarts auto_updater.py
5. Update cycle resumes
6. All other processes continue unaffected
```

### Scenario 5: Too Many Restarts
```
1. Process crashes repeatedly (5 times in 10 minutes)
2. Watchdog logs: "❌ Too many restart attempts (5), waiting for cooldown"
3. Watchdog stops restart attempts for this process
4. Other processes continue running
5. After 10-minute cooldown, restart counter resets
6. Watchdog resumes restart attempts if needed
```

## Monitoring and Debugging

### Check Watchdog Status
```bash
# View watchdog log
tail -f /home/pi/WaveAlert360/updater/logs/watchdog.log

# Check if watchdog is running
ps aux | grep watchdog.py

# Check all process PIDs
ps aux | grep python
```

### Status Banner Example
```
🐕==================================================================🐕
🐕 WAVEALERT360 WATCHDOG STATUS
   🔄 Auto-updater:  ✅ Running (restarts: 0)
   🚨 Main process:  ✅ Running (restarts: 1)
   🌐 Web dashboard: ✅ Running (restarts: 0)
   💡 LED service:   ✅ Running (restarts: 0)
   🕒 Check time: 10/21/25 09:45:30 PM
🐕==================================================================🐕
```

### Manual Restart
```bash
# Stop all processes
sudo pkill -f "wavealert360"

# Start watchdog (which starts everything else)
cd /home/pi/WaveAlert360
./restart_system.sh
```

## Configuration

### Watchdog Settings
Located in `updater/watchdog.py`:
```python
WATCHDOG_INTERVAL = 60  # Check every 60 seconds
MAX_RESTART_ATTEMPTS = 5  # Per process
RESTART_COOLDOWN = 600  # 10 minutes in seconds
```

### Auto-Updater Settings
Located in `device/settings.json` under `auto_updater`:
```json
"update_settings": {
  "check_interval": 120,  // 2 minutes
  "enabled": true,
  "backup_enabled": true
}
```

## Lock Files

The system uses lock files to prevent duplicate instances:

- `.watchdog.lock` - Ensures single watchdog instance
- `.auto_updater.lock` - Ensures single auto-updater instance
- `/tmp/led_service.lock` - Ensures single LED service instance

These are automatically cleaned by `restart_system.sh`.

## Future Enhancements

Possible improvements:
1. ✅ **Health checks** - Verify processes are actually working (not just running)
2. ✅ **Restart cooldown** - Already implemented (10 min)
3. ⏳ **Email alerts** - Notify on repeated failures
4. ⏳ **Metrics collection** - Track uptime, restart frequency
5. ⏳ **Systemd integration** - Auto-start on boot (currently manual)

## Migration Notes

**When upgrading from old architecture:**
1. Pull latest code from GitHub
2. Run `./restart_system.sh`
3. Watchdog will start with new monitoring capabilities
4. All processes will be under watchdog supervision
5. Auto-updater will continue update cycle (but without process monitoring burden)

**No configuration changes required** - the refactoring is transparent to users.
