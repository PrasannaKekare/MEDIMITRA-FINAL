import json, time, os
schedule_file = "d:/MEDIMITRA-FINAL/medimitra-production-main/MediMitra/model/schedule.json"
trigger_time = time.strftime("%H:%M", time.localtime(time.time() + 60))
print(f"Injecting trigger time: {trigger_time}")
data = {"test_user": {"family_members": {"Grandpa": {"schedules": [{"medicine": "TestPill", "dosage": "1", "times": [trigger_time]}]}}}}
with open(schedule_file, "w") as f:
    json.dump(data, f, indent=4)
print("Saved!")
