#!/usr/bin/env python3
"""
Emergency LED OFF - Turn off all LED strips
"""

import board
import neopixel

# Configuration
RED_STRIP_PIN = board.D18      # GPIO 18
YELLOW_STRIP_PIN = board.D21   # GPIO 21
NUM_LEDS = 48

print("🔌 Turning OFF all LED strips...")

try:
    # Initialize RED strip and turn off
    red_strip = neopixel.NeoPixel(RED_STRIP_PIN, NUM_LEDS, brightness=1.0, auto_write=False)
    red_strip.fill((0, 0, 0))
    red_strip.show()
    print("✅ RED strip (GPIO 18) turned OFF")
    
    # Initialize YELLOW strip and turn off
    yellow_strip = neopixel.NeoPixel(YELLOW_STRIP_PIN, NUM_LEDS, brightness=1.0, auto_write=False)
    yellow_strip.fill((0, 0, 0))
    yellow_strip.show()
    print("✅ YELLOW strip (GPIO 21) turned OFF")
    
    print("\n✅ All LED strips are OFF")

except Exception as e:
    print(f"❌ Error: {e}")
    print("Run with: sudo python3 turn_off_leds.py")
