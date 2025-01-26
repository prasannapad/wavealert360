import requests
import datetime
import pytz
import azure.cognitiveservices.speech as speechsdk

# Your Azure subscription key and region
subscription_key = "CddhSq71d2nNjDjJuljQxQPcIYoBTW2u3zrc14ksxbSJfj97AYEEJQQJ99BAAC8vTInXJ3w3AAAYACOGqL6J"
region = "westus2"

# Function to check if the alert is currently in effect
def is_alert_in_effect(alert):
    # Parse the effective and expires time
    effective_time = datetime.datetime.fromisoformat(alert['properties']['effective'].replace('Z', '+00:00'))
    expires_time = datetime.datetime.fromisoformat(alert['properties']['expires'].replace('Z', '+00:00'))

    # Get the current time in UTC
    current_time = datetime.datetime.now(pytz.utc)

    # Check if the current time is between effective and expires times
    return effective_time <= current_time <= expires_time

# Function to get the alerts from the NWS API
def get_alerts():
    url = f'https://api.weather.gov/alerts/active'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        alerts = data['features']
        return alerts
    else:
        print("Error fetching alerts.")
        return []

# Function to speak the alert headline using Azure TTS
def speak_alert(text):
    try:
        # Set up Azure Speech configuration
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        
        # Create an audio configuration (no need to specify use_default_speaker)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)  # Using the default speaker
        
        # Create a speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Start speech synthesis
        result = synthesizer.speak_text_async(text).get()

        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Successfully synthesized the text.")
        else:
            print(f"Error in speech synthesis: {result.error_details}")

    except Exception as e:
        print(f"Error in speech synthesis: {e}")

# Main program to process and speak relevant alerts
def main():
    # Get all active alerts
    alerts = get_alerts()
    
    if alerts:
        for alert in alerts:
            # Check for Rip Current Statement event type
            event_type = alert['properties']['event']
            if event_type == "Rip Current Statement":
                # Access the NWSheadline from the correct location in the JSON
                nws_headline = alert['properties']['parameters']['NWSheadline'][0]  # Correctly fetching from parameters
                # Access and clean the instruction text
                instruction = alert['properties']['instruction'].replace("\n", " ")

                # Be very careful and cautious in understanding the alert's scope and validity
                print(f"ALERT... ALERT... ALERT...: {nws_headline}")
                print(f"Instructions: {instruction}")

                # Check if the alert is currently in effect
                if is_alert_in_effect(alert):
                    # If in effect, speak the headline and instruction
                    speak_alert(f"ALERT! ALERT! ALERT! {nws_headline}. {instruction}")
                else:
                    print(f"Alert {nws_headline} is not currently in effect.")
    else:
        print("No active alerts found.")

if __name__ == "__main__":
    main()
