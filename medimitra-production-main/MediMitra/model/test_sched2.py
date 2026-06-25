import scheduler, time, threading
print("Starting...")
scheduler.user_data = {"user1": {"family_members": {"Grandpa": {"schedules": [{"medicine": "Aspirin", "dosage": "1 pill", "times": [(time.strftime("%H:%M", time.localtime(time.time() + 2)))]}]}}}}
scheduler.save_data_to_file()
print("Data saved. Waiting for reload...")
threading.Thread(target=scheduler.reload_schedule_data, daemon=True).start()
threading.Thread(target=scheduler.run_scheduler, daemon=True).start()
time.sleep(5)
