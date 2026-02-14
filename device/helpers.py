# WaveAlert360 - Helper Functions and Settings Loader
# ===================================================
# Loads settings from settings.json and provides Python helper functions

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import dateutil.parser

# ========== Load Settings from JSON ==========
def load_settings():
    """Load configuration data from settings.json"""
    settings_file = Path(__file__).parent / "settings.json"
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Settings file not found: {settings_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in settings file: {e}")

# Load all settings
SETTINGS = load_settings()

# ========== Location and System Settings (from JSON) ==========
LATITUDE = SETTINGS["location"]["latitude"]
LONGITUDE = SETTINGS["location"]["longitude"] 
LOCATION_NAME = SETTINGS["location"]["name"]
CHECK_INTERVAL = SETTINGS["system"]["check_interval"]
AUDIO_DIR = SETTINGS["system"]["audio_dir"]
REQUEST_TIMEOUT = SETTINGS["system"]["request_timeout"]
USER_AGENT = SETTINGS["system"]["user_agent"]
AUDIO_PLAYER_COMMAND = SETTINGS["system"]["audio_player_command"]

# ========== Azure Configuration (from JSON) ==========
AZURE_REGION = SETTINGS["azure"]["region"]
AZURE_OUTPUT_FORMAT = SETTINGS["azure"]["output_format"]
AZURE_USER_AGENT = SETTINGS["azure"]["user_agent"]
AZURE_REQUEST_TIMEOUT = SETTINGS["azure"]["request_timeout"]
NORMAL_VOICE = SETTINGS["azure"]["voices"]["normal"]
CAUTION_VOICE = SETTINGS["azure"]["voices"]["caution"]
HIGH_ALERT_VOICE = SETTINGS["azure"]["voices"]["high_alert"]
NORMAL_STYLE = SETTINGS["azure"]["styles"]["normal"]
CAUTION_STYLE = SETTINGS["azure"]["styles"]["caution"]
HIGH_ALERT_STYLE = SETTINGS["azure"]["styles"]["high_alert"]
SPEAKING_RATE = SETTINGS["azure"]["speaking_rate"]

# Audio File Names (from JSON)
NORMAL_ALERT_FILE = SETTINGS["audio_files"]["normal"]
CAUTION_ALERT_FILE = SETTINGS["audio_files"]["caution_alert"]
HIGH_ALERT_FILE = SETTINGS["audio_files"]["high_alert"]

# ========== API Configuration (from JSON) ==========
MOCK_MODE = SETTINGS["api"]["mock_mode"]
MOCK_API_BASE = SETTINGS["api"]["mock_base"]
NWS_API_TEMPLATE = SETTINGS["api"]["nws_template"]
MOCK_API_TEMPLATE = SETTINGS["api"]["mock_template"]
MOCK_SCENARIOS = SETTINGS["mock_scenarios"]

# ========== Alert Types (from JSON) ==========
ALERT_TYPES = SETTINGS["alert_types"]

# ========== Complex Logic Functions (Python only) ==========
# These functions cannot be stored in JSON and require Python logic

def call_azure_service():
    """
    Call Azure Function service to get device alert status.
    Returns device alert response or None if service unavailable.
    Caches successful responses for offline use.
    """
    try:
        # Import here to avoid circular import issues
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from config import get_mac_address
        import requests
        
        # Get device MAC address for identification
        mac_address = get_mac_address()
        
        # Azure Function service URL
        service_url = "https://wavealert360-device-service.azurewebsites.net"
        alert_endpoint = f"{service_url}/api/alert/{mac_address}"
        
        print(f"🌐 [SERVICE] Calling Azure Function: {alert_endpoint}")
        
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(alert_endpoint, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        service_response = response.json()
        print(f"✅ [SERVICE] Response: {service_response.get('alert_level', 'Unknown')} alert")
        print(f"📋 [SERVICE] Full response: {json.dumps(service_response, indent=2)}")
        
        # Cache successful response for offline use
        cache_azure_response(service_response)
        
        return service_response
        
    except Exception as e:
        import traceback
        print(f"❌ [SERVICE] Azure Function call failed: {e}")
        print(f"📍 [SERVICE] Error details: {traceback.format_exc()}")
        print(f"⚠️  [SERVICE] Attempting to load cached config...")
        
        # Try to load cached config
        cached_config = load_cached_config()
        if cached_config:
            return cached_config
        
        print(f"⚠️  [SERVICE] No cache available, will trigger FALLBACK to local NWS API")
        return None

def cache_azure_response(response):
    """
    Cache Azure service response for offline use.
    Args:
        response: Dictionary response from Azure service
    """
    try:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_file = os.path.join(script_dir, '.azure_cache.json')
        
        with open(cache_file, 'w') as f:
            json.dump(response, f, indent=2)
        
        print(f"💾 [CACHE] Saved Azure response to cache")
        
    except Exception as e:
        print(f"⚠️  [CACHE] Failed to cache response: {e}")

def load_cached_config():
    """
    Load cached Azure service response for offline operation.
    Returns:
        Cached response dict or None if cache doesn't exist
    """
    try:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_file = os.path.join(script_dir, '.azure_cache.json')
        
        if not os.path.exists(cache_file):
            print(f"📁 [CACHE] No cache file found")
            return None
        
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        print(f"✅ [CACHE] Loaded cached config (Last Known Good)")
        print(f"📋 [CACHE] Operating mode: {cached_data.get('device_mode', 'Unknown')}")
        print(f"🎯 [CACHE] Alert level: {cached_data.get('alert_level', 'Unknown')}")
        
        return cached_data
        
    except Exception as e:
        print(f"❌ [CACHE] Failed to load cache: {e}")
        return None

def get_api_url(lat, lon, scenario=None):
    """
    Get the appropriate API URL based on MOCK_MODE setting.
    Args:
        lat: Latitude
        lon: Longitude  
        scenario: Test scenario name (only used in mock mode)
    Returns:
        Complete API URL string
    """
    if MOCK_MODE:
        if scenario:
            return MOCK_API_TEMPLATE.format(lat=lat, lon=lon, scenario=scenario)
        else:
            return MOCK_API_TEMPLATE.format(lat=lat, lon=lon, scenario="normal")
    else:
        return NWS_API_TEMPLATE.format(lat=lat, lon=lon)

def detect_hazard(alerts):
    """
    Check alerts and return the highest severity level found.
    Returns: "HIGH", "MEDIUM", or None
    Priority: HIGH > MEDIUM > None
    Only alerts that are currently effective are considered.
    """
    if not alerts:
        return None
    
    current_time = datetime.now(timezone.utc)
    high_triggers = ALERT_TYPES["HIGH"]["triggers"]
    medium_triggers = ALERT_TYPES["MEDIUM"]["triggers"]
    
    found_high = False
    found_medium = False
    
    for alert in alerts:
        try:
            props = alert.get("properties", {})
            event = props.get("event", "")
            
            # Check if alert is currently effective
            onset_str = props.get("onset")
            effective_str = props.get("effective") 
            expires_str = props.get("expires")
            
            # Use onset time if available, otherwise fall back to effective time
            start_time_str = onset_str or effective_str
            
            is_active = True  # Default to active if no timing info
            
            if start_time_str and expires_str:
                try:
                    start_time = dateutil.parser.parse(start_time_str)
                    end_time = dateutil.parser.parse(expires_str)
                    
                    # Check if current time is within the alert period
                    if start_time <= current_time <= end_time:
                        is_active = True
                    else:
                        is_active = False
                        # Log timing info for inactive alerts
                        current_pst = current_time.astimezone(timezone(timedelta(hours=-8)))
                        start_pst = start_time.astimezone(timezone(timedelta(hours=-8)))
                        end_pst = end_time.astimezone(timezone(timedelta(hours=-8)))
                        
                        print(f"⏰ Alert '{event}' found but not yet active:")
                        print(f"   Current: {current_pst.strftime('%I:%M %p PST %A, %b %d')}")
                        print(f"   Starts:  {start_pst.strftime('%I:%M %p PST %A, %b %d')}")
                        print(f"   Expires: {end_pst.strftime('%I:%M %p PST %A, %b %d')}")
                except Exception as e:
                    print(f"⚠️  Could not parse alert times for '{event}': {e}")
                    # If we can't parse times, treat as active (safe default)
                    is_active = True
            
            # Check for HIGH alerts (highest priority)
            if is_active and event in high_triggers:
                found_high = True
                # Don't return yet - keep checking all alerts
            
            # Check for MEDIUM alerts
            elif is_active and event in medium_triggers:
                found_medium = True
                    
        except (KeyError, AttributeError):
            continue
    
    # Return highest severity found
    if found_high:
        return "HIGH"
    elif found_medium:
        return "MEDIUM"
    else:
        return None

def get_alert_config(has_hazards=False, hazard_level=None):
    """
    Get the appropriate alert configuration based on hazard detection.
    Args:
        has_hazards: Boolean indicating if any hazards detected
        hazard_level: String - "HIGH", "MEDIUM", or None
    Returns the complete alert config object from JSON settings.
    """
    if hazard_level == "HIGH":
        return ALERT_TYPES["HIGH"]
    elif hazard_level == "MEDIUM":
        return ALERT_TYPES["MEDIUM"]
    else:
        return ALERT_TYPES["NORMAL"]

def get_console_message(has_hazards=False, hazard_type=None, hazard_level=None):
    """
    Get the appropriate console message from JSON config.
    Args:
        has_hazards: Boolean
        hazard_type: String name of specific hazard
        hazard_level: String - "HIGH", "MEDIUM", or None
    """
    if hazard_level == "HIGH" and hazard_type:
        return ALERT_TYPES["HIGH"]["console_message"].format(hazard_type=hazard_type)
    elif hazard_level == "HIGH":
        return ALERT_TYPES["HIGH"]["console_message"].format(hazard_type="Unknown hazard")
    elif hazard_level == "MEDIUM":
        return ALERT_TYPES["MEDIUM"]["console_message"]
    else:
        return ALERT_TYPES["NORMAL"]["console_message"]

# ========== Auto-Updater Configuration (from JSON) ==========
AUTO_UPDATER_CONFIG = SETTINGS.get("auto_updater", {})

def get_auto_updater_repo():
    """Get auto-updater repository configuration"""
    return AUTO_UPDATER_CONFIG.get("repository", {})

def get_auto_updater_check_interval():
    """Get auto-updater check interval in seconds"""
    return AUTO_UPDATER_CONFIG.get("update_settings", {}).get("check_interval", 120)

def get_auto_updater_enabled():
    """Check if auto-updater is enabled"""
    return AUTO_UPDATER_CONFIG.get("update_settings", {}).get("enabled", True)

def get_auto_updater_deployment():
    """Get auto-updater deployment configuration"""
    return AUTO_UPDATER_CONFIG.get("deployment", {})

def get_auto_updater_safety():
    """Get auto-updater safety configuration"""
    return AUTO_UPDATER_CONFIG.get("safety", {})

# ========== Configuration Summary ==========
def print_config_summary():
    """Print a summary of current configuration"""
    print("🔧 WaveAlert360 Simplified Configuration")
    print("=" * 45)
    print(f"📍 Location: {LOCATION_NAME}")
    print(f"🌐 API Mode: {'Mock' if MOCK_MODE else 'Live NWS'}")
    print(f"🎵 Audio Directory: {AUDIO_DIR}")
    print(f"⏱️  Check Interval: {CHECK_INTERVAL}s")
    print(f"☁️  Audio Generation: Azure Function (Cloud)")
    print(f"⏰ Auto-Updater: {'Enabled' if get_auto_updater_enabled() else 'Disabled'}")
    if get_auto_updater_enabled():
        repo = get_auto_updater_repo()
        print(f"📦 Update Repo: {repo.get('owner', 'N/A')}/{repo.get('name', 'N/A')}")
        print(f"⏰ Update Check: {get_auto_updater_check_interval()}s")
    print(f"📋 Settings: settings.json only")
    print("=" * 45)
