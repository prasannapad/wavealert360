#!/usr/bin/env python3
"""
Simple local audio generation for testing purposes
Uses Windows SAPI (Speech API) for text-to-speech conversion
"""

import os
import subprocess
import tempfile
from pathlib import Path

def generate_local_audio(text, output_file, voice_speed=0):
    """
    Generate audio using Windows Speech API (SAPI)
    """
    try:
        # Create PowerShell script for SAPI TTS
        ps_script = f'''
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = {voice_speed}
$speak.SetOutputToWaveFile("{output_file}")
$speak.Speak("{text}")
$speak.Dispose()
'''
        
        # Write PowerShell script to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            ps_file = f.name
        
        # Execute PowerShell script
        result = subprocess.run([
            'powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file
        ], capture_output=True, text=True)
        
        # Clean up temp file
        os.unlink(ps_file)
        
        if result.returncode == 0:
            print(f"✅ Audio generated successfully: {output_file}")
            return True
        else:
            print(f"❌ Error generating audio: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception generating audio: {e}")
        return False

def regenerate_all_audio():
    """
    Regenerate all audio files from current settings.json
    """
    try:
        # Import settings
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from helpers import SETTINGS
        
        alert_audio_dir = Path(__file__).parent
        
        # Generate normal alert audio
        normal_text = SETTINGS['alert_types']['NORMAL']['audio_text']
        normal_file = alert_audio_dir / SETTINGS['audio_files']['normal']
        
        print(f"🎵 Generating NORMAL alert audio...")
        print(f"Text: {normal_text[:100]}...")
        if generate_local_audio(normal_text, str(normal_file)):
            print(f"✅ Normal alert saved to: {normal_file}")
        
        # Generate high alert audio  
        high_text = SETTINGS['alert_types']['HIGH']['audio_text']
        high_file = alert_audio_dir / SETTINGS['audio_files']['high_alert']
        
        print(f"🎵 Generating HIGH alert audio...")
        print(f"Text: {high_text[:100]}...")
        if generate_local_audio(high_text, str(high_file), voice_speed=2):  # Faster for urgency
            print(f"✅ High alert saved to: {high_file}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error regenerating audio: {e}")
        return False

if __name__ == "__main__":
    print("🎙️ Local Audio Generator for WaveAlert360")
    print("=" * 50)
    regenerate_all_audio()
