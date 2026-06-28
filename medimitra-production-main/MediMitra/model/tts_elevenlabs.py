import os
import subprocess
import requests

# Base directory for all file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ELEVEN_API_KEY = "sk_f695aac7f5ad558ed6e48ad82b697fdbc3f1bafadcfd4c72"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
MODEL_ID = "eleven_multilingual_v2"

CARTESIA_API_KEY = "sk_car_MPR5Cd4qSpVxsGBKL3Nwwo"
CARTESIA_VOICE_ID = "f786b574-daa5-4673-aa0c-cbe3e8534c02" # Katie - en-US Female

def generate_tts(text, output_file=None):
    if output_file is None:
        output_file = os.path.join(BASE_DIR, "reminder.mp3")

    # Try ElevenLabs first
    if ELEVEN_API_KEY:
        try:
            # Default output is MP3, which is supported on the Free tier.
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128"

            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }

            payload = {
                "text": text,
                "model_id": MODEL_ID,
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.8
                }
            }

            r = requests.post(url, json=payload, headers=headers, timeout=20)

            if r.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(r.content)
                return output_file
            else:
                print(f"ElevenLabs error: {r.status_code} {r.text}")
        except Exception as e:
            print(f"ElevenLabs request failed: {e}")
    else:
        print("ELEVEN_API_KEY not set")

    # Fallback to Cartesia
    print("Falling back to Cartesia TTS...")
    if CARTESIA_API_KEY:
        try:
            url = "https://api.cartesia.ai/tts/bytes"
            headers = {
                "Cartesia-Version": "2026-03-01",
                "X-API-Key": CARTESIA_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "model_id": "sonic-3.5",
                "transcript": text,
                "voice": {
                    "mode": "id",
                    "id": CARTESIA_VOICE_ID
                },
                "output_format": {
                    "container": "mp3",
                    "sample_rate": 44100,
                    "bit_rate": 128000
                }
            }
            r = requests.post(url, json=payload, headers=headers, timeout=20)
            if r.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(r.content)
                return output_file
            else:
                print(f"Cartesia error: {r.status_code} {r.text}")
        except Exception as e:
            print(f"Cartesia request failed: {e}")
    else:
        print("CARTESIA_API_KEY not set")

    return None
