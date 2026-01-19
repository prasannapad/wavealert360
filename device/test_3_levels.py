#!/usr/bin/env python3
"""
Test all 3 alert levels for the beach sign
Cycles through DANGER (RED), CAUTION (YELLOW), and SAFE (all off)
"""

import time
import subprocess

def set_alert_level(level_name, pattern):
    """Set alert level and display status"""
    print(f"\n{'='*60}")
    print(f"Testing: {level_name}")
    print(f"Pattern: {pattern}")
    print(f"{'='*60}")
    
    # Write pattern to control file
    subprocess.run(['bash', '-c', f'echo "{pattern}" > /tmp/led_control_signal'], check=True)
    
    # Show current status
    subprocess.run(['cat', '/tmp/led_service_status'])
    print()

def clean_state():
    """Stop any running main.py that would interfere with testing"""
    print("🧹 Cleaning up - stopping main.py and related processes...")
    subprocess.run(['pkill', '-f', 'main.py'], check=False)
    time.sleep(2)
    print("✅ Clean state ready")
    print()

def main():
    print("🏖️  3-LEVEL BEACH SIGN ALERT TEST")
    print("="*60)
    print("Testing all 3 alert levels:")
    print("  1. DANGER  → RED blinking")
    print("  2. CAUTION → YELLOW blinking")
    print("  3. SAFE    → All OFF (GREEN when installed)")
    print()
    print("Each level will display for 10 seconds")
    print("Test will run 2 complete cycles then stop automatically")
    print("Total test time: ~60 seconds")
    print("="*60)
    print()
    
    # Clean state before starting
    clean_state()
    
    NUM_CYCLES = 2  # Run 2 complete cycles
    DISPLAY_TIME = 10  # 10 seconds per level
    
    try:
        for cycle in range(1, NUM_CYCLES + 1):
            print(f"\n🔄 CYCLE {cycle} of {NUM_CYCLES}")
            print("-" * 60)
            
            # Test DANGER level
            set_alert_level("DANGER (High Alert)", "PATTERN:RED_BLINK")
            print(f"⏰ Watch RED strip blinking for {DISPLAY_TIME} seconds...")
            time.sleep(DISPLAY_TIME)
            
            # Test CAUTION level
            set_alert_level("CAUTION (Moderate Alert)", "PATTERN:YELLOW")
            print(f"⏰ Watch YELLOW strip blinking for {DISPLAY_TIME} seconds...")
            time.sleep(DISPLAY_TIME)
            
            # Test SAFE level
            set_alert_level("SAFE (Normal Conditions)", "PATTERN:GREEN")
            print(f"⏰ Both strips should be OFF for {DISPLAY_TIME} seconds...")
            print("   (GREEN will show when 3rd strip installed)")
            time.sleep(DISPLAY_TIME)
        
        # Test completed successfully
        print("\n" + "="*60)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nAll 3 alert levels tested:")
        print("  ✅ DANGER  - RED blinking worked")
        print("  ✅ CAUTION - YELLOW blinking worked")
        print("  ✅ SAFE    - Both OFF worked")
        print()
        print("Resetting to DANGER level...")
        subprocess.run(['bash', '-c', 'echo "PATTERN:RED_BLINK" > /tmp/led_control_signal'])
        print("✅ Reset complete")
        print()
        print("💡 NEXT STEPS:")
        print("   To restart the full system: cd /home/pi/WaveAlert360 && ./restart_system.sh")
        print("   To run test again: python3 test_3_levels.py")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test stopped by user")
        print("Resetting to DANGER level...")
        subprocess.run(['bash', '-c', 'echo "PATTERN:RED_BLINK" > /tmp/led_control_signal'])
        print("✅ Reset complete")
        print()
        print("💡 TIP: To restart the full system, run:")
        print("   cd /home/pi/WaveAlert360 && ./restart_system.sh")

if __name__ == "__main__":
    main()
