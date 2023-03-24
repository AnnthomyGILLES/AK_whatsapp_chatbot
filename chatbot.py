import datetime
import os

import openai
from dotenv import load_dotenv
from flask import Flask, request, session
from flask_ngrok import run_with_ngrok
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from mongodb_db import get_user_id, add_history, get_user
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
    session["chat_log"].append({"role": "user", "content": f"{reply_content}"})

    return reply_content


def append_interaction_to_chat_log(user_id, question):
    """Append a new interaction to the chat log.

    Args:
        question (str): The question asked by the user.
    """
    add_history(user_id, question)


def send_message(body_mess, phone_number):
    """Send a message via the Twilio API.

    Args:
        body_mess (str): The message to be sent.
    """
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
    )
    print(message.sid)


def respond(message):
    response = MessagingResponse()
    response.message(message)
    return str(response)


@app.route("/bot", methods=["GET", "POST"])
def bot():
    """Main function to handle incoming requests to the chatbot endpoint."""
    if "chat_log" not in session:
        session["chat_log"] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    incoming_msg = request.values["Body"].lower()
    phone_number = extract_phone_number(request.values["From"].lower())

    user_id = get_user_id(phone_number)
    res = get_user(user_id)

    if user_id is None:
        send_message(
            f"Please submit coordinates through the WhatsApp mobile app.", phone_number
        )
        return ""
    if incoming_msg:
        if not res["history"]:
            message = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg},
            ]
            answer = ask(message)
            message.append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, message)
        else:
            message = res["history"]
            message.append({"role": "user", "content": incoming_msg})
            answer = ask(message)
            res["history"].append({"role": "assistant", "content": answer})
            append_interaction_to_chat_log(user_id, res["history"])

        send_message(answer, phone_number)

    return ""


if __name__ == "__main__":
    app.run()
