# WaveAlert360 - Complete Development Context
*Comprehensive project history and context for AI assistance*

## 📋 Project Overview

**WaveAlert360** is a Raspberry Pi-based coastal weather monitoring system that:
- Monitors NWS (National Weather Service) alerts for coastal areas
- Displays alert status via LED strips (10 LEDs with color coding)
- Generates audio alerts using Azure Text-to-Speech
- Auto-updates from GitHub repository
- Supports remote monitoring and Azure Function integration

**Current Status**: Fully migrated from enterprise to personal GitHub account, successfully deployed on devbox1 with simulation mode for Windows development.

## 🏗️ Development Timeline

### **Phase 1: Initial Development (June 2025)**
- Started with basic NWS API integration
- Implemented LED control system for Raspberry Pi
- Created audio generation using Azure Speech Services
- Developed auto-updater system for remote deployments

### **Phase 2: Hardware Research & Selection (July 2025)**
- **Pi Selection Process**: Extensively researched Raspberry Pi options
- **Decision**: Pi Zero 2 W (Quad-core ARM Cortex-A53 @ 1GHz, 512MB RAM)
- **Rationale**: Perfect balance of performance, power efficiency, and cost for coastal monitoring
- **Hardware Features**: Built-in Wi-Fi/Bluetooth, dual micro USB ports, 40-pin GPIO
- **Alternatives Considered**: Pi 4B (overkill), Pi Zero W (underpowered), Pi 5 (unnecessary cost)

### **Phase 3: GitHub Setup (August 2025)**
- **Repository**: https://github.com/prasannapad/wavealert360
- **Token Type**: Classic GitHub token (ghp_) for broader repository access
- **Authentication**: Token-based for auto-updater GitHub API access

### **Phase 4: Environment Migration (August 31, 2025)**
- **Successfully migrated** from devbox2 to devbox1
- **Transferred secrets** securely via Remote Desktop
- **Verified system operation** with console LED simulation

## 🔧 Technical Architecture

### **Core Components**
```
wavealert360/
├── device/
│   ├── main.py              # Main application entry point
│   ├── config.py            # Configuration management
│   ├── azure_function_client.py  # Azure integration
│   └── alert_audio/         # Audio generation system
├── updater/
│   └── auto_updater.py      # GitHub-based auto-update system
├── azure-function-audio-generator/  # Azure Function for remote audio generation
├── infrastructure/          # Azure deployment scripts
└── tests/                   # Test scenarios and validation
```

### **Key Configuration Files**
- **`.env`**: Contains GitHub token and Azure Speech key (NEVER commit)
- **`local.settings.json`**: Azure Function configuration (gitignored)
- **`requirements.txt`**: Python dependencies (some Pi-specific won't install on Windows)

## 🔐 Security & Secrets Management

### **Current Token Configuration**
- **GitHub Token**: Classic token format (stored in `.env` - not committed)
- **Azure Speech Key**: For text-to-speech generation (stored in Azure only)
- **Repository**: https://github.com/prasannapad/wavealert360.git

### **Token Evolution**
1. **Original**: Fine-grained token (`github_pat_`) - had permission issues
2. **Current**: Classic token (`ghp_`) - works reliably across all components
3. **Backup**: `.env_old_finegrained` preserved for reference locally

### **Security Best Practices**
- All secrets in `.env` and `local.settings.json` are gitignored
- Secrets backed up in `C:\wavealert360_keys_backup\` directory
- Never commit sensitive data to repository

## 🌊 System Operation

### **LED Status Indicators**
- **🔴 Red LEDs**: Emergency alerts (tsunami, hurricane warnings)
- **🟡 Yellow LEDs**: Severe weather warnings  
- **🔵 Blue LEDs**: Coastal advisories (high surf, small craft advisory)
- **⚪ Gray LEDs**: Normal conditions (current status on devbox1)

### **Console Simulation Mode**
When running on Windows (devbox1), system displays:
```
○○○○○○○○○○ [CONSOLE LED] Normal Conditions
```

### **Monitoring Location**
- **Primary**: Cheboygan State Park Beach, Cheboygan County, MI
- **Coordinates**: 45.6469, -84.4744
- **API Endpoint**: NWS alerts for coastal Michigan

## 🎵 Audio System

### **Audio Generation**
- **Service**: Azure Cognitive Services Speech
- **Output**: MP3 files in `device/alert_audio/` directory
- **Playback**: pygame library for cross-platform audio
- **Files**: 
  - `normal_alert.mp3` - Normal conditions message
  - `[alert_type].mp3` - Generated for each alert type

### **Azure Function Integration**
- **Purpose**: Remote audio generation and GitHub commits
- **Location**: `azure-function-audio-generator/` directory
- **Deployment**: Azure Functions with GitHub integration
- **Repository Reference**: Updated to personal account (prasannapad/wavealert360)

## 🔄 Auto-Updater System

### **Functionality**
- **File**: `updater/auto_updater.py`
- **Purpose**: Monitors GitHub for updates and auto-deploys
- **Repository**: Now points to https://github.com/prasannapad/wavealert360.git
- **Authentication**: Uses classic GitHub token from `.env`

### **Migration Updates**
```python
# Updated repository references:
REPO_URL = "https://github.com/prasannapad/wavealert360.git"
REPO_OWNER = "prasannapad"
GITHUB_REPO = "prasannapad/wavealert360"
```

## 🐍 Python Environment

### **Development Setup (devbox1)**
```bash
# Virtual environment
python -m venv .venv
.venv\Scripts\activate

# Core dependencies (Windows-compatible)
pip install requests python-dateutil pygame azure-cognitiveservices-speech
pip install schedule watchdog flask
```

### **Pi-Specific Dependencies (Skip on Windows)**
- `rpi_ws281x` - Requires Visual C++ Build Tools, Pi hardware
- `adafruit-circuitpython-neopixel` - Pi GPIO libraries
- These will be installed when deploying to actual Pi hardware

### **Testing Commands**
```bash
# Test main system
python device\main.py

# Test configuration loading
python device\config.py

# Test auto-updater
python updater\auto_updater.py
```

## 🔍 Common Issues & Solutions

### **1. Git Push Authentication**
- **Issue**: Git push hanging during migration
- **Solution**: Use classic GitHub token, ensure account selection in browser
- **Command**: Choose `prasannapad` account when prompted

### **2. Python Dependencies**
- **Issue**: `rpi_ws281x` compilation fails on Windows
- **Solution**: Install core dependencies manually, skip Pi-specific libraries
- **Note**: System automatically uses simulation mode on Windows

### **3. Secrets Management**
- **Issue**: `.env` files not transferring correctly
- **Solution**: Use explicit file paths, verify gitignore excludes secrets
- **Backup**: Always maintain backup copies during transfers

### **4. LED Status Confusion**
- **Issue**: Gray LEDs appear "broken"
- **Solution**: Gray = Normal conditions, this is correct behavior
- **Context**: LEDs only change color when alerts are ACTIVE

## 🚀 Current Development Environment

### **devbox1 Setup (Current)**
- **Location**: `C:\Users\ppadm\code\wavealert360`
- **Python**: 3.12.10 in virtual environment
- **Status**: ✅ Fully operational with console simulation
- **GitHub**: Connected to personal account (prasannapad)
- **Secrets**: ✅ Properly configured and secured

### **Previous Environment (devbox2)**
- **Status**: Successfully migrated, can be decommissioned
- **Backup**: Secrets preserved in `C:\wavealert360_keys_backup\`

## 🎯 Development Patterns & Preferences

### **Testing Approach**
- Incremental testing after each major change
- Console simulation for Windows development
- Real hardware testing on Pi deployment
- Mock API usage for development (Azure-hosted)

### **Code Organization**
- Modular design with clear separation of concerns
- Configuration centralized in `config.py`
- Hardware abstraction for cross-platform development
- Comprehensive error handling and logging

### **Documentation Standards**
- Rich markdown documentation
- Inline code comments for complex logic
- README files for major components
- Context preservation for AI assistance

## 📚 Key Learning & Decisions

### **GitHub Token Strategy**
- **Learning**: Classic tokens more reliable than fine-grained for cross-repo access
- **Decision**: Standardize on classic tokens for all integrations
- **Rationale**: Simpler permissions, broader compatibility

### **Pi Hardware Selection**
- **Learning**: Pi Zero 2 W perfect for coastal monitoring applications
- **Decision**: Optimal performance-to-cost ratio for project requirements
- **Future**: Can scale to Pi 4B if computational needs increase

### **Development Environment**
- **Learning**: Windows simulation enables rapid development
- **Decision**: Use devbox1 for development, Pi for deployment
- **Benefit**: Faster iteration cycles, easier debugging

## 🔮 Future Development

### **Planned Enhancements**
- Pi Zero 2 W hardware deployment
- Multiple location monitoring
- Advanced weather pattern recognition
- Mobile app integration
- Historical data analysis

### **Technical Debt**
- Consolidate audio generation workflows
- Enhance error recovery mechanisms
- Improve Pi deployment automation
- Add comprehensive unit test coverage

## 💡 Context for New AI Assistant

### **User Background**
- Experienced developer with strong Python skills
- Focused on practical, reliable solutions
- Values comprehensive documentation and context
- Prefers incremental, tested development approach

### **Project Priorities**
1. **Reliability**: System must work consistently for coastal monitoring
2. **Security**: Proper secrets management and access control
3. **Maintainability**: Clean, documented, modular code
4. **Scalability**: Architecture supports future enhancements

### **Communication Style**
- Appreciates detailed explanations with rationale
- Values step-by-step guidance for complex procedures
- Prefers verification steps after major changes
- Likes visual indicators (✅❌🎯) for status clarity

---

**Generated**: August 31, 2025  
**For**: devbox1 Copilot agent context  
**Project**: WaveAlert360 coastal monitoring system  
**Repository**: https://github.com/prasannapad/wavealert360

*This document captures 2 months of collaborative development context. Refer to it when providing assistance to maintain continuity and understanding of project history, decisions, and technical patterns.*
