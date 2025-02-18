"""
DirectDriveNow - SMS Conversation with Location Verification

Flow Summary:
1) Unrecognized user -> ask "YES" or "STOP"
2) If YES -> ask 4-digit code (any digits accepted)
3) Then "Welcome to Delta Chi's dd queue!" -> 
   "Press 1 if going to a party, 2 if riding home."
4) If user says 1 -> ask for location (stage 4). We geocode the location,
   check if within 3 miles of the target. If invalid/out of range, re-ask. 
   If good, ask how many people (stage 5).
5) If user says 2 -> skip location, ask # people (stage 6).
6) # people must be <= 8. If user enters > 8, re-ask. 
7) Once # is valid, "You are in the queue. Wait time is 8 minutes."

Installation:
   pip install flask twilio python-dotenv geopy usaddress

Run:
   python conversation.py
Then in another terminal:
   ngrok http 5000

In Twilio Console, set inbound SMS webhook to:
   https://<ngrok-subdomain>.ngrok-free.app/sms
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv

# For location parsing
import usaddress
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

load_dotenv()

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory dictionary: phone -> { stage: int, data: {...}, location_attempts: int }
user_states = {}

# Set your target coordinates, e.g., Toms Creek Rd in Blacksburg
TARGET_COORDS = (37.244621, -80.431381)  # Example location
MAX_DISTANCE_MILES = 3.0  # Must be within 3 miles

# Geocoder setup
geolocator = Nominatim(user_agent="direct_drive_now_app")

def parse_and_geocode(input_address):
    """
    Attempt to parse input_address using usaddress,
    then geocode with geopy's Nominatim.
    Returns (location, address_string) or (None, error_message).
    """
    try:
        parse_result, _ = usaddress.tag(input_address)
        # Extract something like 'number street' if possible
        street_address = ' '.join([
            part for (part, label) in parse_result.items()
            if 'Street' in label or 'AddressNumber' in label
        ])
        address_query = street_address if street_address else input_address
    except usaddress.RepeatedLabelError:
        # if parsing fails, fallback to raw input
        address_query = input_address

    # Attempt geocode
    location = geolocator.geocode(address_query)
    if not location:
        # fallback if we did something local-scope
        location = geolocator.geocode(input_address)
        if not location:
            return (None, "No valid address found. Please try again.")

    return (location, location.address)

@app.route("/sms", methods=['POST'])
def sms_handler():
    from_number = request.form.get('From', '')
    body = request.form.get('Body', '').strip()
    
    resp = MessagingResponse()

    # If new user, set them to stage 0 with no attempts yet
    if from_number not in user_states:
        user_states[from_number] = {
            'stage': 0,
            'data': {},
            'location_attempts': 0
        }

    stage = user_states[from_number]['stage']

    # ------------- Stage Logic -------------
    if stage == 0:
        # New user -> ask YES or STOP
        resp.message("Text YES to receive texts, or STOP to opt out.")
        user_states[from_number]['stage'] = 1

    elif stage == 1:
        # Expect YES or STOP
        if body.upper() == "YES":
            resp.message("Please enter your 4-digit access code.")
            user_states[from_number]['stage'] = 2
        elif body.upper() == "STOP":
            resp.message("You have opted out of Direct Drive Now texts.")
            user_states.pop(from_number, None)
        else:
            resp.message("Invalid response. Please text YES or STOP.")

    elif stage == 2:
        # Expect 4-digit code
        if len(body) == 4 and body.isdigit():
            resp.message("Welcome to Delta Chi's dd queue!\nPress 1 if going to a party.\nPress 2 if riding home.")
            user_states[from_number]['stage'] = 3
        else:
            resp.message("Invalid code. Please enter a 4-digit number.")

    elif stage == 3:
        # 1=party, 2=home
        if body == "1":
            resp.message("Got it. What's your current location?")
            user_states[from_number]['stage'] = 4
        elif body == "2":
            resp.message("How many people are riding with you? (limit 8)")
            user_states[from_number]['stage'] = 6
        else:
            resp.message("Please type 1 or 2.")

    elif stage == 4:
        # Expect location string -> parse & geocode
        location, result = parse_and_geocode(body)
        if not location:
            # No valid address
            user_states[from_number]['location_attempts'] += 1
            attempts = user_states[from_number]['location_attempts']
            if attempts >= 3:
                resp.message("Failed to get valid location after 3 attempts. Please restart. (text STOP or rejoin)")
                user_states.pop(from_number, None)
            else:
                resp.message(f"{result}\nPlease try again.")
        else:
            # We got a location object. Check distance
            latlng = (location.latitude, location.longitude)
            dist_miles = geodesic(TARGET_COORDS, latlng).miles
            dist_miles = round(dist_miles, 2)
            if dist_miles > MAX_DISTANCE_MILES:
                user_states[from_number]['location_attempts'] += 1
                attempts = user_states[from_number]['location_attempts']
                if attempts >= 3:
                    resp.message(f"Location is {dist_miles} miles away. Must be within {MAX_DISTANCE_MILES} miles.\nToo many attempts. Please restart.")
                    user_states.pop(from_number, None)
                else:
                    resp.message(f"Address is {dist_miles} miles away, must be within {MAX_DISTANCE_MILES}. Try a closer location.")
            else:
                # Good location
                user_states[from_number]['data']['location'] = result
                resp.message("Great! How many people are with you? (limit 8)")
                user_states[from_number]['stage'] = 5

    elif stage == 5:
        # Expect # people <= 8
        if body.isdigit():
            num_people = int(body)
            if num_people > 8:
                resp.message("Limit is 8. Please enter a number up to 8.")
            else:
                user_states[from_number]['data']['people'] = num_people
                resp.message("You are in the queue. Estimated wait time is 8 minutes.")
                user_states.pop(from_number, None)  # end conversation
        else:
            resp.message("Please enter a numeric value up to 8.")

    elif stage == 6:
        # user pressed 2 (ride home) -> # people
        if body.isdigit():
            num_people = int(body)
            if num_people > 8:
                resp.message("Limit is 8. Please enter a number up to 8.")
            else:
                user_states[from_number]['data']['people'] = num_people
                resp.message("You are in the queue. Estimated wait time is 8 minutes.")
                user_states.pop(from_number, None)
        else:
            resp.message("Please enter a numeric value up to 8.")

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
