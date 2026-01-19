#!/usr/bin/env python3
"""
Test Beach Sign LED Alert System
=================================
Tests the two-strip beach sign with different alert levels:
- DANGER: Red strip blinks, yellow OFF
- CAUTION: Yellow strip blinks, red OFF  
- SAFE: Yellow strip shows green (until third strip installed)
"""

import time
import board
import neopixel

# Strip Configuration
RED_STRIP_PIN = board.D18
YELLOW_STRIP_PIN = board.D21
LED_COUNT = 48

# Initialize both strips
print("🏖️  Initializing Beach Sign LED strips...")
red_strip = neopixel.NeoPixel(RED_STRIP_PIN, LED_COUNT, brightness=1.0, auto_write=False)
yellow_strip = neopixel.NeoPixel(YELLOW_STRIP_PIN, LED_COUNT, brightness=1.0, auto_write=False)

# Colors
RED = (255, 0, 0)
YELLOW = (255, 100, 0)
GREEN = (0, 255, 0)
OFF = (0, 0, 0)

def turn_off_all():
    """Turn off both strips"""
    red_strip.fill(OFF)
    red_strip.show()
    yellow_strip.fill(OFF)
    yellow_strip.show()

def test_danger_alert():
    """Test DANGER alert - Red strip blinks, yellow OFF"""
    print("\n🔴 Testing DANGER alert (Red strip blinks)...")
    yellow_strip.fill(OFF)
    yellow_strip.show()
    
    for i in range(6):
        red_strip.fill(RED)
        red_strip.show()
        time.sleep(0.5)
        red_strip.fill(OFF)
        red_strip.show()
        time.sleep(0.5)
    
    print("   ✅ DANGER alert test complete")

def test_caution_alert():
    """Test CAUTION alert - Yellow strip blinks, red OFF"""
    print("\n🟡 Testing CAUTION alert (Yellow strip blinks)...")
    red_strip.fill(OFF)
    red_strip.show()
    
    for i in range(6):
        yellow_strip.fill(YELLOW)
        yellow_strip.show()
        time.sleep(0.5)
        yellow_strip.fill(OFF)
        yellow_strip.show()
        time.sleep(0.5)
    
    print("   ✅ CAUTION alert test complete")

def test_safe_alert():
    """Test SAFE alert - Both strips OFF (waiting for 3rd green strip)"""
    print("\n⚫ Testing SAFE alert (Both strips OFF - no green strip yet)...")
    red_strip.fill(OFF)
    red_strip.show()
    yellow_strip.fill(OFF)
    yellow_strip.show()
    
    time.sleep(3.0)
    
    print("   ✅ SAFE alert test complete")
    print("   ℹ️  Both strips remain OFF until 3rd green strip is installed")

def main():
    print("=" * 60)
    print("🏖️  BEACH SIGN LED ALERT SYSTEM TEST")
    print("=" * 60)
    print(f"Red Strip (Danger): GPIO 18, {LED_COUNT} LEDs")
    print(f"Yellow Strip (Caution): GPIO 21, {LED_COUNT} LEDs")
    print(f"Green Strip (Safe): Not installed yet")
    print()
    
    try:
        # Clear all strips
        turn_off_all()
        time.sleep(1)
        
        # Test each alert level
        test_danger_alert()
        time.sleep(1)
        
        test_caution_alert()
        time.sleep(1)
        
        test_safe_alert()
        time.sleep(1)
        
        # Final cleanup
        turn_off_all()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETE - Beach Sign Ready!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        turn_off_all()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        turn_off_all()

if __name__ == "__main__":
    main()
