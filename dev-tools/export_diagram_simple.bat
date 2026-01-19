@echo off
REM Simple batch script to export Mermaid diagrams to PDF
REM Requires: Node.js and @mermaid-js/mermaid-cli

echo ========================================
echo WaveAlert360 Diagram PDF Exporter
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Then run: npm install -g @mermaid-js/mermaid-cli
    pause
    exit /b 1
)

REM Check if mermaid-cli is installed
where mmdc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Mermaid CLI not found. Installing...
    echo.
    call npm install -g @mermaid-js/mermaid-cli
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install mermaid-cli
        pause
        exit /b 1
    )
)

echo Running Python conversion script...
echo.

python export_diagram_to_pdf.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Conversion failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Check the docs/ folder for PDFs
echo ========================================
pause
