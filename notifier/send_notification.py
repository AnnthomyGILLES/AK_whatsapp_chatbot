import configparser
import os
from pathlib import Path

from dotenv import load_dotenv
from twilio.rest import Client

from mongodb_db import UserCollection

ENV = os.getenv("ENV_WHATIA", "DEVELOPMENT")
config = configparser.ConfigParser()
config_file_path = Path(__file__).resolve().parent.parent / "config.ini"

config.read(config_file_path)

env_path = Path(__file__).resolve().parent.parent / config[ENV]["ENV_FILE_PATH"]

load_dotenv(dotenv_path=env_path)

# Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_numer = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)


def send_message(body_mess, phone_number, media_url=None):
    """
    Send a WhatsApp message to the specified phone number using Twilio.

    Args:
        body_mess (str): The content of the message to send.
        phone_number (str): The recipient's phone number.
    """
    response = client.messages.create(
        from_=f"whatsapp:{twilio_phone_numer}",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
        media_url=media_url,
    )
    print(response.sid)


if __name__ == "__main__":
    users = UserCollection("users")
    list_of_users = users.list_all_users()
    for user in list_of_users:
        print(user)
        if user["phone_number"] == "+33667656197":
            send_message("New feature", user["phone_number"])
