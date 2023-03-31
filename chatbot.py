import datetime
import os
import sys
from pathlib import Path

import openai
import stripe
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from loguru import logger
from twilio.rest import Client

from audio.transcription import audio_to_text
from chatgpt_api.chatgpt import ask_chat_conversation
from mongodb_db import (
    add_user,
    NoUserPhoneNumber,
    DuplicateUser,
    delete_document,
    update_user_history,
    find_document,
    reset_document,
    increment_nb_tokens,
)
from parse_phone_numbers import extract_phone_number
from utils import count_tokens, split_long_string, get_audio_duration

HISTORY_TTL = 10
env_path = Path(".", ".env")
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "top-secret!")
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=10)

# OpenAI Chat GPT
openai.api_key = os.getenv("OPENAI_API_KEY")
completion = openai.Completion()
MAX_TOKEN_LENGTH = os.getenv("MAX_TOKEN_LENGTH", 500)

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


app = Flask(__name__)

# Welcome message
WELCOME_MESSAGE = """Bonjour et bienvenue sur WhatIA ! 🎉

Je suis votre assistant personnel intelligent, prêt à répondre à toutes vos questions et à vous aider avec vos 
demandes. Propulsé par une puissante Intelligence Artificielle', je peux vous assister de manière précise et 
efficace. Voici quelques exemples de ce que je peux faire pour vous : \n\n

1️⃣ Répondre à des questions générales et complexes \n
2️⃣ Vous fournir des informations détaillées sur des événements ou des lieux \n
3️⃣ Vous aider avec des tâches quotidiennes, comme la rédaction de mails ou la proposition de recettes \n
4️⃣ Analyser et résumer des articles \n
5️⃣ Traduire des phrases ou des textes complets dans plusieurs langues \n
6️⃣ Répondre à des questions d'entretien \n
7️⃣ Et bien plus! Tapez la commande "/example" pour avoir une liste d'exemples de ce que vous pouvez demanez \n\n

Et bien plus encore ! Pour profiter pleinement de toutes mes fonctionnalités et bénéficier d'une expérience optimale, 
je vous invite à vous abonner dès maintenant. Pour ce faire, veuillez simplement suivre le lien suivant. \n\n

Si vous avez des questions ou si vous avez besoin d'aide, n'hésitez pas à me le faire savoir. Je suis là pour vous 
assister 24h/24 et 7j/7. Alors, commençons notre aventure ensemble ! 🚀"""


EXAMPLE_MESSAGE = """
📖 Demander une définition : "Qu'est-ce que le machine learning ?"
🚗 Obtenir une explication : "Comment fonctionne un moteur à combustion interne ?"
🍽️ Demander une recommandation : "Quel est le meilleur restaurant italien de la ville ?"
🎁 Obtenir des suggestions : "Pouvez-vous me suggérer des idées pour un cadeau d'anniversaire pour mon frère ?"
📜 Demander des informations sur l'histoire : "Quel est le contexte historique de la Révolution française ?"
💡 Obtenir des conseils : "Comment puis-je améliorer mes compétences en leadership ?"
📊 Demander des statistiques : "Quel est le taux de chômage en France actuellement ?"
🖥️ Obtenir des informations sur un produit ou un service : "Pouvez-vous me dire ce que propose ce logiciel de gestion de projet ?"
🌍 Demander une traduction : "Pouvez-vous traduire cette phrase en espagnol ?"
💬 Obtenir une citation célèbre : "Pouvez-vous me donner une citation célèbre d'Albert Einstein ?"
🌐 Demander de l'aide pour résoudre un problème : "Comment puis-je résoudre un problème de connexion internet ?"
📰 Obtenir des informations sur les actualités : "Quels sont les derniers développements dans la pandémie de COVID-19 ?"
🤔 Demander une opinion : "Que pensez-vous de cette nouvelle politique gouvernementale ?"
📚 Obtenir une recommandation de lecture : "Pouvez-vous me recommander un bon livre sur la psychologie ?"
🎥 Demander des informations sur les célébrités : "Quel est le dernier film dans lequel a joué Leonardo DiCaprio ?
💼 Obtenir des conseils pour développer une carrière : "Comment puis-je me démarquer lors d'un entretien d'embauche ?"
🎓 Demander des informations sur les formations professionnelles : "Quelles sont les options de formation pour devenir développeur web ?"
🚀 Demander des informations sur les start-ups ou les entreprises en croissance : "Quelles sont les start-ups les plus prometteuses du moment ?"
🌴 Obtenir des recommandations de voyages : "Quelles sont les meilleures destinations pour un séjour de détente en Thaïlande ?"
📈 Demander des conseils pour investir : "Quelles sont les meilleures options d'investissement pour un débutant ?"
🏋️‍♂️ Demander des conseils pour la santé et le bien-être : "Comment puis-je trouver le meilleur entraîneur personnel pour mes besoins ?"
🤝 Obtenir des informations sur les réseaux professionnels : "Quels sont les meilleurs événements de networking pour rencontrer des professionnels de mon secteur ?"
🚘 Demander des informations sur l'achat ou la location de voitures : "Quelles sont les meilleures options pour acheter ou louer une voiture en tant que jeune actif ?"
💻 Obtenir des conseils pour travailler à distance : "Comment puis-je optimiser mon espace de travail à domicile pour une meilleure productivité ?"
🏥 Demander des informations sur la santé/ les médicaments : "Comment puis-je prévenir l'arthrite ?"
📚 Obtenir des recommandations de lectures/ restaurants/ magasins : "Pouvez-vous me recommander un bon livre sur l'histoire de France ?"
🎭 Demander des informations sur les événements culturels/ sur les activités en plein air : "Quels sont les meilleurs parcs pour faire une promenade dans la ville ?"
🎵 Demander des recommandations musicales : "Pouvez-vous me recommander un album de jazz à écouter ?"
🎥 Obtenir des suggestions de films ou de séries : "Quel est le meilleur film à regarder sur Netflix en ce moment ?"
🚗 Demander des informations sur les voitures : "Quelle est la meilleure voiture pour les longs trajets ?"
"""

logger.remove(0)
logger.add(
    sys.stderr,
    format="{time:HH:mm:ss.SS} | {file} took {elapsed} to execute | {level} | {message} ",
    colorize=True,
)


def send_message(body_mess, phone_number):
    """
    Send a WhatsApp message to the specified phone number using Twilio.

    Args:
        body_mess (str): The content of the message to send.
        phone_number (str): The recipient's phone number.
    """
    message = client.messages.create(
        from_=f"whatsapp:{twilio_phone_numer}",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
    )
    print(message.sid)


@app.route("/bot", methods=["POST"])
def bot():
    """
    Handle incoming messages from users, process them, and send responses.
    This function is designed to be used as an endpoint for a webhook.

    Returns:
        str: An empty string (required for Twilio to work correctly).
    """
    current_time = datetime.datetime.utcnow()
    oldest_allowed_timestamp = current_time - datetime.timedelta(minutes=HISTORY_TTL)
    incoming_msg = request.values["Body"].lower().strip()
    phone_number = extract_phone_number(request.values["From"].lower())

    media_url = request.form.get("MediaUrl0")
    if not incoming_msg:
        if media_url and request.form["MediaContentType0"] == "audio/ogg":
            duration = get_audio_duration(media_url)
            incoming_msg = audio_to_text(media_url)
        else:
            send_message(
                "Il faut écrire un message textuel ou enregistrer un audio pour discuter avec moi.",
                phone_number,
            )
            return ""

    nb_tokens = count_tokens(incoming_msg)

    if nb_tokens >= int(MAX_TOKEN_LENGTH):
        send_message("Ta question est beaucoup trop longue.", phone_number)
        return ""
    if not incoming_msg:
        return ""

    doc = find_document("phone_number", phone_number)

    if doc is None:
        send_message(WELCOME_MESSAGE, phone_number)
        send_message(stripe_payment_link, phone_number)
        return ""

    if doc["history"]:
        if doc["history_timestamp"] < oldest_allowed_timestamp:
            reset_document(doc)
            message = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg},
            ]
        else:
            message = doc["history"]
            message.append({"role": "user", "content": incoming_msg})
    else:
        reset_document(doc)
        message = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": incoming_msg},
        ]
    answer = ask_chat_conversation(message)
    nb_tokens += count_tokens(answer)
    increment_nb_tokens(doc, nb_tokens)
    answers = split_long_string(answer)
    for answer in answers:
        send_message(answer, phone_number)
    message.append({"role": "assistant", "content": answer})
    update_user_history(phone_number, message)

    return ""


# TODO Anonymize phone number
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Handle Stripe webhook events, including payment success, subscription deletion, and subscription pausing.

    Returns:
        tuple: A JSON object with the status and an HTTP status code.
    """
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
    print(stripe_customer_id, stripe_customer_phone)
    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        try:
            id_invoice = object_["invoice"]
            id_subscription = stripe.Invoice.retrieve(id_invoice)["subscription"]
            sub_current_period_end = stripe.Subscription.retrieve(id_subscription)[
                "current_period_end"
            ]
            _ = add_user(stripe_customer_phone, sub_current_period_end)
            send_message(
                """Bienvenue dans le club d'utilisateurs privé de WhatIA ! Nous sommes ravis de t'avoir parmi nous.
                Ton compte est maintenant actif et tu disposes d'un accès illimité à toutes les fonctionnalités de notre bot intelligent. N'hésite pas à nous contacter (contact@ak-intelligence.com) si tu as des questions ou besoin d'aide.""",
                stripe_customer_phone,
            )
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
