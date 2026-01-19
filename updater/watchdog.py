#!/usr/bin/env python3
"""
WaveAlert360 Auto-Updater Watchdog
==================================
Monitors the auto-updater and restarts it if it fails.
This runs as a separate process to ensure the auto-updater stays alive.
"""

import os
import sys
import time
import subprocess
import logging
import platform
import atexit
from datetime import datetime, timedelta
from pathlib import Path

# Platform-specific imports for file locking
if platform.system() != "Windows":
    import fcntl
else:
    import msvcrt

def safe_log(level, message):
    """Log message safely, replacing emojis with text for console compatibility"""
    # Replace common emojis with text equivalents for console safety
    safe_message = message
    emoji_replacements = {
        '🐕': '[DOG]',
        '🚀': '[START]', 
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        '🛑': '[STOP]',
        '🔍': '[CHECK]',
        '🔄': '[RESTART]',
        '⏰': '[TIME]',
        '🕒': '[CLOCK]',
        '😴': '[SLEEP]'
    }
    
    for emoji, replacement in emoji_replacements.items():
        safe_message = safe_message.replace(emoji, replacement)
    
    # Use the appropriate logging level
    if level == 'info':
        logger.info(safe_message)
    elif level == 'error':
        logger.error(safe_message)
    elif level == 'warning':
        logger.warning(safe_message)
    else:
        logger.info(safe_message)

class ProcessLock:
    """Cross-platform process lock to ensure only one instance runs"""
    
    def __init__(self, lock_file_path):
        self.lock_file_path = lock_file_path
        self.lock_file = None
        self.is_locked = False
        
    def acquire(self):
        """Acquire the process lock"""
        try:
            # Create lock file
            self.lock_file = open(self.lock_file_path, 'w')
            
            if platform.system() == "Windows":
                # Windows file locking
                try:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    self.is_locked = True
                except OSError:
                    self.lock_file.close()
                    return False
            else:
                # Unix/Linux file locking
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.is_locked = True
                except OSError:
                    self.lock_file.close()
                    return False
            
            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            
            # Register cleanup on exit
            atexit.register(self.release)
            
            return True
            
        except Exception as e:
            if self.lock_file:
                self.lock_file.close()
            return False
    
    def release(self):
        """Release the process lock"""
        if self.is_locked and self.lock_file:
            try:
                if platform.system() == "Windows":
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                
                self.lock_file.close()
                
                # Remove lock file
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
                    
                self.is_locked = False
                
            except Exception:
                pass  # Ignore cleanup errors
    
    def check_existing_process(self):
        """Check if another process is already running"""
        if os.path.exists(self.lock_file_path):
            try:
                with open(self.lock_file_path, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is still running
                if platform.system() == "Windows":
                    import subprocess
                    try:
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                              capture_output=True, text=True)
                        return str(pid) in result.stdout
                    except:
                        return False
                else:
                    try:
                        os.kill(pid, 0)  # Signal 0 checks if process exists
                        return True
                    except OSError:
                        return False
            except:
                pass
        return False

# Configuration
UPDATER_SCRIPT = "updater/auto_updater.py"
MAIN_SCRIPT = "device/main.py"
WEB_SCRIPT = "device/web_status.py"
LED_SCRIPT = "device/led_failsafe_manager.py"

WATCHDOG_INTERVAL = 60  # Check every 60 seconds (more frequent for critical processes)
MAX_RESTART_ATTEMPTS = 5
RESTART_COOLDOWN = 600  # 10 minutes between restart attempts

# Logging setup
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'watchdog.log')

# Configure logging with UTF-8 encoding for file, but safe console output
file_handler = logging.FileHandler(log_file, encoding='utf-8')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

class AutoUpdaterWatchdog:
    """Monitors and restarts critical WaveAlert360 processes"""
    
    def __init__(self):
        # Process tracking
        self.updater_process = None
        self.main_process = None
        self.web_process = None
        self.led_process = None
        
        # Restart tracking per process
        self.restart_counts = {
            'updater': 0,
            'main': 0,
            'web': 0,
            'led': 0
        }
        self.last_restarts = {
            'updater': None,
            'main': None,
            'web': None,
            'led': None
        }
        
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.python_executable = sys.executable
        
        # Set up process lock
        lock_file = os.path.join(self.project_root, '.watchdog.lock')
        self.process_lock = ProcessLock(lock_file)
        
    def ensure_single_instance(self):
        """Ensure only one watchdog instance is running"""
        if self.process_lock.check_existing_process():
            safe_log('error', "❌ Another watchdog instance is already running!")
            safe_log('info', "🔍 Check processes with: tasklist | findstr python")
            return False
            
        if not self.process_lock.acquire():
            safe_log('error', "❌ Failed to acquire process lock - another instance may be running")
            return False
            
        safe_log('info', "🔒 Process lock acquired - this is the only watchdog instance")
        return True
        
    def is_updater_running(self):
        """Check if the auto-updater process is still running"""
        if self.updater_process is None:
            return False
        return self.updater_process.poll() is None
    
    def is_main_running(self):
        """Check if the main.py process is still running"""
        if self.main_process is None:
            return False
        return self.main_process.poll() is None
    
    def is_web_running(self):
        """Check if the web_status.py process is still running"""
        if self.web_process is None:
            return False
        return self.web_process.poll() is None
    
    def is_led_running(self):
        """Check if the LED service is still running"""
        if self.led_process is None:
            return False
        return self.led_process.poll() is None
    
    def start_updater(self):
        """Start the auto-updater process"""
        try:
            updater_path = os.path.join(self.project_root, UPDATER_SCRIPT)
            if not os.path.exists(updater_path):
                safe_log('error', f"❌ Auto-updater script not found: {updater_path}")
                return False
            
            safe_log('info', "🚀 Starting auto-updater process...")
            self.updater_process = subprocess.Popen([
                self.python_executable, updater_path
            ], cwd=self.project_root)
            
            safe_log('info', f"✅ Auto-updater started (PID: {self.updater_process.pid})")
            return True
            
        except Exception as e:
            safe_log('error', f"❌ Failed to start auto-updater: {e}")
            return False
    
    def start_main(self):
        """Start the main.py alert monitoring process"""
        try:
            main_path = os.path.join(self.project_root, MAIN_SCRIPT)
            if not os.path.exists(main_path):
                safe_log('error', f"❌ Main script not found: {main_path}")
                return False
            
            safe_log('info', "🚀 Starting main alert process...")
            device_dir = os.path.join(self.project_root, 'device')
            self.main_process = subprocess.Popen([
                self.python_executable, main_path
            ], cwd=device_dir)
            
            safe_log('info', f"✅ Main process started (PID: {self.main_process.pid})")
            return True
            
        except Exception as e:
            safe_log('error', f"❌ Failed to start main process: {e}")
            return False
    
    def start_web(self):
        """Start the web_status.py dashboard process"""
        try:
            web_path = os.path.join(self.project_root, WEB_SCRIPT)
            if not os.path.exists(web_path):
                safe_log('error', f"❌ Web script not found: {web_path}")
                return False
            
            safe_log('info', "🌐 Starting web dashboard...")
            device_dir = os.path.join(self.project_root, 'device')
            
            # Redirect stdout/stderr to prevent hanging
            with open(os.devnull, 'w') as devnull:
                self.web_process = subprocess.Popen([
                    self.python_executable, web_path
                ], cwd=device_dir, stdout=devnull, stderr=devnull,
                   preexec_fn=os.setsid if hasattr(os, 'setsid') else None)
            
            safe_log('info', f"✅ Web dashboard started (PID: {self.web_process.pid})")
            return True
            
        except Exception as e:
            safe_log('error', f"❌ Failed to start web dashboard: {e}")
            return False
    
    def start_led(self):
        """Start the LED failsafe manager (requires sudo)"""
        try:
            led_path = os.path.join(self.project_root, LED_SCRIPT)
            if not os.path.exists(led_path):
                safe_log('error', f"❌ LED script not found: {led_path}")
                return False
            
            safe_log('info', "💡 Starting LED service...")
            device_dir = os.path.join(self.project_root, 'device')
            
            # LED service needs sudo - redirect output to log
            log_file = '/tmp/led_service.log'
            with open(log_file, 'w') as f:
                self.led_process = subprocess.Popen([
                    'sudo', self.python_executable, led_path
                ], cwd=device_dir, stdout=f, stderr=subprocess.STDOUT,
                   preexec_fn=os.setsid if hasattr(os, 'setsid') else None)
            
            safe_log('info', f"✅ LED service started (PID: {self.led_process.pid})")
            return True
            
        except Exception as e:
            safe_log('error', f"❌ Failed to start LED service: {e}")
            return False
    
    def stop_updater(self):
        """Stop the auto-updater process"""
        if self.updater_process and self.is_updater_running():
            logger.info("🛑 Stopping auto-updater...")
            try:
                self.updater_process.terminate()
                self.updater_process.wait(timeout=10)
                logger.info("✅ Auto-updater stopped")
            except:
                try:
                    self.updater_process.kill()
                    logger.info("✅ Auto-updater force-stopped")
                except:
                    pass
    
    def stop_main(self):
        """Stop the main.py process"""
        if self.main_process and self.is_main_running():
            logger.info("🛑 Stopping main process...")
            try:
                self.main_process.terminate()
                self.main_process.wait(timeout=10)
                logger.info("✅ Main process stopped")
            except:
                try:
                    self.main_process.kill()
                    logger.info("✅ Main process force-stopped")
                except:
                    pass
    
    def stop_web(self):
        """Stop the web dashboard process"""
        if self.web_process and self.is_web_running():
            logger.info("🛑 Stopping web dashboard...")
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=10)
                logger.info("✅ Web dashboard stopped")
            except:
                try:
                    self.web_process.kill()
                    logger.info("✅ Web dashboard force-stopped")
                except:
                    pass
    
    def stop_led(self):
        """Stop the LED service"""
        if self.led_process and self.is_led_running():
            logger.info("🛑 Stopping LED service...")
            try:
                self.led_process.terminate()
                self.led_process.wait(timeout=10)
                logger.info("✅ LED service stopped")
            except:
                try:
                    self.led_process.kill()
                    logger.info("✅ LED service force-stopped")
                except:
                    pass
    
    def stop_all(self):
        """Stop all managed processes"""
        logger.info("🛑 Stopping all processes...")
        self.stop_main()
        self.stop_web()
        self.stop_led()
        self.stop_updater()
    
    def can_restart(self, process_name):
        """Check if we can restart a specific process (not too many recent attempts)"""
        restart_count = self.restart_counts[process_name]
        last_restart = self.last_restarts[process_name]
        
        if restart_count >= MAX_RESTART_ATTEMPTS:
            if last_restart:
                time_since_last = datetime.now() - last_restart
                if time_since_last.total_seconds() < RESTART_COOLDOWN:
                    return False
                else:
                    # Reset counter after cooldown
                    self.restart_counts[process_name] = 0
        return True
    
    def restart_process(self, process_name, start_func):
        """Generic process restart with safety limits"""
        if not self.can_restart(process_name):
            logger.error(f"❌ Too many {process_name} restart attempts ({self.restart_counts[process_name]}), waiting for cooldown")
            return False
        
        logger.warning(f"⚠️  {process_name} appears to have stopped, restarting...")
        
        time.sleep(2)  # Brief pause
        
        if start_func():
            self.restart_counts[process_name] += 1
            self.last_restarts[process_name] = datetime.now()
            logger.info(f"✅ {process_name} restarted (attempt {self.restart_counts[process_name]})")
            return True
        else:
            logger.error(f"❌ Failed to restart {process_name}")
            return False
    

    def print_status_banner(self):
        """Print watchdog status"""
        banner_width = 70
        border = "🐕" + "="*(banner_width-2) + "🐕"
        logger.info(border)
        logger.info("🐕 WAVEALERT360 WATCHDOG STATUS")
        logger.info(f"   � Auto-updater:  {'✅ Running' if self.is_updater_running() else '❌ Stopped'} (restarts: {self.restart_counts['updater']})")
        logger.info(f"   � Main process:  {'✅ Running' if self.is_main_running() else '❌ Stopped'} (restarts: {self.restart_counts['main']})")
        logger.info(f"   🌐 Web dashboard: {'✅ Running' if self.is_web_running() else '❌ Stopped'} (restarts: {self.restart_counts['web']})")
        logger.info(f"   💡 LED service:   {'✅ Running' if self.is_led_running() else '❌ Stopped'} (restarts: {self.restart_counts['led']})")
        logger.info(f"   🕒 Check time: {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}")
        logger.info(border)
    
    def run_forever(self):
        """Main watchdog loop - monitors all critical processes"""
        # Ensure only one instance is running
        if not self.ensure_single_instance():
            safe_log('error', "❌ Exiting - another watchdog instance is already running")
            return
            
        safe_log('info', "🐕 WaveAlert360 Watchdog started")
        logger.info(f"   Monitoring: Auto-updater, Main.py, Web Dashboard, LED Service")
        logger.info(f"   Check interval: {WATCHDOG_INTERVAL} seconds")
        logger.info(f"   Max restarts per process: {MAX_RESTART_ATTEMPTS}")
        logger.info(f"   Lock file: {self.process_lock.lock_file_path}")
        logger.info("")
        
        # Start all processes initially
        safe_log('info', "🚀 Starting all WaveAlert360 processes...")
        
        # Order matters: LED first (hardware), then main (core), then web (UI), then updater (management)
        if not self.start_led():
            safe_log('error', "❌ Failed to start LED service")
        
        if not self.start_main():
            safe_log('error', "❌ Failed to start main process")
        
        if not self.start_web():
            safe_log('error', "❌ Failed to start web dashboard")
        
        if not self.start_updater():
            safe_log('error', "❌ Failed to start auto-updater")
        
        logger.info("")
        safe_log('info', "✅ Initial startup complete - entering monitoring loop")
        logger.info("")
        
        while True:
            try:
                time.sleep(WATCHDOG_INTERVAL)
                
                self.print_status_banner()
                
                # Check each process and restart if needed
                # Note: Auto-updater is checked last because it may restart main.py during updates
                
                if not self.is_led_running():
                    logger.error("❌ LED service has stopped!")
                    self.restart_process('led', self.start_led)
                
                if not self.is_web_running():
                    logger.error("❌ Web dashboard has stopped!")
                    self.restart_process('web', self.start_web)
                
                if not self.is_main_running():
                    logger.error("❌ Main process has stopped!")
                    self.restart_process('main', self.start_main)
                
                if not self.is_updater_running():
                    logger.error("❌ Auto-updater has stopped!")
                    self.restart_process('updater', self.start_updater)
                
                # All processes running
                if (self.is_updater_running() and self.is_main_running() and 
                    self.is_web_running() and self.is_led_running()):
                    logger.info("✅ All processes running normally")
                
            except KeyboardInterrupt:
                logger.info("🛑 Watchdog stopped by user")
                self.stop_all()
                break
            except Exception as e:
                logger.error(f"❌ Watchdog error: {e}")
                # Try to keep critical processes running even if watchdog has issues
                logger.info("🔄 Watchdog continuing despite error...")
                time.sleep(WATCHDOG_INTERVAL)

def main():
    """Entry point"""
    watchdog = AutoUpdaterWatchdog()
    watchdog.run_forever()

if __name__ == "__main__":
    main()
