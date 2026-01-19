# Azure Device Service Deployment

## Overview
Azure Function for WaveAlert360 multi-device management system.

## Endpoints

### Device Alerts
- `GET /api/alert/{mac_address}` - Get current alert level for device
- Response: `{"alert_level": "SAFE|CAUTION|DANGER", "led_color": "GREEN|YELLOW|RED", "audio_url": "...", "timestamp": "...", "device_mode": "LIVE|TEST"}`

### Device Management
- `GET /api/devices` - List all registered devices
- `POST /api/devices/{mac}/mode` - Set device mode (LIVE/TEST)
- `POST /api/devices/{mac}/test-scenario` - Set test scenario (SAFE/CAUTION/DANGER)

### Device Configuration
Devices are configured manually in the JSON file - no auto-registration needed for small deployments.

### Admin
- `GET /api/dashboard` - Web dashboard for device management
- `GET /api/health` - Health check

## Configuration

### GitHub Access
- **Private Repository**: This repo is private and requires authentication
- **GITHUB_TOKEN**: Configure GitHub Personal Access Token as environment variable
- **Device Registry**: Devices read from `https://raw.githubusercontent.com/prasannapad/wavealert360/main/devices.json`

To update device configurations:
1. Edit `devices.json` in the repository root
2. Commit and push changes  
3. Azure Function will automatically use the updated configuration

### Environment Variables
- `GITHUB_TOKEN`: GitHub Personal Access Token for private repo access

### Local Development
```bash
func start
```

### Azure Deployment
```bash
func azure functionapp publish wavealert360-device-service
```

## Device Registry Schema
Stored in GitHub at `devices.json`:

```json
{
  "devices": [
    {
      "mac_address": "88:a2:9e:0d:fb:17",
      "display_name": "Cowell Beach Pi Device",
      "location_name": "Cowell Beach",
      "lat": 37.421035,
      "lon": -122.434162,
      "nws_zone": "CAZ529",
      "operating_mode": "TEST",
      "test_scenario": "CAUTION",
      "audio_files": {
        "SAFE": "https://raw.githubusercontent.com/.../safe.mp3",
        "CAUTION": "https://raw.githubusercontent.com/.../caution.mp3", 
        "DANGER": "https://raw.githubusercontent.com/.../danger.mp3"
      },
      "last_seen": "2025-09-21T05:30:00Z",
      "firmware_version": "1.2.3",
      "status": "active"
    }
  ]
}
```
