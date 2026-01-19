# Azure Function Settings Schema Alignment Guide

## ⚠️ CRITICAL: Always Update Azure Function When Changing Settings Schema

When making changes to `device/settings.json` structure, you **MUST** also update the Azure Function code to maintain compatibility.

## 📋 Settings Schema Dependencies

The Azure Audio Generator Function (`azure-function-audio-generator/function_app.py`) directly reads and parses `device/settings.json`. Any structural changes require corresponding updates in the function code.

### Current Settings Structure Used by Azure Function:

```json
{
  "alert_types": {
    "NORMAL": {
      "audio_text": "Normal alert message..."
    },
    "HIGH": {
      "audio_text": "High alert message..."
    }
  },
  "azure": {
    "voices": {
      "normal": "en-US-AriaNeural",
      "high_alert": "en-US-DavisNeural"
    },
    "styles": {
      "normal": "friendly", 
      "high_alert": "urgent"
    }
  }
}
```

## 🎯 Function Code Locations to Update

When changing settings schema, check these specific locations in `function_app.py`:

### 1. Timer Function (Line ~658-670)
```python
# Audio text extraction
current_settings['alert_types']['NORMAL']['audio_text']
current_settings['alert_types']['HIGH']['audio_text']

# Voice and style extraction  
current_settings['azure']['voices']['normal']
current_settings['azure']['voices']['high_alert']
current_settings['azure']['styles']['normal'] 
current_settings['azure']['styles']['high_alert']
```

### 2. Test GitHub Function (Line ~368-369)
```python
normal_text = settings['alert_types']['NORMAL']['audio_text']
high_text = settings['alert_types']['HIGH']['audio_text']
```

### 3. Monitor and Update Function (Line ~490-491)
```python
current_normal_text = settings['alert_types']['NORMAL']['audio_text']
current_high_text = settings['alert_types']['HIGH']['audio_text']
```

### 4. Generate Audio Function (Line ~429-430)
```python
voice = azure_config['voices']['normal'] if alert_type == 'NORMAL' else azure_config['voices']['high_alert']
style = azure_config['styles']['normal'] if alert_type == 'NORMAL' else azure_config['styles']['high_alert']
```

## 🔄 Update Process Checklist

When changing `device/settings.json` structure:

- [ ] **1. Update Local Function Code**
  - Modify `azure-function-audio-generator/function_app.py`
  - Update all JSON path references
  - Test locally if possible

- [ ] **2. Test with Status API**
  - Deploy updated function: `.\deploy-audio-generator.ps1`
  - Check status: `GET /api/status`
  - Verify no parsing errors

- [ ] **3. Validate Timer Function**
  - Wait 3 minutes for next timer execution
  - Check `/api/status` for successful runs
  - Ensure `"status": "success"` instead of `"status": "error"`

- [ ] **4. Test Manual Trigger**
  - Call `POST /api/monitor_and_update`
  - Verify it detects changes correctly
  - Check audio generation works

## 🚨 Common Schema Change Scenarios

### Adding New Alert Type
```json
"alert_types": {
  "NORMAL": {...},
  "HIGH": {...},
  "CRITICAL": {...}  // NEW
}
```
**Required**: Update timer function to handle CRITICAL type

### Changing Voice Configuration
```json
"azure": {
  "voices": {
    "default": "en-US-AriaNeural",  // CHANGED
    "emergency": "en-US-DavisNeural"  // CHANGED
  }
}
```
**Required**: Update all voice references in function code

### Restructuring Alert Text Location
```json
"messages": {  // NEW STRUCTURE
  "normal": "text...",
  "high": "text..."
}
```
**Required**: Update all `alert_types` references to `messages`

## 🔍 Monitoring and Validation

### Status API Endpoint
```bash
GET https://wavealert360-audio-generator.azurewebsites.net/api/status
```

**Success Response:**
```json
{
  "total_logs": 5,
  "last_5_executions": [
    {
      "status": "success",
      "changes_detected": true,
      "files_updated": ["high_alert.mp3"]
    }
  ]
}
```

**Error Response (Schema Mismatch):**
```json
{
  "status": "error", 
  "details": "Timer-triggered audio monitoring failed: 'alert_texts'"
}
```

### Dashboard Monitoring
- **URL**: https://wavealert360-audio-generator.azurewebsites.net/api/dashboard
- **Auto-refresh**: Every 30 seconds
- **Shows**: Visual status of last hour executions

## 📝 Documentation Updates

When making schema changes, also update:

- [ ] This alignment guide
- [ ] `azure-function-audio-generator/README.md`
- [ ] Function code comments
- [ ] API endpoint documentation

## ⚡ Quick Fix Commands

```bash
# Deploy updated function
cd azure-function-audio-generator
.\deploy-audio-generator.ps1

# Check status
curl https://wavealert360-audio-generator.azurewebsites.net/api/status

# Test manual trigger
curl -X POST https://wavealert360-audio-generator.azurewebsites.net/api/monitor_and_update
```

---

**Remember: Settings schema changes without corresponding Azure Function updates will break the timer-based audio generation! Always test after making changes.**
