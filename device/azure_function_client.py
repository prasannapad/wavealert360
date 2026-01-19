import requests
import json
import os
import hashlib
from datetime import datetime

def trigger_audio_generation(audio_text, audio_type='normal'):
    """Trigger Azure Function to generate audio"""
    
    function_url = os.environ.get('AZURE_FUNCTION_URL', 'https://wavealert360-audio-generator.azurewebsites.net/api/audio_generator')
    
    data = {
        'audio_text': audio_text,
        'audio_type': audio_type
    }
    
    try:
        print(f"🎵 Triggering audio generation for {audio_type} alert...")
        
        response = requests.post(function_url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Audio generated successfully!")
            print(f"   Filename: {result.get('filename')}")
            print(f"   URL: {result.get('url')}")
            print(f"   Size: {result.get('size')} bytes")
            return result
        else:
            print(f"❌ Audio generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error triggering audio generation: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the functions
    print("🧪 Testing Azure Function integration...")
    
    # Test audio generation
    test_text = "This is a test of the Azure Function audio generation system."
    result = trigger_audio_generation(test_text, 'normal')
