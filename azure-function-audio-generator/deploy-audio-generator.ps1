# Deploy WaveAlert360 Audio Generator - Working Version
param(
    [string]$ResourceGroup = "wavealert360",
    [string]$Location = "westus2", 
    [string]$FunctionAppName = "wavealert360-audio-generator",
    [string]$StorageAccountName = "audiogende$(Get-Date -Format 'MMdd')",
    [string]$GitHubToken = $env:GITHUB_TOKEN,
    [switch]$SkipResourceCreation
)

# Set default to skip resource creation
if (-not $PSBoundParameters.ContainsKey('SkipResourceCreation')) {
    $SkipResourceCreation = $true
}

if (-not $GitHubToken -and -not $SkipResourceCreation) {
    Write-Error "GITHUB_TOKEN is required for resource creation. Set it with: `$env:GITHUB_TOKEN = 'your_token_here'"
    exit 1
}

Write-Host "Deploying Audio Generator Function App..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan  
Write-Host "Function App: $FunctionAppName" -ForegroundColor Cyan

if (-not $SkipResourceCreation) {
    Write-Host "Storage Account: $StorageAccountName" -ForegroundColor Cyan

    # Create Storage Account
    Write-Host "Creating storage account..." -ForegroundColor Yellow
    az storage account create --name $StorageAccountName --resource-group $ResourceGroup --location $Location --sku "Standard_LRS"

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create storage account"
        exit 1
    }

    # Create Function App
    Write-Host "Creating function app..." -ForegroundColor Yellow
    az functionapp create --resource-group $ResourceGroup --consumption-plan-location $Location --runtime "python" --runtime-version "3.11" --functions-version "4" --name $FunctionAppName --storage-account $StorageAccountName --os-type "Linux"

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create function app"
        exit 1
    }

    # Get Speech Service Key
    Write-Host "Getting speech service key..." -ForegroundColor Yellow
    $SpeechKey = az cognitiveservices account keys list --name "wavealert360" --resource-group $ResourceGroup --query "key1" --output tsv

    # Configure App Settings
    Write-Host "Configuring app settings..." -ForegroundColor Yellow
    az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings "GITHUB_TOKEN=$GitHubToken" "AZURE_SPEECH_REGION=$Location" "FUNCTIONS_WORKER_RUNTIME=python" "AZURE_SPEECH_KEY=$SpeechKey"

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to configure app settings"
        exit 1
    }
}
else {
    Write-Host "Skipping resource creation, deploying to existing function..." -ForegroundColor Yellow
}

# Deploy Function Code
Write-Host "Deploying function code..." -ForegroundColor Yellow
if (-not (Test-Path "./wavealert360-audio-generator-code.zip")) {
    Write-Host "Creating deployment package..." -ForegroundColor Yellow
    Compress-Archive -Path ".\function_app.py", ".\host.json", ".\requirements.txt" -DestinationPath ".\wavealert360-audio-generator-code.zip" -Force
}

az functionapp deployment source config-zip --resource-group $ResourceGroup --name $FunctionAppName --src "./wavealert360-audio-generator-code.zip"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy function code"
    exit 1
}

# Test Deployment
Write-Host "Testing deployment..." -ForegroundColor Yellow
$FunctionUrl = "https://$FunctionAppName.azurewebsites.net"

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "   Function App: $FunctionAppName" -ForegroundColor Cyan
Write-Host "   URL: $FunctionUrl" -ForegroundColor Cyan
Write-Host "   Health Check: $FunctionUrl/api/ping" -ForegroundColor Cyan
Write-Host "   Audio Generator: $FunctionUrl/api/audio_generator" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test with:" -ForegroundColor White
Write-Host "   Invoke-RestMethod -Uri '$FunctionUrl/api/ping' -Method Get" -ForegroundColor Gray
