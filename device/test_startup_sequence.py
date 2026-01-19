#!/usr/bin/env python3
"""
Test Beach Sign LED Startup Sequence
Tests both strips (RED GPIO 18 and YELLOW GPIO 21) with complete startup animations
"""

import time
import board
import neopixel

# LED strip configuration
RED_STRIP_PIN = board.D18      # GPIO 18 (Physical pin 12) - RED/DANGER strip
YELLOW_STRIP_PIN = board.D21   # GPIO 21 (Physical pin 40) - YELLOW/CAUTION strip
NUM_LEDS = 48                  # 48 LEDs per strip
BRIGHTNESS = 1.0               # 100% brightness

# Colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

def startup_sequence(strip, color, strip_name):
    """Run a startup sequence on a single strip"""
    print(f"\n{'='*60}")
    print(f"🚀 {strip_name} STARTUP SEQUENCE")
    print(f"{'='*60}")
    
    # Phase 1: Quick flash to show strip is alive
    print(f"Phase 1: Power-on flash...")
    strip.fill(color)
    strip.show()
    time.sleep(0.2)
    strip.fill(OFF)
    strip.show()
    time.sleep(0.2)
    strip.fill(color)
    strip.show()
    time.sleep(0.2)
    strip.fill(OFF)
    strip.show()
    time.sleep(0.5)
    
    # Phase 2: Chase pattern (pixels lighting up one by one)
    print(f"Phase 2: Chase pattern...")
    for i in range(NUM_LEDS):
        strip[i] = color
        strip.show()
        time.sleep(0.02)
    time.sleep(0.3)
    
    # Phase 3: Fade out
    print(f"Phase 3: Fade out...")
    for brightness in range(255, 0, -15):
        scaled_color = tuple(int(c * brightness / 255) for c in color)
        strip.fill(scaled_color)
        strip.show()
        time.sleep(0.03)
    
    strip.fill(OFF)
    strip.show()
    time.sleep(0.5)
    
    print(f"✅ {strip_name} startup complete!")

def test_beach_sign_patterns(red_strip, yellow_strip):
    """Test the three beach sign alert patterns"""
    print(f"\n{'='*60}")
    print(f"🏖️  BEACH SIGN ALERT PATTERNS")
    print(f"{'='*60}")
    
    # Pattern 1: DANGER (RED blinking)
    print(f"\nPattern 1: DANGER - Red blinking (5 cycles)")
    for cycle in range(5):
        red_strip.fill(RED)
        red_strip.show()
        yellow_strip.fill(OFF)
        yellow_strip.show()
        print(f"  🔴 RED ON  (cycle {cycle + 1}/5)")
        time.sleep(0.5)
        
        red_strip.fill(OFF)
        red_strip.show()
        print(f"  ⚫ RED OFF (cycle {cycle + 1}/5)")
        time.sleep(0.5)
    
    time.sleep(1)
    
    # Pattern 2: CAUTION (YELLOW blinking)
    print(f"\nPattern 2: CAUTION - Yellow blinking (5 cycles)")
    for cycle in range(5):
        yellow_strip.fill(YELLOW)
        yellow_strip.show()
        red_strip.fill(OFF)
        red_strip.show()
        print(f"  🟡 YELLOW ON  (cycle {cycle + 1}/5)")
        time.sleep(0.5)
        
        yellow_strip.fill(OFF)
        yellow_strip.show()
        print(f"  ⚫ YELLOW OFF (cycle {cycle + 1}/5)")
        time.sleep(0.5)
    
    time.sleep(1)
    
    # Pattern 3: SAFE (Both OFF - waiting for green strip)
    print(f"\nPattern 3: SAFE - Both strips OFF (waiting for GREEN strip)")
    print(f"  Note: GREEN strip (GPIO 12) not yet installed")
    red_strip.fill(OFF)
    red_strip.show()
    yellow_strip.fill(OFF)
    yellow_strip.show()
    print(f"  ⚫⚫ BOTH OFF (GREEN will show SAFE when installed)")
    time.sleep(2)
    
    print(f"\n✅ All beach sign patterns tested!")

def test_both_strips_together(red_strip, yellow_strip):
    """Fun test showing both strips working together"""
    print(f"\n{'='*60}")
    print(f"🎨 DUAL STRIP COORDINATION TEST")
    print(f"{'='*60}")
    
    # Alternating pattern
    print(f"\nAlternating red and yellow (5 cycles)...")
    for cycle in range(5):
        red_strip.fill(RED)
        yellow_strip.fill(OFF)
        red_strip.show()
        yellow_strip.show()
        print(f"  🔴⚫ RED / YELLOW OFF (cycle {cycle + 1}/5)")
        time.sleep(0.3)
        
        red_strip.fill(OFF)
        yellow_strip.fill(YELLOW)
        red_strip.show()
        yellow_strip.show()
        print(f"  ⚫🟡 RED OFF / YELLOW (cycle {cycle + 1}/5)")
        time.sleep(0.3)
    
    # Both on together (should not happen in production)
    print(f"\nBoth strips ON together (test only - not used in production)...")
    red_strip.fill(RED)
    yellow_strip.fill(YELLOW)
    red_strip.show()
    yellow_strip.show()
    print(f"  🔴🟡 BOTH ON")
    time.sleep(1)
    
    # Turn both off
    red_strip.fill(OFF)
    yellow_strip.fill(OFF)
    red_strip.show()
    yellow_strip.show()
    print(f"  ⚫⚫ BOTH OFF")
    
    print(f"\n✅ Dual strip coordination test complete!")

def main():
    print(f"\n{'*'*60}")
    print(f"🏖️  BEACH SIGN LED STARTUP SEQUENCE TEST")
    print(f"{'*'*60}")
    print(f"\nHardware Configuration:")
    print(f"  RED Strip:    GPIO 18 (Physical Pin 12)  - 48 LEDs - DANGER alerts")
    print(f"  YELLOW Strip: GPIO 21 (Physical Pin 40)  - 48 LEDs - CAUTION alerts")
    print(f"  GREEN Strip:  GPIO 12 (Physical Pin 32)  - Not yet installed - SAFE")
    print(f"\nBrightness: {int(BRIGHTNESS * 100)}%")
    print(f"\nInitializing LED strips...")
    
    try:
        # Initialize both strips
        red_strip = neopixel.NeoPixel(
            RED_STRIP_PIN, 
            NUM_LEDS, 
            brightness=BRIGHTNESS, 
            auto_write=False,
            pixel_order=neopixel.GRB
        )
        
        yellow_strip = neopixel.NeoPixel(
            YELLOW_STRIP_PIN, 
            NUM_LEDS, 
            brightness=BRIGHTNESS, 
            auto_write=False,
            pixel_order=neopixel.GRB
        )
        
        print(f"✅ Both strips initialized successfully!")
        
        # Run startup sequence for RED strip
        startup_sequence(red_strip, RED, "RED STRIP (GPIO 18)")
        
        # Run startup sequence for YELLOW strip
        startup_sequence(yellow_strip, YELLOW, "YELLOW STRIP (GPIO 21)")
        
        # Test beach sign alert patterns
        test_beach_sign_patterns(red_strip, yellow_strip)
        
        # Test both strips working together
        test_both_strips_together(red_strip, yellow_strip)
        
        # Final cleanup
        print(f"\n{'='*60}")
        print(f"🧹 CLEANUP")
        print(f"{'='*60}")
        red_strip.fill(OFF)
        yellow_strip.fill(OFF)
        red_strip.show()
        yellow_strip.show()
        print(f"✅ All strips turned OFF")
        
        print(f"\n{'*'*60}")
        print(f"✅ STARTUP SEQUENCE TEST COMPLETE!")
        print(f"{'*'*60}")
        print(f"\nNext Steps:")
        print(f"  1. Install GREEN strip on GPIO 12 (Physical Pin 32)")
        print(f"  2. Run this test again to verify all 3 strips")
        print(f"  3. Deploy to production with led_failsafe_manager.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check that both LED strips are connected")
        print(f"  2. Verify power supply (5V to pin 4)")
        print(f"  3. Check data connections:")
        print(f"     - RED strip data → GPIO 18 (Pin 12)")
        print(f"     - YELLOW strip data → GPIO 21 (Pin 40)")
        print(f"  4. Run with sudo: sudo python3 test_startup_sequence.py")

if __name__ == "__main__":
    main()
