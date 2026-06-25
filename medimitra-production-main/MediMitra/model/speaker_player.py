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

    # FALLBACK: If no exact match, use the FIRST available speaker
    # This ensures reminders always play even if family member names don't match exactly
    if speakers:
        first_id = next(iter(speakers))
        first_info = speakers[first_id]
        print(f"[WARNING] No speaker mapped for '{family_member}'. "
              f"Falling back to first available speaker: {first_info.get('name', first_id)} "
              f"(mapped to '{first_info.get('family_member', 'unknown')}')")
        return first_id, first_info

    raise ValueError(
        f"No speakers available at all. Please map a speaker first."
    )


def play_audio_for_family_member(family_member, audio_file):
    speaker_id, speaker = find_speaker_by_family_member(family_member)
    mac = speaker["mac"]

    # 1. Ensure bluetooth connection
    try:
        subprocess.run(
            ["bluetoothctl", "connect", mac],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
    except Exception as e:
        print(f"[WARNING] Bluetooth connect command failed or not available: {e}")

    # 2. Wait for the audio sink to become available and find its current name
    env = os.environ.copy()
    if "XDG_RUNTIME_DIR" not in env:
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"

    active_sink = None
    if os.name != 'nt':
        print(f"[INFO] Waiting for audio sink to activate for {mac}...")
        for attempt in range(15):
            try:
                output = subprocess.check_output(
                    ["pactl", "list", "short", "sinks"],
                    stderr=subprocess.STDOUT,
                    env=env
                ).decode()

                mac_formatted = mac.replace(":", "_")

                for line in output.splitlines():
                    if mac_formatted in line:
                        active_sink = line.split()[1]
                        break

                if active_sink:
                    print(f"[INFO] Found sink {active_sink} on attempt {attempt + 1}")
                    break
            except Exception as e:
                print(f"[WARNING] pactl failed on attempt {attempt + 1}: {e}")

            time.sleep(1)

    name_to_print = speaker.get("name", speaker.get("mac", "Unknown Speaker"))

    # 3. Play the audio
    if os.name == 'nt':
        # Windows fallback routing
        print(f"[Windows] Playing audio for {family_member} on: {name_to_print}")
        if audio_file.endswith(".wav"):
            import winsound
            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
        else:
            os.startfile(audio_file)
    else:
        if not active_sink:
            print(f"[WARNING] No active sink found for {mac}. Using saved sink as fallback.")
            active_sink = speaker.get("sink")

        if not active_sink:
            print(f"[ERROR] No sink available at all for {mac}. Cannot play audio.")
            return

        # Wait for speaker's internal "connected" chime to finish
        print(f"[INFO] Waiting 5 seconds for speaker chime to finish...")
        time.sleep(5)

        print(f"[PLAY] Routing audio for {family_member} to {name_to_print} (Sink: {active_sink})")

        # Set PulseAudio sink globally for the child process
        env["PULSE_SINK"] = active_sink

        try:
            # Force volume to 100%
            subprocess.run(
                ["pactl", "set-sink-volume", active_sink, "100%"],
                env=env, check=False, timeout=5
            )
        except Exception:
            pass

        # Determine file type
        is_mp3 = audio_file.lower().endswith(".mp3")
        is_wav = audio_file.lower().endswith(".wav")

        # Build player list based on file type
        players = []
        if is_wav:
            players.append(["paplay", "--device", active_sink, audio_file])
            players.append(["aplay", "-D", "pulse", audio_file])
        if is_mp3:
            players.append(["mpg123", audio_file])  # uses PULSE_SINK env var
            players.append(["ffplay", "-nodisp", "-autoexit", audio_file])
        # Generic fallbacks that handle both
        players.append(["pw-play", "--target", active_sink, audio_file])
        players.append(["mplayer", "-ao", f"pulse::{active_sink}", audio_file])
        players.append(["cvlc", "--play-and-exit", "--aout=pulse", audio_file])

        success = False
        for cmd in players:
            try:
                print(f"[PLAY] Trying: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
                )
                if result.returncode == 0:
                    success = True
                    print(f"[SUCCESS] Audio played with {cmd[0]}!")
                    break
                else:
                    stderr_text = result.stderr.decode(errors='replace')[:200]
                    print(f"[FAILED] {cmd[0]} returned {result.returncode}: {stderr_text}")
            except FileNotFoundError:
                print(f"[SKIP] {cmd[0]} not installed")
            except subprocess.TimeoutExpired:
                print(f"[TIMEOUT] {cmd[0]} timed out after 30s")
            except Exception as e:
                print(f"[ERROR] {cmd[0]} failed: {e}")

        if not success:
            print("[ERROR] ALL audio players failed. Install mpg123: sudo apt install mpg123")
