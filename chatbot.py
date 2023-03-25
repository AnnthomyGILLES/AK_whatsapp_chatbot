import datetime
import os

import openai
from dotenv import load_dotenv
from flask import Flask, request
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
client = Client(account_sid, auth_token)


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
        from_="whatsapp:+14155238886",
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


if __name__ == "__main__":
    app.run()
