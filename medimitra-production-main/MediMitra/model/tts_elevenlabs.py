import os
import subprocess
import requests

# Base directory for all file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ELEVEN_API_KEY = "66f20a19b395bf97be41e80cf1a87bfb1943c898b818d21ed21ed36a45cb2455"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
MODEL_ID = "eleven_multilingual_v2"

def generate_tts(text, output_file=None):
    if output_file is None:
        output_file = os.path.join(BASE_DIR, "reminder.wav")

    # Try ElevenLabs first
    if ELEVEN_API_KEY:
        try:
            # Request WAV format directly from ElevenLabs
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=wav_44100"

            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": MODEL_ID,
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.7
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

    # Fallback: use espeak-ng (offline, always available on Pi)
    print("Falling back to espeak-ng for TTS")
    fallback_file = os.path.join(BASE_DIR, "reminder_fallback.wav")
    try:
        subprocess.run(
            ["espeak-ng", "-w", fallback_file, text],
            check=True,
            timeout=10
        )
        return fallback_file
    except Exception as e:
        print(f"espeak-ng fallback also failed: {e}")
        return None
