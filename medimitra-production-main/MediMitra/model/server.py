import os
import time
import json
import PIL.Image
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import google.generativeai as genai

# Base directory for all file paths (directory where this script lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load GEMINI_API_KEY from interface/.env
def _load_gemini_key():
    env_path = os.path.join(BASE_DIR, '..', 'interface', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('GEMINI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY', '')

# Configure Gemini API
GEMINI_API_KEY = _load_gemini_key()
genai.configure(api_key=GEMINI_API_KEY)
gemini_generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}
gemini_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=gemini_generation_config,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins so it works from other devices on the network
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection setup using pymongo
client = MongoClient("mongodb+srv://prasanna:nGiZt8iWMh7nRiCR@proj.fqffb3j.mongodb.net/")  # Replace with your MongoDB URI
db = client['test']  # Replace with your database name
family_members_collection = db['members']  # Replace with your collection name
medicine_collection = db['medicines']  # Replace with your collection name

# Path for saving the schedule
SCHEDULE_FILE_PATH = os.path.join(BASE_DIR, 'schedule.json')

# Load schedule from JSON
def load_data_from_file():
    try:
        with open(SCHEDULE_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("No existing data found. Starting fresh.")
        return {}

# Save schedule to JSON
def save_data_to_file(data):
    with open(SCHEDULE_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)
    print("Data saved to file.")

# Function to add a new user
def add_new_user(user_name):
    data = load_data_from_file()
    if user_name not in data:
        data[user_name] = {"family_members": {}}
        save_data_to_file(data)
        print(f"Added new user: {user_name}")

# Function to add a family member under a user
def add_new_family_member(user_name, family_name, dob, meal_times):
    data = load_data_from_file()
    if user_name in data:
        data[user_name]["family_members"][family_name] = {
            "dob": dob,
            "meal_times": meal_times,
            "schedules": []
        }
        save_data_to_file(data)
        print(f"Added family member {family_name} for user {user_name}.")

# Function to remove a family member
def remove_family_member(user_name, family_name):
    data = load_data_from_file()
    if user_name in data and family_name in data[user_name]["family_members"]:
        del data[user_name]["family_members"][family_name]
        save_data_to_file(data)
        print(f"Removed family member {family_name} for user {user_name}.")

# Function to remove a user
def remove_user(user_name):
    data = load_data_from_file()
    if user_name in data:
        del data[user_name]
        save_data_to_file(data)
        print(f"Removed user {user_name}.")

# Function to add or update a family member's schedule
def add_or_update_schedule(user_name, family_name, medicine, dosage, times):
    data = load_data_from_file()
    if user_name in data and family_name in data[user_name]["family_members"]:
        schedules = data[user_name]["family_members"][family_name]["schedules"]
        existing_schedule = next((s for s in schedules if s['medicine'] == medicine), None)

        if existing_schedule:
            existing_schedule['dosage'] = dosage
            existing_schedule['times'] = times
            print(f"Updated schedule for {family_name}: {medicine}, {dosage} at {', '.join(times)}")
        else:
            schedules.append({
                "medicine": medicine,
                "dosage": dosage,
                "times": times
            })
            print(f"Added new schedule for {family_name}: {medicine}, {dosage} at {', '.join(times)}")

        save_data_to_file(data)

# Function to add or update a family member's schedule in MongoDB
def add_or_update_schedule_mongodb(family_member_id, medicine, dosage, times):
    # Validate the medicine name
    if not medicine:
        raise ValueError("Medicine name cannot be empty.")

    # Create the document
    medicine_doc = {
        "family_member_id": family_member_id,
        "name": medicine,  # Ensure the 'name' field is included
        "dosage": dosage,
        "times": times
    }

    # Upsert document into MongoDB
    result = medicine_collection.update_one(
        {
            "family_member_id": family_member_id,
            "name": medicine  # Ensure we check against both family_member_id and name
        },
        {"$set": medicine_doc},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"Inserted new medicine schedule for family member {family_member_id}: {medicine}")
    else:
        print(f"Updated existing medicine schedule for family member {family_member_id}: {medicine}")


# OCR + Gemini pipeline

def parse_image_with_gemini(image_path, default_prompt):
    img = PIL.Image.open(image_path)
    response = gemini_model.generate_content([default_prompt, img])
    return response.text

# Create the prompt for Gemini based on meal times
def create_default_prompt(user_name, family_name, family_member_id=None):
    data = load_data_from_file()
    meal_times = None
    
    # Try to get from local file first
    if user_name in data and family_name in data[user_name].get("family_members", {}):
        meal_times = data[user_name]["family_members"][family_name].get("meal_times")
    
    # Fallback to MongoDB if not in file or missing meal_times
    if not meal_times and family_member_id:
        try:
            member = family_members_collection.find_one({"_id": ObjectId(family_member_id)})
            if member:
                # Handle both capitalized and lowercase keys
                meal_times = {
                    "breakfast": member.get("Breakfast") or member.get("breakfast", "08:00"),
                    "lunch": member.get("Lunch") or member.get("lunch", "13:00"),
                    "dinner": member.get("Dinner") or member.get("dinner", "20:00")
                }
        except Exception as e:
            print(f"Error fetching meal times from MongoDB: {e}")

    # Final fallback to defaults
    if not meal_times:
        meal_times = {"breakfast": "08:00", "lunch": "13:00", "dinner": "20:00"}
        print(f"Warning: Using default meal times for {family_name}")

    meal_times_str = f'Breakfast: {meal_times["breakfast"]}, Lunch: {meal_times["lunch"]}, Dinner: {meal_times["dinner"]}'
    
    prompt = f"""
You are a medical assistant AI. You will be provided with an image of a prescription or the text of a prescription. 
Your job is to extract the following details from it and return them in JSON format strictly following this schema:
{{
    "medicines": [
        {{
            "name": "string",
            "dosage": "string",
            "times": ["string"]  # format: HH:MM
        }}
    ],
    "duration": "string",
    "advice": "string",
    "follow_up": "string"
}}

Ensure times are in 24-hour format (HH:MM). Provide the response only as JSON. 
IMPORTANT: Use the specific times provided in the 'Meal Times' section below to fill the 'times' field. 
- For 'Morning' or 'Breakfast', use the time listed for Breakfast.
- For 'Afternoon' or 'Lunch', use the time listed for Lunch.
- For 'Night' or 'Dinner', use the time listed for Dinner.

Feel free to correct OCR misreadings as you see fit.

Meal Times: {meal_times_str}
"""
    return prompt

def create_default_prompt_audio(user_name, family_name, family_member_id=None):
    # Reuse the same logic for audio
    return create_default_prompt(user_name, family_name, family_member_id)

# Parse the extracted text using Gemini
def parse_with_gemini(extracted_text, default_prompt):
    """Uses Gemini API to parse prescription text."""
    response = gemini_model.generate_content([default_prompt, extracted_text])
    return response.text

# Process parsed info to update both MongoDB and schedule.json
def process_parsed_info(parsed_info, user_name, family_member_id):
    try:
        parsed_json = json.loads(parsed_info)

        if "medicines" not in parsed_json or not parsed_json["medicines"]:
            raise ValueError("No medicines found in the parsed prescription data.")

        for medicine in parsed_json.get("medicines", []):
            med_name = medicine.get("name")
            dosage = medicine.get("dosage")
            times = medicine.get("times", [])

            family_member_name = find_family_member(family_member_id)

            if med_name and dosage and all(validate_time_format(time) for time in times):
                # Update JSON
                add_or_update_schedule(user_name, family_member_name, med_name, dosage, times)
                
                # Update MongoDB
                add_or_update_schedule_mongodb(family_member_id, med_name, dosage, times)
            else:
                print(f"Invalid data for medicine: {med_name}, skipping this entry.")
    except json.JSONDecodeError:
        raise ValueError("Error parsing the response from Gemini. Ensure the data is in the correct format.")

# Validate time format (HH:MM)
def validate_time_format(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

# Find a family member given the family member object id as a parameter
def find_family_member(family_member_id):
    try:
        # Check if ID is a valid ObjectId
        if not ObjectId.is_valid(family_member_id):
            print(f"Invalid family_member_id: {family_member_id}")
            return "Unknown"
            
        family_member = family_members_collection.find_one({"_id": ObjectId(family_member_id)})
        if not family_member:
            print(f"Family member not found in DB: {family_member_id}")
            return "Unknown"
            
        return family_member.get('name', 'Unknown')
    except Exception as e:
        print(f"Error finding family member: {e}")
        return "Unknown"
# FastAPI routes

# 1. Add a new user

class User(BaseModel):
    email: str

@app.post("/users/")
async def create_user(user: User):
    add_new_user(user.email)  # Change user.user_name to user.email
    return {"message": f"User {user.email} added successfully."}

# 2. Add a new family member under a user
# Define a model for the request body
class FamilyMember(BaseModel):
    family_name: str
    dob: str
    breakfast: str
    lunch: str
    dinner: str

@app.post("/users/{user_name}/family/")
async def create_family_member(user_name: str, member: FamilyMember):
    meal_times = {
        "breakfast": member.breakfast,
        "lunch": member.lunch,
        "dinner": member.dinner
    }
    add_new_family_member(user_name, member.family_name, member.dob, meal_times)
    return {"message": f"Family member {member.family_name} added under user {user_name}."}

# 3. Add or update a schedule for a family member under a user
@app.post("/users/{user_name}/family/{family_name}/schedule/")
async def add_or_update_family_schedule(user_name: str, family_name: str, medicine: str, dosage: str, times: list[str]):
    add_or_update_schedule(user_name, family_name, medicine, dosage, times)
    return {"message": f"Schedule for {medicine} updated for family member {family_name} under user {user_name}."}

# 4. Remove a family member under a user
@app.delete("/users/{user_name}/family/{family_name}/")
async def delete_family_member(user_name: str, family_name: str):
    remove_family_member(user_name, family_name)
    return {"message": f"Family member {family_name} removed from user {user_name}."}

# 5. Remove a user
@app.delete("/users/{user_name}/")
async def delete_user(user_name: str):
    remove_user(user_name)
    return {"message": f"User {user_name} removed successfully."}

@app.post("/ocr/")
async def upload_image(
    user_name: str = Form(...),                
    family_member_id: str = Form(...), 
    file: UploadFile = File(...),
):
    try:
        # Save the uploaded file locally
        contents = await file.read()
        file_location = os.path.join(BASE_DIR, "uploaded_image.png")
        with open(file_location, "wb") as temp_file:
            temp_file.write(contents)

        family_member_name = find_family_member(family_member_id)

        # Step 2: Create the prompt for Gemini
        default_prompt = create_default_prompt(user_name, family_member_name, family_member_id)

        # Step 3: Parse the image using Gemini
        parsed_info = parse_image_with_gemini(file_location, default_prompt)
        print(f"\nParsed Prescription Information:\n{parsed_info}")

        # Step 4: Process the parsed info and update the family member's schedule
        process_parsed_info(parsed_info, user_name, family_member_id)

        return {"status": "success", "message": "Prescription processed and data saved successfully."}
    except Exception as e:
        print(f"Error in /ocr/: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/audio-prescription/")
async def record_audio(
    user_name: str = Form(...),                
    family_member_id: str = Form(...), 
    transcript: str = Form(...),
):
    try:
        family_member_name = find_family_member(family_member_id)

        # Step 3: Create the prompt for Gemini
        default_prompt = create_default_prompt_audio(user_name, family_member_name, family_member_id)

        # Step 4: Parse the extracted text using Gemini
        parsed_info = parse_with_gemini(transcript, default_prompt)
        print(f"\nParsed Prescription Information:\n{parsed_info}")

        # Step 5: Process the parsed info and update the family member's schedule
        process_parsed_info(parsed_info, user_name, family_member_id)

        return {"status": "success", "message": "Prescription processed and data saved successfully."}
    except Exception as e:
        print(f"Error in /audio-prescription/: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

import subprocess
import re

@app.get("/speakers/scan")
def scan_speakers():
    try:
        # Try to run pactl (Linux/Raspberry Pi)
        output = subprocess.check_output(
            ["pactl", "list", "short", "sinks"],
            stderr=subprocess.STDOUT
        ).decode()

        print("PACTL OUTPUT:\n", output)

        speakers = []
        for line in output.splitlines():
            if "bluez_output" in line:
                parts = line.split()
                sink = parts[1]
                mac = sink.replace("bluez_output.", "").split(".")[0].replace("_", ":")
                speakers.append({
                    "speaker_id": f"speaker_{mac[-5:].replace(':','')}",
                    "mac": mac,
                    "sink": sink
                })

        return {
            "raw": output,
            "speakers": speakers
        }

    except FileNotFoundError:
        # If pactl is not found (e.g. running on Windows), return a mock speaker for testing
        print("pactl command not found (likely running on Windows). Returning a mock speaker for testing.")
        return {
            "raw": "Mock Windows Environment",
            "speakers": [
                {
                    "speaker_id": "speaker_mock1",
                    "mac": "00:11:22:33:44:55",
                    "sink": "windows_mock_speaker"
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/users/{email}/family")
def get_family(email: str):
    data = load_data_from_file()
    return data.get(email, {}).get("family_members", {})

class SpeakerMap(BaseModel):
    family_member: str
    speaker_id: str
    mac: str
    sink: str

@app.post("/speakers/map")
def map_speaker(mapping: SpeakerMap):
    path = os.path.join(BASE_DIR, "speaker_map.json")

    try:
        with open(path, "r") as f:
            speaker_map = json.load(f)
    except:
        speaker_map = {}

    speaker_map[mapping.speaker_id] = {
        "mac": mapping.mac,
        "sink": mapping.sink,
        "family_member": mapping.family_member
    }

    with open(path, "w") as f:
        json.dump(speaker_map, f, indent=2)

    return {"status": "mapped"}

from fastapi import HTTPException
import subprocess
from speaker_player import play_audio_for_family_member

@app.post("/speakers/test")
def test_speaker(
    family_member: str | None = None,
    speaker_id: str | None = None
):
    # Explicitly reject old API usage
    if speaker_id and not family_member:
        raise HTTPException(
            status_code=400,
            detail="speaker_id is deprecated. Use family_member instead."
        )

    if not family_member:
        raise HTTPException(
            status_code=422,
            detail="family_member is required"
        )

    # Generate test audio
    try:
        subprocess.run(
            [
                "espeak-ng",
                "-w", os.path.join(BASE_DIR, "test.wav"),
                f"This is a test for {family_member}"
            ],
            check=True
        )

        try:
            play_audio_for_family_member(family_member, os.path.join(BASE_DIR, "test.wav"))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    except FileNotFoundError:
        print("espeak-ng not found. Assuming Windows mock testing environment.")
        # We are on Windows, just return a mock success
        pass

    return {
        "status": "played (mocked if on Windows)",
        "family_member": family_member
    }



# Load existing data at startup
load_data_from_file()

# Run the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
