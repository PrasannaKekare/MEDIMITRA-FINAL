#!/bin/bash
# End-to-End OCR Test Script for MediMitra

echo "🚀 Starting E2E OCR Test for MediMitra"

# 1. Define test parameters
USER_EMAIL="ocr_test_$(date +%s)@gmail.com"
MEMBER_NAME="Prasanna" # Mapped to D8:80:19:48:36:20 speaker
PRESCRIPTION_IMG="/home/vip/Desktop/Medimitra-voice/medimitra-production-main/MediMitra/model/sample_prescription.png"

# We will set Breakfast to current_time + 2 minutes
# Assuming sample_prescription.png says "morning" or something similar.
TARGET_TIME=$(date -d "+2 minutes" +"%H:%M")

echo "=========================================="
echo "User: $USER_EMAIL"
echo "Member: $MEMBER_NAME"
echo "Breakfast Target Time: $TARGET_TIME"
echo "=========================================="

echo "1️⃣ Injecting test user and family member directly into MongoDB..."
# Python script to insert directly into MongoDB to bypass NextAuth for the test
MEMBER_ID=$(/home/vip/Desktop/Medimitra-voice/medimitra-production-main/MediMitra/model/venv/bin/python -c "
import sys
from pymongo import MongoClient

client = MongoClient('mongodb+srv://prasanna:nGiZt8iWMh7nRiCR@proj.fqffb3j.mongodb.net/')
db = client['test']

user_doc = {'name': 'OCR Test', 'email': '$USER_EMAIL', 'password': 'hashed_password_for_test', 'members': []}
user_res = db.users.insert_one(user_doc)
user_id = user_res.inserted_id

member_doc = {'name': '$MEMBER_NAME', 'dob': '1990-01-01', 'Breakfast': '$TARGET_TIME', 'Lunch': '13:00', 'Dinner': '20:00', 'user': user_id}
member_res = db.members.insert_one(member_doc)
member_id = member_res.inserted_id

print(str(member_id))
")

if [ -z "$MEMBER_ID" ]; then
    echo "❌ Failed to inject into MongoDB."
    exit 1
fi
echo "✅ MongoDB Injection Success. Member ID: $MEMBER_ID"
echo -e "\n"

# 3. Create User in FastAPI (schedule.json)
echo "2️⃣ Creating User in FastAPI..."
curl -s -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d "{\"email\": \"$USER_EMAIL\"}"
echo -e "\n"

# 4. Create Family Member in FastAPI (schedule.json)
echo "3️⃣ Creating Family Member in FastAPI..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/" \
     -H "Content-Type: application/json" \
     -d "{\"family_name\": \"$MEMBER_NAME\", \"dob\": \"1990-01-01\", \"breakfast\": \"$TARGET_TIME\", \"lunch\": \"13:00\", \"dinner\": \"20:00\"}"
echo -e "\n"

# 5. Execute OCR endpoint
echo "4️⃣ Uploading Prescription to OCR endpoint..."
curl -s -X POST "http://localhost:8000/ocr/" \
     -F "user_name=$USER_EMAIL" \
     -F "family_member_id=$MEMBER_ID" \
     -F "file=@$PRESCRIPTION_IMG"
echo -e "\n"

# 6. Wait for execution
echo "=========================================="
echo "⏳ Waiting for OCR to process and scheduler to trigger at $TARGET_TIME..."
echo "Monitor the logs for audio playback (will wait up to 150 seconds)"
echo "=========================================="

timeout 150 tail -f /home/vip/medimitra.log | grep -E "Routing audio|Reminder for|failed|Extracted Text|Parsed Prescription"

echo "✅ Test script completed."
