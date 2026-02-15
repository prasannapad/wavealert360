# WaveAlert360 - Device Main Script (Hardware-Free Version -- small change)
# -----------------------------------------------------------
# AUTO-UPDATE TEST: This comment added to test auto-update functionality
# LED INTEGRATION: Hardware LED control via led_failsafe_manager.py active
# This script runs the core logic for detecting coastal hazards using console output.
# It polls the National Weather Service (NWS) API for active alerts and displays
# LED patterns and audio alerts in the console. No GPIO or hardware dependencies.
# All alert behaviors, triggers, and responses are defined in helpers.py.

import requests
import time
import os
import shlex
from datetime import datetime
from pathlib import Path
from helpers import (
    # Location and system settings
    LATITUDE, LONGITUDE, LOCATION_NAME, CHECK_INTERVAL, AUDIO_DIR,
    REQUEST_TIMEOUT, USER_AGENT, AUDIO_PLAYER_COMMAND,
    # Centralized config functions - NO hardcoded alert logic here
    detect_hazard, get_alert_config, get_console_message, get_api_url
)

# ========== GitHub Version Information ==========
def get_github_commit_info():
    """Get current GitHub commit information for each check"""
    try:
        device_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for .last_commit in the device directory first (self-contained)
        commit_file = os.path.join(device_dir, '.last_commit')
        
        # If not found in device directory, fall back to root directory (for backward compatibility)
        if not os.path.exists(commit_file):
            root_dir = os.path.dirname(device_dir)
            commit_file = os.path.join(root_dir, '.last_commit')
        
        if os.path.exists(commit_file):
            with open(commit_file, 'r') as f:
                current_commit = f.read().strip()
                commit_short = current_commit[:8]
                
                # Try to get commit message using git
                try:
                    import subprocess
                    original_dir = os.getcwd()
                    # Try git from device directory first, then root directory
                    git_dir = device_dir if os.path.exists(os.path.join(device_dir, '.git')) else os.path.dirname(device_dir)
                    os.chdir(git_dir)
                    result = subprocess.run(['git', 'show', '-s', '--format=%s', current_commit], 
                                          capture_output=True, text=True, timeout=3)
                    os.chdir(original_dir)  # Always restore directory
                    
                    if result.returncode == 0:
                        commit_message = result.stdout.strip()[:50]  # Limit to 50 chars for regular display
                        if len(result.stdout.strip()) > 50:
                            commit_message += "..."
                        return f"{commit_short} - {commit_message}"
                except Exception as e:
                    # Git failed, but we have a commit SHA - that's enough for field trials
                    pass
                
                # Return commit SHA without message - this is still useful information
                return f"{commit_short} - Git info unavailable"
        else:
            # No .last_commit file - this means auto-updater hasn't run or it's a manual deployment
            return "Manual deployment - No auto-updater tracking"
    except Exception as e:
        # Something went wrong, but provide helpful context
        return "Standalone deployment - Version tracking disabled"

# ========== Simulated Audio Playback ==========
def play_audio(alert_config):
    """
    Plays audio files using the centralized alert configuration.
    Replace with a real audio player command like omxplayer on deployment.
    """
    import os
    import subprocess
    
    filename = alert_config["audio_file"]
    lock_fd = None
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, AUDIO_DIR, filename)
    
    if os.path.exists(path):
        # Check if it's a real audio file or placeholder
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100)  # Read first 100 chars
                if content.startswith('#'):
                    print(f"[AUDIO] Placeholder found: {filename} (needs real TTS audio)")
                    return
        except:
            pass  # If we can't read it as text, assume it's a real audio file
        
        # Get actual audio duration (for logging only)
        try:
            import importlib
            mp3_module = importlib.import_module("mutagen.mp3")
            audio = mp3_module.MP3(path)
            duration = audio.info.length
            print(f"[AUDIO] {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - Starting: {filename} ({duration:.1f}s)")
        except:
            duration = None
            print(f"[AUDIO] {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - Starting: {filename} (unknown duration)")
        
        # Use system audio player that works with Bluetooth
        try:
            abs_path = os.path.abspath(path)
            lock_file_path = '/tmp/wavealert_audio.lock'

            # Serialize playback across processes to prevent overlapping audio.
            lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR, 0o666)
            try:
                import fcntl
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
            except Exception:
                # If file locking is unavailable, continue with best effort.
                pass

            # Run optional pre-play connection step only when explicitly configured.
            try:
                if 'bluetoothctl connect' in AUDIO_PLAYER_COMMAND:
                    bt_mac = AUDIO_PLAYER_COMMAND.split('bluetoothctl connect', 1)[1].strip().split()[0]
                    subprocess.run(
                        ['bluetoothctl', 'connect', bt_mac],
                        stderr=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        check=False
                    )
                    time.sleep(1.0)
            except Exception:
                pass

            configured_cmd = []
            if AUDIO_PLAYER_COMMAND and all(token not in AUDIO_PLAYER_COMMAND for token in ['&&', ';', '|']):
                configured_cmd = shlex.split(AUDIO_PLAYER_COMMAND) + [abs_path]

            # Prefer proven blocking players first.
            audio_commands = [
                ['mpg123', '-q', abs_path],
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', abs_path],
                ['cvlc', '--intf', 'dummy', '--play-and-exit', abs_path],
                ['omxplayer', '-o', 'both', abs_path]
            ]
            if configured_cmd:
                audio_commands.insert(0, configured_cmd)
            
            # Preserve audio environment variables for Bluetooth
            env = os.environ.copy()
            env['PULSE_RUNTIME_PATH'] = env.get('PULSE_RUNTIME_PATH', '/run/user/1000/pulse')
            
            # Run audio player in foreground and wait for true playback completion
            for cmd in audio_commands:
                try:
                    print(f"[AUDIO] Using player: {' '.join(cmd[:-1])}")
                    result = subprocess.run(
                        cmd,
                        env=env,
                        stderr=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        check=False
                    )

                    if result.returncode == 0:
                        print(f"[AUDIO] {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - Finished: {filename}")
                        try:
                            os.close(lock_fd)
                        except Exception:
                            pass
                        return True

                    print(f"[AUDIO] Player exited with code {result.returncode}, trying fallback...")
                except FileNotFoundError:
                    continue
                except Exception as e:
                    print(f"[AUDIO] Player error ({cmd[0]}): {e}")
                    continue
            
            print(f"[AUDIO] All players failed for: {filename}")
            try:
                os.close(lock_fd)
            except Exception:
                pass
            
        except Exception as e:
            print(f"[AUDIO] Error playing {filename}: {e}")
            try:
                os.close(lock_fd)
            except Exception:
                pass
            
        # Fallback to pygame if all system players fail
            
            # Fallback to pygame for audio playback
            try:
                import pygame
                # Initialize pygame mixer if not already done
                if not pygame.get_init():
                    pygame.mixer.init()
                
                # Load and play the audio file
                pygame.mixer.music.load(abs_path)
                pygame.mixer.music.play()
                print(f"[AUDIO] Playing via pygame: {filename}")

                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                print(f"[AUDIO] {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - Finished: {filename}")
                try:
                    os.close(lock_fd)
                except Exception:
                    pass
                return True
                
            except ImportError:
                print(f"[AUDIO] pygame not installed. Install with: pip install pygame")
                print(f"[AUDIO] Simulating: {filename}")
                try:
                    os.close(lock_fd)
                except Exception:
                    pass
                return False
            except Exception as e:
                print(f"[AUDIO] Error playing {filename}: {e}")
                print(f"[AUDIO] Simulating: {filename}")
                try:
                    os.close(lock_fd)
                except Exception:
                    pass
                return False
                
        except Exception as e:
            print(f"[AUDIO] Error playing {filename}: {e}")
            print(f"[AUDIO] Simulating: {filename}")
            try:
                os.close(lock_fd)
            except Exception:
                pass
            return False
    else:
        print(f"[AUDIO] File not found: {filename}")
        print(f"[AUDIO] Simulating: {filename}")
        return False

# ========== LED Control Integration ==========
def flash_led(alert_config):
    """
    Displays LED patterns in console AND controls hardware LEDs.
    Integrates with led_failsafe_manager.py via control file.
    """
    pattern = alert_config["led_pattern"]
    message_type = alert_config["message_type"]
    
    # Control hardware LEDs via led_failsafe_manager.py
    _control_hardware_leds(alert_config)
    
    # Also show console display for debugging
    _flash_console_leds(pattern, message_type)

def _control_hardware_leds(alert_config):
    """
    Control hardware LEDs by writing to the LED control file.
    Maps service alert levels to LED hardware patterns.
    """
    LED_CONTROL_FILE = "/tmp/led_control_signal"
    
    try:
        # Get current alert level from global variable if available
        alert_level = getattr(_control_hardware_leds, '_current_alert_level', None)
        
        # Map service alert levels to LED patterns
        led_command_map = {
            "DANGER": "PATTERN:RED_BLINK",  # High danger - flashing red LEDs
            "CAUTION": "PATTERN:YELLOW",    # Moderate caution - yellow LEDs
            "SAFE": "PATTERN:GREEN"         # Safe conditions - green LEDs
        }        # If alert level is cached, use it directly
        if alert_level:
            led_command = led_command_map.get(alert_level, "PATTERN:YELLOW")
            print(f"🚦 [LED] Using cached alert level: {alert_level} → {led_command}")
        else:
            # Fallback: determine alert level from message type
            message_type = alert_config.get("message_type", "").upper()
            print(f"🔍 [LED] No cached alert level, parsing message: {message_type}")
            
            if "HIGH ALERT" in message_type or "DANGER" in message_type:
                alert_level = "DANGER"
            elif "NORMAL" in message_type:
                alert_level = "SAFE"
            else:
                alert_level = "CAUTION"  # Default for unknown
            
            led_command = led_command_map.get(alert_level, "PATTERN:YELLOW")
            print(f"🚦 [LED] Parsed alert level: {alert_level} → {led_command}")
        
        # Write control signal to LED manager
        with open(LED_CONTROL_FILE, 'w') as f:
            f.write(led_command)
        
        print(f"✅ [LED] Hardware control: {alert_level} → {led_command}")
        
    except Exception as e:
        print(f"❌ [LED] Error controlling hardware LEDs: {e}")
        print(f"🔄 [LED] LED manager will continue with fail-safe mode")

def set_alert_level_for_leds(alert_level):
    """
    Set the current alert level for LED control.
    Call this before flash_led() to ensure proper LED mapping.
    """
    _control_hardware_leds._current_alert_level = alert_level

def _flash_console_leds(pattern, message_type):
    """Display LED patterns in console with colored emojis"""
    import time
    
    # Check if this is a flashing pattern (multiple different colors)
    unique_emojis = list(set(pattern))
    
    if len(unique_emojis) <= 1:
        # Solid pattern - just show it once
        print(f"{pattern} [LED] {message_type}")
    else:
        # Flashing pattern - animate in console
        print(f"[LED] {message_type} - Flashing...")
        
        # Create alternating pattern from the emojis
        flash_colors = unique_emojis[:2]  # Use first 2 unique colors
        
        # Show flashing sequence in console
        for cycle in range(3):
            for color in flash_colors:
                # Create pattern with all LEDs showing current color
                flash_pattern = color * 10  # 10 LEDs of same color
                print(f"{flash_pattern} [FLASH {cycle+1}]")
                time.sleep(0.5)
        
        # Show final state
        print(f"{pattern} [LED] {message_type} - Final State")

# ========== Fetch Alerts from Azure Service ==========
def fetch_device_alert():
    """
    Calls Azure Function service to get device-specific alert status.
    Returns alert response with level, audio URL, and display info.
    Falls back to local NWS API if service unavailable.
    """
    from helpers import call_azure_service

    # Try Azure service first
    service_response = call_azure_service()

    if service_response:
        # Check if this is DEMO mode response (has scenarios array)
        if service_response.get("device_mode") == "DEMO":
            return {
                "status": "success",
                "alert_level": "DEMO",
                "demo_config": service_response,  # Pass entire config
                "device_config": {
                    "display_name": "WaveAlert360 Device",
                    "location_name": "Cowell Ranch State Beach",
                    "operating_mode": "DEMO"
                }
            }
        
        # Regular LIVE or TEST mode response
        return {
            "status": "success",
            "alert_level": service_response.get("alert_level", "SAFE"),
            "display_text": f"{service_response.get('alert_level', 'SAFE')} - Azure service response",
            "audio_url": service_response.get("audio_url"),
            "device_config": {
                "display_name": "WaveAlert360 Device",
                "location_name": "Cowell Ranch State Beach",
                "operating_mode": service_response.get("device_mode", "UNKNOWN")
            }
        }

    # Fallback to local NWS API if service unavailable
    print("="*60)
    print(f"⚠️  [FALLBACK] Azure service unavailable at {datetime.now().isoformat()}")
    print(f"⚠️  [FALLBACK] Switching to local NWS API (LIVE mode, ignoring TEST scenario)")
    print("="*60)
    return fetch_alerts_fallback()

def fetch_alerts_fallback():
    """
    Fallback function - uses original NWS API approach.
    Returns formatted response matching Azure service structure.
    """
    try:
        # Get the appropriate API URL based on MOCK_MODE setting
        api_url = get_api_url(LATITUDE, LONGITUDE)
        
        print(f"🌐 [FALLBACK API] Calling: {api_url}")
        print(f"📍 [LOCATION] Monitoring: {LOCATION_NAME} ({LATITUDE}, {LONGITUDE})")
        
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        alerts = response.json().get("features", [])
        hazard_level = detect_hazard(alerts)  # Returns "HIGH", "MEDIUM", or None
        
        # Format response to match Azure service structure
        if hazard_level == "HIGH":
            return {
                "status": "success",
                "alert_level": "DANGER",
                "display_text": "🚨 HIGH ALERT: Dangerous coastal conditions detected",
                "audio_url": None,  # Will use local audio
                "device_config": {
                    "location_name": LOCATION_NAME,
                    "operating_mode": "FALLBACK"
                }
            }
        elif hazard_level == "MEDIUM":
            return {
                "status": "success",
                "alert_level": "CAUTION",
                "display_text": "⚠️ CAUTION: Elevated beach hazards detected",
                "audio_url": None,  # Will use local audio
                "device_config": {
                    "location_name": LOCATION_NAME,
                    "operating_mode": "FALLBACK"
                }
            }
        else:
            return {
                "status": "success", 
                "alert_level": "SAFE",
                "display_text": "✅ No coastal hazards detected",
                "audio_url": None,  # Will use local audio
                "device_config": {
                    "location_name": LOCATION_NAME,
                    "operating_mode": "FALLBACK"
                }
            }
            
    except Exception as e:
        print(f"[ERROR] Fallback API fetch failed: {e}")
        return {
            "status": "error",
            "alert_level": "SAFE",
            "display_text": "❌ Unable to check coastal conditions",
            "audio_url": None,
            "device_config": {
                "location_name": LOCATION_NAME,
                "operating_mode": "ERROR"
            }
        }

# ========== Fetch Alerts from NWS ==========
def fetch_alerts():
    """
    Sends a GET request to the NWS API and parses the active alerts.
    Returns a list of alert features (JSON).
    """
    try:
        # Get the appropriate API URL based on MOCK_MODE setting
        api_url = get_api_url(LATITUDE, LONGITUDE)
        
        # Print the API endpoint and location being monitored for debugging
        print(f"🌐 [API] Calling: {api_url}")
        print(f"📍 [LOCATION] Monitoring: {LOCATION_NAME} ({LATITUDE}, {LONGITUDE})")
        
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("features", [])
    except Exception as e:
        print(f"[ERROR] API fetch failed: {e}")
        return []

# ========== Main Execution Loop ==========
def main():
    """
    Main execution loop.
    Simplified version that focuses on core coastal alert monitoring and LED control.
    """
    import os
    from pathlib import Path
    
    print(f"\n🌊 WaveAlert360 SIMPLIFIED started at {datetime.now()}")
    print(f"📍 Monitoring conditions for: {LOCATION_NAME} ({LATITUDE}, {LONGITUDE})")
    print(f"🎯 [SYSTEM] Simplified initialization - no complex process management")
    
    # Get the directory where this script is located and ensure audio directory exists
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_full_path = os.path.join(script_dir, AUDIO_DIR)
    Path(audio_full_path).mkdir(exist_ok=True)
    print(f"🎵 Audio directory: {audio_full_path}")
    
    # Import mode settings to show which API mode we're using
    from helpers import MOCK_MODE, MOCK_API_BASE
    if MOCK_MODE:
        print(f"🧪 [MOCK MODE] Using test API: {MOCK_API_BASE}")
    else:
        print(f"🌐 [LIVE MODE] Using real NWS API")
    print()

    # Run immediate first check on startup
    first_check = True

    while True:
        # Display current check time and GitHub commit info
        current_time = datetime.now().strftime("%A %m/%d/%y %I:%M:%S %p")
        github_commit = get_github_commit_info()
        
        if first_check:
            print(f"\n🚀 [IMMEDIATE STARTUP CHECK] Running first coastal monitoring check...")
            first_check = False
        else:
            print(f"\n⏰ [{current_time}] Running WaveAlert360 check...")
        
        print(f"📦 Running commit: {github_commit}")
        
        # Call Azure Function service for device-specific alert status
        device_alert = fetch_device_alert()          # Get alert status from Azure service
        
        if device_alert and device_alert.get("status") == "success":
            alert_level = device_alert.get("alert_level", "SAFE")
            device_config = device_alert.get("device_config", {})
            operating_mode = device_config.get('operating_mode', 'Unknown')
            
            print(f"🏷️  [CONFIG] Device: {device_config.get('display_name', 'Unknown')}")
            print(f"📍 [LOCATION] {device_config.get('location_name', 'Unknown')}")
            print(f"🔧 [MODE] {operating_mode}")
            
            # ===== DEMO MODE: Cycle through all scenarios =====
            if alert_level == "DEMO":
                demo_config = device_alert.get("demo_config", {})
                scenarios = demo_config.get("scenarios", [])
                pause_seconds = 0
                
                print(f"🎭 [DEMO] Starting cycling demo with {len(scenarios)} scenarios")
                print(f"⏸️  [DEMO] {pause_seconds}s pause between scenarios")
                
                for scenario in scenarios:
                    scenario_level = scenario.get("alert_level")
                    audio_url = scenario.get("audio_url")
                    
                    print(f"\n{'='*60}")
                    print(f"🎭 [DEMO] Scenario: {scenario_level}")
                    print(f"{'='*60}")
                    
                    # Map to internal hazard levels
                    has_hazards = scenario_level in ["CAUTION", "DANGER"]
                    hazard_level_map = {
                        "DANGER": "HIGH",
                        "CAUTION": "MEDIUM",
                        "SAFE": "NORMAL"
                    }
                    hazard_level = hazard_level_map.get(scenario_level, "NORMAL")
                    
                    # Get alert config
                    alert_config = get_alert_config(has_hazards=has_hazards, hazard_level=hazard_level)
                    
                    # Set alert level for LED hardware control
                    set_alert_level_for_leds(scenario_level)
                    
                    # Start LED pattern first
                    flash_led(alert_config)
                    
                    # Wait for LED to visibly change before starting audio
                    print(f"⏸️  [DEMO] Waiting 1s for LED to change to {scenario_level}...")
                    time.sleep(1.0)
                    
                    # Now start audio
                    play_audio(alert_config)  # Blocks until audio finishes
                
                print(f"\n✅ [DEMO] Complete cycle finished, will repeat on next check")
                # In DEMO mode, restart cycle immediately to avoid end-of-loop idle gap.
                continue
                
            # ===== LIVE or TEST MODE: Single alert =====
            else:
                display_text = device_alert.get("display_text", "No information available")
                audio_url = device_alert.get("audio_url")
                
                print(f"🎯 [DEVICE] {display_text}")
                
                # Determine if this is a hazard condition
                has_hazards = alert_level in ["CAUTION", "DANGER"]
                
                # Map alert levels to hazard levels for configuration
                hazard_level_map = {
                    "DANGER": "HIGH",
                    "CAUTION": "MEDIUM",
                    "SAFE": "NORMAL"
                }
                hazard_level = hazard_level_map.get(alert_level, "NORMAL")
                
                # Set alert level for LED hardware control
                print(f"🚦 [LED] Setting alert level to: {alert_level} at {datetime.now().isoformat()}")
                set_alert_level_for_leds(alert_level)
                
                # Get appropriate alert configuration from centralized config
                alert_config = get_alert_config(has_hazards=has_hazards, hazard_level=hazard_level)
                
                # Override audio file if service provides audio URL
                if audio_url:
                    print(f"🎵 [AUDIO] Using service audio: {audio_url}")
                    # TODO: Download and play service audio
                
                # Display alerts and trigger actions
                flash_led(alert_config)
                print(f"⏸️  [LIVE/TEST] Waiting 1s for LED to change to {alert_level}...")
                time.sleep(1.0)
                play_audio(alert_config)
                
        else:
            print("❌ [ERROR] Unable to get device alert status")
            print("🔄 [SYSTEM] Continuing with next check...")

        print(f"✅ Check completed at {datetime.now().strftime('%I:%M:%S %p')}")
        print("-" * 40)
        
        # Sleep for check interval (immediate first check already happened)
        time.sleep(CHECK_INTERVAL)

def cleanup_on_exit():
    """Clean up PID file on exit"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pid_file = os.path.join(script_dir, '.main.pid')
        if os.path.exists(pid_file):
            os.remove(pid_file)
            print("\n🧹 Cleaned up PID file")
    except Exception as e:
        print(f"\n⚠️  Could not clean up PID file: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {sig} - shutting down gracefully...")
    cleanup_on_exit()
    sys.exit(0)

# ========== Entry Point ==========
if __name__ == "__main__":
    import signal
    import sys
    import atexit
    
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        cleanup_on_exit()
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        cleanup_on_exit()

        sys.exit(1)
