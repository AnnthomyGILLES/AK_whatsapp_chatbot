import datetime
import os
import re
from pathlib import Path

import openai
import stripe
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from loguru import logger
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
    delete_document,
    keep_last_n_records,
)
from parse_phone_numbers import extract_phone_number

env_path = Path(".", ".env")
load_dotenv(dotenv_path=env_path)

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


# Welcome message
WELCOME_MESSAGE = """Bonjour et bienvenue sur WhatIA ! 🎉

Je suis votre assistant personnel intelligent, prêt à répondre à toutes vos questions et à vous aider avec vos 
demandes. Propulsé par une puissante Intelligence Artificielle', je peux vous assister de manière précise et 
efficace. Voici quelques exemples de ce que je peux faire pour vous : \n\n

1️⃣ Répondre à des questions générales et complexes \n
2️⃣ Vous fournir des informations détaillées sur des événements ou des lieux \n
3️⃣ Vous aider avec des tâches quotidiennes, comme la rédaction de mails ou de messages \n
4️⃣ Analyser et résumer des articles ou des documents pour vous \n\n

Et bien plus encore ! Pour profiter pleinement de toutes mes fonctionnalités et bénéficier d'une expérience optimale, 
je vous invite à vous abonner dès maintenant. Pour ce faire, veuillez simplement suivre le lien suivant. \n\n

Si vous avez des questions ou si vous avez besoin d'aide, n'hésitez pas à me le faire savoir. Je suis là pour vous 
assister 24h/24 et 7j/7. Alors, commençons notre aventure ensemble ! 🚀"""


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


def split_long_string(text, max_len=1200):
    if len(text) <= max_len:
        return [text]

    sentences = re.split("(?<=[.!?]) +", text)
    result = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_len:
            current_chunk += " " + sentence
        else:
            result.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        result.append(current_chunk.strip())

    return result


@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values["Body"].lower().strip()
    print(incoming_msg)
    phone_number = extract_phone_number(request.values["From"].lower())
    print(phone_number)

    user_id = get_user_id_with_phone_number(phone_number)
    user = get_user(user_id)

    if user_id is None:
        send_message(WELCOME_MESSAGE, phone_number)
        send_message(stripe_payment_link, phone_number)
        return ""

    if incoming_msg:
        if not user["history"]:
            message = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg},
            ]
            answer = ask_chat_conversation(message)
            answers = split_long_string(answer)
            for answer in answers:
                send_message(answer, phone_number)
            message.append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, message)
            keep_last_n_records()
        else:
            message = user["history"]
            message.append({"role": "user", "content": incoming_msg})
            answer = ask_chat_conversation(message)
            answers = split_long_string(answer)
            for answer in answers:
                send_message(answer, phone_number)
            user["history"].append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, user["history"])
            keep_last_n_records()

    return ""


# TODO Anonymize phone number
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

    object_ = event["data"]["object"]
    event_type = event["type"]
    stripe_customer_id = object_["customer"]
    stripe_customer_phone = stripe.Customer.retrieve(stripe_customer_id)["phone"]

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        try:
            id_invoice = object_["invoice"]
            id_subscription = stripe.Invoice.retrieve(id_invoice)["subscription"]
            sub_current_period_end = stripe.Subscription.retrieve(id_subscription)[
                "current_period_end"
            ]
            _ = add_user(stripe_customer_phone, sub_current_period_end)
            print("PaymentIntent was successful!")
        except NoUserPhoneNumber:
            print("[Log] No Phone number provided")
            logger.error(f"User deleted from database: {stripe_customer_phone}")
        except DuplicateUser:
            logger.error(f"Duplicated users creation attempt: {stripe_customer_phone}")

    elif event_type in [
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ]:
        delete_document({"phone_number": stripe_customer_phone})
        logger.info(f"User deleted from database: {stripe_customer_phone}")
    # TODO Handle subscription resume
    elif event_type == "customer.subscription.updated" and object_.status == "canceled":
        if not object_.cancel_at_period_end:
            delete_document({"phone_number": stripe_customer_phone})
            logger.info(f"User deleted from database: {stripe_customer_phone}")
    else:
        logger.warning("Unhandled event type {}".format(event_type))

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
