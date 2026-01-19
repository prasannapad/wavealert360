#!/usr/bin/env python3
"""Simple LED test to verify hardware works"""

try:
    from rpi_ws281x import PixelStrip, Color
    print("✅ Library imported successfully")
    
    # Red strip on GPIO 18
    strip = PixelStrip(48, 18, 800000, 10, False, 255, 0)
    strip.begin()
    print("✅ Strip initialized")
    
    # Turn first LED red
    strip.setPixelColor(0, Color(255, 0, 0))
    strip.show()
    print("✅ LED test complete - first LED should be RED")
    print("✅ HARDWARE IS WORKING!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
