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
    mac = speaker["mac"]

    # 1. Ensure bluetooth connection
    try:
        # We don't check=True because it might already be connected, or might take time
        subprocess.run(
            ["bluetoothctl", "connect", mac],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
    except Exception as e:
        print(f"⚠️ Bluetooth connect command failed or not available: {e}")

    # 2. Wait for the audio sink to become available and find its current name
    # When a speaker reconnects, its sink name can change (e.g. from .1 to .2)
    # So we must dynamically find the active sink for this MAC.
    env = os.environ.copy()
    if "XDG_RUNTIME_DIR" not in env:
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"

    active_sink = None
    if os.name != 'nt':
        print(f"⏳ Waiting for audio sink to activate for {mac}...")
        # Poll for up to 10 seconds for the sink to appear
        for _ in range(10):
            try:
                output = subprocess.check_output(
                    ["pactl", "list", "short", "sinks"],
                    stderr=subprocess.STDOUT,
                    env=env
                ).decode()
                
                # Format MAC for pactl output (e.g. D8_80_19_48_36_20)
                mac_formatted = mac.replace(":", "_")
                
                for line in output.splitlines():
                    if mac_formatted in line:
                        active_sink = line.split()[1]
                        break
                        
                if active_sink:
                    break
            except Exception:
                pass
            
            time.sleep(1)

    name_to_print = speaker.get("name", speaker.get("mac", "Unknown Speaker"))

    # 3. Play the audio
    if os.name == 'nt':
        # Windows fallback routing
        print(f"🔊 [Windows Routing] Playing audio for {family_member} on Windows speaker: {name_to_print}")
        if audio_file.endswith(".wav"):
            import winsound
            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
        else:
            os.startfile(audio_file)
    else:
        if not active_sink:
            print(f"❌ Failed to find active audio sink for {mac} after waiting. Using fallback sink...")
            active_sink = speaker.get("sink") # fallback to the old saved sink
        else:
            print(f"✅ Found active sink {active_sink}. Waiting 4 seconds for speaker chime to finish...")
            # CRITICAL: Bluetooth speakers play an internal chime/beep when connected.
            # We MUST wait for this chime to finish, otherwise the 3-second voice reminder 
            # will play silently while the speaker is busy beeping!
            time.sleep(4)

        print(f"🔊 Routing audio for {family_member} to speaker {name_to_print} (Sink: {active_sink})")

        try:
            # Force volume to 100% in case it reset during reconnection
            subprocess.run(["pactl", "set-sink-volume", active_sink, "100%"], env=env, check=False)

            subprocess.run([
                "paplay",
                "--device", active_sink,
                audio_file
            ], env=env, check=True)
        except Exception as e:
            print(f"❌ Failed to play audio using paplay: {e}")

