import time
import requests
import json
import os
import threading
import scheduler

# --- CONFIGURATION ---
# Replace this with your actual Render URL
RENDER_URL = "https://medimitra-final.onrender.com"
# ---------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILE_PATH = os.path.join(BASE_DIR, 'schedule.json')

def sync_from_cloud():
    """Continuously fetches the schedule from Render and updates the local file."""
    print(f"☁️ Cloud Sync Engine started. Pulling from {RENDER_URL}/sync-schedule")
    while True:
        try:
            response = requests.get(f"{RENDER_URL}/sync-schedule", timeout=10)
            if response.status_code == 200:
                cloud_data = response.json()
                
                # Check if we got valid data (not an error)
                if "error" not in cloud_data:
                    with open(SCHEDULE_FILE_PATH, 'w') as file:
                        json.dump(cloud_data, file, indent=4)
                    print(f"[SYNC] Downloaded latest schedule from Render")
        except Exception as e:
            print(f"[WARNING] Cloud sync failed: {e}")
            
        # Wait 10 seconds before polling again
        time.sleep(10)

if __name__ == "__main__":
    print("========================================")
    print("MEDIMITRA RASPBERRY PI HARDWARE NODE")
    print("========================================")
    
    # 1. Start the cloud sync thread
    sync_thread = threading.Thread(target=sync_from_cloud, daemon=True)
    sync_thread.start()
    
    # 2. Start the local file watcher thread
    watcher_thread = threading.Thread(target=scheduler.reload_schedule_data, daemon=True)
    watcher_thread.start()
    
    # 3. Start the actual scheduler in the main thread
    scheduler.main()
