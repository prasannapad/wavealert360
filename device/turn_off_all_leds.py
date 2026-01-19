#!/usr/bin/env python3
"""Turn off all LED strips"""

from rpi_ws281x import PixelStrip, Color
import time

LED_COUNT = 48
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255

# Initialize all three strips
print("Initializing all strips...")
red_strip = PixelStrip(LED_COUNT, 18, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, 0)
yellow_strip = PixelStrip(LED_COUNT, 21, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, 0)
green_strip = PixelStrip(LED_COUNT, 13, LED_FREQ_HZ, LED_DMA, False, LED_BRIGHTNESS, 1)

red_strip.begin()
yellow_strip.begin()
green_strip.begin()

print("Turning off all LEDs...")
for j in range(LED_COUNT):
    red_strip.setPixelColor(j, Color(0, 0, 0))
    yellow_strip.setPixelColor(j, Color(0, 0, 0))
    green_strip.setPixelColor(j, Color(0, 0, 0))

red_strip.show()
yellow_strip.show()
green_strip.show()

print("✅ All LEDs turned OFF")
