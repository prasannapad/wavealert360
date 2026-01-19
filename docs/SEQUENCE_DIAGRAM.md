# WaveAlert360 Alert Flow Sequence Diagram

## Main Alert Flow

```mermaid
sequenceDiagram
    participant Hardware as GPIO LEDs + Speaker
    participant Device as Raspberry Pi<br/>(88:a2:9e:0d:fb:17)
    participant Azure as Azure Device Service<br/>(Cloud)
    participant GitHub as GitHub<br/>(devices.json)
    participant NWS as National Weather Service<br/>(api.weather.gov)

    Note over Device: Every 30 seconds
    
    Device->>Device: Get MAC address<br/>(/sys/class/net/eth0/address)
    activate Device
    Note right of Device: "88:a2:9e:0d:fb:17"
    
    Device->>Azure: GET /api/alert/88:a2:9e:0d:fb:17
    activate Azure
    Note right of Device: Timeout: 10s
    
    Azure->>GitHub: GET devices.json<br/>(if cache expired)
    activate GitHub
    GitHub-->>Azure: {devices: [{mac, mode, scenario}]}
    deactivate GitHub
    Note right of Azure: Cache for 30s
    
    Azure->>Azure: Find device by MAC
    Note right of Azure: device.operating_mode?
    
    alt TEST Mode
        Note right of Azure: Use test_scenario
        Azure->>Azure: alert_level = "CAUTION"
    else REAL Mode
        Azure->>NWS: GET /alerts/active?<br/>point=37.421035,-122.434162
        activate NWS
        NWS-->>Azure: {features: [{event, severity}]}
        deactivate NWS
        Note right of NWS: "Beach Hazards Statement"
        
        Azure->>Azure: analyze_nws_alerts()<br/>Match keywords
        Note right of Azure: "Beach Hazards" → CAUTION
    end
    
    Azure->>Azure: Build response
    Note right of Azure: {alert_level: "CAUTION",<br/>led_color: "YELLOW",<br/>audio_url: "..."}
    
    Azure-->>Device: HTTP 200 OK<br/>{alert_level, led_color, audio_url}
    deactivate Azure
    
    Device->>Device: Map CAUTION → MEDIUM
    Note right of Device: Load settings.json
    
    Device->>Device: alert_config = {<br/>led_pattern: "🟡🟡🟡",<br/>audio_file: "caution_alert.mp3"}
    
    Device->>Hardware: Write to /tmp/led_control_signal<br/>"PATTERN:YELLOW"
    activate Hardware
    Note left of Hardware: Yellow LEDs blink
    
    Device->>Hardware: Play caution_alert.mp3<br/>(mpg123/vlc)
    Note left of Hardware: Audio: "Caution! Elevated<br/>beach hazards..."
    deactivate Hardware
    
    deactivate Device
    
    Note over Device: Sleep 30 seconds
    Note over Device: Repeat cycle...
    
    rect rgb(255, 240, 240)
        Note over Hardware,Azure: FALLBACK PATH (if Azure fails)
        Device->>NWS: GET /alerts/active?<br/>point=37.421035,-122.434162
        activate NWS
        NWS-->>Device: {features: [...]}
        deactivate NWS
        Device->>Device: detect_hazard()<br/>Analyze locally
        Note right of Device: Same result,<br/>no cloud dependency
    end
```

## Timeline

| Time | Action |
|------|--------|
| 0.0s | Device starts check cycle |
| 0.1s | Get MAC address from network interface |
| 0.2s | HTTP GET to Azure Device Service |
| 0.3s | Azure receives request |
| 0.4s | Azure loads devices.json (from cache or GitHub) |
| 0.5s | Azure finds device in registry |
| 0.6s | Azure checks operating mode (TEST or REAL) |
| 0.7-1.5s | If REAL: Call NWS API and analyze alerts |
| 1.2s | Azure builds response |
| 1.3s | Azure returns HTTP 200 to device |
| 1.4s | Device maps cloud response to local config |
| 1.5s | Device controls LEDs and plays audio |
| 30.0s | Cycle repeats |

## Key Components

### Actors
- **GPIO LEDs + Speaker**: Physical hardware on Raspberry Pi
- **Raspberry Pi**: Edge device running main.py
- **Azure Device Service**: Cloud function managing device fleet
- **GitHub**: Configuration storage (devices.json)
- **NWS API**: National Weather Service real-time alerts

### Data Flow
1. Device → Azure: MAC address
2. Azure → GitHub: Device lookup (cached 30s)
3. Azure → NWS: Location-based alert query (REAL mode only)
4. Azure → Device: Alert level + metadata
5. Device → Hardware: LED patterns + audio playback

### Resilience
- **Azure fails**: Device falls back to direct NWS API call
- **NWS fails**: System shows safe default (green LEDs)
- **GitHub fails**: Device uses local cached audio files
- **Internet fails**: Device continues with last known state
