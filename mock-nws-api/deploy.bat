@echo off
REM Azure Functions Deployment Script for WaveAlert360 Mock NWS API

echo 🚀 Deploying WaveAlert360 Mock NWS API to Azure Functions
echo ========================================================

REM Configuration
set RESOURCE_GROUP=wavealert360-rg
set FUNCTION_APP_NAME=wavealert360-mock-api
set STORAGE_ACCOUNT=wavealert360storage
set LOCATION=westus2

REM Check if Azure CLI is installed
where az >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Azure CLI is not installed. Please install it first.
    exit /b 1
)

REM Login check
echo 🔐 Checking Azure login status...
az account show >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Please log in to Azure:
    az login
)

REM Create resource group
echo 📁 Creating resource group...
az group create --name %RESOURCE_GROUP% --location %LOCATION%

REM Create storage account
echo 💾 Creating storage account...
az storage account create ^
    --name %STORAGE_ACCOUNT% ^
    --location %LOCATION% ^
    --resource-group %RESOURCE_GROUP% ^
    --sku Standard_LRS

REM Create function app
echo ⚡ Creating Azure Function App...
az functionapp create ^
    --resource-group %RESOURCE_GROUP% ^
    --consumption-plan-location %LOCATION% ^
    --runtime python ^
    --runtime-version 3.11 ^
    --functions-version 4 ^
    --name %FUNCTION_APP_NAME% ^
    --storage-account %STORAGE_ACCOUNT% ^
    --os-type Linux

REM Deploy function code
echo 📦 Deploying function code...
func azure functionapp publish %FUNCTION_APP_NAME%

echo ✅ Deployment complete!
echo 🌐 Function App URL: https://%FUNCTION_APP_NAME%.azurewebsites.net
echo.
echo 📋 Test endpoints:
echo    • List scenarios: https://%FUNCTION_APP_NAME%.azurewebsites.net/api/scenarios
echo    • Normal conditions: https://%FUNCTION_APP_NAME%.azurewebsites.net/api/alerts/active?point=15.2130,145.7545^&scenario=normal
echo    • High surf: https://%FUNCTION_APP_NAME%.azurewebsites.net/api/alerts/active?point=15.2130,145.7545^&scenario=high_surf
echo.
echo 🔧 Update your config.py:
echo    MOCK_MODE = True
echo    MOCK_API_BASE = 'https://%FUNCTION_APP_NAME%.azurewebsites.net/api'

pause
