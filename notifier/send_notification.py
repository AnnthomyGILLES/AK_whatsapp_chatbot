import os

from twilio.rest import Client

from chatbot import logger
from utils import load_config

load_config()
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
        messaging_service_sid="MG19e644894066c03828cf0217bf3764f2",
        from_=f"whatsapp:{twilio_phone_numer}",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
        media_url=media_url,
    )
    logger.info(response.sid)


if __name__ == "__main__":
    ACTIVATION_MESSAGE_FR = """🇫🇷
    					🎉Bienvenue dans le cercle privilégié des utilisateurs premium de WhatIA! Félicitations! 🎊 \n
    					Nous sommes ravis de t'accueillir parmi nous et de te proposer un accès privilegié à toutes les fonctionnalités de notre chatbot. Avec ton compte premium, tu es prêt à profiter d'une expérience de qualité supérieure. Seule ton imagination est la limite!💡📱 \n
    					Que tu souhaites améliorer ton expérience utilisateur ou découvrir de nouvelles fonctionnalités, nous sommes là pour t'accompagner tout au long de ton utilisation. N'hésite donc pas à nous contacter si tu as des questions ou si tu as besoin d'aide. Notre équipe est à ta disposition pour t'offrir une expérience inoubliable sur WhatIA. 🤝👨‍💼 \n\n

    					📧 Mail: contact@whatia.fr \n
    					🔑 Gérer ton abonnement (si abonné): app.whatia.fr/abonnement \n
    					📷 Instagram (-5% pour les abonnés! Sur demande): https://www.instagram.com/app.whatia.fr  \n\n

    					Félicitations pour ton choix! Tu ne le regretteras pas, profites de l'expérience! 🚀"""
    send_message(ACTIVATION_MESSAGE_FR, "+590690976015")
