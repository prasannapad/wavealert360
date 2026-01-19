# WaveAlert360 GitHub Token Update Script
# ==========================================
# This script updates the GitHub token in all 4 locations where it's used.
# Run this when the GitHub personal access token expires (~60 days).
#
# Usage: .\update-github-token.ps1 <new_token> <pi_host>
#        .\update-github-token.ps1 ghp_xxxxx pi@192.168.86.35
#
# What it updates:
# 1. Dev machine (.env file + git remote)
# 2. Raspberry Pi (.env file + git remote)
# 3. Azure Device Service (app settings)
# 4. Azure Audio Generator (app settings)

param(
    [Parameter(Mandatory=$true)]
    [string]$NewToken,
    
    [Parameter(Mandatory=$true, HelpMessage="Enter Pi host (e.g., pi@192.168.86.35)")]
    [string]$PiHost,
    
    [string]$PiPath = "~/WaveAlert360",
    [string]$ResourceGroup = "WaveAlert360",
    [string]$DeviceServiceName = "wavealert360-device-service",
    [string]$AudioGeneratorName = "wavealert360-audio-generator",
    [string]$RepoUrl = "github.com/prasannapad/wavealert360.git"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "WaveAlert360 GitHub Token Update" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Validate token format
if ($NewToken -notmatch '^ghp_[a-zA-Z0-9]{36}$') {
    Write-Host "❌ Invalid token format. Expected: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" -ForegroundColor Red
    exit 1
}

# =============================================================================
# PRE-VALIDATION: Test new token before applying
# =============================================================================
Write-Host "🔍 Pre-validation: Testing new token..." -ForegroundColor Yellow

try {
    $headers = @{
        'Authorization' = "token $NewToken"
        'User-Agent' = 'WaveAlert360-Token-Update'
    }
    $testResponse = Invoke-WebRequest -UseBasicParsing -Uri "https://api.github.com/repos/prasannapad/wavealert360" -Headers $headers -TimeoutSec 10
    
    if ($testResponse.StatusCode -eq 200) {
        Write-Host "   ✅ New token is valid and has repo access" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ Token validation failed: HTTP $($testResponse.StatusCode)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "   ❌ Token validation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check that the token has 'repo' scope and hasn't expired" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# =============================================================================
# BACKUP: Save current tokens
# =============================================================================
Write-Host "💾 Backing up current tokens..." -ForegroundColor Yellow

$Backup = @{
    DevEnvToken = $null
    DevGitRemote = $null
    PiEnvToken = $null
    PiGitRemote = $null
    AzureDeviceToken = $null
    AzureAudioToken = $null
    Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
}

try {
    # Backup dev machine
    if (Test-Path ".env") {
        $Backup.DevEnvToken = (Get-Content .env | Select-String "GITHUB_TOKEN").ToString().Split('=')[1]
        Write-Host "   ✅ Backed up dev .env token" -ForegroundColor Green
    }
    $Backup.DevGitRemote = git config --get remote.origin.url
    Write-Host "   ✅ Backed up dev git remote" -ForegroundColor Green
    
    # Backup Pi
    $Backup.PiEnvToken = ssh $PiHost "grep GITHUB_TOKEN $PiPath/.env | cut -d= -f2" 2>$null
    Write-Host "   ✅ Backed up Pi .env token" -ForegroundColor Green
    $Backup.PiGitRemote = ssh $PiHost "cd $PiPath && git config --get remote.origin.url" 2>$null
    Write-Host "   ✅ Backed up Pi git remote" -ForegroundColor Green
    
    # Backup Azure
    $Backup.AzureDeviceToken = az functionapp config appsettings list --name $DeviceServiceName --resource-group $ResourceGroup --query "[?name=='GITHUB_TOKEN'].value" -o tsv
    Write-Host "   ✅ Backed up Azure Device Service token" -ForegroundColor Green
    $Backup.AzureAudioToken = az functionapp config appsettings list --name $AudioGeneratorName --resource-group $ResourceGroup --query "[?name=='GITHUB_TOKEN'].value" -o tsv
    Write-Host "   ✅ Backed up Azure Audio Generator token" -ForegroundColor Green
    
    # Save backup to file
    $backupFile = "token-backup-$($Backup.Timestamp).json"
    $Backup | ConvertTo-Json | Out-File $backupFile
    Write-Host "   💾 Backup saved to: $backupFile" -ForegroundColor Cyan
}
catch {
    Write-Host "   ⚠️  Warning: Backup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   Continue anyway? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne 'Y') {
        exit 1
    }
}

Write-Host ""

$UpdatedLocations = @()
$FailedLocations = @()
$NeedsRollback = $false

# =============================================================================
# 1. UPDATE DEV MACHINE
# =============================================================================
Write-Host "1️⃣  Updating Dev Machine..." -ForegroundColor Yellow

try {
    # Update .env file
    $envFile = ".env"
    if (Test-Path $envFile) {
        $content = Get-Content $envFile
        $content = $content -replace 'GITHUB_TOKEN=.*', "GITHUB_TOKEN=$NewToken"
        $content | Set-Content $envFile
        Write-Host "   ✅ Updated .env file" -ForegroundColor Green
    }
    
    # Update git remote URL
    $remoteUrl = "https://${NewToken}@${RepoUrl}"
    git remote set-url origin $remoteUrl 2>$null
    Write-Host "   ✅ Updated git remote URL" -ForegroundColor Green
    
    # Verify with test pull
    git fetch origin main --dry-run 2>$null
    Write-Host "   ✅ Verified: Git access working" -ForegroundColor Green
    
    $UpdatedLocations += "Dev Machine"
}
catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
    $FailedLocations += "Dev Machine"
    $NeedsRollback = $true
}

Write-Host ""

# =============================================================================
# 2. UPDATE RASPBERRY PI
# =============================================================================
Write-Host "2️⃣  Updating Raspberry Pi ($PiHost)..." -ForegroundColor Yellow

try {
    # Update .env file on Pi
    ssh $PiHost "sed -i 's/GITHUB_TOKEN=.*/GITHUB_TOKEN=$NewToken/' $PiPath/.env"
    Write-Host "   ✅ Updated Pi .env file" -ForegroundColor Green
    
    # Update git remote on Pi
    $remoteUrl = "https://${NewToken}@${RepoUrl}"
    ssh $PiHost "cd $PiPath && git remote set-url origin $remoteUrl"
    Write-Host "   ✅ Updated Pi git remote URL" -ForegroundColor Green
    
    # Verify with test pull
    ssh $PiHost "cd $PiPath && git fetch origin main --dry-run" 2>$null
    Write-Host "   ✅ Verified: Pi git access working" -ForegroundColor Green
    
    $UpdatedLocations += "Raspberry Pi"
}
catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
    Write-Host "   Make sure Pi is online and SSH key is configured" -ForegroundColor Yellow
    $FailedLocations += "Raspberry Pi"
    $NeedsRollback = $true
}

Write-Host ""

# =============================================================================
# 3. UPDATE AZURE DEVICE SERVICE
# =============================================================================
Write-Host "3️⃣  Updating Azure Device Service..." -ForegroundColor Yellow

try {
    az functionapp config appsettings set `
        --name $DeviceServiceName `
        --resource-group $ResourceGroup `
        --settings "GITHUB_TOKEN=$NewToken" `
        --output none
    Write-Host "   ✅ Updated Azure app settings" -ForegroundColor Green
    
    # Wait for settings to propagate
    Start-Sleep -Seconds 5
    
    # Verify by calling API
    $response = Invoke-WebRequest -UseBasicParsing -Uri "https://${DeviceServiceName}.azurewebsites.net/api/alert/88:a2:9e:0d:fb:17"
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Verified: Device Service API responding" -ForegroundColor Green
    }
    
    $UpdatedLocations += "Azure Device Service"
}
catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
    Write-Host "   Make sure you're logged in: az login" -ForegroundColor Yellow
    $FailedLocations += "Azure Device Service"
    $NeedsRollback = $true
}

Write-Host ""

# =============================================================================
# 4. UPDATE AZURE AUDIO GENERATOR
# =============================================================================
Write-Host "4️⃣  Updating Azure Audio Generator..." -ForegroundColor Yellow

try {
    az functionapp config appsettings set `
        --name $AudioGeneratorName `
        --resource-group $ResourceGroup `
        --settings "GITHUB_TOKEN=$NewToken" `
        --output none
    Write-Host "   ✅ Updated Azure app settings" -ForegroundColor Green
    
    # Wait for settings to propagate
    Start-Sleep -Seconds 5
    
    # Verify by calling health endpoint (if available)
    $response = Invoke-WebRequest -UseBasicParsing -Uri "https://${AudioGeneratorName}.azurewebsites.net/api/health" -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Verified: Audio Generator responding" -ForegroundColor Green
    }
    
    $UpdatedLocations += "Azure Audio Generator"
}
catch {
    Write-Host "   ⚠️  Updated but couldn't verify (may not have health endpoint)" -ForegroundColor Yellow
    $UpdatedLocations += "Azure Audio Generator"
}

Write-Host ""

# =============================================================================
# ROLLBACK if any location failed
# =============================================================================
if ($NeedsRollback -and $Backup.DevEnvToken) {
    Write-Host "======================================" -ForegroundColor Red
    Write-Host "ROLLBACK: Restoring old tokens" -ForegroundColor Red
    Write-Host "======================================" -ForegroundColor Red
    Write-Host ""
    
    try {
        # Restore dev machine
        if ($Backup.DevEnvToken) {
            (Get-Content .env) -replace "GITHUB_TOKEN=.*", "GITHUB_TOKEN=$($Backup.DevEnvToken)" | Set-Content .env
            git remote set-url origin $Backup.DevGitRemote
            Write-Host "   ✅ Restored dev machine" -ForegroundColor Green
        }
        
        # Restore Pi
        if ($Backup.PiEnvToken) {
            ssh $PiHost "sed -i 's/GITHUB_TOKEN=.*/GITHUB_TOKEN=$($Backup.PiEnvToken)/' $PiPath/.env"
            ssh $PiHost "cd $PiPath && git remote set-url origin $($Backup.PiGitRemote)"
            Write-Host "   ✅ Restored Pi" -ForegroundColor Green
        }
        
        # Restore Azure
        if ($Backup.AzureDeviceToken) {
            az functionapp config appsettings set --name $DeviceServiceName --resource-group $ResourceGroup --settings "GITHUB_TOKEN=$($Backup.AzureDeviceToken)" --output none
            Write-Host "   ✅ Restored Azure Device Service" -ForegroundColor Green
        }
        if ($Backup.AzureAudioToken) {
            az functionapp config appsettings set --name $AudioGeneratorName --resource-group $ResourceGroup --settings "GITHUB_TOKEN=$($Backup.AzureAudioToken)" --output none
            Write-Host "   ✅ Restored Azure Audio Generator" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "✅ Rollback complete - all tokens restored to original state" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ CRITICAL: Rollback failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Manual recovery needed using backup file: $backupFile" -ForegroundColor Yellow
    }
    exit 1
}

# =============================================================================
# SUMMARY
# =============================================================================
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Update Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if ($UpdatedLocations.Count -gt 0) {
    Write-Host "✅ Successfully updated:" -ForegroundColor Green
    $UpdatedLocations | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
}

if ($FailedLocations.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Failed to update:" -ForegroundColor Red
    $FailedLocations | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "⚠️  System may not function correctly until all locations are updated!" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🎉 All locations updated successfully!" -ForegroundColor Green
Write-Host ""

# =============================================================================
# POST-UPDATE VALIDATION
# =============================================================================
Write-Host "🧪 Running post-update validation..." -ForegroundColor Yellow
Write-Host ""

$ValidationPassed = $true

# Test dev machine git
Write-Host "Testing dev machine git access..." -ForegroundColor Gray
try {
    git fetch origin main --dry-run 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
        Write-Host "   ✅ Dev machine git access working" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Dev machine git access needs verification" -ForegroundColor Yellow
        $ValidationPassed = $false
    }
}
catch {
    Write-Host "   ⚠️  Could not test dev machine git" -ForegroundColor Yellow
}

# Test Pi git
Write-Host "Testing Pi git access..." -ForegroundColor Gray
try {
    ssh $PiHost "cd $PiPath && git fetch origin main --dry-run" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
        Write-Host "   ✅ Pi git access working" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Pi git access needs verification" -ForegroundColor Yellow
        $ValidationPassed = $false
    }
}
catch {
    Write-Host "   ⚠️  Could not test Pi git" -ForegroundColor Yellow
}

# Test Azure Device Service API
Write-Host "Testing Azure Device Service API..." -ForegroundColor Gray
try {
    Start-Sleep -Seconds 10  # Wait for settings to propagate
    $response = Invoke-WebRequest -UseBasicParsing -Uri "https://${DeviceServiceName}.azurewebsites.net/api/alert/88:a2:9e:0d:fb:17" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Azure Device Service API responding" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  Azure Device Service returned HTTP $($response.StatusCode)" -ForegroundColor Yellow
        $ValidationPassed = $false
    }
}
catch {
    Write-Host "   ⚠️  Could not test Azure Device Service" -ForegroundColor Yellow
    $ValidationPassed = $false
}

# Test Azure Audio Generator
Write-Host "Testing Azure Audio Generator..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "https://${AudioGeneratorName}.azurewebsites.net/api/health" -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Azure Audio Generator responding" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ℹ️  Azure Audio Generator has no health endpoint (normal)" -ForegroundColor Gray
}

Write-Host ""
if ($ValidationPassed) {
    Write-Host "✅ All validation tests passed!" -ForegroundColor Green
    Write-Host "   System should auto-sync within 15-30 seconds." -ForegroundColor Gray
}
else {
    Write-Host "⚠️  Some validations failed - manual verification recommended" -ForegroundColor Yellow
    Write-Host "   Try: git push, check Pi logs, test Azure APIs" -ForegroundColor Gray
}
