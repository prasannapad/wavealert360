# Quick script to check Raspberry Pi auto-updater status
# Run this after SSH'ing into your Pi

Write-Host "=== WaveAlert360 Pi Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check if auto-updater is running
Write-Host "Checking auto-updater process..." -ForegroundColor Yellow
ssh pi@your-pi-ip "ps aux | grep auto_updater.py | grep -v grep"

Write-Host ""
Write-Host "Checking last git pull time..." -ForegroundColor Yellow
ssh pi@your-pi-ip "cd /opt/wavealert360 && git log -1 --format='%H %ai'"

Write-Host ""
Write-Host "Checking audio file timestamps..." -ForegroundColor Yellow
ssh pi@your-pi-ip "ls -lh /opt/wavealert360/device/alert_audio/*.mp3"

Write-Host ""
Write-Host "Checking auto-updater logs (last 20 lines)..." -ForegroundColor Yellow
ssh pi@your-pi-ip "tail -20 /opt/wavealert360/updater/logs/auto_update.log"
