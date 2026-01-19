# Deploy WaveAlert360 Mock API Function Code
# =========================================
# This script deploys the function code after infrastructure is provisioned

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$FunctionAppName = ""
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green" 
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput($Message, $Color) {
    Write-Host $Message -ForegroundColor $Color
}

# Set function app name if not provided
if ([string]::IsNullOrEmpty($FunctionAppName)) {
    $FunctionAppName = "wavealert360-mock-api-$Environment"
}

Write-ColorOutput "🚀 Deploying WaveAlert360 Mock API Function Code" $InfoColor
Write-ColorOutput "Environment: $Environment" $InfoColor
Write-ColorOutput "Function App: $FunctionAppName" $InfoColor
Write-Host ""

# Check prerequisites
Write-ColorOutput "ℹ️  Checking prerequisites..." $InfoColor

# Check if Azure Functions Core Tools is installed
try {
    $funcVersion = func --version 2>$null
    Write-ColorOutput "✅ Azure Functions Core Tools: $funcVersion" $SuccessColor
} catch {
    Write-ColorOutput "❌ Azure Functions Core Tools not found. Please install it:" $ErrorColor
    Write-Host "npm install -g azure-functions-core-tools@4 --unsafe-perm true"
    exit 1
}

# Check if Azure CLI is installed and logged in
try {
    $account = az account show --query name -o tsv 2>$null
    Write-ColorOutput "✅ Azure CLI logged in: $account" $SuccessColor
} catch {
    Write-ColorOutput "❌ Azure CLI not found or not logged in" $ErrorColor
    Write-Host "Please install Azure CLI and run 'az login'"
    exit 1
}

# Verify function app exists
Write-ColorOutput "ℹ️  Verifying function app exists..." $InfoColor
try {
    $appInfo = az functionapp show --name $FunctionAppName --query "{name:name, state:state}" -o json 2>$null | ConvertFrom-Json
    if ($appInfo.state -eq "Running") {
        Write-ColorOutput "✅ Function app '$($appInfo.name)' is running" $SuccessColor
    } else {
        Write-ColorOutput "⚠️  Function app '$($appInfo.name)' state: $($appInfo.state)" $WarningColor
    }
} catch {
    Write-ColorOutput "❌ Function app '$FunctionAppName' not found. Deploy infrastructure first:" $ErrorColor
    Write-Host "infrastructure\deploy.bat $Environment"
    exit 1
}

# Change to function code directory
$functionCodePath = "mock-nws-api"
if (-not (Test-Path $functionCodePath)) {
    Write-ColorOutput "❌ Function code directory '$functionCodePath' not found" $ErrorColor
    exit 1
}

Push-Location $functionCodePath

try {
    # Deploy function code
    Write-ColorOutput "📦 Deploying function code..." $InfoColor
    $deployResult = func azure functionapp publish $FunctionAppName --python 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Function code deployed successfully!" $SuccessColor
        Write-Host ""
        
        # Extract function app URL
        $functionUrl = "https://$FunctionAppName.azurewebsites.net"
        $apiBaseUrl = "$functionUrl/api"
        
        Write-ColorOutput "🌐 Function App URL: $functionUrl" $InfoColor
        Write-ColorOutput "🔗 API Base URL: $apiBaseUrl" $InfoColor
        Write-Host ""
        
        Write-ColorOutput "📋 Available Endpoints:" $InfoColor
        Write-Host "  • List scenarios: $apiBaseUrl/scenarios"
        Write-Host "  • Normal conditions: $apiBaseUrl/alerts/active?point=15.2130,145.7545&scenario=normal"
        Write-Host "  • High surf: $apiBaseUrl/alerts/active?point=15.2130,145.7545&scenario=high_surf"
        Write-Host "  • Coastal flood: $apiBaseUrl/alerts/active?point=15.2130,145.7545&scenario=flood"
        Write-Host ""
        
        Write-ColorOutput "🔧 Update your device/config.py:" $InfoColor
        Write-Host "MOCK_MODE = True"
        Write-Host "MOCK_API_BASE = `"$apiBaseUrl`""
        Write-Host ""
        
        Write-ColorOutput "🧪 Test the deployment:" $InfoColor
        Write-Host "python device/test_mock_api.py"
        Write-Host ""
        
        # Test a simple endpoint
        Write-ColorOutput "🔍 Testing scenarios endpoint..." $InfoColor
        try {
            $response = Invoke-RestMethod -Uri "$apiBaseUrl/scenarios" -Method Get -TimeoutSec 10
            Write-ColorOutput "✅ API is responding correctly" $SuccessColor
        } catch {
            Write-ColorOutput "⚠️  API test failed. Function might still be starting up." $WarningColor
            Write-Host "Wait a few minutes and test manually: $apiBaseUrl/scenarios"
        }
        
    } else {
        Write-ColorOutput "❌ Function deployment failed:" $ErrorColor
        Write-Host $deployResult
        exit 1
    }
    
} finally {
    Pop-Location
}

Write-ColorOutput "✅ Deployment completed!" $SuccessColor
