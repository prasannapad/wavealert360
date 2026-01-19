# Quick Git & Pi Verification Commands
# Save these as aliases or functions for efficiency

# Quick local git check
git-check() {
    echo "📊 Git Status:"
    git status --porcelain
    echo ""
    echo "📝 Last commit:"
    git log -1 --oneline
}

# Quick Pi sync check  
pi-check() {
    local file=${1:-"restart_system.sh"}
    echo "🔍 Checking Pi sync for: $file"
    ssh pi@192.168.86.38 "cd ~/WaveAlert360 && git log -1 --oneline && head -5 $file"
}

# Quick deployment verification (only for critical changes)
deploy-verify() {
    echo "🚀 Pre-deployment verification..."
    git status --porcelain
    if [ $? -eq 0 ]; then
        echo "✅ Git working directory clean"
        ssh pi@192.168.86.38 "cd ~/WaveAlert360 && git pull && echo 'Pi updated'"
    else
        echo "❌ Uncommitted changes - commit first"
    fi
}
