import datetime
import os

import openai
import stripe
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits
from twilio.rest import Client

from mongodb_db import (
    get_user_id_with_phone_number,
    update_history,
    get_user,
    add_user,
    NoUserPhoneNumber,
    DuplicateUser,
)
from parse_phone_numbers import extract_phone_number

load_dotenv()

app = Flask(__name__)

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 30

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

stripe_payment_link = os.getenv("STRIPE_PAYMENT_LINK")
stripe.api_key = stripe_keys["secret_key"]


@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def ask_chat_conversation(message_log):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_log,
            max_tokens=1024,
            stop=None,
            temperature=0.7,
        )

        reply_content = response.choices[0].message.content

        return reply_content
    except RateLimitError:
        print("[Log] Rate limit reached")


@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
def ask_pronpt(prompt):
    try:
        response = openai.Completion.create(
            model="text-davinci-003", prompt=prompt, max_tokens=100, temperature=0.7
        )

        reply_content = response.choices[0].text

        return reply_content
    except RateLimitError:
        print("[Log] Rate limit reached")


def append_interaction_to_chat_log(user_id, question):
    update_history(user_id, question)


def send_message(body_mess, phone_number):
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
        send_message(stripe_payment_link, phone_number)
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
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            request.data, sig_header, stripe_keys["endpoint_secret"]
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": "Invalid payload"}), 400

    stripe_customer_id = request.json["data"]["object"]["customer"]
    stripe_customer_phone = stripe.Customer.retrieve(stripe_customer_id)["phone"]

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        try:
            _ = add_user(stripe_customer_phone)
            print("PaymentIntent was successful!")
        except (DuplicateUser, NoUserPhoneNumber) as e:
            print("[Log] No Phone number provided")
    elif event["type"] in [
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ]:
        delete_document({"phone_number": stripe_customer_phone})
        print(" User unsubscribe.")
    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        if (
            subscription.status == "canceled"
            and subscription.cancel_at_period_end == False
        ):
            delete_document({"phone_number": stripe_customer_phone})
            print(" User unsubscribe.")
    else:
        print("Unhandled event type {}".format(event.type))

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run()
