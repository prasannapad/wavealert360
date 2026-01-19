#!/usr/bin/env python3
"""Simple test to blink the yellow LED strip on GPIO 21"""

from rpi_ws281x import PixelStrip, Color
import time

# Yellow strip configuration - GPIO 21
YELLOW_PIN = 21
LED_COUNT = 48
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_CHANNEL = 0

print("Initializing yellow LED strip on GPIO 21...")
strip = PixelStrip(LED_COUNT, YELLOW_PIN, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

print("Starting blink test (10 cycles)...")
for i in range(10):
    # All LEDs yellow (same as WaveAlert yellow: 255, 100, 0)
    for j in range(LED_COUNT):
        strip.setPixelColor(j, Color(255, 100, 0))
    strip.show()
    print(f"Cycle {i+1}: ON")
    time.sleep(0.5)
    
    # All LEDs off
    for j in range(LED_COUNT):
        strip.setPixelColor(j, Color(0, 0, 0))
    strip.show()
    print(f"Cycle {i+1}: OFF")
    time.sleep(0.5)

print("✅ Blink test complete - all LEDs should be OFF")
