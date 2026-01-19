#!/usr/bin/env python3
"""
LED Service Manager - Three-Strip Beach Sign Version
===================================================
Controls 3 independent LED strips for beach alert system:
- Strip 1 (GPIO 18): RED/DANGER alerts (48 LEDs)
- Strip 2 (GPIO 21): YELLOW/CAUTION alerts (48 LEDs)
- Strip 3 (GPIO 12): GREEN/SAFE alerts (48 LEDs) - FUTURE

Only ONE strip blinks at a time based on alert level.
"""

import os
import sys
import time
import signal
import fcntl
import atexit
from datetime import datetime

try:
    from rpi_ws281x import PixelStrip, Color, ws
    HARDWARE_AVAILABLE = True
except Exception as e:
    HARDWARE_AVAILABLE = False
    with open('/tmp/led_import_error.txt', 'w') as f:
        f.write(f"Import failed: {e}\n")
        import traceback
        traceback.print_exc(file=f)
    print(f"WARNING: LED hardware not available - {e}")
    class Color:
        def __init__(self, r, g, b): self.r, self.g, self.b = r, g, b
    class PixelStrip:
        def __init__(self, *args, **kwargs): pass
        def begin(self): pass
        def numPixels(self): return 48
        def setPixelColor(self, i, color): pass
        def show(self): pass

# LED Strip Configuration
LED_COUNT = 48  # Each strip has 48 LEDs

# Strip 1: RED/DANGER (GPIO 18)
RED_STRIP_PIN = 18
RED_STRIP_CHANNEL = 0

# Strip 2: YELLOW/CAUTION (GPIO 21) 
YELLOW_STRIP_PIN = 21
YELLOW_STRIP_CHANNEL = 0  # Same channel OK for different GPIOs

# Strip 3: GREEN/SAFE (GPIO 12) - FUTURE
GREEN_STRIP_PIN = 13
GREEN_STRIP_CHANNEL = 1  # Different channel from red/yellow (which use 0)
GREEN_STRIP_ENABLED = True  # Set to True when third strip is installed

# Common LED Settings
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 65
LED_INVERT = False

# Control Files
LOCK_FILE = "/tmp/led_service.lock"
CONTROL_FILE = "/tmp/led_control_signal"
STATUS_FILE = "/tmp/led_service_status"

# Colors
COLORS = {
    'OFF': Color(0, 0, 0),
    'RED': Color(255, 0, 0),         # Danger
    'YELLOW': Color(255, 100, 0),    # Caution
    'GREEN': Color(0, 255, 0),       # Safe
}

class ProcessLock:
    """File-based process lock to prevent duplicate instances"""
    
    def __init__(self, lockfile):
        self.lockfile = lockfile
        self.lock = None

    def acquire(self):
        """Acquire exclusive lock - returns True if successful"""
        try:
            self.lock = open(self.lockfile, 'w')
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock.write(f"{os.getpid()}\n{datetime.now().isoformat()}\n")
            self.lock.flush()
            return True
        except (IOError, OSError):
            if self.lock:
                self.lock.close()
                self.lock = None
            return False

    def release(self):
        """Release lock"""
        if self.lock:
            try:
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
                self.lock.close()
                os.unlink(self.lockfile)
            except:
                pass
            self.lock = None

class BeachSignLEDManager:
    """Three-strip LED manager for beach alert sign"""

    def __init__(self):
        self.running = True
        self.red_strip = None
        self.yellow_strip = None
        self.green_strip = None
        self.hardware_available = HARDWARE_AVAILABLE

        # CRITICAL: Acquire process lock first
        self.process_lock = ProcessLock(LOCK_FILE)
        if not self.process_lock.acquire():
            print("❌ Another LED service is running - cannot start")
            print("   Use: sudo pkill -f led_failsafe_manager to stop existing service")
            sys.exit(1)

        print("✅ Process lock acquired - starting Beach Sign LED service")
        
        # Initialize hardware strips
        if self.hardware_available:
            try:
                strip_type = getattr(ws, 'WS2811_STRIP_GRB', None)
                
                # Initialize RED strip (GPIO 18)
                self.red_strip = PixelStrip(LED_COUNT, RED_STRIP_PIN, LED_FREQ_HZ, LED_DMA,
                                           LED_INVERT, LED_BRIGHTNESS, RED_STRIP_CHANNEL, strip_type)
                self.red_strip.begin()
                print(f"✅ RED strip initialized (GPIO {RED_STRIP_PIN}, {LED_COUNT} LEDs)")
                
                # Initialize YELLOW strip (GPIO 21)
                self.yellow_strip = PixelStrip(LED_COUNT, YELLOW_STRIP_PIN, LED_FREQ_HZ, LED_DMA,
                                              LED_INVERT, LED_BRIGHTNESS, YELLOW_STRIP_CHANNEL, strip_type)
                self.yellow_strip.begin()
                print(f"✅ YELLOW strip initialized (GPIO {YELLOW_STRIP_PIN}, {LED_COUNT} LEDs)")
                
                # Initialize GREEN strip (GPIO 12) - FUTURE
                if GREEN_STRIP_ENABLED:
                    self.green_strip = PixelStrip(LED_COUNT, GREEN_STRIP_PIN, LED_FREQ_HZ, LED_DMA,
                                                 LED_INVERT, LED_BRIGHTNESS, GREEN_STRIP_CHANNEL, strip_type)
                    self.green_strip.begin()
                    print(f"✅ GREEN strip initialized (GPIO {GREEN_STRIP_PIN}, {LED_COUNT} LEDs)")
                
                # Turn off all LEDs on startup
                self.set_strip_color(self.red_strip, COLORS['OFF'])
                self.set_strip_color(self.yellow_strip, COLORS['OFF'])
                if GREEN_STRIP_ENABLED and self.green_strip:
                    self.set_strip_color(self.green_strip, COLORS['OFF'])
                
                time.sleep(0.5)
                print("✅ All LED strips initialized and cleared")
                
            except Exception as e:
                print(f"❌ LED hardware init failed: {e}")
                import traceback
                traceback.print_exc()
                with open('/tmp/led_init_error.txt', 'w') as f:
                    f.write(f"LED initialization failed: {e}\n\n")
                    traceback.print_exc(file=f)
                self.hardware_available = False

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        atexit.register(self.cleanup)

    def set_strip_color(self, strip, color):
        """Set all LEDs on a strip to specified color"""
        if self.hardware_available and strip:
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, color)
            strip.show()

    def turn_off_all_strips(self):
        """Turn off all LED strips"""
        if self.hardware_available:
            self.set_strip_color(self.red_strip, COLORS['OFF'])
            self.set_strip_color(self.yellow_strip, COLORS['OFF'])
            if GREEN_STRIP_ENABLED and self.green_strip:
                self.set_strip_color(self.green_strip, COLORS['OFF'])
        else:
            print("🔌 [SIMULATION] All strips: OFF")

    def get_alert_level(self):
        """Determine current alert level from control file"""
        try:
            if os.path.exists(CONTROL_FILE):
                with open(CONTROL_FILE, 'r') as f:
                    control_mode = f.read().strip()
                
                # Parse control modes
                if control_mode == "MAIN_ACTIVE":
                    return "QUIET"
                elif control_mode.startswith("PATTERN:"):
                    pattern = control_mode.split(":", 1)[1]
                    if "RED" in pattern.upper():
                        return "DANGER"
                    elif "YELLOW" in pattern.upper():
                        return "CAUTION"
                    elif "GREEN" in pattern.upper():
                        return "SAFE"
                    elif pattern == "RED_BLINK":
                        return "DANGER"
                    elif pattern == "YELLOW":
                        return "CAUTION"
                    elif pattern == "GREEN":
                        return "SAFE"
                        
                return "FAILSAFE"
        except:
            return "FAILSAFE"

    def update_status(self, level):
        """Update service status file"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'alert_level': level,
                'pid': os.getpid(),
                'hardware': self.hardware_available,
                'strips': {
                    'red': f'GPIO {RED_STRIP_PIN}',
                    'yellow': f'GPIO {YELLOW_STRIP_PIN}',
                    'green': f'GPIO {GREEN_STRIP_PIN}' if GREEN_STRIP_ENABLED else 'Not installed'
                }
            }
            with open(STATUS_FILE, 'w') as f:
                import json
                json.dump(status, f)
        except:
            pass

    def run_alert_pattern(self, level):
        """Execute LED pattern based on alert level - only ONE strip active"""
        
        if level == "DANGER":
            # RED strip blinks - others OFF
            if self.hardware_available:
                # Blink 10 times before checking alert level again
                for cycle in range(10):
                    self.set_strip_color(self.yellow_strip, COLORS['OFF'])
                    if GREEN_STRIP_ENABLED and self.green_strip:
                        self.set_strip_color(self.green_strip, COLORS['OFF'])
                    
                    self.set_strip_color(self.red_strip, COLORS['RED'])
                    time.sleep(0.5)
                    self.set_strip_color(self.red_strip, COLORS['OFF'])
                    time.sleep(0.5)
            else:
                print("🔴 [SIMULATION] RED strip: BLINKING (Danger)")
                time.sleep(1.0)

        elif level == "CAUTION":
            # YELLOW strip blinks - others OFF
            if self.hardware_available:
                # Blink 10 times before checking alert level again
                for cycle in range(10):
                    self.set_strip_color(self.red_strip, COLORS['OFF'])
                    if GREEN_STRIP_ENABLED and self.green_strip:
                        self.set_strip_color(self.green_strip, COLORS['OFF'])
                    
                    self.set_strip_color(self.yellow_strip, COLORS['YELLOW'])
                    time.sleep(0.5)
                    self.set_strip_color(self.yellow_strip, COLORS['OFF'])
                    time.sleep(0.5)
            else:
                print("🟡 [SIMULATION] YELLOW strip: BLINKING (Caution)")
                time.sleep(1.0)

        elif level == "SAFE":
            # GREEN strip blinks - others OFF
            if self.hardware_available:
                # Blink 10 times before checking alert level again
                for cycle in range(10):
                    self.set_strip_color(self.red_strip, COLORS['OFF'])
                    self.set_strip_color(self.yellow_strip, COLORS['OFF'])
                    
                    if GREEN_STRIP_ENABLED and self.green_strip:
                        self.set_strip_color(self.green_strip, COLORS['GREEN'])
                        time.sleep(0.5)
                        self.set_strip_color(self.green_strip, COLORS['OFF'])
                        time.sleep(0.5)
                    else:
                        # No green strip yet - keep all OFF for SAFE condition
                        time.sleep(1.0)
            else:
                print(" [SIMULATION] GREEN strip: BLINKING (Safe)")
                time.sleep(1.0)
        elif level == "QUIET":
            # Main system active - all strips OFF
            self.turn_off_all_strips()
            time.sleep(1.0)

        elif level == "FAILSAFE":
            # Fail-safe: YELLOW strip blinks slowly
            if self.hardware_available:
                self.set_strip_color(self.red_strip, COLORS['OFF'])
                if GREEN_STRIP_ENABLED and self.green_strip:
                    self.set_strip_color(self.green_strip, COLORS['OFF'])
                
                self.set_strip_color(self.yellow_strip, COLORS['YELLOW'])
                time.sleep(1.0)
                self.set_strip_color(self.yellow_strip, COLORS['OFF'])
                time.sleep(1.0)
            else:
                print("⚠️  [SIMULATION] YELLOW strip: FAILSAFE BLINK")
                time.sleep(2.0)

        else:
            # Unknown - default to fail-safe
            self.turn_off_all_strips()
            time.sleep(1.0)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum} - shutting down gracefully")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Clean shutdown"""
        print("🧹 Cleaning up Beach Sign LED service...")
        self.turn_off_all_strips()

        if hasattr(self, 'process_lock'):
            self.process_lock.release()

        try:
            if os.path.exists(STATUS_FILE):
                os.unlink(STATUS_FILE)
        except:
            pass

        print("🧹 Beach Sign LED service cleanup complete")

    def run(self):
        """Main service loop"""
        print("🏖️  Beach Sign LED Manager starting")
        print(f"   RED strip (Danger): GPIO {RED_STRIP_PIN}")
        print(f"   YELLOW strip (Caution): GPIO {YELLOW_STRIP_PIN}")
        print(f"   GREEN strip (Safe): GPIO {GREEN_STRIP_PIN} {'✅ Enabled' if GREEN_STRIP_ENABLED else '❌ Not installed yet'}")
        print("   Control file: /tmp/led_control_signal")
        print("   Press Ctrl+C to stop")
        print()

        try:
            while self.running:
                level = self.get_alert_level()
                self.update_status(level)
                self.run_alert_pattern(level)

        except KeyboardInterrupt:
            print("\n🛑 Service stopped by user")
        except Exception as e:
            print(f"\n❌ Service error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

def main():
    """Entry point"""
    print("🚀 Starting Beach Sign LED Service Manager")
    print("=" * 60)
    manager = BeachSignLEDManager()
    manager.run()

if __name__ == "__main__":
    main()
