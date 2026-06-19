#!/bin/bash
# End-to-End Multi-Speaker Test Script for MediMitra

echo "🚀 Starting E2E MULTI-SPEAKER Test for MediMitra"

# 1. Define test parameters
USER_EMAIL="multi_test_$(date +%s)@gmail.com"
MEMBER_1="Prasanna" # Mapped to D8:80:19:48:36:20
MEMBER_2="Anish Sontakke" # Mapped to 8D:E6:F1:BC:5A:A1
MEDICINE_1="Vitamin_C"
MEDICINE_2="Aspirin"

# Get current time and add 1 and 2 minutes
TIME_1=$(date -d "+1 minute" +"%H:%M")
TIME_2=$(date -d "+2 minutes" +"%H:%M")

echo "=========================================="
echo "User: $USER_EMAIL"
echo "Member 1 ($MEMBER_1) -> $MEDICINE_1 at $TIME_1"
echo "Member 2 ($MEMBER_2) -> $MEDICINE_2 at $TIME_2"
echo "=========================================="

# 2. Create User
echo "1️⃣ Creating User..."
curl -s -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d "{\"email\": \"$USER_EMAIL\"}"
echo -e "\n"

# 3. Create Family Members
echo "2️⃣ Creating Family Member 1 ($MEMBER_1)..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/" \
     -H "Content-Type: application/json" \
     -d "{\"family_name\": \"$MEMBER_1\", \"dob\": \"1990-01-01\", \"breakfast\": \"08:00\", \"lunch\": \"13:00\", \"dinner\": \"20:00\"}"
echo -e "\n"

echo "3️⃣ Creating Family Member 2 ($MEMBER_2)..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/" \
     -H "Content-Type: application/json" \
     -d "{\"family_name\": \"$MEMBER_2\", \"dob\": \"1992-01-01\", \"breakfast\": \"08:30\", \"lunch\": \"13:30\", \"dinner\": \"20:30\"}"
echo -e "\n"

# 4. Add Schedules
echo "4️⃣ Adding Medicine Schedule for Member 1 ($TIME_1)..."
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/$MEMBER_1/schedule/?medicine=$MEDICINE_1&dosage=1_tablet" \
     -H "Content-Type: application/json" \
     -d "[\"$TIME_1\"]"
echo -e "\n"

echo "5️⃣ Adding Medicine Schedule for Member 2 ($TIME_2)..."
# We need to URL encode the space in Member 2's name for the URL path
MEMBER_2_URL="Anish%20Sontakke"
curl -s -X POST "http://localhost:8000/users/$USER_EMAIL/family/$MEMBER_2_URL/schedule/?medicine=$MEDICINE_2&dosage=2_tablets" \
     -H "Content-Type: application/json" \
     -d "[\"$TIME_2\"]"
echo -e "\n"

# 6. Wait for execution
echo "=========================================="
echo "⏳ Waiting for scheduler to trigger at $TIME_1 and $TIME_2..."
echo "Monitor the logs for BOTH audio playbacks (will wait up to 130 seconds)"
echo "=========================================="

timeout 130 tail -f /home/vip/medimitra.log | grep -E "Routing audio|Reminder for|failed"

echo "✅ Test script completed."
