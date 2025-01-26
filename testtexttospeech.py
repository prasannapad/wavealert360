from gtts import gTTS
import pygame
import tempfile
import os

# Initialize the mixer
pygame.mixer.init()

try:
    # Create speech
    tts = gTTS(text="This is a test of Google Text-to-Speech.", lang='en', slow=False)

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
        tts.save(tmpfile.name)  # Save the audio file
        tmpfile_path = tmpfile.name  # Store the path of the temporary file
        print(f"Temporary file saved at: {tmpfile_path}")
        
    # Play the MP3 file using pygame
    pygame.mixer.music.load(tmpfile_path)
    pygame.mixer.music.play()

    # Wait for the audio to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Optionally delete the file after use
    os.remove(tmpfile_path)
    print(f"Temporary file {tmpfile_path} removed.")
except Exception as e:
    print(f"An error occurred: {e}")
