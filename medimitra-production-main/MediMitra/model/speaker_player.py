import subprocess
import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPEAKER_MAP_PATH = os.path.join(BASE_DIR, "speaker_map.json")


def load_speakers():
    if not os.path.exists(SPEAKER_MAP_PATH):
        return {}

    with open(SPEAKER_MAP_PATH, "r") as f:
        return json.load(f)


def normalize(text):
    return text.strip().lower()


def find_speaker_by_family_member(family_member):
    speakers = load_speakers()
    target = normalize(family_member)

    for speaker_id, info in speakers.items():
        if normalize(info.get("family_member", "")) == target:
            return speaker_id, info

    raise ValueError(
        f"No speaker mapped for family member '{family_member}'. "
        f"Available: {[v.get('family_member') for v in speakers.values()]}"
    )


def play_audio_for_family_member(family_member, audio_file):
    speaker_id, speaker = find_speaker_by_family_member(family_member)

    # ensure bluetooth connection
    try:
        subprocess.run(
            ["bluetoothctl", "connect", speaker["mac"]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except Exception:
        pass # Probably on Windows or no bluetoothctl

    time.sleep(1)  # allow PipeWire to activate sink
    
    name_to_print = speaker.get("name", speaker.get("mac", "Unknown Speaker"))
    print(f"🔊 Routing audio for {family_member} to speaker {name_to_print} (Sink: {speaker['sink']})")

    if os.name == 'nt':
        # Windows fallback routing
        print(f"🔊 [Windows Routing] Playing audio for {family_member} on Windows speaker: {name_to_print}")
        if audio_file.endswith(".wav"):
            import winsound
            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
        else:
            os.startfile(audio_file)
    else:
        # play audio on correct sink on Linux
        try:
            subprocess.run([
                "paplay",
                "--device", speaker["sink"],
                audio_file
            ], check=True)
        except Exception as e:
            print(f"❌ Failed to play audio using paplay: {e}")

