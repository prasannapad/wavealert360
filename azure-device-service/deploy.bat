@echo off
echo Deploying WaveAlert360 Device Service to Azure...

REM Get function app name from user or use default
set /p FUNCTION_APP_NAME="Enter Function App Name (default: wavealert360-device-service): "
if "%FUNCTION_APP_NAME%"=="" set FUNCTION_APP_NAME=wavealert360-device-service

echo Deploying to: %FUNCTION_APP_NAME%

REM Deploy the function app
func azure functionapp publish %FUNCTION_APP_NAME% --python

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Deployment failed!
    pause
    exit /b 1
)

echo ✅ Deployment successful!
echo.
echo Function App URL: https://%FUNCTION_APP_NAME%.azurewebsites.net
echo Dashboard: https://%FUNCTION_APP_NAME%.azurewebsites.net/api/dashboard
echo Health Check: https://%FUNCTION_APP_NAME%.azurewebsites.net/api/health
echo.
echo Don't forget to configure AZURE_STORAGE_CONNECTION_STRING in Azure portal!

pause
