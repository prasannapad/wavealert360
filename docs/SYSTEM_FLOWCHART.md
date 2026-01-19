# WaveAlert360 System Flowchart

## High-Level System Architecture

```mermaid
graph TB
    %% Main Actors and Systems
    Developer[👨‍💻 WaveAlert360 Developer<br/>Code Development]
    Operator[👤 WaveAlert360 Operator<br/>County/State Parks]
    GitHub[📦 GitHub Repository<br/>Code & Config Storage]
    Pi[🖥️ WaveAlert360 Beach Alert Device<br/>Raspberry Pi]
    Azure[☁️ WaveAlert360 Service<br/>Device Service API<br/>Microsoft Azure Function]
    NWS[🌊 NWS API<br/>Weather Alerts]
    LED[💡 LED Strips<br/>Red Yellow Green]
    Speaker[🔊 Speaker<br/>Audio Alerts]
    
    %% Power System
    Solar[☀️ Solar Panel<br/>20W Polycrystalline]
    Battery[🔋 LiFePO4 Battery<br/>12V 20Ah]
    PowerReg[⚡ Power Regulator<br/>5V USB Output]
    
    %% Developer Interactions
    Developer -->|Push Code Updates| GitHub
    Developer -->|Deploy Infrastructure| Azure
    
    %% Operator Interactions
    Operator -->|Update Config<br/>devices.json| GitHub
    Operator -->|Monitor Dashboard| Pi
    
    %% GitHub to Pi
    GitHub -->|Auto-Pull Updates<br/>Every 2 min| Pi
    
    %% Power Flow
    Solar -.->|Charge| Battery
    Battery -->|12V DC| PowerReg
    PowerReg -->|5V USB| Pi
    PowerReg -->|Power| Speaker
    
    %% Pi Internal Flow
    Pi -->|1. GET /api/alert/MAC| Azure
    Azure -->|2. Fetch Alerts| NWS
    NWS -->|3. Return Alert Data| Azure
    Azure -->|4. Return Alert Level<br/>SAFE/CAUTION/DANGER| Pi
    Pi -->|5. Control GPIO| LED
    Pi -->|6. Play Audio| Speaker
    
    %% Styling
    classDef developer fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    classDef operator fill:#fff3e0,stroke:#e65100,stroke-width:3px
    classDef cloud fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    classDef device fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    classDef hardware fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef external fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    classDef power fill:#fff8e1,stroke:#f57c00,stroke-width:3px
    
    class Developer developer
    class Operator operator
    class GitHub,Azure cloud
    class Pi device
    class LED,Speaker hardware
    class NWS external
    class Solar,Battery,PowerReg power
```

## Detailed Component Architecture

```mermaid
flowchart TB
    %% External Data Sources
    NWS[National Weather Service API<br/>alerts.weather.gov]
    NOAA[NOAA Tides & Currents API<br/>tidesandcurrents.noaa.gov]
    GitHub[GitHub Repository<br/>prasannapad/wavealert360]
    AzureBlob[Azure Blob Storage<br/>Audio Files]
    
    %% Azure Cloud Services
    DeviceAPI[Device Service API<br/>/api/alert/mac]
    DeviceLogic{Check Device Config}
    DeviceMode{Operating Mode?}
    TestScenario[Return Test Scenario<br/>from devices.json]
    LiveAlert[Fetch Live NWS Alerts<br/>for Device Location]
    DeviceResponse[Return Alert Level<br/>SAFE/CAUTION/DANGER]
    
    MockAPI[Mock NWS API<br/>/api/alerts/active]
    MockScenarios[Test Scenarios<br/>coastal_flood_warning<br/>high_surf_advisory<br/>rip_current_statement]
    
    DevicesDB[(devices.json<br/>Device Registry)]
    
    %% Main Process
    Start([System Startup])
    LoadConfig[Load Configuration<br/>settings.json devices.json]
    GetMAC[Get Device MAC Address<br/>from wlan0]
    Timer{Check Timer<br/>15 seconds}
    
    CallService[HTTP GET to<br/>Device Service API]
    AudioCheck[Check Audio Updates<br/>manifest.json]
    DownloadAudio[Download Updated<br/>Audio Files if needed]
    
    ParseResponse{Parse Alert<br/>Response}
    DetermineLevel[Determine Alert Level<br/>SAFE/CAUTION/DANGER]
    
    WriteLEDSignal[Write to<br/>/tmp/led_control_signal<br/>PATTERN:color]
    PlayAudio[Play Audio via mpg123<br/>normal/caution/high_alert.mp3]
    
    LogStatus[Log Check Status<br/>Timestamp Level Location]
    Sleep[Sleep until next check]
    
    %% LED Service
    LEDStart([LED Service Start])
    LEDLock{Acquire Process<br/>Lock?}
    LEDExit1[Exit - Another<br/>Instance Running]
    
    InitHardware{Initialize<br/>Hardware?}
    ImportLib[Import rpi_ws281x]
    InitStrips[Initialize 3 LED Strips:<br/>Red GPIO 18<br/>Yellow GPIO 21<br/>Green GPIO 13]
    HardwareOK[hardware_available = true]
    HardwareFail[hardware_available = false<br/>Simulation Mode]
    
    LEDLoop{Monitor Loop<br/>Every 2 seconds}
    ReadSignal[Read /tmp/led_control_signal]
    ParseSignal{Parse Signal<br/>Type?}
    
    PatternRed[Blink Red Strip<br/>10 cycles 0.5s on/off]
    PatternYellow[Blink Yellow Strip<br/>10 cycles 0.5s on/off]
    PatternGreen[Blink Green Strip<br/>10 cycles 0.5s on/off]
    PatternOff[Turn All Strips OFF]
    
    WriteStatus[Write Status to<br/>/tmp/led_service_status<br/>JSON with PID hardware level]
    
    %% Watchdog
    WDStart([Watchdog Start])
    WDLock{Acquire Process<br/>Lock?}
    WDExit[Exit - Another<br/>Instance Running]
    
    StartAll[Start All Processes:<br/>LED Service<br/>Main Process<br/>Web Dashboard<br/>Auto-Updater]
    
    WDLoop{Monitor Loop<br/>Every 60 seconds}
    CheckProc{Check Each<br/>Process}
    ProcRunning{Is Process<br/>Running?}
    RestartCount{Restart<br/>Count less than 5?}
    RestartProc[Restart Process]
    IncCount[Increment Restart Count]
    Cooldown[Wait for Cooldown]
    WDLog[Log Watchdog Status]
    
    %% Auto-Updater
    AUStart([Auto-Updater Start])
    AULock{Acquire Process<br/>Lock?}
    AUExit[Exit - Another<br/>Instance Running]
    
    AULoop{Update Loop<br/>Every 120 seconds}
    FetchCommit[Fetch Latest Commit<br/>from GitHub API]
    CompareCommit{Current vs<br/>Latest Commit?}
    NoUpdate[No Update Needed]
    
    StopWeb[Stop Web Dashboard]
    Backup[Create Backup<br/>.tar in backup/]
    GitPull[git pull origin main]
    PullSuccess{Pull<br/>Successful?}
    RestartWeb[Restart Web Dashboard]
    UpdateFail[Log Update Failure<br/>Continue with Old Code]
    HealthCheck[Health Check<br/>Web Dashboard]
    
    %% Web Dashboard
    WebStart([Web Dashboard Start])
    FlaskInit[Initialize Flask App<br/>Port 5000]
    LoadData[Load System Data:<br/>LED Status<br/>Device Config<br/>Git Info]
    
    Routes{HTTP Routes}
    RootRoute[GET /<br/>HTML Dashboard]
    StatusRoute[GET /status<br/>JSON API]
    HealthRoute[GET /health<br/>Health Check]
    
    IPCheck{Verify IP<br/>Allowed?}
    Serve403[HTTP 403 Forbidden]
    ServeData[Serve Response]
    
    %% File System
    LEDSignal["File: /tmp/led_control_signal"]
    LEDStatus["File: /tmp/led_service_status"]
    LEDLog["File: /tmp/led_service.log"]
    LEDLockFile["File: /tmp/led_service.lock"]
    WDLockFile["File: .watchdog.lock"]
    AULockFile["File: .updater.lock"]
    LocalConfig["Config Files:<br/>devices.json<br/>settings.json"]
    
    %% Hardware
    RedLED["Red LED Strip<br/>GPIO 18 Channel 0<br/>48 LEDs - DANGER"]
    YellowLED["Yellow LED Strip<br/>GPIO 21 Channel 0<br/>48 LEDs - CAUTION"]
    GreenLED["Green LED Strip<br/>GPIO 13 Channel 1<br/>48 LEDs - SAFE"]
    Speaker["Audio Output<br/>mpg123 player"]
    
    %% Main Flow Connections
    Start --> LoadConfig
    LoadConfig --> GetMAC
    GetMAC --> Timer
    Timer -->|15s elapsed| AudioCheck
    AudioCheck --> DownloadAudio
    DownloadAudio --> CallService
    CallService --> ParseResponse
    ParseResponse --> DetermineLevel
    DetermineLevel --> WriteLEDSignal
    WriteLEDSignal --> PlayAudio
    PlayAudio --> LogStatus
    LogStatus --> Sleep
    Sleep --> Timer
    
    %% Service API Flow
    CallService --> DeviceAPI
    DeviceAPI --> DeviceLogic
    DeviceLogic --> DevicesDB
    DevicesDB --> DeviceMode
    DeviceMode -->|TEST| TestScenario
    DeviceMode -->|LIVE| LiveAlert
    LiveAlert --> NWS
    NWS --> DeviceResponse
    TestScenario --> DeviceResponse
    DeviceResponse --> ParseResponse
    
    %% LED Service Flow
    LEDStart --> LEDLock
    LEDLock -->|Success| InitHardware
    LEDLock -->|Failed| LEDExit1
    InitHardware -->|Try| ImportLib
    ImportLib -->|Success| InitStrips
    InitStrips -->|Success| HardwareOK
    InitStrips -->|Error| HardwareFail
    ImportLib -->|Error| HardwareFail
    HardwareOK --> LEDLoop
    HardwareFail --> LEDLoop
    
    LEDLoop --> ReadSignal
    ReadSignal --> LEDSignal
    ReadSignal --> ParseSignal
    ParseSignal -->|PATTERN:RED| PatternRed
    ParseSignal -->|PATTERN:YELLOW| PatternYellow
    ParseSignal -->|PATTERN:GREEN| PatternGreen
    ParseSignal -->|OFF| PatternOff
    
    PatternRed --> RedLED
    PatternYellow --> YellowLED
    PatternGreen --> GreenLED
    
    PatternRed --> WriteStatus
    PatternYellow --> WriteStatus
    PatternGreen --> WriteStatus
    PatternOff --> WriteStatus
    WriteStatus --> LEDStatus
    WriteStatus --> LEDLoop
    
    %% Watchdog Flow
    WDStart --> WDLock
    WDLock -->|Success| StartAll
    WDLock -->|Failed| WDExit
    StartAll --> WDLoop
    WDLoop --> CheckProc
    CheckProc --> ProcRunning
    ProcRunning -->|Yes| WDLog
    ProcRunning -->|No| RestartCount
    RestartCount -->|Yes| RestartProc
    RestartCount -->|No| Cooldown
    RestartProc --> IncCount
    IncCount --> WDLog
    Cooldown --> WDLog
    WDLog --> WDLoop
    
    %% Auto-Updater Flow
    AUStart --> AULock
    AULock -->|Success| AULoop
    AULock -->|Failed| AUExit
    AULoop --> FetchCommit
    FetchCommit --> GitHub
    GitHub --> CompareCommit
    CompareCommit -->|Different| StopWeb
    CompareCommit -->|Same| NoUpdate
    StopWeb --> Backup
    Backup --> GitPull
    GitPull --> GitHub
    GitPull --> PullSuccess
    PullSuccess -->|Yes| RestartWeb
    PullSuccess -->|No| UpdateFail
    UpdateFail --> RestartWeb
    RestartWeb --> HealthCheck
    HealthCheck --> NoUpdate
    NoUpdate --> AULoop
    
    %% Web Dashboard Flow
    WebStart --> FlaskInit
    FlaskInit --> LoadData
    LoadData --> LEDStatus
    LoadData --> LocalConfig
    LoadData --> Routes
    Routes --> RootRoute
    Routes --> StatusRoute
    Routes --> HealthRoute
    RootRoute --> IPCheck
    StatusRoute --> IPCheck
    HealthRoute --> IPCheck
    IPCheck -->|Allowed| ServeData
    IPCheck -->|Denied| Serve403
    
    %% Audio Flow
    AudioCheck --> AzureBlob
    AzureBlob --> DownloadAudio
    PlayAudio --> Speaker
    
    %% Lock Files
    LEDLock -.->|Creates| LEDLockFile
    WDLock -.->|Creates| WDLockFile
    AULock -.->|Creates| AULockFile
    
    %% Watchdog manages all processes
    StartAll -.->|Starts & Monitors| LEDStart
    StartAll -.->|Starts & Monitors| Start
    StartAll -.->|Starts & Monitors| WebStart
    StartAll -.->|Starts & Monitors| AUStart
    
    %% Styling
    classDef external fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef azure fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef process fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef hardware fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef file fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef decision fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class NWS,NOAA,GitHub,AzureBlob external
    class DeviceAPI,MockAPI,DevicesDB azure
    class Start,LEDStart,WDStart,AUStart,WebStart process
    class RedLED,YellowLED,GreenLED,Speaker hardware
    class LEDSignal,LEDStatus,LEDLog,LEDLockFile,WDLockFile,AULockFile,LocalConfig file
    class Timer,DeviceLogic,DeviceMode,ParseResponse,ParseSignal,LEDLock,WDLock,AULock,InitHardware,ProcRunning,RestartCount,CompareCommit,PullSuccess,IPCheck,CheckProc decision
```

## System Components Summary

### 1. **Main Process (main.py)**
- **Purpose**: Core application logic for beach alert monitoring
- **Cycle**: Runs every 15 seconds
- **Functions**:
  - Calls Azure Device Service API with device MAC address
  - Receives alert level (SAFE/CAUTION/DANGER)
  - Writes LED control signal to `/tmp/led_control_signal`
  - Plays appropriate audio alert via mpg123
  - Checks for and downloads audio file updates
  - Logs all activity with timestamps

### 2. **LED Service (led_failsafe_manager.py)**
- **Purpose**: Hardware controller for 3 independent LED strips
- **Hardware**:
  - Red Strip: GPIO 18, PWM Channel 0 (DANGER)
  - Yellow Strip: GPIO 21, PWM Channel 0 (CAUTION)
  - Green Strip: GPIO 13, PWM Channel 1 (SAFE)
- **Functions**:
  - Monitors `/tmp/led_control_signal` every 2 seconds
  - Blinks appropriate LED strip based on signal
  - Writes status to `/tmp/led_service_status`
  - Falls back to simulation mode if hardware unavailable
  - Uses process lock to prevent multiple instances

### 3. **Watchdog (watchdog.py)**
- **Purpose**: Process manager and health monitor
- **Monitors**:
  - LED Service
  - Main Process
  - Web Dashboard
  - Auto-Updater
- **Functions**:
  - Starts all processes on system boot
  - Checks process health every 60 seconds
  - Automatically restarts crashed processes
  - Limits to 5 restart attempts before cooldown
  - Logs all monitoring activity

### 4. **Auto-Updater (auto_updater.py)**
- **Purpose**: Automatic code deployment from GitHub
- **Cycle**: Checks every 120 seconds (2 minutes)
- **Functions**:
  - Fetches latest commit from GitHub API
  - Compares with current commit
  - Creates backup before updating
  - Pulls latest code via `git pull`
  - Restarts web dashboard after update
  - Continues with old code if update fails

### 5. **Web Dashboard (web_status.py)**
- **Purpose**: Web-based system status interface
- **Port**: 5000
- **Routes**:
  - `/` - HTML dashboard with system status
  - `/status` - JSON API for programmatic access
  - `/health` - Health check endpoint
- **Security**: IP-based access control
- **Data Sources**:
  - LED service status file
  - Device configuration
  - Git commit information

### 6. **Azure Device Service**
- **Purpose**: Centralized alert decision service
- **Endpoint**: `/api/alert/{mac}`
- **Logic**:
  - Looks up device by MAC address in devices.json
  - In TEST mode: Returns configured test scenario
  - In LIVE mode: Fetches real NWS alerts for device location
  - Analyzes alert severity and type
  - Returns standardized alert level

### 7. **Hardware Components**
- **3 LED Strips**: 48 WS2812B LEDs each
  - Independently controlled via PWM
  - Blink pattern: 10 cycles of 0.5s on, 0.5s off
- **Audio Output**: Via mpg123 player
  - normal_alert.mp3 (SAFE)
  - caution_alert.mp3 (CAUTION)
  - high_alert.mp3 (DANGER)

## Data Flow Summary

1. **Alert Monitoring Flow**:
   ```
   Timer → Device Service API → NWS/Test Data → Parse Response → 
   Write LED Signal → Play Audio → Log → Sleep
   ```

2. **LED Control Flow**:
   ```
   Read Signal File → Parse Pattern → Control Hardware → 
   Write Status → Loop
   ```

3. **Update Flow**:
   ```
   Check GitHub → Compare Commits → Backup → Git Pull → 
   Restart Services → Health Check
   ```

4. **Monitoring Flow**:
   ```
   Check All Processes → Detect Failures → Restart if Needed → 
   Log Status → Wait → Loop
   ```

## Key Files

- **Configuration**: `devices.json`, `settings.json`
- **Control Signals**: `/tmp/led_control_signal`
- **Status Files**: `/tmp/led_service_status`
- **Lock Files**: `/tmp/led_service.lock`, `.watchdog.lock`, `.updater.lock`
- **Logs**: `/tmp/led_service.log`, `watchdog.log`
- **Audio**: `device/alert_audio/*.mp3`

## Process Dependencies

```
Watchdog (Parent)
├── LED Service (Child)
├── Main Process (Child)
├── Web Dashboard (Child)
└── Auto-Updater (Child)
    └── Manages Web Dashboard lifecycle
```

## Error Handling

- **Process Crashes**: Watchdog restarts up to 5 times
- **Update Failures**: Continue with existing code
- **Hardware Failures**: Fall back to simulation mode
- **Network Failures**: Use cached data, retry next cycle
- **Lock Conflicts**: Exit gracefully if another instance running
