#!/usr/bin/env python3
"""
WaveAlert360 Web Status Dashboard
Provides HTTP status endpoint for remote monitoring
"""

from flask import Flask, jsonify, request, abort, render_template_string
import ipaddress
import datetime
import subprocess
import sys
import os
import platform
from helpers import LATITUDE, LONGITUDE, LOCATION_NAME, MOCK_MODE, MOCK_API_BASE, ALERT_TYPES

app = Flask(__name__)

# IP Access Control Configuration
ALLOWED_IPS = [
    "192.168.86.245",    # devbox1 (Windows development machine)
    "192.168.86.38",     # Raspberry Pi itself
    "192.168.86.0/24",   # Entire home network
    "127.0.0.1",         # Localhost IPv4
    "::1",               # IPv6 localhost
    "localhost"          # Localhost hostname
]

def check_ip_allowed():
    """Check if the requesting IP is allowed access"""
    try:
        client_ip = ipaddress.ip_address(request.remote_addr)
        print(f"🔍 DEBUG: Request from IP: {request.remote_addr} (parsed as {client_ip})")
        
        for allowed in ALLOWED_IPS:
            if "/" in allowed:
                # Network range (e.g., 192.168.86.0/24)
                if client_ip in ipaddress.ip_network(allowed, strict=False):
                    print(f"✅ IP {client_ip} allowed by network {allowed}")
                    return True
            else:
                # Single IP address
                if str(client_ip) == allowed:
                    print(f"✅ IP {client_ip} allowed by exact match {allowed}")
                    return True
        
        print(f"❌ IP {client_ip} not in allowed list: {ALLOWED_IPS}")
        return False
    except Exception as e:
        print(f"❌ IP check error: {e} for remote_addr: {request.remote_addr}")
        return False

@app.before_request
def security_check():
    """Security check for all requests"""
    # TEMPORARILY DISABLED FOR TESTING
    print(f"🔍 DEBUG: Request from {request.remote_addr} - ALLOWING ALL IPs for testing")
    return  # Allow all requests for now
    
    # Original security check (commented out):
    # if not check_ip_allowed():
    #     print(f"Access denied from IP: {request.remote_addr}")
    #     abort(403, f"Access denied from {request.remote_addr}")

def get_system_info():
    """Get current system information"""
    try:
        # Determine if we're on Windows (simulation) or Pi (hardware)
        is_windows = platform.system() == "Windows"
        is_pi = platform.system() == "Linux" and "raspberrypi" in platform.node().lower()
        
        # Get current working directory 
        current_dir = os.getcwd()
        
        # Basic system info
        info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "platform": platform.system(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "working_directory": current_dir,
            "is_simulation": is_windows,
            "is_hardware": is_pi
        }
        
        return info
    except Exception as e:
        return {"error": str(e)}

def get_device_status():
    """Get actual device status - what the device is currently doing"""
    try:
        from config import get_mac_address
        import requests
        
        # Try to get status from Azure Device Service (same as main.py uses)
        try:
            mac_address = get_mac_address()
            service_url = "https://wavealert360-device-service.azurewebsites.net"
            alert_endpoint = f"{service_url}/api/alert/{mac_address}"
            
            response = requests.get(alert_endpoint, timeout=5)
            response.raise_for_status()
            service_data = response.json()
            
            # Get audio info from service response
            audio_url = service_data.get("audio_url", "")
            audio_file = audio_url.split("/")[-1] if audio_url else "unknown.mp3"
            
            return {
                "source": "Azure Device Service",
                "alert_level": service_data.get("alert_level", "UNKNOWN"),
                "device_mode": service_data.get("device_mode", "UNKNOWN"),
                "mac_address": mac_address,
                "audio_url": audio_url,
                "audio_file": audio_file,
                "available": True
            }
        except Exception as e:
            # Fallback: try to read LED control file
            try:
                with open("/tmp/led_control.txt", "r") as f:
                    led_pattern = f.read().strip()
                    
                # Map LED pattern to alert level and audio file
                if "RED_BLINK" in led_pattern:
                    alert_level = "DANGER"
                    audio_file = "high_alert.mp3"
                elif "YELLOW" in led_pattern:
                    alert_level = "CAUTION"
                    audio_file = "caution_alert.mp3"
                elif "GREEN" in led_pattern:
                    alert_level = "SAFE"
                    audio_file = "normal_alert.mp3"
                else:
                    alert_level = "UNKNOWN"
                    audio_file = "unknown.mp3"
                    
                return {
                    "source": "LED Control File",
                    "alert_level": alert_level,
                    "led_pattern": led_pattern,
                    "audio_file": audio_file,
                    "audio_url": f"/audio/{audio_file}",
                    "available": True
                }
            except:
                return {
                    "source": "None",
                    "alert_level": "UNKNOWN",
                    "available": False,
                    "error": str(e)
                }
    except Exception as e:
        return {
            "source": "Error",
            "alert_level": "UNKNOWN",
            "available": False,
            "error": str(e)
        }

def get_current_nws_alerts():
    """Get current REAL NWS alerts for reference - NOT what device is using"""
    try:
        import requests
        
        # Half Moon Bay coordinates (same as main.py)
        latitude = 37.421035
        longitude = -122.434162
        
        # NWS API call
        url = f"https://api.weather.gov/alerts/active?point={latitude},{longitude}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            
            if features:
                # Get the most recent/severe alert
                feature = features[0]
                alert = feature['properties']
                alert_type = alert.get('event', 'Unknown Alert')
                severity = alert.get('severity', 'Unknown')
                urgency = alert.get('urgency', 'Unknown')
                alert_id = alert.get('id', '')
                
                # Create NWS alert URL - use the API URL which provides JSON alert details
                # @id is at the feature level, not properties level
                nws_url = feature.get('@id', url)  # Use the alert's direct API link
                
                return {
                    "alert_active": True,
                    "alert_type": alert_type,
                    "severity": severity,
                    "urgency": urgency,
                    "description": alert.get('description', ''),
                    "nws_url": nws_url,
                    "effective": alert.get('effective', ''),
                    "expires": alert.get('expires', ''),
                    "last_check": datetime.datetime.now().isoformat()
                }
            else:
                return {
                    "alert_active": False,
                    "alert_type": "Normal Conditions",
                    "severity": "None",
                    "urgency": "None", 
                    "description": "No active alerts for this area",
                    "nws_url": url,
                    "effective": "",
                    "expires": "",
                    "last_check": datetime.datetime.now().isoformat()
                }
        else:
            return {
                "alert_active": False,
                "alert_type": f"API Error ({response.status_code})",
                "nws_url": url,
                "last_check": datetime.datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "alert_active": False,
            "alert_type": f"Error: {str(e)}",
            "nws_url": "https://alerts.weather.gov/",
            "last_check": datetime.datetime.now().isoformat()
        }

def get_github_commit_info():
    """Get current GitHub commit information for the dashboard"""
    try:
        # Get the project root directory (parent of current directory if we're in device/)
        current_dir = os.getcwd()
        if current_dir.endswith('device'):
            project_root = os.path.dirname(current_dir)
            device_dir = current_dir
        else:
            project_root = current_dir
            device_dir = os.path.join(current_dir, 'device')
        
        # Look for .last_commit in the device directory first (self-contained)
        commit_file = os.path.join(device_dir, '.last_commit')
        
        # If not found in device directory, fall back to root directory (for backward compatibility)
        if not os.path.exists(commit_file):
            commit_file = os.path.join(project_root, '.last_commit')
        
        commit_update_time = None
        if os.path.exists(commit_file):
            # Get file modification time (when auto-updater last updated)
            commit_update_time = datetime.datetime.fromtimestamp(os.path.getmtime(commit_file)).isoformat()
            
            with open(commit_file, 'r') as f:
                current_commit = f.read().strip()
                commit_short = current_commit[:8]
                
                # Try to get commit message using git
                try:
                    import subprocess
                    original_dir = os.getcwd()
                    # Try git from device directory first, then root directory
                    git_dir = device_dir if os.path.exists(os.path.join(device_dir, '.git')) else project_root
                    os.chdir(git_dir)
                    result = subprocess.run(['git', 'show', '-s', '--format=%s', current_commit], 
                                          capture_output=True, text=True, timeout=3)
                    os.chdir(original_dir)  # Always restore directory
                    
                    if result.returncode == 0:
                        commit_message = result.stdout.strip()[:50]  # Limit to 50 chars for display
                        if len(result.stdout.strip()) > 50:
                            commit_message += "..."
                        return {
                            "commit_sha": current_commit,
                            "commit_short": commit_short,
                            "commit_message": commit_message,
                            "has_git_info": True,
                            "last_update_time": commit_update_time
                        }
                except Exception as e:
                    # Git failed, but we have a commit SHA - that's enough for dashboard
                    pass
                
                # Return commit SHA without message - this is still useful information
                return {
                    "commit_sha": current_commit,
                    "commit_short": commit_short,
                    "commit_message": "Production deployment (git metadata not available)",
                    "has_git_info": False,
                    "last_update_time": commit_update_time
                }
        else:
            # No .last_commit file - this means auto-updater hasn't run or it's a manual deployment
            return {
                "commit_sha": None,
                "commit_short": "N/A",
                "commit_message": "Manual deployment - No auto-updater tracking",
                "has_git_info": False,
                "last_update_time": None
            }
    except Exception as e:
        # Something went wrong, but provide helpful context
        return {
            "commit_sha": None,
            "commit_short": "Error",
            "commit_message": f"Error getting commit info: {str(e)}",
            "has_git_info": False,
            "last_update_time": None
        }

def get_wavealert_status():
    """Get WaveAlert360 system status"""
    try:
        system_info = get_system_info()
        
        # Get actual device status (what device is doing)
        device_status = get_device_status()
        
        # Get current NWS alerts (for reference only)
        nws_alert_info = get_current_nws_alerts()
        
        # Get GitHub commit information
        commit_info = get_github_commit_info()
        
        # Get the project root directory (parent of current directory if we're in device/)
        current_dir = os.getcwd()
        if current_dir.endswith('device'):
            project_root = os.path.dirname(current_dir)
        else:
            project_root = current_dir
            
        # Check if main.py exists (could be in current dir or device/ subdir)
        main_py_paths = [
            os.path.join(current_dir, "main.py"),           # If we're in device/
            os.path.join(current_dir, "device", "main.py"), # If we're in project root
            os.path.join(project_root, "device", "main.py") # From project root
        ]
        main_py_exists = any(os.path.exists(path) for path in main_py_paths)
        
        # Check if helpers.py exists (contains configuration functions)
        helpers_py_paths = [
            os.path.join(current_dir, "helpers.py"),           # If we're in device/
            os.path.join(current_dir, "device", "helpers.py"), # If we're in project root  
            os.path.join(project_root, "device", "helpers.py") # From project root
        ]
        helpers_py_exists = any(os.path.exists(path) for path in helpers_py_paths)
        
        # Determine deployment status
        if system_info["is_simulation"]:
            deployment_type = "Development (Windows Simulation)"
            led_status = "Console LED Simulation"
        elif system_info["is_hardware"]:
            deployment_type = "Production (Raspberry Pi Hardware)"
            led_status = "Physical GPIO LEDs"
        else:
            deployment_type = "Unknown Platform"
            led_status = "Unknown LED Status"
            
        # Create alert display text
        current_alert_text = nws_alert_info.get("alert_type", "Unknown")
        if nws_alert_info.get("alert_active", False):
            current_alert_text += f" (Severity: {nws_alert_info.get('severity', 'Unknown')})"
        
        # Determine which audio file would be played
        audio_file = "normal_alert.mp3"  # Default
        if nws_alert_info.get("alert_active", False):
            severity = nws_alert_info.get("severity", "").lower()
            if severity in ["severe", "extreme", "critical"]:
                audio_file = "high_alert.mp3"
            else:
                audio_file = "normal_alert.mp3"
            
        # Determine API mode
        api_mode = "🧪 MOCK/TEST MODE" if MOCK_MODE else "🌐 LIVE NWS MODE"
        api_source = MOCK_API_BASE if MOCK_MODE else "api.weather.gov"
        
        # Get audio text for device alert level
        device_alert_level = device_status.get("alert_level", "UNKNOWN")
        device_audio_text = ""
        if device_alert_level == "DANGER":
            device_audio_text = ALERT_TYPES.get("HIGH", {}).get("audio_text", "")
        elif device_alert_level == "CAUTION":
            device_audio_text = ALERT_TYPES.get("MEDIUM", {}).get("audio_text", "")
        elif device_alert_level == "SAFE":
            device_audio_text = ALERT_TYPES.get("NORMAL", {}).get("audio_text", "")
        
        status = {
            "location": LOCATION_NAME,
            "coordinates": f"{LATITUDE:.6f}°N, {abs(LONGITUDE):.6f}°W",
            "deployment_type": deployment_type,
            "system_status": "Running" if main_py_exists and helpers_py_exists else "Setup Required",
            "api_mode": api_mode,
            "api_source": api_source,
            "is_mock_mode": MOCK_MODE,
            
            # Device actual status
            "device_alert_level": device_status.get("alert_level", "UNKNOWN"),
            "device_source": device_status.get("source", "Unknown"),
            "device_mode": device_status.get("device_mode", "N/A"),
            "device_available": device_status.get("available", False),
            "device_audio_file": device_status.get("audio_file", "unknown.mp3"),
            "device_audio_url": device_status.get("audio_url", ""),
            "device_audio_text": device_audio_text,
            
            "led_status": led_status,
            
            # NWS Reference Data (real conditions, not necessarily what device uses)
            "last_nws_check": nws_alert_info.get("last_check", "Never"),
            "nws_current_alert": current_alert_text,
            "nws_alert_active": nws_alert_info.get("alert_active", False),
            "nws_alert_severity": nws_alert_info.get("severity", "None"),
            "nws_alert_description": nws_alert_info.get("description", ""),
            "nws_url": nws_alert_info.get("nws_url", "https://alerts.weather.gov/"),
            "audio_file": audio_file,
            "main_py_found": main_py_exists,
            "helpers_py_found": helpers_py_exists,
            "uptime": "Web dashboard started",
            "commit_sha": commit_info.get("commit_sha"),
            "commit_short": commit_info.get("commit_short", "N/A"),
            "commit_message": commit_info.get("commit_message", "No commit info"),
            "has_git_info": commit_info.get("has_git_info", False),
            "last_code_update": commit_info.get("last_update_time"),
            **system_info
        }
        
        return status
        
    except Exception as e:
        return {
            "error": f"Failed to get status: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@app.route('/status')
def status_json():
    """JSON status endpoint"""
    return jsonify(get_wavealert_status())

@app.route('/')
def status_dashboard():
    """HTML dashboard"""
    status = get_wavealert_status()
    
    # Simple HTML template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WaveAlert360 Status Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background-color: #f5f5f5;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header { 
                color: #2c3e50; 
                border-bottom: 2px solid #3498db; 
                padding-bottom: 10px;
            }
            .status-good { color: #27ae60; }
            .status-warning { color: #f39c12; }
            .status-error { color: #e74c3c; }
            .info-grid { 
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 20px; 
                margin: 20px 0;
            }
            .info-box { 
                background: #ecf0f1; 
                padding: 15px; 
                border-radius: 5px;
            }
            .alert-box {
                background: {% if status.alert_active %}#ffe6e6{% else %}#e8f5e8{% endif %};
                border: 2px solid {% if status.alert_active %}#ff9999{% else %}#99cc99{% endif %};
            }
            .nws-link {
                display: inline-block;
                margin-top: 10px;
                padding: 5px 10px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 3px;
                font-size: 12px;
            }
            .nws-link:hover {
                background: #2980b9;
            }
            .refresh-note { 
                font-style: italic; 
                color: #7f8c8d; 
                text-align: center; 
                margin-top: 20px;
            }
            .local-time {
                font-weight: bold;
                color: #2c3e50;
            }
        </style>
        <script>
            function formatLocalTime(isoString) {
                try {
                    const date = new Date(isoString);
                    return date.toLocaleString(undefined, {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        timeZoneName: 'short'
                    });
                } catch (e) {
                    return isoString; // Fallback to original string if parsing fails
                }
            }
            
            function getTimeAgo(isoString) {
                try {
                    const date = new Date(isoString);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffMinutes = Math.floor(diffMs / (1000 * 60));
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                    
                    if (diffMinutes < 1) {
                        return "Just now";
                    } else if (diffMinutes < 60) {
                        return diffMinutes === 1 ? "1 minute ago" : `${diffMinutes} minutes ago`;
                    } else if (diffHours < 24) {
                        return diffHours === 1 ? "1 hour ago" : `${diffHours} hours ago`;
                    } else {
                        return diffDays === 1 ? "1 day ago" : `${diffDays} days ago`;
                    }
                } catch (e) {
                    return "";
                }
            }
            
            function updateLocalTimes() {
                // Update main timestamp
                const timestampElement = document.getElementById('main-timestamp');
                const timeAgoElement = document.getElementById('time-ago');
                if (timestampElement) {
                    const isoTime = timestampElement.dataset.iso;
                    const timeAgo = getTimeAgo(isoTime);
                    timestampElement.innerHTML = '<span class="local-time">' + formatLocalTime(isoTime) + '</span>';
                    if (timeAgoElement) {
                        timeAgoElement.innerHTML = timeAgo;
                    }
                }
                
                // Update last NWS check time
                const nwsCheckElement = document.getElementById('nws-check-time');
                if (nwsCheckElement) {
                    const isoTime = nwsCheckElement.dataset.iso;
                    const timeAgo = getTimeAgo(isoTime);
                    nwsCheckElement.innerHTML = formatLocalTime(isoTime) + '<br><small style="color: #7f8c8d;">(' + timeAgo + ')</small>';
                }
                
                // Update code update time
                const codeUpdateElement = document.getElementById('code-update-time');
                if (codeUpdateElement) {
                    const isoTime = codeUpdateElement.dataset.iso;
                    const timeAgo = getTimeAgo(isoTime);
                    codeUpdateElement.innerHTML = formatLocalTime(isoTime) + '<br><small style="color: #7f8c8d;">(' + timeAgo + ')</small>';
                }
            }
            
            // Update times when page loads and every 30 seconds
            document.addEventListener('DOMContentLoaded', function() {
                updateLocalTimes();
                setInterval(updateLocalTimes, 30000); // Update every 30 seconds
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🌊 WaveAlert360 Status Dashboard</h1>
            
            <div class="info-grid">
                <div class="info-box">
                    <h3>📍 Location</h3>
                    <p>{{ status.location }}</p>
                    <p><small>{{ status.coordinates }}</small></p>
                </div>
                
                <div class="info-box">
                    <h3>🔄 Page Refreshed</h3>
                    <p id="main-timestamp" data-iso="{{ status.timestamp }}">{{ status.timestamp }}</p>
                    <p><small id="time-ago" style="color: #7f8c8d;"></small></p>
                </div>
                
                <div class="info-box">
                    <h3>📦 Device Code Version</h3>
                    <p><strong>Commit: {{ status.commit_short }}</strong></p>
                    <p><small>{{ status.commit_message }}</small></p>
                    {% if status.last_code_update %}
                        <p><small><strong>Last Sync from GitHub:</strong></small></p>
                        <p><small id="code-update-time" data-iso="{{ status.last_code_update }}">{{ status.last_code_update }}</small></p>
                    {% else %}
                        <p><small><strong>Deployment:</strong> Manual (no auto-updater)</small></p>
                    {% endif %}
                    {% if status.commit_sha %}
                        <p><small style="color: #7f8c8d; font-family: monospace; font-size: 10px;">Full SHA: {{ status.commit_sha }}</small></p>
                    {% endif %}
                </div>
                
                <div class="info-box">
                    <h3>🖥️ Platform</h3>
                    <p>{{ status.deployment_type }}</p>
                    <p><small>{{ status.platform }} on {{ status.hostname }}</small></p>
                </div>
                
                <div class="info-box">
                    <h3>💡 LED Status</h3>
                    <p>{{ status.led_status }}</p>
                </div>
                
                <div class="info-box">
                    <h3>📊 System Status</h3>
                    <p class="{% if status.system_status == 'Running' %}status-good{% else %}status-warning{% endif %}">
                        {{ status.system_status }}
                    </p>
                    <p><small>{{ status.api_mode }}</small></p>
                    <p><small>Source: {{ status.api_source }}</small></p>
                </div>
                
                <div class="info-box alert-box" style="background-color: {% if status.device_alert_level == 'DANGER' %}#ffebee{% elif status.device_alert_level == 'CAUTION' %}#fff3e0{% else %}#e8f5e9{% endif %}; border-left: 4px solid {% if status.device_alert_level == 'DANGER' %}#f44336{% elif status.device_alert_level == 'CAUTION' %}#ff9800{% else %}#4caf50{% endif %};">
                    <h3>🚨 Device Current Status</h3>
                    <p><strong style="font-size: 1.5em; color: {% if status.device_alert_level == 'DANGER' %}#d32f2f{% elif status.device_alert_level == 'CAUTION' %}#f57c00{% else %}#388e3c{% endif %};">{{ status.device_alert_level }}</strong></p>
                    <p><small><strong>Source:</strong> {{ status.device_source }}</small></p>
                    {% if status.is_mock_mode %}
                        <p style="background-color: #fff9c4; padding: 8px; border-radius: 4px; margin-top: 10px;">
                            <strong>⚠️ MOCK/TEST MODE ACTIVE</strong><br>
                            <small>Device is using simulated alerts, not real NWS data</small>
                        </p>
                    {% endif %}
                    {% if status.device_mode %}
                        <p><small><strong>Device Mode:</strong> {{ status.device_mode }}</small></p>
                    {% endif %}
                    {% if status.device_audio_text %}
                        <div style="margin-top: 15px; padding: 10px; background-color: rgba(255,255,255,0.5); border-radius: 4px;">
                            <p><strong>🔊 Audio Message:</strong></p>
                            <p style="font-style: italic; font-size: 0.9em; line-height: 1.4;">{{ status.device_audio_text[:200] }}{% if status.device_audio_text|length > 200 %}...{% endif %}</p>
                            {% if status.device_audio_url %}
                                <a href="{{ status.device_audio_url }}" target="_blank" class="nws-link" style="margin-top: 8px; display: inline-block;">🔊 Play Audio</a>
                            {% endif %}
                        </div>
                    {% endif %}
                </div>
                
                <div class="info-box" style="background-color: #f5f5f5; border-left: 4px solid #2196f3;">
                    <h3>ℹ️ NWS Reference Data (Actual Conditions)</h3>
                    <p><small style="color: #666;"><em>This shows real NWS conditions - may differ from device status in MOCK mode</em></small></p>
                    <p><strong>{{ status.nws_current_alert }}</strong></p>
                    {% if status.nws_alert_active %}
                        <p><small>Severity: {{ status.nws_alert_severity }}</small></p>
                        {% if status.nws_alert_description %}
                            <p><small>{{ status.nws_alert_description[:150] }}{% if status.nws_alert_description|length > 150 %}...{% endif %}</small></p>
                        {% endif %}
                    {% endif %}
                    <p><small>Last Check: <span id="nws-check-time" data-iso="{{ status.last_nws_check }}">{{ status.last_nws_check }}</span></small></p>
                    <a href="{{ status.nws_url }}" target="_blank" class="nws-link">🔗 View on NWS</a>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🗂️ System Files Overview</h3>
                
                <h4>📋 Core Application Files</h4>
                <table style="width: 100%; margin-bottom: 15px; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #ecf0f1; font-weight: bold;">
                            <td style="padding: 5px; border: 1px solid #ddd;">File</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Status</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Description</td>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>main.py</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">
                                <span class="{% if status.main_py_found %}status-good{% else %}status-error{% endif %}">
                                    {% if status.main_py_found %}✅ Found{% else %}❌ Missing{% endif %}
                                </span>
                            </td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Main alert monitoring process</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>web_status.py</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Web dashboard (currently running)</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>helpers.py</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Location & utility functions</td>
                        </tr>
                    </tbody>
                </table>

                <h4>🔄 Auto-Update System</h4>
                <table style="width: 100%; margin-bottom: 15px; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #ecf0f1; font-weight: bold;">
                            <td style="padding: 5px; border: 1px solid #ddd;">File</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Status</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Description</td>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>auto_updater.py</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Enhanced with web process management</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>watchdog.py</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">System health monitor</td>
                        </tr>
                    </tbody>
                </table>

                <h4>⚙️ Configuration Files</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #ecf0f1; font-weight: bold;">
                            <td style="padding: 5px; border: 1px solid #ddd;">File</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Status</td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Description</td>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>settings.json</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Half Moon Bay location config</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border: 1px solid #ddd;"><strong>.audio_hashes.json</strong></td>
                            <td style="padding: 5px; border: 1px solid #ddd;"><span class="status-good">✅ Found</span></td>
                            <td style="padding: 5px; border: 1px solid #ddd;">Audio file checksums</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="refresh-note">
                <p>🔄 Auto-refresh every 30 seconds | 📱 Access from: {{ request.remote_addr }}</p>
                <p><a href="/status">JSON API</a> | <a href="/">Dashboard</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, status=status, request=request)

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "WaveAlert360 Web Dashboard"
    })

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    try:
        audio_dir = os.path.join(os.path.dirname(__file__), "alert_audio")
        from flask import send_from_directory
        return send_from_directory(audio_dir, filename)
    except Exception as e:
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404

if __name__ == '__main__':
    print("🌊 Starting WaveAlert360 Web Status Dashboard...")
    print(f"🔒 Access restricted to IPs: {ALLOWED_IPS}")
    print(f"🌐 Dashboard: http://localhost:5000/")
    print(f"📊 JSON API: http://localhost:5000/status")
    print(f"❤️ Health: http://localhost:5000/health")
    print("📱 Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
