import azure.functions as func
import logging
import json
import os
import urllib.request
import urllib.parse
import base64
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime, timezone, timedelta

app = func.FunctionApp()

# Configuration
GITHUB_REPO = "prasannapad/wavealert360"
SETTINGS_FILE_PATH = "device/settings.json"

# Global execution log storage (in-memory)
execution_logs = []

def log_execution(status, details, changes_detected=False, files_updated=None, commit_id=None):
    """Log execution details for dashboard"""
    global execution_logs
    
    timestamp = datetime.now(timezone.utc)
    pst_time = utc_to_pst(timestamp)
    
    log_entry = {
        "timestamp": timestamp.isoformat(),
        "timestamp_pst": pst_time.strftime("%Y-%m-%d %H:%M:%S PST"),
        "status": status,
        "details": details,
        "changes_detected": changes_detected,
        "files_updated": files_updated or [],
        "execution_time": timestamp.strftime("%H:%M:%S UTC"),
        "execution_time_pst": pst_time.strftime("%H:%M:%S PST")
    }
    
    # Add commit ID if provided
    if commit_id:
        log_entry["commit_id"] = commit_id
    
    # Keep only last hour of logs (20 entries for 3-minute intervals)
    execution_logs.append(log_entry)
    cutoff_time = datetime.now(timezone.utc).timestamp() - 3600  # 1 hour ago
    execution_logs[:] = [log for log in execution_logs 
                        if datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00')).timestamp() > cutoff_time]

def get_github_token():
    """Get GitHub token from environment variable"""
    return os.environ.get('GITHUB_TOKEN')

def get_azure_speech_config():
    """Get Azure Speech configuration from environment variables"""
    return {
        'key': os.environ.get('AZURE_SPEECH_KEY'),
        'region': os.environ.get('AZURE_SPEECH_REGION', 'eastus')
    }

def calculate_md5(content):
    """Calculate MD5 hash of content"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def utc_to_pst(utc_dt):
    """Convert UTC datetime to PST/PDT"""
    if isinstance(utc_dt, str):
        utc_dt = datetime.fromisoformat(utc_dt.replace('Z', '+00:00'))
    
    # PST is UTC-8, PDT is UTC-7
    # Simple approach: assume PST (UTC-8) for now
    pst_offset = timedelta(hours=-8)
    pst_dt = utc_dt.replace(tzinfo=timezone.utc) + pst_offset
    return pst_dt

def format_pst_time(utc_dt):
    """Format UTC datetime as PST string"""
    pst_dt = utc_to_pst(utc_dt)
    return pst_dt.strftime("%Y-%m-%d %H:%M:%S PST")

def create_ssml(text, voice, style="friendly", rate="medium"):
    """Create SSML for Azure Speech Services"""
    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{voice}">
            <prosody rate="{rate}">
                <mstts:express-as style="{style}" xmlns:mstts="https://www.w3.org/2001/mstts">
                    {text}
                </mstts:express-as>
            </prosody>
        </voice>
    </speak>
    """.strip()
    return ssml

def generate_audio_with_urllib(text, voice, style, region, subscription_key):
    """Generate audio using Azure Speech Services with urllib"""
    # Get access token
    token_url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    token_request = urllib.request.Request(token_url, method='POST')
    token_request.add_header('Ocp-Apim-Subscription-Key', subscription_key)
    token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    with urllib.request.urlopen(token_request) as response:
        if response.status != 200:
            raise Exception(f"Failed to get access token: {response.status}")
        access_token = response.read().decode()
    
    # Generate SSML
    ssml = create_ssml(text, voice, style)
    
    # Make speech request
    speech_url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    speech_request = urllib.request.Request(speech_url, method='POST')
    speech_request.add_header('Authorization', f'Bearer {access_token}')
    speech_request.add_header('Content-Type', 'application/ssml+xml')
    speech_request.add_header('X-Microsoft-OutputFormat', 'audio-16khz-128kbitrate-mono-mp3')
    speech_request.add_header('User-Agent', 'WaveAlert360-Azure-Function')
    
    speech_data = ssml.encode('utf-8')
    
    with urllib.request.urlopen(speech_request, data=speech_data) as response:
        if response.status == 200:
            return response.read()
        else:
            raise Exception(f"Speech synthesis failed: {response.status}")

def get_file_from_github(file_path, token):
    """Get file content from GitHub using urllib"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"token {token}")
    request.add_header("Accept", "application/vnd.github.v3+json")
    request.add_header("User-Agent", "WaveAlert360-Azure-Function")
    
    with urllib.request.urlopen(request) as response:
        if response.status == 200:
            return json.loads(response.read().decode())
        else:
            raise Exception(f"GitHub file fetch failed: {response.status}")

def commit_file_to_github(file_path, content, message, token, is_binary=False):
    """Commit a file to GitHub repository using urllib"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    
    # First, try to get existing file to get its SHA
    existing_sha = None
    try:
        existing_file = get_file_from_github(file_path, token)
        existing_sha = existing_file['sha']
    except:
        pass  # File doesn't exist yet
    
    # Prepare content
    if is_binary:
        content_b64 = base64.b64encode(content).decode()
    else:
        content_b64 = base64.b64encode(content.encode('utf-8')).decode()
    
    # Prepare commit data
    commit_data = {
        "message": message,
        "content": content_b64,
        "branch": "main"
    }
    
    if existing_sha:
        commit_data["sha"] = existing_sha
    
    # Make commit request
    request = urllib.request.Request(url, method='PUT')
    request.add_header("Authorization", f"token {token}")
    request.add_header("Accept", "application/vnd.github.v3+json")
    request.add_header("User-Agent", "WaveAlert360-Azure-Function")
    request.add_header("Content-Type", "application/json")
    
    commit_json = json.dumps(commit_data).encode('utf-8')
    
    with urllib.request.urlopen(request, data=commit_json) as response:
        if response.status in [200, 201]:
            return json.loads(response.read().decode())
        else:
            raise Exception(f"GitHub commit failed: {response.status}")

def get_stored_audio_hashes(token):
    """Get stored hashes of previous audio texts to detect changes"""
    try:
        hash_file = get_file_from_github("device/alert_audio/.audio_hashes.json", token)
        hash_content = base64.b64decode(hash_file['content']).decode('utf-8')
        return json.loads(hash_content)
    except:
        return {"normal_text_hash": "", "high_text_hash": ""}

def store_audio_hashes(hashes, token):
    """Store hashes of current audio texts for future comparison"""
    hash_content = json.dumps(hashes, indent=2)
    commit_file_to_github(
        "device/alert_audio/.audio_hashes.json",
        hash_content,
        "Update audio text hashes for change detection",
        token,
        is_binary=False
    )

def calculate_text_hash(text):
    """Calculate simple hash of text for change detection"""
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()

@app.route(route="ping", auth_level=func.AuthLevel.ANONYMOUS)
def ping(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Ping function triggered')
    return func.HttpResponse("PONG - WITH URLLIB", status_code=200)

@app.route(route="dashboard", auth_level=func.AuthLevel.ANONYMOUS)
def dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """Web dashboard showing last hour of execution logs"""
    logging.info('Dashboard function triggered')
    
    try:
        # Get current time for display in PST
        current_utc = datetime.now(timezone.utc)
        current_pst = utc_to_pst(current_utc)
        current_time = current_pst.strftime("%Y-%m-%d %H:%M:%S PST")
        
        # Create HTML dashboard
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>WaveAlert360 Audio Generator Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .status-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .success { border-left: 5px solid #28a745; }
        .no-changes { border-left: 5px solid #6c757d; }
        .error { border-left: 5px solid #dc3545; }
        .timestamp { color: #666; font-size: 0.9em; }
        .details { margin: 10px 0; }
        .files-updated { background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .no-data { text-align: center; color: #666; font-style: italic; }
        .refresh-info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { background: white; padding: 15px; border-radius: 10px; flex: 1; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
    </style>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() { window.location.reload(); }, 30000);
        
        // Convert UTC timestamps to browser timezone and show "X minutes ago"
        function formatTimestamp(utcTimestamp) {
            const date = new Date(utcTimestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / (1000 * 60));
            
            // Format in browser timezone
            const localTime = date.toLocaleTimeString([], {
                hour: '2-digit', 
                minute: '2-digit',
                timeZoneName: 'short'
            });
            
            // Show "X minutes ago"
            let timeAgo;
            if (diffMins < 1) {
                timeAgo = "just now";
            } else if (diffMins === 1) {
                timeAgo = "1 minute ago";
            } else if (diffMins < 60) {
                timeAgo = `${diffMins} minutes ago`;
            } else {
                const hours = Math.floor(diffMins / 60);
                timeAgo = hours === 1 ? "1 hour ago" : `${hours} hours ago`;
            }
            
            return `${localTime} (${timeAgo})`;
        }
        
        // Update all timestamps when page loads
        document.addEventListener('DOMContentLoaded', function() {
            const timestampElements = document.querySelectorAll('.utc-timestamp');
            timestampElements.forEach(function(element) {
                const utcTime = element.getAttribute('data-utc');
                element.textContent = element.textContent.replace('[TIMESTAMP]', formatTimestamp(utcTime));
            });
            
            // Update current time in header
            const headerTime = document.getElementById('current-time');
            if (headerTime) {
                const now = new Date();
                headerTime.textContent = now.toLocaleString([], {
                    timeZoneName: 'short'
                });
            }
        });
    </script>
</head>
<body>
    <div class="header">
        <h1>🎵 WaveAlert360 Audio Generator Dashboard</h1>
        <p>Last Hour Execution History | Current Time: <span id="current-time">Loading...</span></p>
        <p>⏱️ Runs every 3 minutes | 🔄 Auto-refresh in 30 seconds</p>
    </div>
    
    <div class="refresh-info">
        <strong>📊 Live Monitoring:</strong> This dashboard shows the execution history for the last hour. 
        The Azure Function runs every 3 minutes to check for changes in alert settings and generate new audio files when needed.
    </div>
"""
        
        if execution_logs:
            # Calculate stats
            total_runs = len(execution_logs)
            changes_detected = len([log for log in execution_logs if log["changes_detected"]])
            successful_runs = len([log for log in execution_logs if log["status"] == "success"])
            
            html_content += f"""
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{total_runs}</div>
            <div>Total Runs</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{changes_detected}</div>
            <div>Changes Detected</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{successful_runs}</div>
            <div>Successful Runs</div>
        </div>
    </div>
"""
            
            # Display logs in reverse chronological order
            for log in reversed(execution_logs):
                status_class = "success" if log["status"] == "success" else "error"
                if log["status"] == "success" and not log["changes_detected"]:
                    status_class = "no-changes"
                
                icon = "✅" if log["status"] == "success" else "❌"
                if log["status"] == "success" and not log["changes_detected"]:
                    icon = "⏭️"
                
                files_html = ""
                if log["files_updated"]:
                    files_html = f"""
                    <div class="files-updated">
                        <strong>📁 Files Updated:</strong> {', '.join(log["files_updated"])}
                    </div>"""
                
                html_content += f"""
    <div class="status-card {status_class}">
        <div class="timestamp utc-timestamp" data-utc="{log["timestamp"]}">{icon} [TIMESTAMP]</div>
        <div class="details">{log["details"]}</div>
        {files_html}
    </div>
"""
        else:
            html_content += """
    <div class="status-card no-data">
        <div class="no-data">📭 No execution logs available yet. The timer function will start logging once it runs.</div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        return func.HttpResponse(
            html_content,
            status_code=200,
            mimetype="text/html"
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Dashboard error: {error_msg}")
        return func.HttpResponse(
            f"<html><body><h1>Dashboard Error</h1><p>{error_msg}</p></body></html>",
            status_code=500,
            mimetype="text/html"
        )

@app.route(route="status", auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Get last 5 execution logs as JSON"""
    logging.info('Status API function triggered')
    
    try:
        # Get last 5 logs (or all if less than 5)
        recent_logs = execution_logs[-5:] if len(execution_logs) >= 5 else execution_logs
        
        # Create response data with PST times
        current_utc = datetime.now(timezone.utc)
        current_pst = utc_to_pst(current_utc)
        
        response_data = {
            "total_logs": len(execution_logs),
            "last_5_executions": recent_logs,
            "current_time_utc": current_utc.isoformat(),
            "current_time_pst": current_pst.strftime("%Y-%m-%d %H:%M:%S PST"),
            "timer_interval": "every 3 minutes"
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Status API error: {error_msg}")
        return func.HttpResponse(
            json.dumps({
                "error": error_msg,
                "status": "error"
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="test_github", auth_level=func.AuthLevel.ANONYMOUS)
def test_github(req: func.HttpRequest) -> func.HttpResponse:
    """Test GitHub API access using urllib"""
    logging.info('GitHub test function triggered')
    
    try:
        github_token = get_github_token()
        if not github_token:
            raise Exception("GitHub token not configured")
        
        # Get settings from GitHub
        logging.info("Fetching settings from GitHub...")
        settings_data = get_file_from_github(SETTINGS_FILE_PATH, github_token)
        settings_content = base64.b64decode(settings_data['content']).decode('utf-8')
        settings = json.loads(settings_content)
        
        # Get the texts
        normal_text = settings['alert_types']['NORMAL']['audio_text']
        high_text = settings['alert_types']['HIGH']['audio_text']
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "github_api_working": True,
                "settings_loaded": True,
                "normal_text_length": len(normal_text),
                "high_text_length": len(high_text),
                "high_text_preview": high_text[:100] + "...",
                "method": "urllib"
            }, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"GitHub test function failed: {error_msg}")
        return func.HttpResponse(
            json.dumps({
                "status": "error", 
                "error": error_msg
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="generate_audio", auth_level=func.AuthLevel.ANONYMOUS)
def generate_audio(req: func.HttpRequest) -> func.HttpResponse:
    """Generate audio for alert types"""
    logging.info('Audio generation function triggered')
    
    try:
        # Get alert type from query parameter
        alert_type = req.params.get('alert_type', 'NORMAL').upper()
        if alert_type not in ['NORMAL', 'HIGH']:
            alert_type = 'NORMAL'
        
        # Get configuration
        github_token = get_github_token()
        if not github_token:
            raise Exception("GitHub token not configured")
        
        speech_config = get_azure_speech_config()
        if not speech_config['key']:
            raise Exception("Azure Speech key not configured")
        
        # Get settings from GitHub
        logging.info("Fetching settings from GitHub...")
        settings_data = get_file_from_github(SETTINGS_FILE_PATH, github_token)
        settings_content = base64.b64decode(settings_data['content']).decode('utf-8')
        settings = json.loads(settings_content)
        
        # Get alert configuration
        alert_config = settings['alert_types'][alert_type]
        audio_text = alert_config['audio_text']
        
        # Get Azure configuration
        azure_config = settings['azure']
        voice = azure_config['voices']['normal'] if alert_type == 'NORMAL' else azure_config['voices']['high_alert']
        style = azure_config['styles']['normal'] if alert_type == 'NORMAL' else azure_config['styles']['high_alert']
        
        logging.info(f"Generating audio for {alert_type} alert using voice {voice} with style {style}")
        
        # Generate audio
        audio_data = generate_audio_with_urllib(
            text=audio_text,
            voice=voice,
            style=style,
            region=speech_config['region'],
            subscription_key=speech_config['key']
        )
        
        # Return audio file
        filename = f"{alert_type.lower()}_alert.mp3"
        return func.HttpResponse(
            audio_data,
            status_code=200,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Audio generation failed: {error_msg}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": error_msg,
                "alert_type": req.params.get('alert_type', 'NORMAL')
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="monitor_and_update", auth_level=func.AuthLevel.ANONYMOUS)
def monitor_and_update(req: func.HttpRequest) -> func.HttpResponse:
    """Monitor for changes in alert texts and update MP3 files in repository"""
    logging.info('Audio monitoring and update function triggered')
    
    try:
        # Get configuration
        github_token = get_github_token()
        if not github_token:
            raise Exception("GitHub token not configured")
        
        speech_config = get_azure_speech_config()
        if not speech_config['key']:
            raise Exception("Azure Speech key not configured")
        
        # Get current settings from GitHub
        logging.info("Fetching current settings from GitHub...")
        settings_data = get_file_from_github(SETTINGS_FILE_PATH, github_token)
        settings_content = base64.b64decode(settings_data['content']).decode('utf-8')
        settings = json.loads(settings_content)
        
        # Get current alert texts for all three levels
        current_normal_text = settings['alert_types']['NORMAL']['audio_text']
        current_medium_text = settings['alert_types'].get('MEDIUM', {}).get('audio_text', '')
        current_high_text = settings['alert_types']['HIGH']['audio_text']
        
        # Calculate current hashes
        current_normal_hash = calculate_text_hash(current_normal_text)
        current_medium_hash = calculate_text_hash(current_medium_text) if current_medium_text else ''
        current_high_hash = calculate_text_hash(current_high_text)
        
        # Get stored hashes
        stored_hashes = get_stored_audio_hashes(github_token)
        stored_normal_hash = stored_hashes.get('normal_text_hash', '')
        stored_medium_hash = stored_hashes.get('medium_text_hash', '')
        stored_high_hash = stored_hashes.get('high_text_hash', '')
        
        # Check what changed
        normal_changed = current_normal_hash != stored_normal_hash
        medium_changed = current_medium_hash != stored_medium_hash and current_medium_text != ''
        high_changed = current_high_hash != stored_high_hash
        
        results = {
            "status": "success",
            "changes_detected": normal_changed or medium_changed or high_changed,
            "normal_changed": normal_changed,
            "medium_changed": medium_changed,
            "high_changed": high_changed,
            "files_updated": []
        }
        
        # Get Azure configuration for voice settings
        azure_config = settings['azure']
        
        # Update NORMAL alert if changed
        if normal_changed:
            logging.info("NORMAL alert text changed, generating new audio...")
            
            voice = azure_config['voices']['normal']
            style = azure_config['styles']['normal']
            
            audio_data = generate_audio_with_urllib(
                text=current_normal_text,
                voice=voice,
                style=style,
                region=speech_config['region'],
                subscription_key=speech_config['key']
            )
            
            # Commit to repository
            commit_result = commit_file_to_github(
                "device/alert_audio/normal_alert.mp3",
                audio_data,
                f"Update normal alert audio - text hash: {current_normal_hash[:8]}",
                github_token,
                is_binary=True
            )
            
            results["files_updated"].append({
                "file": "normal_alert.mp3",
                "size": len(audio_data),
                "commit_sha": commit_result.get('commit', {}).get('sha', 'unknown')
            })
            
            logging.info(f"Normal alert MP3 updated: {len(audio_data)} bytes")
        
        # Update MEDIUM alert if changed
        if medium_changed:
            logging.info("MEDIUM alert text changed, generating new audio...")
            
            voice = azure_config['voices'].get('caution', azure_config['voices']['normal'])
            style = azure_config['styles'].get('caution', 'newscast')
            
            audio_data = generate_audio_with_urllib(
                text=current_medium_text,
                voice=voice,
                style=style,
                region=speech_config['region'],
                subscription_key=speech_config['key']
            )
            
            # Commit to repository
            commit_result = commit_file_to_github(
                "device/alert_audio/caution_alert.mp3",
                audio_data,
                f"Update caution alert audio - text hash: {current_medium_hash[:8]}",
                github_token,
                is_binary=True
            )
            
            results["files_updated"].append({
                "file": "caution_alert.mp3",
                "size": len(audio_data),
                "commit_sha": commit_result.get('commit', {}).get('sha', 'unknown')
            })
            
            logging.info(f"Caution alert MP3 updated: {len(audio_data)} bytes")
        
        # Update HIGH alert if changed
        if high_changed:
            logging.info("HIGH alert text changed, generating new audio...")
            
            voice = azure_config['voices']['high_alert']
            style = azure_config['styles']['high_alert']
            
            audio_data = generate_audio_with_urllib(
                text=current_high_text,
                voice=voice,
                style=style,
                region=speech_config['region'],
                subscription_key=speech_config['key']
            )
            
            # Commit to repository
            commit_result = commit_file_to_github(
                "device/alert_audio/high_alert.mp3",
                audio_data,
                f"Update high alert audio - text hash: {current_high_hash[:8]}",
                github_token,
                is_binary=True
            )
            
            results["files_updated"].append({
                "file": "high_alert.mp3",
                "size": len(audio_data),
                "commit_sha": commit_result.get('commit', {}).get('sha', 'unknown')
            })
            
            logging.info(f"High alert MP3 updated: {len(audio_data)} bytes")
        
        # Update stored hashes if any changes were made
        if normal_changed or medium_changed or high_changed:
            new_hashes = {
                "normal_text_hash": current_normal_hash,
                "medium_text_hash": current_medium_hash,
                "high_text_hash": current_high_hash,
                "last_updated": "automated_check"
            }
            store_audio_hashes(new_hashes, github_token)
            results["hashes_updated"] = True
        else:
            results["hashes_updated"] = False
            
        return func.HttpResponse(
            json.dumps(results, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Audio monitoring failed: {error_msg}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": error_msg
            }, indent=2),
            status_code=500,
            mimetype="application/json"
        )

@app.timer_trigger(schedule="0 */3 * * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def automated_monitor_timer(mytimer: func.TimerRequest) -> None:
    """Timer-triggered function that runs every 3 minutes to monitor and update audio files"""
    logging.info('Timer triggered - starting automated audio monitoring')
    
    try:
        # Get configuration
        github_token = get_github_token()
        if not github_token:
            error_msg = "GitHub token not configured"
            logging.error(error_msg)
            log_execution("error", error_msg)
            return
        
        speech_config = get_azure_speech_config()
        if not speech_config['key']:
            error_msg = "Azure Speech key not configured"
            logging.error(error_msg)
            log_execution("error", error_msg)
            return
        
        # Get current settings from GitHub
        logging.info("Fetching current settings from GitHub...")
        settings_data = get_file_from_github(SETTINGS_FILE_PATH, github_token)
        settings_content = base64.b64decode(settings_data['content']).decode('utf-8')
        current_settings = json.loads(settings_content)
        
        # Extract audio texts from settings for all three levels
        current_normal_text = current_settings['alert_types']['NORMAL']['audio_text']
        current_medium_text = current_settings['alert_types'].get('MEDIUM', {}).get('audio_text', '')
        current_high_text = current_settings['alert_types']['HIGH']['audio_text']
        
        # Calculate hashes of ONLY the audio texts (not entire settings)
        current_normal_hash = calculate_text_hash(current_normal_text)
        current_medium_hash = calculate_text_hash(current_medium_text) if current_medium_text else ''
        current_high_hash = calculate_text_hash(current_high_text)
        logging.info(f"Current audio text hashes - NORMAL: {current_normal_hash}, MEDIUM: {current_medium_hash}, HIGH: {current_high_hash}")
        
        # Get stored hashes
        stored_hashes = get_stored_audio_hashes(github_token)
        stored_normal_hash = stored_hashes.get('normal_text_hash', '')
        stored_medium_hash = stored_hashes.get('medium_text_hash', '')
        stored_high_hash = stored_hashes.get('high_text_hash', '')
        logging.info(f"Stored audio text hashes - NORMAL: {stored_normal_hash}, MEDIUM: {stored_medium_hash}, HIGH: {stored_high_hash}")
        
        # Check what changed
        normal_changed = current_normal_hash != stored_normal_hash
        medium_changed = current_medium_hash != stored_medium_hash and current_medium_text != ''
        high_changed = current_high_hash != stored_high_hash
        
        # Only regenerate if audio texts actually changed
        if normal_changed or medium_changed or high_changed:
            logging.info(f"Audio text changed - NORMAL: {normal_changed}, MEDIUM: {medium_changed}, HIGH: {high_changed}")
            
            files_updated = []
            commit_ids = []
            
            # Get Azure configuration for voice settings
            azure_config = current_settings['azure']
            
            # Regenerate NORMAL alert if text changed
            if normal_changed:
                logging.info("Regenerating NORMAL alert audio...")
                normal_mp3 = generate_audio_with_urllib(
                    current_normal_text,
                    azure_config['voices']['normal'],
                    azure_config['styles']['normal'],
                    speech_config['region'],
                    speech_config['key']
                )
                
                normal_commit = commit_file_to_github(
                    "device/alert_audio/normal_alert.mp3",
                    normal_mp3,
                    f"Auto-update normal alert audio - text hash: {current_normal_hash[:8]}",
                    github_token,
                    is_binary=True
                )
                
                files_updated.append("normal_alert.mp3")
                commit_ids.append(normal_commit.get('commit', {}).get('sha', 'unknown')[:8])
                logging.info(f"✅ Normal alert MP3 updated: {len(normal_mp3)} bytes")
            
            # Regenerate MEDIUM alert if text changed
            if medium_changed:
                logging.info("Regenerating MEDIUM/CAUTION alert audio...")
                medium_mp3 = generate_audio_with_urllib(
                    current_medium_text,
                    azure_config['voices'].get('caution', azure_config['voices']['normal']),
                    azure_config['styles'].get('caution', 'newscast'),
                    speech_config['region'],
                    speech_config['key']
                )
                
                medium_commit = commit_file_to_github(
                    "device/alert_audio/caution_alert.mp3",
                    medium_mp3,
                    f"Auto-update caution alert audio - text hash: {current_medium_hash[:8]}",
                    github_token,
                    is_binary=True
                )
                
                files_updated.append("caution_alert.mp3")
                commit_ids.append(medium_commit.get('commit', {}).get('sha', 'unknown')[:8])
                logging.info(f"✅ Caution alert MP3 updated: {len(medium_mp3)} bytes")
            
            # Regenerate HIGH alert if text changed
            if high_changed:
                logging.info("Regenerating HIGH alert audio...")
                high_mp3 = generate_audio_with_urllib(
                    current_high_text,
                    azure_config['voices']['high_alert'],
                    azure_config['styles']['high_alert'],
                    speech_config['region'],
                    speech_config['key']
                )
                
                high_commit = commit_file_to_github(
                    "device/alert_audio/high_alert.mp3",
                    high_mp3,
                    f"Auto-update high alert audio - text hash: {current_high_hash[:8]}",
                    github_token,
                    is_binary=True
                )
                
                files_updated.append("high_alert.mp3")
                commit_ids.append(high_commit.get('commit', {}).get('sha', 'unknown')[:8])
                logging.info(f"✅ High alert MP3 updated: {len(high_mp3)} bytes")
            
            # Update stored hashes for future comparison
            new_hashes = {
                "normal_text_hash": current_normal_hash,
                "medium_text_hash": current_medium_hash,
                "high_text_hash": current_high_hash,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            store_audio_hashes(new_hashes, github_token)
            files_updated.append(".audio_hashes.json")
            
            logging.info("✅ Audio files updated and committed to GitHub via timer")
            log_execution(
                "success", 
                f"Audio text changed - Successfully regenerated and committed {len(files_updated)-1} audio file(s). Commits: {', '.join(commit_ids)}",
                changes_detected=True,
                files_updated=files_updated,
                commit_id=commit_ids[0] if commit_ids else None
            )
        else:
            logging.info("⏭️ No changes detected in audio texts - skipping regeneration")
            log_execution(
                "success",
                "No changes detected in audio texts - audio files are up to date",
                changes_detected=False
            )
            
    except Exception as e:
        error_msg = f"Timer-triggered audio monitoring failed: {str(e)}"
        logging.error(error_msg)
        log_execution("error", error_msg)
