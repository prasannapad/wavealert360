#!/usr/bin/env python3
# WaveAlert360 Auto-Update System
# ================================
# Monitors GitHub repository for changes and automatically updates the device
# Runs as a background service to keep the system evergreen
#
# NOTE: As of the latest architecture update, process monitoring (main.py, web_status.py, LED service)
# is now handled by watchdog.py. This auto-updater focuses solely on GitHub monitoring and updates.
# The watchdog monitors ALL critical processes including this auto-updater itself.

import os
import sys
import time
import subprocess
import logging
import json
import requests
import platform
import atexit
from datetime import datetime
from pathlib import Path

# Platform-specific imports for file locking
if platform.system() != "Windows":
    import fcntl
else:
    import msvcrt

# Load environment variables
def load_env_file():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def load_settings():
    """Load settings from the main settings.json file"""
    try:
        settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'device', 'settings.json')
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get('auto_updater', {})
    except Exception as e:
        print(f"Warning: Could not load settings.json, using defaults: {e}")
        return {}

# Load environment configuration
env_config = load_env_file()
auto_updater_config = load_settings()

# Configuration with fallbacks to defaults
repo_config = auto_updater_config.get('repository', {})
update_config = auto_updater_config.get('update_settings', {})

REPO_URL = repo_config.get('url', 'https://github.com/prasannapad/wavealert360.git')
REPO_OWNER = repo_config.get('owner', 'prasannapad')
REPO_NAME = repo_config.get('name', 'wavealert360')
BRANCH = repo_config.get('branch', 'main')
CHECK_INTERVAL = update_config.get('check_interval', 120)  # 2 minutes in seconds

# GitHub Authentication
GITHUB_TOKEN = env_config.get('GITHUB_TOKEN')
if not GITHUB_TOKEN or GITHUB_TOKEN == 'your_github_personal_access_token_here':
    GITHUB_TOKEN = None

# Auto-detect platform and set appropriate paths
deployment_config = auto_updater_config.get('deployment', {})
logging_config = auto_updater_config.get('logging', {})

if platform.system() == "Windows":
    DEVICE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Parent directory on Windows
    PYTHON_EXECUTABLE = sys.executable  # Use current Python executable
else:
    DEVICE_PATH = deployment_config.get('production_path', '/opt/wavealert360')  # Production path on Raspberry Pi
    # Check for virtual environment first, then fall back to system python3
    venv_python = os.path.join(DEVICE_PATH, '.venv', 'bin', 'python3')
    if os.path.exists(venv_python):
        PYTHON_EXECUTABLE = venv_python  # Virtual environment Python
    else:
        PYTHON_EXECUTABLE = "/usr/bin/python3"  # System Python on Linux

# GitHub API endpoints
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
COMMITS_ENDPOINT = f"{GITHUB_API_BASE}/commits/{BRANCH}"

# Logging setup with Unicode support
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, logging_config.get('file', 'auto_update.log'))

# Create handlers with proper encoding
file_handler = logging.FileHandler(log_file, encoding='utf-8')
console_handler = logging.StreamHandler()

# Set console handler to only log to file on Windows to avoid Unicode issues
if platform.system() == "Windows":
    # Only log to file on Windows to avoid console Unicode issues
    handlers = [file_handler]
else:
    # Log to both file and console on Linux
    handlers = [file_handler, console_handler]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

class ProcessLock:
    """Cross-platform process lock to ensure only one instance runs"""
    
    def __init__(self, lock_file_path):
        self.lock_file_path = lock_file_path
        self.lock_file = None
        self.is_locked = False
        
    def acquire(self):
        """Acquire the process lock"""
        try:
            # Create lock file
            self.lock_file = open(self.lock_file_path, 'w')
            
            if platform.system() == "Windows":
                # Windows file locking
                try:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    self.is_locked = True
                except OSError:
                    self.lock_file.close()
                    return False
            else:
                # Unix/Linux file locking
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.is_locked = True
                except OSError:
                    self.lock_file.close()
                    return False
            
            # Write PID to lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            
            # Register cleanup on exit
            atexit.register(self.release)
            
            return True
            
        except Exception as e:
            if self.lock_file:
                self.lock_file.close()
            return False
    
    def release(self):
        """Release the process lock"""
        if self.is_locked and self.lock_file:
            try:
                if platform.system() == "Windows":
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                
                self.lock_file.close()
                
                # Remove lock file
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
                    
                self.is_locked = False
                
            except Exception:
                pass  # Ignore cleanup errors

class WaveAlert360AutoUpdater:
    def __init__(self):
        self.device_path = DEVICE_PATH
        self.python_executable = PYTHON_EXECUTABLE
        self.is_windows = platform.system() == "Windows"
        self.last_commit_sha = None
        self.web_process = None  # Track web_status.py process for updates only
        
        # Detect environment type
        self.is_development = self._detect_development_environment()
        
        # Set up process lock for auto-updater
        lock_file = os.path.join(self.device_path, '.auto_updater.lock')
        self.process_lock = ProcessLock(lock_file)
        
        # Register cleanup on exit
        atexit.register(self.cleanup_processes)
        
        self.load_last_commit()
        
        logger.info(f"Platform: {platform.system()}")
        logger.info(f"Device path: {self.device_path}")
        logger.info(f"Python executable: {self.python_executable}")
        logger.info(f"Environment: {'Development' if self.is_development else 'Production'}")
        
        # Check GitHub authentication
        if GITHUB_TOKEN:
            logger.info(f"✅ GitHub token configured ({GITHUB_TOKEN[:8]}...)")
        else:
            logger.warning("⚠️  No GitHub token found - private repository access may fail")
            logger.warning("   See GITHUB_TOKEN_SETUP.md for configuration instructions")
    
    def cleanup_processes(self):
        """Clean up managed processes on exit"""
        try:
            if self.web_process:
                self.stop_web_process()
        except Exception as e:
            logger.error(f"Error during process cleanup: {e}")
    
    def _detect_development_environment(self):
        """Detect if we're running in a development environment vs production Pi"""
        # Check for indicators that this is a development environment:
        # 1. Windows platform (dev machines are typically Windows/Mac)
        # 2. Presence of development folders (scripts/, docs/, infrastructure/)
        # 3. Full repository structure vs sparse checkout
        
        if self.is_windows:
            logger.info("🖥️  Windows detected - likely development environment")
            return True
            
        # Check for development-only folders
        dev_folders = ['scripts', 'docs', 'infrastructure', 'mock-nws-api', 'azure-function-audio-generator']
        dev_folder_count = sum(1 for folder in dev_folders if os.path.exists(os.path.join(self.device_path, folder)))
        
        if dev_folder_count >= 3:  # If we have most dev folders, it's likely development
            logger.info(f"📁 Development folders detected ({dev_folder_count}/{len(dev_folders)}) - development environment")
            return True
            
        # Check if sparse checkout is active (production Pi uses sparse checkout)
        try:
            result = subprocess.run(['git', 'config', 'core.sparseCheckout'], 
                                  capture_output=True, text=True, cwd=self.device_path)
            if result.returncode == 0 and result.stdout.strip().lower() == 'true':
                logger.info("🎯 Sparse checkout active - production environment")
                return False
        except:
            pass
            
        # Default to production if uncertain
        logger.info("🏭 Assuming production environment")
        return False
        
    def load_last_commit(self):
        """Load the last known commit SHA from file"""
        # Check device directory first (primary location)
        device_commit_file = os.path.join(self.device_path, 'device', '.last_commit')
        # Fall back to root directory (backward compatibility)
        root_commit_file = os.path.join(self.device_path, '.last_commit')
        
        try:
            # Try device directory first
            if os.path.exists(device_commit_file):
                with open(device_commit_file, 'r') as f:
                    self.last_commit_sha = f.read().strip()
                logger.info(f"Loaded last commit from device: {self.last_commit_sha[:8]}...")
            elif os.path.exists(root_commit_file):
                with open(root_commit_file, 'r') as f:
                    self.last_commit_sha = f.read().strip()
                logger.info(f"Loaded last commit from root: {self.last_commit_sha[:8]}...")
                # Copy to device directory for future self-contained operation
                try:
                    os.makedirs(os.path.dirname(device_commit_file), exist_ok=True)
                    with open(device_commit_file, 'w') as f:
                        f.write(self.last_commit_sha)
                    logger.info("Copied commit info to device directory")
                except:
                    pass
        except Exception as e:
            logger.warning(f"Could not load last commit: {e}")
    
    def save_last_commit(self, commit_sha):
        """Save the current commit SHA to file"""
        # Save only to device directory (self-contained)
        device_commit_file = os.path.join(self.device_path, 'device', '.last_commit')
        
        try:
            # Ensure device directory exists
            os.makedirs(os.path.dirname(device_commit_file), exist_ok=True)
            
            # Save to device directory only (self-contained operation)
            with open(device_commit_file, 'w') as f:
                f.write(commit_sha)
                
            self.last_commit_sha = commit_sha
            logger.info(f"Saved new commit: {commit_sha[:8]} (device)")
        except Exception as e:
            logger.error(f"Could not save commit SHA: {e}")
    
    def check_for_updates(self):
        """Check GitHub for new commits"""
        try:
            headers = {
                'User-Agent': 'WaveAlert360-AutoUpdater',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Add GitHub authentication for private repos
            if GITHUB_TOKEN:
                headers['Authorization'] = f'token {GITHUB_TOKEN}'
            
            response = requests.get(COMMITS_ENDPOINT, headers=headers, timeout=10)
            response.raise_for_status()
            
            commit_data = response.json()
            latest_sha = commit_data['sha']
            commit_message = commit_data['commit']['message']
            commit_date = commit_data['commit']['committer']['date']
            
            logger.info(f"Latest commit: {latest_sha[:8]} - {commit_message.split()[0]}")
            
            if self.last_commit_sha != latest_sha:
                logger.info(f"🔄 New update available!")
                logger.info(f"   Current: {self.last_commit_sha[:8] if self.last_commit_sha else 'None'}")
                logger.info(f"   Latest:  {latest_sha[:8]}")
                logger.info(f"   Message: {commit_message.strip()}")
                logger.info(f"   Date:    {commit_date}")
                return True, latest_sha, commit_message
            
            return False, latest_sha, commit_message
            
        except Exception as e:
            logger.error(f"❌ Failed to check for updates: {e}")
            return False, None, None
    
    def stop_main_process(self):
        """Stop the running WaveAlert360 main process with enhanced safety"""
        try:
            if self.main_process and self.main_process.poll() is None:
                logger.info("🛑 Stopping WaveAlert360 main process...")
                
                # Step 1: Graceful shutdown (SIGTERM)
                self.main_process.terminate()
                
                # Step 2: Wait for graceful shutdown
                try:
                    self.main_process.wait(timeout=15)  # Increased timeout
                    logger.info("✅ Main process stopped gracefully")
                    return True
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️  Main process didn't stop gracefully, forcing...")
                
                # Step 3: Force kill if graceful shutdown failed
                try:
                    self.main_process.kill()  # SIGKILL
                    self.main_process.wait(timeout=5)
                    logger.info("✅ Main process force-stopped")
                except:
                    pass
                
            # Step 4: System-level cleanup (fallback)
            try:
                if self.is_windows:
                    # More targeted Windows kill
                    subprocess.run(['taskkill', '/f', '/fi', 'IMAGENAME eq python.exe', '/fi', 'COMMANDLINE eq *main.py*'], 
                                 capture_output=True, timeout=5)
                else:
                    # More targeted Linux kill
                    subprocess.run(['pkill', '-f', 'python.*main.py'], 
                                 capture_output=True, timeout=5)
                logger.info("✅ System-level cleanup completed")
            except:
                pass
                
            # Step 5: Verify process is actually stopped
            time.sleep(2)  # Give it a moment
            if self.main_process and self.main_process.poll() is None:
                logger.error("❌ Failed to stop main process!")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error stopping main process: {e}")
            return False
    
    def backup_current_version(self):
        """Create a backup of the current version"""
        try:
            backup_dir = os.path.join(self.device_path, 'backup')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup using git archive if possible, otherwise cp
            result = subprocess.run([
                'git', 'archive', '--format=tar', 'HEAD', f'--output={backup_path}.tar'
            ], cwd=self.device_path, capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Backup created: {backup_path}.tar")
                return True
            else:
                logger.warning("Git archive failed, skipping backup")
                return False
                
        except Exception as e:
            logger.warning(f"Backup failed: {e}")
            return False
    
    def pull_updates(self):
        """Pull the latest updates from GitHub with environment-appropriate strategy"""
        try:
            if self.is_development:
                logger.info("📥 Pulling latest updates (development mode - full repository)...")
                return self._pull_updates_development()
            else:
                logger.info("📥 Pulling latest updates with sparse checkout...")
                return self._pull_updates_production()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git command failed with return code {e.returncode}")
            logger.error(f"   Command: {' '.join(e.cmd)}")
            if e.stdout:
                logger.error(f"   Stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"   Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Update failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def _pull_updates_development(self):
        """Pull updates for development environment (full repository)"""
        # Ensure we're in the right directory
        os.chdir(self.device_path)
        
        # Set up authenticated remote URL for private repos
        if GITHUB_TOKEN:
            auth_url = f"https://{GITHUB_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
            subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], check=True)
        
        # For development, do a normal git pull without destructive operations
        result = subprocess.run([
            'git', 'pull', 'origin', BRANCH
        ], capture_output=True, text=True, check=True)
        
        logger.info(f"✅ Development update successful: {result.stdout.strip()}")
        logger.info("🖥️  Full repository maintained for development")
        return True
    
    def _pull_updates_production(self):
        """Pull updates for production environment (sparse checkout)"""
        # Ensure we're in the right directory
        os.chdir(self.device_path)
        
        # Set up authenticated remote URL for private repos
        if GITHUB_TOKEN:
            auth_url = f"https://{GITHUB_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
            subprocess.run(['git', 'remote', 'set-url', 'origin', auth_url], capture_output=True, text=True, check=True)
        
        # Configure sparse checkout FIRST (before any git operations)
        self.setup_sparse_checkout()
        
        # Fetch latest changes from remote
        logger.info("📡 Fetching latest changes from GitHub...")
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin', BRANCH],
            capture_output=True, text=True, check=True
        )
        if fetch_result.stdout.strip():
            logger.info(f"   {fetch_result.stdout.strip()}")
        
        # Reset to remote branch (handles binary files like MP3s properly)
        logger.info(f"🔄 Resetting to origin/{BRANCH}...")
        reset_result = subprocess.run(
            ['git', 'reset', '--hard', f'origin/{BRANCH}'],
            capture_output=True, text=True, check=True
        )
        if reset_result.stdout.strip():
            logger.info(f"   {reset_result.stdout.strip()}")
        
        # Clean any untracked files
        logger.info("🧹 Cleaning untracked files...")
        subprocess.run(['git', 'clean', '-fd'], capture_output=True, text=True, check=True)
        
        logger.info(f"✅ Production update successful - now on {BRANCH}")
        logger.info("🎯 Sparse checkout active - only essential files pulled")
        return True
    
    def setup_sparse_checkout(self):
        """Configure sparse checkout to only pull essential device files (production only)"""
        if self.is_development:
            logger.info("🖥️  Development environment - skipping sparse checkout")
            return
            
        try:
            # Define sparse checkout patterns for absolute minimum files
            sparse_patterns = [
                '.gitignore',                        # Git ignore rules (CRITICAL)
                'devices.json',                      # Device registry
                'device/main.py',                    # Main application
                'device/helpers.py',                 # Helper functions (renamed from config.py)
                'device/config.py',                  # MAC address and device identification
                'device/led_failsafe_manager.py',    # LED hardware control
                'device/azure_function_client.py',   # API client
                'device/settings.json',              # Device configuration
                'device/alert_audio/',               # Audio files directory (includes all contents)
                'device/web_status.py',              # Web dashboard for restart_system.sh
                'updater/auto_updater.py',           # Update system
                'updater/watchdog.py',               # Watchdog system for restart_system.sh
                'requirements.txt',                  # Python dependencies
                'restart_system.sh',                 # System restart script (interactive)
                'start_on_boot.sh'                   # Boot startup script (non-interactive)
            ]
            
            # Check if sparse checkout file exists and has correct patterns
            sparse_checkout_file = os.path.join(self.device_path, '.git', 'info', 'sparse-checkout')
            needs_update = True
            
            if os.path.exists(sparse_checkout_file):
                with open(sparse_checkout_file, 'r') as f:
                    existing_patterns = set(line.strip() for line in f if line.strip())
                if existing_patterns == set(sparse_patterns):
                    needs_update = False
                    logger.info("🎯 Sparse checkout already configured correctly")
            
            if needs_update:
                # Enable sparse checkout
                subprocess.run(['git', 'config', 'core.sparseCheckout', 'true'], 
                             capture_output=True, text=True, check=True)
                
                # Disable cone mode for pattern-based sparse checkout
                subprocess.run(['git', 'config', 'core.sparseCheckoutCone', 'false'],
                             capture_output=True, text=True, check=True)
                
                # Write sparse checkout patterns
                os.makedirs(os.path.dirname(sparse_checkout_file), exist_ok=True)
                with open(sparse_checkout_file, 'w') as f:
                    for pattern in sparse_patterns:
                        f.write(f"{pattern}\n")
                
                logger.info("🎯 Sparse checkout patterns configured:")
                for pattern in sparse_patterns:
                    logger.info(f"   ✓ {pattern}")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not setup sparse checkout: {type(e).__name__}: {e}")
            logger.warning("   Falling back to full repository pull")
            # Disable sparse checkout on failure
            try:
                subprocess.run(['git', 'config', 'core.sparseCheckout', 'false'], 
                             capture_output=True, text=True, check=False)
            except:
                pass
    
    def install_dependencies(self):
        """Install any new Python dependencies"""
        try:
            requirements_file = os.path.join(self.device_path, 'requirements.txt')
            if os.path.exists(requirements_file):
                logger.info("📦 Installing dependencies...")
                
                # Use the current Python executable (works in virtual environment)
                result = subprocess.run([
                    self.python_executable, '-m', 'pip', 'install', '-r', requirements_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Dependencies installed")
                else:
                    logger.warning(f"Dependency installation warning: {result.stderr}")
                    
        except Exception as e:
            logger.warning(f"Could not install dependencies: {e}")
    
    def start_main_process(self):
        """Start the WaveAlert360 main process"""
        try:
            main_script = os.path.join(self.device_path, 'device', 'main.py')
            if os.path.exists(main_script):
                logger.info("🚀 Starting WaveAlert360 main process...")
                
                # Use the correct Python executable and working directory
                self.main_process = subprocess.Popen([
                    self.python_executable, main_script
                ], cwd=os.path.join(self.device_path, 'device'))
                
                logger.info(f"✅ Main process started (PID: {self.main_process.pid})")
                return True
            else:
                logger.error(f"❌ Main script not found: {main_script}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start main process: {e}")
            return False
    
    def start_web_process(self):
        """Start the web_status.py dashboard process"""
        try:
            web_script = os.path.join(self.device_path, 'device', 'web_status.py')
            if os.path.exists(web_script):
                logger.info("🌐 Starting web dashboard process...")
                
                # Start web_status.py in background with correct working directory (device subdirectory)
                device_dir = os.path.join(self.device_path, 'device')
                
                # Redirect stdout/stderr to prevent hanging and properly detach process
                with open(os.devnull, 'w') as devnull:
                    self.web_process = subprocess.Popen([
                        self.python_executable, web_script
                    ], cwd=device_dir, stdout=devnull, stderr=devnull, 
                       preexec_fn=os.setsid if hasattr(os, 'setsid') else None)
                
                logger.info(f"✅ Web dashboard started (PID: {self.web_process.pid})")
                return True
            else:
                logger.error(f"❌ Web script not found: {web_script}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start web process: {e}")
            return False
    
    def stop_web_process(self):
        """Stop the running web_status.py process"""
        try:
            if self.web_process and self.web_process.poll() is None:
                logger.info("🛑 Stopping web dashboard process...")
                
                # Graceful shutdown first
                self.web_process.terminate()
                
                try:
                    # Wait for graceful shutdown
                    self.web_process.wait(timeout=10)
                    logger.info("✅ Web dashboard stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning("⚠️  Web dashboard didn't stop gracefully, forcing...")
                    self.web_process.kill()
                    self.web_process.wait(timeout=5)
                    logger.info("✅ Web dashboard force-stopped")
                    
                self.web_process = None
            else:
                logger.info("ℹ️  No web dashboard process to stop")
                
        except Exception as e:
            logger.warning(f"Error stopping web process: {e}")
            self.web_process = None
    
    def print_status_banner(self, status, details=None):
        """Print a visually clear status banner"""
        banner_width = 60
        if status == "checking":
            border = "🔍" + "="*(banner_width-2) + "🔍"
            logger.info(border)
            logger.info(f"🔍 CHECKING FOR UPDATES - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(border)
        elif status == "no_update":
            border = "✅" + "="*(banner_width-2) + "✅"
            logger.info(border)
            logger.info("✅ NO UPDATES NEEDED - SYSTEM UP TO DATE")
            if details:
                logger.info(f"   Current commit: {details}")
            logger.info(border)
        elif status == "updating":
            border = "🔄" + "="*(banner_width-2) + "🔄"
            logger.info(border)
            logger.info("🔄 UPDATE IN PROGRESS - DEPLOYING NEW VERSION")
            if details:
                logger.info(f"   New commit: {details}")
            logger.info(border)
        elif status == "update_complete":
            border = "🎉" + "="*(banner_width-2) + "🎉"
            logger.info(border)
            logger.info("🎉 UPDATE COMPLETED SUCCESSFULLY!")
            if details:
                logger.info(f"   Now running: {details}")
            logger.info(border)
        elif status == "update_failed":
            border = "❌" + "="*(banner_width-2) + "❌"
            logger.info(border)
            logger.info("❌ UPDATE FAILED - CONTINUING WITH CURRENT VERSION")
            if details:
                logger.info(f"   Error: {details}")
            logger.info(border)
    
    def perform_update(self, commit_sha, commit_message):
        """Perform the complete update process with enhanced safety"""
        self.print_status_banner("updating", f"{commit_sha[:8]} - {commit_message.strip()}")
        
        # Create update lock file to prevent concurrent updates
        lock_file = os.path.join(self.device_path, '.update_in_progress')
        try:
            with open(lock_file, 'w') as f:
                f.write(f"Update started at {datetime.now().isoformat()}\n")
                f.write(f"Target commit: {commit_sha}\n")
            
            # Step 1: Stop web dashboard for clean update
            # NOTE: main.py is managed by watchdog, not auto-updater
            self.stop_web_process()
            
            # Step 2: Backup current version
            self.backup_current_version()
            
            # Step 3: Pull updates
            if not self.pull_updates():
                self.print_status_banner("update_failed", "Git pull failed")
                logger.error("❌ Update failed - restarting web dashboard with old code")
                self.start_web_process()
                return False
            
            # Step 4: Install dependencies
            self.install_dependencies()
            
            # Step 5: Save the new commit SHA
            self.save_last_commit(commit_sha)
            
            # Step 6: Check if auto_updater.py itself was updated - if so, restart ourselves
            updated_files = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD@{1}', 'HEAD'],
                capture_output=True, text=True, cwd=self.device_path
            ).stdout.strip().split('\n')
            
            auto_updater_changed = any('auto_updater.py' in f for f in updated_files)
            
            if auto_updater_changed:
                logger.info("🔄 auto_updater.py was updated - restarting self to load new code...")
                self.start_web_process()
                self.print_status_banner("update_complete", f"{commit_sha[:8]} - Auto-updater restarting with new code")
                
                # Save commit before restarting
                self.save_last_commit(commit_sha)
                
                # Release lock before restart
                try:
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
                except:
                    pass
                
                # Restart ourselves with new code
                logger.info("🔄 Executing restart with new code...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
            # Step 7: Start the updated web dashboard
            if not self.start_web_process():
                logger.warning("⚠️  Failed to start web dashboard, continuing anyway")
            
                logger.error("❌ Failed to start updated web dashboard")
                return False
            
            # NOTE: main.py will auto-restart via watchdog when it detects new code
            # No need to manage it here
            
            self.print_status_banner("update_complete", f"{commit_sha[:8]} - {commit_message.strip()}")
            return True
            
        except Exception as e:
            self.print_status_banner("update_failed", f"Unexpected error: {str(e)}")
            logger.error(f"❌ Update process failed: {e}")
            # Try to restart web dashboard with old code
            self.start_web_process()
            return False
            
        finally:
            # Always remove lock file
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except:
                pass
    
    def write_health_check(self):
        """Write a health check file to indicate auto-updater is alive"""
        try:
            health_file = os.path.join(self.device_path, '.updater_health')
            with open(health_file, 'w') as f:
                f.write(f"alive:{datetime.now().isoformat()}\n")
                f.write(f"pid:{os.getpid()}\n")
                f.write(f"checks:{getattr(self, 'check_count', 0)}\n")
        except Exception as e:
            logger.warning(f"Could not write health check: {e}")
    
    def _run_development_mode(self):
        """Simple monitoring loop for development environment"""
        logger.info("🖥️  Entering development monitoring mode...")
        logger.info("   - Auto-updates: DISABLED")
        logger.info("   - Process monitoring: ENABLED")
        logger.info("   - Sparse checkout: DISABLED")
        logger.info("")
        
        while True:
            try:
                # Just monitor the main process, no updates
                if self.main_process and self.main_process.poll() is not None:
                    logger.warning("🔄 Main process stopped - restarting...")
                    self.start_main_process()
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 Development mode stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Development monitoring error: {e}")
                time.sleep(10)  # Brief pause before retry
    
    def perform_initial_commit_check(self):
        """Perform initial commit comparison on startup"""
        try:
            banner_width = 60
            check_border = "🔍" + "="*(banner_width-2) + "🔍"
            logger.info(check_border)
            logger.info("🔍 INITIAL COMMIT COMPARISON CHECK")
            logger.info(check_border)
            
            # Get local commit info
            local_commit = self.last_commit_sha
            local_short = local_commit[:8] if local_commit else "None"
            
            logger.info(f"📁 Local commit:  {local_short}")
            
            # Get remote commit info
            try:
                headers = {
                    'User-Agent': 'WaveAlert360-AutoUpdater',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                # Add GitHub authentication for private repos
                if GITHUB_TOKEN:
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'
                
                response = requests.get(COMMITS_ENDPOINT, headers=headers, timeout=10)
                response.raise_for_status()
                
                commit_data = response.json()
                remote_commit = commit_data['sha']
                remote_short = remote_commit[:8]
                commit_message = commit_data['commit']['message'].strip()
                commit_date = commit_data['commit']['committer']['date']
                
                logger.info(f"🌐 Remote commit: {remote_short}")
                logger.info(f"📝 Message:      {commit_message}")
                logger.info(f"📅 Date:         {commit_date}")
                
                # Compare commits
                if local_commit == remote_commit:
                    logger.info("✅ COMMITS MATCH - System is up to date")
                elif local_commit is None:
                    logger.info("⚠️  NO LOCAL COMMIT - First run or missing .last_commit file")
                    logger.info("🔄 Update will be triggered on first check cycle")
                else:
                    logger.info("🔄 COMMITS DIFFER - Update available")
                    logger.info(f"   Will update from {local_short} to {remote_short}")
                
            except requests.RequestException as e:
                logger.error(f"❌ Failed to fetch remote commit: {e}")
                logger.info(f"📁 Local commit only: {local_short}")
            except Exception as e:
                logger.error(f"❌ Error during remote check: {e}")
                logger.info(f"📁 Local commit only: {local_short}")
            
            logger.info(check_border)
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Initial commit check failed: {e}")
    
    def run_forever(self):
        """Main loop - check for updates every 2 minutes"""
        # Startup banner
        banner_width = 60
        startup_border = "🌊" + "="*(banner_width-2) + "🌊"
        logger.info(startup_border)
        logger.info("🌊 WAVEALERT360 AUTO-UPDATER STARTED")
        logger.info(f"   Repository: {REPO_URL}")
        logger.info(f"   Device Path: {self.device_path}")
        logger.info(f"   Check Interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL//60} minutes)")
        logger.info(f"   Platform: {platform.system()}")
        
        if self.is_development:
            logger.info(f"   Mode: Development (full repository) 🖥️")
            logger.info("   Auto-updates ENABLED for testing")
        else:
            logger.info(f"   Mode: Production (sparse checkout) 🎯")
            
        logger.info(startup_border)
        logger.info("")
        
        # Always run full auto-update functionality regardless of environment
        # Start the web dashboard initially if not running
        if not self.web_process or self.web_process.poll() is not None:
            logger.info("🚀 Starting initial web dashboard...")
            self.start_web_process()
            logger.info("")
            
        # NOTE: main.py is now monitored by watchdog.py, not auto-updater
        # Auto-updater only handles GitHub updates and web dashboard
        
        # Perform initial commit comparison check
        self.perform_initial_commit_check()
        
        # Initialize check counter for health monitoring
        self.check_count = 0

        while True:
            try:
                self.check_count += 1
                self.write_health_check()  # Write health status
                
                self.print_status_banner("checking")
                
                has_update, commit_sha, commit_message = self.check_for_updates()
                
                # Check for existing update lock
                lock_file = os.path.join(self.device_path, '.update_in_progress')
                if os.path.exists(lock_file):
                    logger.warning("⚠️  Update already in progress, skipping this check")
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                if has_update and commit_sha:
                    update_success = self.perform_update(commit_sha, commit_message)
                    if not update_success:
                        logger.warning("⚠️  Update failed but system continues running")
                else:
                    current_commit = self.last_commit_sha[:8] if self.last_commit_sha else "unknown"
                    self.print_status_banner("no_update", current_commit)

                # NOTE: main.py health checking is now handled by watchdog.py
                # Auto-updater only manages web dashboard

                # Check if web process is still running
                try:
                    if not self.web_process or self.web_process.poll() is not None:
                        if not self.web_process:
                            logger.info("🌐 Web dashboard not started yet - starting now...")
                        else:
                            logger.warning("⚠️  Web dashboard stopped unexpectedly - restarting...")

                        success = self.start_web_process()
                        if success:
                            logger.info("✅ Web dashboard health check: Started successfully")
                        else:
                            logger.error("❌ Web dashboard health check: Failed to start")
                except Exception as e:
                    logger.error(f"❌ Web process health check failed: {e}")
                    logger.info("🌐 Attempting to start web dashboard anyway...")
                    self.start_web_process()
                
                # Sleep with countdown
                logger.info(f"😴 Sleeping for {CHECK_INTERVAL} seconds until next check...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 Auto-updater stopped by user")
                # No need to stop main_process - watchdog handles it
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error details: {str(e)}")
                
                # Continue running despite errors (fail-safe)
                logger.info("🔄 Auto-updater continuing despite error...")
                time.sleep(CHECK_INTERVAL)

def main():
    """Entry point"""
    updater = WaveAlert360AutoUpdater()
    
    # Ensure only one auto-updater instance is running
    if not updater.process_lock.acquire():
        logger.error("❌ Another auto-updater instance is already running!")
        logger.info("🔍 Check processes with: tasklist | findstr python")
        sys.exit(1)
    
    logger.info("🔒 Auto-updater process lock acquired")
    
    try:
        updater.run_forever()
    finally:
        updater.process_lock.release()

if __name__ == "__main__":
    main()
