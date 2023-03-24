import datetime
import os

import openai
from dotenv import load_dotenv
from flask import Flask, request, session
from flask_ngrok import run_with_ngrok
from twilio.rest import Client

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
        message_log (list[dict]): The conversation history up to this point, as a list of dictionaries.

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


def append_interaction_to_chat_log(question):
    """Append a new interaction to the chat log.

    Args:
        question (str): The question asked by the user.
    """
    session["chat_log"].append({"role": "user", "content": question})


def send_message(body_mess):
    """Send a message via the Twilio API.

    Args:
        body_mess (str): The message to be sent.
    """
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=body_mess,
        to="whatsapp:+33667656197",
    )
    print(message.sid)


@app.route("/bot", methods=["POST"])
def bot():
    """Main function to handle incoming requests to the chatbot endpoint."""
    if "chat_log" not in session:
        session["chat_log"] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    incoming_msg = request.values["Body"].lower()
    print(incoming_msg)

    if incoming_msg:
        append_interaction_to_chat_log(incoming_msg)
        answer = ask(session["chat_log"])
        send_message(answer)
    else:
        send_message("Message Cannot Be Empty!")
        print("Message Is Empty")

    return ""


if __name__ == "__main__":
    app.run()
