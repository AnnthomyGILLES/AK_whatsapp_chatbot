import datetime
import os

import openai
import stripe
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_ngrok import run_with_ngrok
from twilio.rest import Client

from mongodb_db import get_user_id_with_phone_number, update_history, get_user
from parse_phone_numbers import extract_phone_number

load_dotenv()

app = Flask(__name__)
run_with_ngrok(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "top-secret!")
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=10)

# OpenAI Chat GPT
openai.api_key = os.getenv("OPENAI_API_KEY")
completion = openai.Completion()

# Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_numer = os.getenv("TWILIO_PHONE_NUMER")

client = Client(account_sid, auth_token)

# Stripe
stripe_keys = {
    "secret_key": os.getenv("STRIPE_SECRET_KEY"),
    "publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY"),
    "endpoint_secret": os.getenv("STRIPE_ENDPOINT"),
}

stripe.api_key = stripe_keys["secret_key"]


def ask(message_log):
    """Send a message to the OpenAI chatbot model and return its response.

    Args:
        message_log: The conversation history up to this point, as a list of dictionaries.

    Returns:
        str: The response of the chatbot model.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_log,
        max_tokens=1024,
        stop=None,
        temperature=0.7,
    )

    reply_content = response.choices[0].message.content

    return reply_content


def append_interaction_to_chat_log(user_id, question):
    """Append a new interaction to the chat log.

    Args:
        user_id (str): The id of the user.
        question (str): The question asked by the user.
    """
    update_history(user_id, question)


def send_message(body_mess, phone_number):
    """Send a message via the Twilio API.

    Args:
        body_mess (str): The message to be sent.
        phone_number (str): The phone number of the recipient.
    """
    message = client.messages.create(
        from_=f"whatsapp:{twilio_phone_numer}",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
    )
    print(message.sid)


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values["Body"].lower()
    phone_number = extract_phone_number(request.values["From"].lower())

    user_id = get_user_id_with_phone_number(phone_number)
    user = get_user(user_id)

    if user_id is None:
        send_message(f"Inscrivez-vous pour utiliser WhatIA.", phone_number)
        return ""

    if incoming_msg:
        if not user["history"]:
            message = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg},
            ]
            answer = ask(message)
            message.append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, message)
        else:
            message = user["history"]
            message.append({"role": "user", "content": incoming_msg})
            answer = ask(message)
            user["history"].append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, user["history"])

        send_message(answer, phone_number)

    return ""


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": "Invalid payload"}), 400

    # Handle the event
    if event.type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]  # contains a stripe.PaymentIntent
        # Add user
        # user = {
        #     "phone_number": {customer_phone_number},
        #     "is_active": True,
        #     "history": None,
        # }
        # _ = add_user(**user)
        print("PaymentIntent was successful!")
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        print("PaymentIntent was failed!")
    else:
        print("Unhandled event type {}".format(event.type))

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run()
