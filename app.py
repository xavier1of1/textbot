"""
Twilio SMS Relay Flask Application (Simplified)

Description:
    This Flask application listens for inbound SMS messages from Twilio.
    1) If it's the first time we've heard from this phone number, we respond with:
       "Welcome to direct drive now."
    2) If they've messaged us before, we echo their text back with a ":)" appended.

Environment variables (via .env or system):
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_PHONE_NUMBER

Contents:
1. Imports and Setup
2. Environment Variables
3. Global State
4. Main Handler (sms_reply function)
5. Application Entry Point
"""

# 1. Imports and Setup
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env variables, if present

app = Flask(__name__)

# 2. Environment Variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# 3. Global State
# A simple dictionary to keep track of which numbers have already received a "welcome" message.
user_states = {}

# 4. Main Handler (sms_reply)
@app.route("/sms", methods=['POST'])
def sms_reply():
    """
    Handles inbound SMS from Twilio.

    - If it's the first time we see this from_number, respond with "Welcome to direct drive now."
    - If they've already been welcomed, echo their message back with a " :)"
    """
    from_number = request.form.get('From', '')
    body = request.form.get('Body', '')
    
    # Initialize TwiML response
    resp = MessagingResponse()
    
    # Check if user is new
    if from_number not in user_states:
        # New user, so welcome them
        resp.message("Welcome to direct drive now.")
        user_states[from_number] = "welcomed"
    else:
        # They already got the welcome, so echo back their text + " :)"
        response_text = f"You said: {body} :)"
        resp.message(response_text)

    return str(resp)

# 5. Application Entry Point
if __name__ == "__main__":
    # debug=True is fine for local dev; set to False in production
    app.run(debug=True, port=5000)
