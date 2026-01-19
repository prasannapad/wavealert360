#!/usr/bin/env python3
"""Test if rpi_ws281x imports successfully"""

print("Testing import...")
try:
    from rpi_ws281x import PixelStrip, Color, ws
    print("✅ Import succeeded!")
    print(f"PixelStrip: {PixelStrip}")
    print(f"Color: {Color}")
    print(f"ws: {ws}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
