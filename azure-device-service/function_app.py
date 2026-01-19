#!/usr/bin/env python3
"""
WaveAlert360 Device Management Service - Azure Function
Manages multiple devices and provides alert coordination via Azure Functions
"""

import azure.functions as func
import json
import logging
import os
import requests
from datetime import datetime, timezone

app = func.FunctionApp()

# Configuration
GITHUB_DEVICES_URL = "https://api.github.com/repos/prasannapad/wavealert360/contents/devices.json"
NWS_USER_AGENT = 'WaveAlert360/1.0 (github.com/prasannapad/wavealert360)'

# Global cache for devices with timestamp
_devices_cache = None
_cache_timestamp = None
CACHE_TTL_SECONDS = 15  # Refresh every 15 seconds

def load_devices():
    """Load device registry from GitHub with 30-second caching"""
    global _devices_cache, _cache_timestamp
    
    # Check if cache is still valid
    if _devices_cache and _cache_timestamp:
        cache_age = (datetime.now(timezone.utc) - _cache_timestamp).total_seconds()
        if cache_age < CACHE_TTL_SECONDS:
            logging.info(f"📦 Using cached devices (age: {cache_age:.1f}s)")
            return _devices_cache
    
    # Cache expired or doesn't exist - fetch from GitHub
    try:
        headers = {'User-Agent': NWS_USER_AGENT}
        
        # Add GitHub token if available
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
            
        response = requests.get(GITHUB_DEVICES_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            # GitHub API returns base64-encoded content
            import base64
            content_data = response.json()
            content_b64 = content_data['content']
            content_decoded = base64.b64decode(content_b64).decode('utf-8')
            _devices_cache = json.loads(content_decoded)
            _cache_timestamp = datetime.now(timezone.utc)
            logging.info(f"✅ Refreshed devices from GitHub (cached for {CACHE_TTL_SECONDS}s)")
            return _devices_cache
        else:
            logging.warning(f"Failed to load devices from GitHub: {response.status_code}")
            if _devices_cache:  # Use stale cache if GitHub fails
                logging.info("📦 Using stale cached devices")
                return _devices_cache
            return get_fallback_devices()
    except Exception as e:
        logging.error(f"Error loading devices from GitHub: {e}")
        if _devices_cache:  # Use stale cache if error
            logging.info("📦 Using stale cached devices due to error")
            return _devices_cache
        return get_fallback_devices()

def get_fallback_devices():
    """Fallback device registry when GitHub is unavailable"""
    return {
        "devices": [
            {
                "mac_address": "88:a2:9e:0d:fb:17",
                "display_name": "Cowell Ranch State Beach Pi Device",
                "location_name": "Cowell Ranch State Beach",
                "lat": 37.421035,
                "lon": -122.434162,
                "nws_zone": "CAZ529",
                "operating_mode": "TEST",
                "test_scenario": "CAUTION",
                "audio_files": {
                    "SAFE": "https://raw.githubusercontent.com/prasannapad/wavealert360/main/device/alert_audio/normal_alert.mp3",
                    "CAUTION": "https://raw.githubusercontent.com/prasannapad/wavealert360/main/device/alert_audio/caution_alert.mp3",
                    "DANGER": "https://raw.githubusercontent.com/prasannapad/wavealert360/main/device/alert_audio/high_alert.mp3"
                }
            }
        ]
    }

def find_device_by_mac(mac_address):
    """Find device in registry by MAC address"""
    devices_data = load_devices()
    for device in devices_data['devices']:
        if device['mac_address'] == mac_address:
            return device
    return None

def get_nws_alert_level(device):
    """Get alert level from NWS API for device location"""
    try:
        nws_url = f"https://api.weather.gov/alerts/active?point={device['lat']},{device['lon']}"
        headers = {'User-Agent': NWS_USER_AGENT}
        
        response = requests.get(nws_url, headers=headers, timeout=10)
        if response.status_code == 200:
            alerts = response.json().get('features', [])
            return analyze_nws_alerts(alerts)
        else:
            logging.warning(f"NWS API error: {response.status_code}")
            return "CAUTION"  # Safe default
    except Exception as e:
        logging.error(f"NWS API exception: {e}")
        return "CAUTION"  # Safe default

def analyze_nws_alerts(alerts):
    """Analyze NWS alerts and return SAFE/CAUTION/DANGER"""
    # High priority danger keywords
    danger_keywords = [
        "High Surf Warning", 
        "Coastal Flood Warning",
        "Storm Warning",
        "Hurricane Warning"
    ]
    
    # Medium priority caution keywords
    caution_keywords = [
        "High Surf Advisory",
        "Beach Hazards Statement", 
        "Coastal Flood Advisory",
        "Special Weather Statement",
        "Rip Current Statement"
    ]
    
    for alert in alerts:
        event = alert.get('properties', {}).get('event', '')
        
        if any(keyword in event for keyword in danger_keywords):
            return "DANGER"
        elif any(keyword in event for keyword in caution_keywords):
            return "CAUTION"
    
    return "SAFE"

# Color mapping for LED control
COLOR_MAP = {
    "SAFE": "GREEN",
    "CAUTION": "YELLOW", 
    "DANGER": "RED"
}

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "WaveAlert360 Device Service"}),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="alert/{mac_address}", auth_level=func.AuthLevel.ANONYMOUS)
def get_alert(req: func.HttpRequest) -> func.HttpResponse:
    """Get current alert for a device by MAC address"""
    mac_address = req.route_params.get('mac_address')
    
    if not mac_address:
        return func.HttpResponse(
            json.dumps({"error": "mac_address required"}),
            status_code=400,
            mimetype="application/json"
        )
    
    device = find_device_by_mac(mac_address)
    
    if not device:
        return func.HttpResponse(
            json.dumps({
                "error": "Device not found - add device to devices.json manually", 
                "mac_address": mac_address,
                "fallback": {
                    "alert_level": "CAUTION",
                    "led_color": "YELLOW",
                    "audio_url": "https://raw.githubusercontent.com/prasannapad/wavealert360/main/audio/default_caution.mp3",
                    "device_mode": "FALLBACK"
                }
            }),
            status_code=404,
            mimetype="application/json"
        )
    
    # Determine alert level based on operating mode
    if device['operating_mode'] == 'TEST':
        alert_level = device['test_scenario']
        logging.info(f"Device {mac_address} in TEST mode: {alert_level}")
    else:  # LIVE mode
        alert_level = get_nws_alert_level(device)
        logging.info(f"Device {mac_address} in LIVE mode: {alert_level} (from NWS)")
    
    response_data = {
        "alert_level": alert_level,
        "led_color": COLOR_MAP[alert_level],
        "audio_url": device['audio_files'][alert_level],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_mode": device['operating_mode']
    }
    
    return func.HttpResponse(
        json.dumps(response_data),
        status_code=200,
        mimetype="application/json"
    )

# Registration removed - devices configured manually in JSON

@app.route(route="devices", auth_level=func.AuthLevel.ANONYMOUS)
def list_devices(req: func.HttpRequest) -> func.HttpResponse:
    """List all registered devices"""
    devices_data = load_devices()
    return func.HttpResponse(
        json.dumps(devices_data),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="devices/{mac_address}/mode", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def set_device_mode(req: func.HttpRequest) -> func.HttpResponse:
    """Set device operating mode (LIVE or TEST)"""
    mac_address = req.route_params.get('mac_address')
    
    try:
        req_body = req.get_json()
        mode = req_body.get('operating_mode')
        
        if mode not in ['LIVE', 'TEST']:
            return func.HttpResponse(
                json.dumps({"error": "operating_mode must be LIVE or TEST"}),
                status_code=400,
                mimetype="application/json"
            )
        
        device = find_device_by_mac(mac_address)
        if not device:
            return func.HttpResponse(
                json.dumps({"error": "Device not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        device['operating_mode'] = mode
        logging.info(f"✅ Set device {mac_address} to {mode} mode (NOTE: Change not persisted - update GitHub manually)")
        return func.HttpResponse(
            json.dumps({"status": f"Device {mac_address} mode change requested - update GitHub devices.json to persist"}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Set mode error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="devices/{mac_address}/test-scenario", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def set_test_scenario(req: func.HttpRequest) -> func.HttpResponse:
    """Set test scenario for device in TEST mode"""
    mac_address = req.route_params.get('mac_address')
    
    try:
        req_body = req.get_json()
        scenario = req_body.get('test_scenario')
        
        if scenario not in ['SAFE', 'CAUTION', 'DANGER']:
            return func.HttpResponse(
                json.dumps({"error": "test_scenario must be SAFE, CAUTION, or DANGER"}),
                status_code=400,
                mimetype="application/json"
            )
        
        device = find_device_by_mac(mac_address)
        if not device:
            return func.HttpResponse(
                json.dumps({"error": "Device not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        device['test_scenario'] = scenario
        logging.info(f"✅ Set device {mac_address} test scenario to {scenario} (NOTE: Change not persisted - update GitHub manually)")
        return func.HttpResponse(
            json.dumps({"status": f"Device {mac_address} test scenario change requested - update GitHub devices.json to persist"}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Set test scenario error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="dashboard", auth_level=func.AuthLevel.ANONYMOUS)
def dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """Admin dashboard for device management"""
    devices_data = load_devices()
    device_count = len(devices_data['devices'])
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WaveAlert360 Device Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .device {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .live {{ background-color: #e8f5e8; }}
            .test {{ background-color: #fff3cd; }}
            .status {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>🌊 WaveAlert360 Device Dashboard</h1>
        <p>Managing {device_count} devices</p>
        
        <div id="devices">
    """
    
    for device in devices_data['devices']:
        mode_class = device['operating_mode'].lower()
        dashboard_html += f"""
            <div class="device {mode_class}">
                <h3>{device['display_name']}</h3>
                <p><strong>MAC:</strong> {device['mac_address']}</p>
                <p><strong>Location:</strong> {device['location_name']}</p>
                <p><strong>Mode:</strong> <span class="status">{device['operating_mode']}</span></p>
                {"<p><strong>Test Scenario:</strong> " + device['test_scenario'] + "</p>" if device['operating_mode'] == 'TEST' else ""}
                <p><strong>Last Seen:</strong> {device['last_seen']}</p>
                <p><strong>Status:</strong> {device['status']}</p>
            </div>
        """
    
    dashboard_html += """
        </div>
        
        <h2>API Endpoints</h2>
        <ul>
            <li>GET /api/alert/{mac_address} - Get device alert</li>
            <li>POST /api/register - Register new device</li>
            <li>GET /api/devices - List all devices</li>
            <li>POST /api/devices/{mac}/mode - Set device mode</li>
            <li>POST /api/devices/{mac}/test-scenario - Set test scenario</li>
        </ul>
    </body>
    </html>
    """
    
    return func.HttpResponse(
        dashboard_html,
        status_code=200,
        mimetype="text/html"
    )
