from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

#connect to Firebase
cred = credentials.Certificate('D:/VSC Programs/ddnow/ddnow-text-interface/privateKeys/twilio-f9b81-firebase-adminsdk-au5oh-ac1a338d18.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

#Twilio
account_sid = os.environ["TWILIO_ACCOUNT_SID"] = "AC7852a19f05d16f465ac14b97154abe7c"
auth_token = os.environ["TWILIO_AUTH_TOKEN"] = "a36ecce24998313e0eb23e27f3b165b7"
client = Client(account_sid, auth_token)

#Store in keys later
xavier = "+15713645671"
michael= "+19086753948"
ela = "+17036185811"


message = client.messages.create(
    body ="Welcome to DD Now",
    from_="+18662413602",
    to = xavier,
)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    resp = MessagingResponse()
    message_body = request.values.get('Body', None)
    reversed_message = message_body[::-1]
    resp.message("You said: " + message_body + " Backwards: " + reversed_message)

    # Test Firebase query
    try:
        doc_ref = db.collection('settings').document('config')
        doc = doc_ref.get()
        if doc.exists:
            db_name = doc.to_dict().get('name', 'No name found')
            resp.message(f"DB Name: {db_name}")
        else:
            resp.message("No config found in DB.")
    except Exception as e:
        resp.message(f"Error accessing Firebase: {str(e)}")

    return str(resp)


'''
#modify this to send a text message to the user, and respond to the user with their text beackwords
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    # Start our TwiML response
    resp = MessagingResponse()

    #respond to the user with their text backwards
    message_body = request.values.get('Body', None)
    reversed_message = message_body[::-1]
    resp.message("You said: " + message_body + " Backwards: " + reversed_message)

    # Add a message
    return str(resp)
'''



if __name__ == "__main__":
    app.run(debug=True)