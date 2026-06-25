"""
Full end-to-end scheduler trigger test.
Injects a schedule 90 seconds from now, starts the scheduler, and waits.
"""
import json
import time
import os
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import scheduler

# Calculate trigger time = now + 90 seconds
trigger_time = time.strftime("%H:%M", time.localtime(time.time() + 90))
print(f"[SETUP] Current time: {time.strftime('%H:%M:%S')}")
print(f"[SETUP] Trigger time: {trigger_time}")
print(f"[SETUP] You should hear audio in ~90 seconds.\n")

# Write schedule.json with this trigger time
schedule_data = {
    "test_user": {
        "family_members": {
            "Grandpa": {
                "schedules": [{
                    "medicine": "Paracetamol",
                    "dosage": "1 tablet",
                    "times": [trigger_time]
                }]
            }
        }
    }
}

schedule_path = os.path.join(BASE_DIR, "schedule.json")
with open(schedule_path, "w") as f:
    json.dump(schedule_data, f, indent=4)
print(f"[SETUP] Wrote schedule.json with trigger at {trigger_time}")

# Start watcher thread (picks up schedule.json changes)
watcher = threading.Thread(target=scheduler.reload_schedule_data, daemon=True)
watcher.start()
print("[SETUP] Watcher thread started")

# Wait a moment for watcher to pick up
time.sleep(6)

# Now run the scheduler loop
print(f"[RUNNING] Scheduler loop active. Waiting for {trigger_time}...")
print(f"[RUNNING] Press Ctrl+C to stop.\n")

scheduler.run_scheduler()
