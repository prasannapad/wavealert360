# GitHub Token Configuration Protocol
# ===================================
# CRITICAL: This is the complete checklist to follow whenever a GitHub token is provided
# Date Created: August 19, 2025
# Context: Learned from audio sync failure - token was set in Azure Function but NOT in local .env

## THE PROBLEM WE SOLVED
- Azure Function HAD the token → could commit new audio files to GitHub
- Local auto-updater MISSING token → couldn't pull updates from GitHub  
- Result: Device played old "Cowell Ranch" audio instead of new "Cheboygan" audio
- Root Cause: Incomplete token configuration (only 1 of 2 locations)

## COMPLETE GITHUB TOKEN SETUP PROTOCOL

### ✅ STEP 1: Azure Function Configuration (Cloud Write Access)
```bash
# Set environment variable in Azure Function
az functionapp config appsettings set \
  --name wavealert360-audio-generator \
  --resource-group wavealert360-rg \
  --settings GITHUB_TOKEN=<provided_token>
```

### ✅ STEP 2: Local Device Configuration (Device Read Access) 
```bash
# Create/update .env file in project root
echo GITHUB_TOKEN=<provided_token> > .env

# Verify .env file exists and contains token
cat .env | grep GITHUB_TOKEN
```

### ✅ STEP 3: Verify Both Configurations Work
```bash
# Test 1: Azure Function can commit
curl -X POST https://wavealert360-audio-generator.azurewebsites.net/api/audio_generator

# Test 2: Local auto-updater can authenticate  
python -c "from updater.auto_updater import GITHUB_TOKEN; print(f'Token loaded: {GITHUB_TOKEN[:8] if GITHUB_TOKEN else None}...')"
```

### ✅ STEP 4: Restart Auto-Updater
```bash
# Kill existing auto-updater processes (Windows)
taskkill /f /fi "IMAGENAME eq python.exe" /fi "COMMANDLINE eq *auto_updater.py*"

# Or on Linux/Pi
pkill -f "auto_updater.py"

# Restart system to pick up new token
restart_system.bat  # Windows
./restart_system.sh # Linux/Pi
```

### ✅ STEP 5: Test Complete Audio Sync Chain
```bash
# 1. Modify settings.json audio text and commit to GitHub
# 2. Wait up to 3 minutes for Azure Function timer (runs every 3 minutes)
# 3. Wait up to 2 minutes for auto-updater check (runs every 2 minutes)
# 4. Verify new audio files downloaded
dir device\alert_audio\*.mp3 /t:c

# 5. Play audio to confirm correct content
```

## VALIDATION CHECKLIST
- [ ] Azure Function has GITHUB_TOKEN environment variable
- [ ] Local .env file contains GITHUB_TOKEN=<token>
- [ ] Auto-updater logs show "✅ GitHub token configured"
- [ ] Auto-updater can successfully check for updates (no 401 errors)
- [ ] Audio files update when settings.json changes
- [ ] Played audio matches current location in settings.json

## CRITICAL REMINDER
**ONE TOKEN, TWO LOCATIONS:**
- Azure Function: Needs token to WRITE (commit audio files)
- Local Device: Needs token to READ (pull audio updates)

**BOTH MUST BE CONFIGURED OR THE CHAIN BREAKS!**

## NEVER FORGET AGAIN
When someone provides a GitHub token:
1. Configure Azure Function ✅
2. Configure local .env file ✅ ← THIS WAS MISSED BEFORE
3. Test both work ✅
4. Restart services ✅  
5. Validate end-to-end ✅

This prevents the "wrong location in audio" bug from recurring.
