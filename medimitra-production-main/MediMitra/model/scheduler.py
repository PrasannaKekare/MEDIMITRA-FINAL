import os
import subprocess
import schedule
import time
import json

# Base directory for all file paths (directory where this script lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path for saving the schedule
SCHEDULE_FILE_PATH = os.path.join(BASE_DIR, 'schedule.json')
user_data = {}

# Function to load schedule from JSON
def load_data_from_file():
    global user_data
    try:
        with open(SCHEDULE_FILE_PATH, 'r') as file:
            user_data = json.load(file)
            # Ensure that each user has schedules initialized as a list
            for user in user_data:
                if "schedules" not in user_data[user]:
                    user_data[user]["schedules"] = []  # Initialize if missing
        print("Loaded existing schedule data.")
    except FileNotFoundError:
        print("No existing data found. Starting fresh.")
        user_data = {}

# Function to save schedule to JSON
def save_data_to_file():
    with open(SCHEDULE_FILE_PATH, 'w') as file:
        json.dump(user_data, file, indent=4)
    print("Data saved to file.")

# Update the reminder_alert function to use family member's name
from tts_elevenlabs import generate_tts
from speaker_player import play_audio_for_family_member


def reminder_alert(person_name, medicine, dosage):
    reminder_text = f"Reminder for {person_name}. Please take {dosage} of {medicine}."
    print(reminder_text)

    audio_file = generate_tts(reminder_text)

    # Fallback: if ElevenLabs TTS failed, use espeak-ng (offline)
    if audio_file is None:
        print("⚠️ ElevenLabs TTS failed, falling back to espeak-ng")
        fallback_wav = os.path.join(BASE_DIR, "reminder_fallback.wav")
        try:
            subprocess.run(
                ["espeak-ng", "-w", fallback_wav, reminder_text],
                check=True,
                timeout=10
            )
            audio_file = fallback_wav
        except Exception as e:
            print(f"❌ espeak-ng fallback also failed: {e}")
            return

    try:
        play_audio_for_family_member(person_name, audio_file)
    except Exception as e:
        print(f"❌ Failed to play audio for {person_name}: {e}")


# Function to clear existing scheduled reminders
def clear_existing_reminders():
    for job in schedule.get_jobs():
        schedule.cancel_job(job)

# Function to add schedules from user data to the scheduler
def schedule_reminders():
    clear_existing_reminders()  # Clear existing jobs before adding new ones
    for user, user_info in user_data.items():
        for family_member, family_info in user_info.get("family_members", {}).items():
            for schedule_info in family_info.get("schedules", []):
                medicine = schedule_info['medicine']
                dosage = schedule_info['dosage']
                times = schedule_info['times']
                for reminder_time in times:
                    # Schedule the reminder for the family member
                    schedule.every().day.at(reminder_time).do(
                        reminder_alert,
                        family_member,
                        medicine,
                        dosage
)



# Function to run the scheduler in a background thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Function to periodically reload the schedule data
def reload_schedule_data(interval=5):
    last_mtime = 0
    while True:
        try:
            if os.path.exists(SCHEDULE_FILE_PATH):
                current_mtime = os.path.getmtime(SCHEDULE_FILE_PATH)
                if current_mtime > last_mtime:
                    load_data_from_file()  # Reload the data
                    schedule_reminders()  # Reschedule reminders
                    print(f"Scheduler reloaded (file updated).")
                    last_mtime = current_mtime
        except Exception as e:
            print(f"Error checking schedule file: {e}")
        time.sleep(interval)

# Main function to load schedules and start the scheduler
def main():
    load_data_from_file()
    schedule_reminders()  # Schedule all reminders from loaded data

    # Run the scheduler
    run_scheduler()

# Entry point
if __name__ == "__main__":
    # Start the reload data thread
    from threading import Thread
    reload_thread = Thread(target=reload_schedule_data)
    reload_thread.daemon = True
    reload_thread.start()

    main()
