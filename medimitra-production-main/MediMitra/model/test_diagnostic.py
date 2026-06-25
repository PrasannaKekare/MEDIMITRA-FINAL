"""
Standalone end-to-end test of the reminder pipeline.
Tests: schedule loading -> time matching -> TTS generation -> audio playback
Run this INSTEAD of server.py to diagnose issues.
"""
import os
import sys
import json
import time
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("MEDIMITRA DIAGNOSTIC TEST")
print("=" * 60)

# --- Test 1: Can we read schedule.json? ---
print("\n[TEST 1] Reading schedule.json...")
schedule_path = os.path.join(BASE_DIR, "schedule.json")
if not os.path.exists(schedule_path):
    print(f"  FAIL: {schedule_path} does not exist!")
    sys.exit(1)

with open(schedule_path, "r") as f:
    data = json.load(f)
print(f"  OK: Loaded schedule.json")
print(f"  Contents: {json.dumps(data, indent=2)}")

# Find a family member to test with
test_member = None
test_medicine = None
test_dosage = None
for user, user_info in data.items():
    for fm, fm_info in user_info.get("family_members", {}).items():
        for sched in fm_info.get("schedules", []):
            test_member = fm
            test_medicine = sched["medicine"]
            test_dosage = sched["dosage"]
            break

if not test_member:
    print("  FAIL: No family member found in schedule.json!")
    sys.exit(1)
print(f"  Using: member={test_member}, medicine={test_medicine}, dosage={test_dosage}")

# --- Test 2: Can we read speaker_map.json? ---
print("\n[TEST 2] Reading speaker_map.json...")
speaker_map_path = os.path.join(BASE_DIR, "speaker_map.json")
if not os.path.exists(speaker_map_path):
    print(f"  WARNING: {speaker_map_path} does not exist!")
    print("  The reminder will trigger but speaker routing will fail.")
else:
    with open(speaker_map_path, "r") as f:
        speakers = json.load(f)
    print(f"  OK: {len(speakers)} speaker(s) mapped")
    for sid, info in speakers.items():
        print(f"    Speaker: {info.get('name', 'unknown')} -> Family: {info.get('family_member', 'unmapped')}")

# --- Test 3: Can we generate TTS? ---
print("\n[TEST 3] Generating TTS audio...")
try:
    from tts_elevenlabs import generate_tts
    reminder_text = f"Reminder for {test_member}. Please take {test_dosage} of {test_medicine}."
    print(f"  Text: {reminder_text}")
    audio_file = generate_tts(reminder_text)
    if audio_file and os.path.exists(audio_file):
        size = os.path.getsize(audio_file)
        print(f"  OK: Generated {audio_file} ({size} bytes)")
        if size < 100:
            print(f"  WARNING: File is suspiciously small ({size} bytes). May be corrupted.")
    else:
        print(f"  FAIL: generate_tts returned {audio_file}")
        print("  Neither ElevenLabs nor espeak-ng produced a file.")
        sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- Test 4: Can we play audio? ---
print("\n[TEST 4] Playing audio...")
try:
    from speaker_player import play_audio_for_family_member
    play_audio_for_family_member(test_member, audio_file)
    print("  DONE: play_audio_for_family_member completed without error.")
except ValueError as e:
    print(f"  FAIL (no speaker mapped): {e}")
    print("  This means the family member name in schedule.json doesn't match speaker_map.json")
except Exception as e:
    print(f"  FAIL: {e}")
    traceback.print_exc()

# --- Test 5: Does the schedule library work? ---
print("\n[TEST 5] Testing schedule library...")
import schedule as sched_lib

triggered = []

def test_job():
    triggered.append(True)
    print("  >> Job triggered!")

# Schedule for 1 second from now
target = time.strftime("%H:%M", time.localtime(time.time() + 60))
print(f"  Scheduling test job for {target} (1 min from now)")
sched_lib.every().day.at(target).do(test_job)
print(f"  OK: {len(sched_lib.get_jobs())} job(s) in scheduler")
print(f"  Jobs: {sched_lib.get_jobs()}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print(f"\nSummary:")
print(f"  Schedule data:  OK")
print(f"  TTS generation: OK ({audio_file})")
print(f"  Audio playback: Check output above for errors")
print(f"  Schedule lib:   OK ({len(sched_lib.get_jobs())} jobs)")
print(f"\nIf audio played on your speaker, the system is working.")
print(f"If not, check the [FAILED]/[SKIP]/[ERROR] lines above.")
