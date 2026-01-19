# WaveAlert360 Audio Function

This module contains the Azure Function responsible for generating audio alerts for the WaveAlert360 system.

## Overview

The audio function provides intelligent audio generation with smart monitoring capabilities:
- Monitors NWS alert settings for changes
- Automatically generates MP3 audio files when settings change
- Commits generated audio files directly to the GitHub repository
- Provides API endpoints for manual audio generation and testing

## Files

- `function_app.py` - Main Azure Function with 4 HTTP endpoints
- `host.json` - Azure Functions v4 runtime configuration
- `requirements.txt` - Python dependencies (minimal azure-functions only)
- `deploy-audio-generator.ps1` - PowerShell deployment script
- `SETTINGS_SCHEMA_ALIGNMENT.md` - **CRITICAL**: Guide for keeping function aligned with settings schema changes

## API Endpoints

- `GET /api/ping` - Health check endpoint
- `GET /api/dashboard` - Web dashboard showing last hour of execution logs
- `GET /api/test_github` - Test GitHub connectivity and authentication
- `POST /api/generate_audio` - Manual audio generation (body: `{"text": "Alert message"}`)
- `POST /api/monitor_and_update` - Smart monitoring endpoint that checks for changes and updates audio files

## Features

### Smart Monitoring
- MD5 hash-based change detection
- Only regenerates audio when settings actually change
- Automatic GitHub commit with timestamped messages

### Audio Generation
- Uses Azure Speech Services (westus2 region)
- Generates high-quality MP3 files with SSML formatting
- Two audio types: high_alert.mp3 and normal_alert.mp3

### GitHub Integration
- Reads settings from `device/settings.json`
- Commits generated MP3 files to `device/alert_audio/`
- Uses Personal Access Token authentication

## Deployment

Run the deployment script:
```powershell
.\deploy-audio-generator.ps1
```

This will:
1. Create Azure Function App in westus2 region
2. Deploy the function code
3. Configure necessary app settings
4. Display the function URLs for testing

## Configuration

The function requires these Azure App Settings:
- `SPEECH_KEY` - Azure Speech Services subscription key
- `SPEECH_REGION` - Azure Speech Services region (westus2)
- `GITHUB_TOKEN` - GitHub Personal Access Token with repo access
- `GITHUB_REPO` - GitHub repository (ppadmavilasom/wavealert360)

## Testing

After deployment, test the endpoints:
- Health: `GET https://your-function.azurewebsites.net/api/ping`
- Dashboard: `GET https://your-function.azurewebsites.net/api/dashboard`
- GitHub: `GET https://your-function.azurewebsites.net/api/test_github`
- Monitor: `POST https://your-function.azurewebsites.net/api/monitor_and_update`

## Dependencies

- Python 3.11
- Azure Functions v4
- urllib (built-in HTTP client)
- Azure Speech Services REST API
