# GitHub Token Management

## When Token Expires

GitHub personal access tokens expire after 60-90 days. When this happens:

### For Users
Just provide the new token to Copilot:
```
"Here's the new GitHub token: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Copilot will handle updating all locations automatically.

### For Copilot/AI Assistants

When the user provides a new token, run:
```powershell
.\scripts\update-github-token.ps1 ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX pi@192.168.86.35
```

This updates all 4 locations:
1. Dev machine (.env + git remote)
2. Raspberry Pi (.env + git remote)  
3. Azure Device Service (app settings)
4. Azure Audio Generator (app settings)

The script verifies each location after updating.

## Manual Update (if script fails)

### 1. Dev Machine
```powershell
# Update .env
(Get-Content .env) -replace 'GITHUB_TOKEN=.*', 'GITHUB_TOKEN=NEW_TOKEN' | Set-Content .env

# Update git remote
git remote set-url origin https://NEW_TOKEN@github.com/prasannapad/wavealert360.git
```

### 2. Raspberry Pi
```bash
ssh pi@192.168.86.35
cd ~/WaveAlert360
sed -i 's/GITHUB_TOKEN=.*/GITHUB_TOKEN=NEW_TOKEN/' .env
git remote set-url origin https://NEW_TOKEN@github.com/prasannapad/wavealert360.git
```

### 3. Azure Functions
```powershell
az functionapp config appsettings set --name wavealert360-device-service --resource-group WaveAlert360 --settings "GITHUB_TOKEN=NEW_TOKEN"
az functionapp config appsettings set --name wavealert360-audio-generator --resource-group WaveAlert360 --settings "GITHUB_TOKEN=NEW_TOKEN"
```

## Symptoms of Expired Token

- Pi auto-updater stops pulling updates
- Azure Device Service returns stale device config
- Azure Audio Generator can't read settings
- Git push/pull fails with 401 Unauthorized
- "Bad credentials" errors in logs
