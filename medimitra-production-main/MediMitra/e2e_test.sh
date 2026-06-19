#!/bin/bash
# End-to-End Test Script for MediMitra

echo "🚀 Starting E2E Test for MediMitra"

# 1. Define test parameters
USER_EMAIL="e2e_test_$(date +%s)@gmail.com"
MEMBER_NAME="Prasanna" # Mapped to actual speaker in speaker_map.json
MEDICINE="TestMedicine"
DOSAGE="1_tablet"

# Get current time and add 1 minute for the scheduled time
TARGET_TIME=$(date -d "+1 minute" +"%H:%M")

echo "=========================================="
echo "User: $USER_EMAIL"
echo "Member: $MEMBER_NAME"
echo "Medicine: $MEDICINE"
echo "Target Time: $TARGET_TIME"
echo "=========================================="

# 2. Create User
echo "1️⃣ Creating User..."
curl -s -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d "{\"email\": \"$USER_EMAIL\"}"
echo -e "\n"

# 3. Create Family Member
echo "2️⃣ Creating Family Member ($MEMBER_NAME)..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/" \
     -H "Content-Type: application/json" \
     -d "{\"family_name\": \"$MEMBER_NAME\", \"dob\": \"1990-01-01\", \"breakfast\": \"08:00\", \"lunch\": \"13:00\", \"dinner\": \"20:00\"}"
echo -e "\n"

# 4. Add Schedule
echo "3️⃣ Adding Medicine Schedule for $TARGET_TIME..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/$MEMBER_NAME/schedule/?medicine=$MEDICINE&dosage=$DOSAGE" \
     -H "Content-Type: application/json" \
     -d "[\"$TARGET_TIME\"]"
echo -e "\n"

# 5. Verify in schedule.json
echo "4️⃣ Verifying schedule.json..."
grep -A 10 "$USER_EMAIL" /home/vip/Desktop/Medimitra-voice/medimitra-production-main/MediMitra/model/schedule.json | head -n 15

# 6. Wait for execution
echo "=========================================="
echo "⏳ Waiting for scheduler to trigger at $TARGET_TIME..."
echo "Monitor the logs for audio playback (will wait up to 90 seconds)"
echo "=========================================="

timeout 90 tail -f /home/vip/medimitra.log | grep -E "Playing reminder|scheduler|TestMedicine|Prasanna"

echo "✅ Test script completed."
