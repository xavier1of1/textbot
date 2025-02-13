import os
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Retrieve Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/sms', methods=['POST'])
def sms_webhook():
    incoming_msg = request.form.get('Body', '')
    resp = MessagingResponse()
    resp.message(f'You said: {incoming_msg}')
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
