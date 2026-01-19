#!/usr/bin/env python3
"""
WaveAlert360 Device Configuration
Handles device identification and system configuration
"""

import os
import socket

def get_mac_address():
    """
    Get device MAC address for identification
    
    Returns:
        str: MAC address in format 'xx:xx:xx:xx:xx:xx'
    """
    try:
        # Try eth0 first (wired connection)
        if os.path.exists('/sys/class/net/eth0/address'):
            with open('/sys/class/net/eth0/address', 'r') as f:
                mac = f.read().strip()
                print(f"✅ Got MAC from eth0: {mac}")
                return mac
        
        # Fallback to wlan0 (wireless connection)
        if os.path.exists('/sys/class/net/wlan0/address'):
            with open('/sys/class/net/wlan0/address', 'r') as f:
                mac = f.read().strip()
                print(f"✅ Got MAC from wlan0: {mac}")
                return mac
                
        # Fallback for testing/development (use hostname-based identifier)
        hostname = socket.gethostname()
        test_mac = f"test-{hostname}"
        print(f"⚠️  Using test MAC (no network interfaces found): {test_mac}")
        return test_mac
        
    except Exception as e:
        print(f"❌ Error getting MAC address: {e}")
        # Final fallback
        return "unknown-device"

def get_device_id():
    """Alias for get_mac_address for backwards compatibility"""
    return get_mac_address()

# Service configuration
SERVICE_URL = "http://localhost:5000"  # Will be configurable later

# Device settings
DEVICE_NAME = "WaveAlert360"
CHECK_INTERVAL = 60  # seconds between service calls
AUDIO_DOWNLOAD_TIMEOUT = 30  # seconds
SERVICE_TIMEOUT = 10  # seconds