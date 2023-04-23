import datetime
import os
import re
from logging.config import dictConfig

import openai
import stripe
from flask import Flask, request, jsonify
from flask_caching import Cache

from audio.transcription import audio_to_text
from chatgpt_api.chatgpt import ask_chat_conversation
from mongodb_db import UserCollection
from notifier.send_notification import send_message
from parse_phone_numbers import extract_phone_number
from utils import count_tokens, split_long_string, load_config

env_name = "PROD"
config = load_config(env_name)

HISTORY_TTL = config.getint(env_name, "HISTORY_TTL")
FREE_TRIAL_LIMIT = config.getint(env_name, "FREE_TRIAL_LIMIT")


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "top-secret!")
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=10)

cache = Cache(app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 60})

# OpenAI Chat GPT
openai.api_key = os.getenv("OPENAI_API_KEY")
completion = openai.Completion()
MAX_TOKEN_LENGTH = os.getenv("MAX_TOKEN_LENGTH", 200)

# Stripe
stripe_keys = {
    "secret_key": os.getenv("STRIPE_SECRET_KEY"),
    "publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY"),
    "endpoint_secret": os.getenv("STRIPE_ENDPOINT"),
}

WHATIA_WEBSITE = os.getenv("WHATIA_WEBSITE")

stripe.api_key = stripe_keys["secret_key"]

WELCOME_MESSAGE = """🇫🇷
					Bienvenue!🤖 \n
					Je suis ton assistant personnel intelligent, prêt à répondre à toutes tes questions. 💬💡 \n
					Propulsé par une intelligence artificielle, je peux t'assister de manière précise et efficace. Voici quelques exemples de ce que je peux faire pour toi : 🧐🤖 \n\n

						1️⃣ Répondre à des questions générales et complexes \n
						2️⃣ Te fournir des informations détaillées sur des événements ou des lieux \n
						3️⃣ T'aider avec des tâches quotidiennes, comme la rédaction de mails ou la préparation de recettes \n
						4️⃣ Analyser et résumer des articles pour toi \n
						5️⃣ Traduire des phrases ou des textes complets dans plusieurs langues \n
						6️⃣ Répondre à des questions d'entretien \n\n

						Et bien plus encore !  🤩 \n\n


					N'hésite pas à contacter le support si tu as des questions ou si tu as besoin d'aide. Notre équipe est disponible pour répondre à toutes tes interrogations pour t'aider à profiter pleinement de ce que je peux t'offrir🙌 \n

					🌐 Site web: https://app.whatia.fr \n
					📧 Mail: contact@whatia.fr \n
					📷 Instagram (Abonne-toi pour ne pas rater les bons plans!💰): https://www.instagram.com/app.whatia.fr"""

WELCOME_MESSAGE_GB = """🇬🇧
					Welcome! 🤖 \n
					I am your intelligent personal assistant, ready to answer all your questions. 💬💡 \n
					Powered by artificial intelligence, I can assist you accurately and efficiently. Here are some examples of what I can do for you: 🧐🤖 \n\n

					1️⃣ Answer general and complex questions \n
					2️⃣ Provide detailed information on events or places \n
					3️⃣ Help you with daily tasks, such as writing emails or preparing recipes \n
					4️⃣ Analyze and summarize articles for you \n
					5️⃣ Translate or complete texts in multiple languages \n
					6️⃣ Answer interview questions \n

					And so much more! 🤩 \n\n

					Do not hesitate to contact our team if you have any questions or need help. They are available to answer all your questions 🙌 \n

					🌐 Website: https://app.whatia.fr \n
					📧 Email: contact@whatia.fr \n
					📷 Instagram (Follow me so you don't miss out on great deals!💰): https://www.instagram.com/app.whatia.fr"""
WELCOME_MESSAGE_CTA = """🇬🇧
					👉 If you have read the message above carefully, your free trial has started and you are now ready to discover all my features. To get started, simply chat with me by replying to this message in the language of your choice.  \n
					Let's go! Tell me what you want! 🎬 \n\n

					🇫🇷 
					👉 Si tu as bien lu le message précédent, ton essai gratuit a commencé, tu es maintenant prêt à découvrir toutes mes fonctionnalités. 
					Pour commencer il suffit de discuter avec moi en répondant à ce message dans la langue que tu souhaites. \n
					Allons-y! Dis-moi ce que tu veux! 🎬"""

TRIAL_END_MESSAGE_GB = """🇬🇧
					We are delighted that you enjoyed your free trial. That's a great start! 😊 \n
					To continue enjoying WhatIA, you can choose between a one-time payment or a subscription. Here are the benefits: \n

					    - Nearly unlimited messages 📩 \n
					    - Available 24/7 🕰️ \n
                        - All chatbot updates \n
					    - No advertising 🚫 \n\n

					So don't waste any more time searching for answers to your questions! Imagine all the questions you could ask and the instant answers you could receive! \n\n

					The offers are right here: \n

					    🔑 Weekly pass (one-time payment) €4.90: app.whatia.fr/week \n
					    🔑 Monthly pass (one-time payment) €9.90: app.whatia.fr/month \n
					    🔁 Weekly subscription (-50%) €2.49: app.whatia.fr/weekly \n
					    🔁 Monthly subscription (-25%) €7.49: app.whatia.fr/monthly \n\n

					You will receive a confirmation message for any purchase. 📩👍 \n
					For subscribers (not weekly or monthly pass), the management/cancellation of your subscription takes place here: app.whatia.fr/subscription 📅 \n\n

					Any questions? We are here to support you on this adventure with WhatIA: \n
					📧 Email: contact@whatia.fr \n
					📷 Instagram: https://www.instagram.com/app.whatia.fr \n\n

					We look forward to seeing you again as a premium user of WhatIA! 🤝
"""

TRIAL_END_MESSAGE_FR = """🇫🇷 
					Nous sommes ravis que vous ayez profité de vos messages d'essai gratuit de WhatIA. C'est un très bon départ! 😊 \n
					Passez par un paiement unique ou un abonnement pour continuer à profiter de Whatia. Les avantages: \n
						- Message quasiment illimités 📩 \n
						- Disponible 24h/24h 7j/7j 🕰️ \n
                        - Toutes les mises à jour du chatbot \n
						- Sans publicité 🚫 \n

					Ne perdez donc plus des heures à chercher des réponses à vos questions! Imaginez toutes les questions que vous pourriez poser, et les réponses que vous pourriez recevoir instantanément! \n\n

					Les offres sont par ici: \n

						- 🔑 pass semaine (paiement unique) 4€90 : app.whatia.fr/week \n
						- 🔑 pass mois (paiement unique) 9€90 : app.whatia.fr/month \n
						- 🔁 abonnement hebdomadaire (-50%) 2€49 : app.whatia.fr/weekly \n
						- 🔁 abonnement mensuel (-25%) 7€49 : app.whatia.fr/monthly \n\n

					Un message de confirmation vous sera envoyé pour tout achat. 📩👍 \n
					Pour les abonnés (=non pass semaine ou mois) la gestion/résiliation de votre abonnement se passe ensuite ici: app.whatia.fr/subscription 📅 \n\n

					Des questions? Nous sommes là pour vous accompagner dans cette aventure avec WhatIA \n
						📧 Mail: contact@whatia.fr \n
						📷 Instagram: https://www.instagram.com/app.whatia.fr \n\n


					Nous sommes impatients de vous revoir en tant qu'utilisateur premium de WhatIA! 🤝
"""

ACTIVATION_MESSAGE = """🇬🇧
					🎉Welcome to the privileged circle of WhatIA premium users! Congrats! 🎊 \n
					We are delighted to welcome you among us and offer you privileged access to all the features of our chatbot. With your premium account, you are ready to enjoy a superior quality experience. Only your imagination is the limit! 💡📱 \n
					Whether you want to improve your user experience or discover new features, we are here to accompany you throughout your use. So don't hesitate to contact us if you have any questions or need help. Our team is at your disposal to offer you an unforgettable experience on WhatIA. 🤝👨‍💼 \n\n

					📧 Email: contact@whatia.fr \n
					🔑 Manage your subscription (if subscribed): app.whatia.fr/subscription \n
					📷 Instagram (-5% for subscribers! On request): https://www.instagram.com/app.whatia.fr \n\n

					Congratulations on your choice! You won't regret it, enjoy the experience! 🚀

					\n\n\n

					🇫🇷
					🎉Bienvenue dans le cercle privilégié des utilisateurs premium de WhatIA! Félicitations! 🎊 \n
					Nous sommes ravis de t'accueillir parmi nous et de te proposer un accès privilegié à toutes les fonctionnalités de notre chatbot. Avec ton compte premium, tu es prêt à profiter d'une expérience de qualité supérieure. Seule ton imagination est la limite!💡📱 \n
					Que tu souhaites améliorer ton expérience utilisateur ou découvrir de nouvelles fonctionnalités, nous sommes là pour t'accompagner tout au long de ton utilisation. N'hésite donc pas à nous contacter si tu as des questions ou si tu as besoin d'aide. Notre équipe est à ta disposition pour t'offrir une expérience inoubliable sur WhatIA. 🤝👨‍💼 \n\n

					📧 Mail: contact@whatia.fr \n
					🔑 Gérer ton abonnement (si abonné): app.whatia.fr/abonnement \n
					📷 Instagram (-5% pour les abonnés! Sur demande): https://www.instagram.com/app.whatia.fr  \n\n

					Félicitations pour ton choix! Tu ne le regretteras pas, profites de l'expérience! 🚀"""

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


def split_long_string(text, max_len=1599):
    """
    Split a long string into a list of strings of maximum length `max_len`.

    Args:0
        text (str): The input text to be split.
        max_len (int, optional): The maximum length of each chunk. Defaults to 1599.

    Returns:
        list[str]: A list of strings, each with a length not exceeding `max_len`.
    """
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
async def bot():
    """
    Handle incoming messages from users, process them, and send responses.
    This function is designed to be used as an endpoint for a webhook.

    Returns:
        str: An empty string (required for Twilio to work correctly).
    """
    collection_name = "users"
    incoming_msg = str(request.values["Body"].lower().strip())
    phone_number = extract_phone_number(request.values["From"].lower())

    media_url = request.form.get("MediaUrl0")
    if not incoming_msg:
        if media_url and request.form["MediaContentType0"] == "audio/ogg":
            # TODO handle audio duration
            # duration = get_audio_duration(media_url)
            incoming_msg = audio_to_text(media_url)
        else:
            send_message(
                "Il faut écrire un message textuel ou enregistrer un audio pour discuter avec moi.",
                phone_number,
            )
            return ""

    nb_tokens = count_tokens(incoming_msg)

    app.logger.info(f"Incoming message is: {incoming_msg}")
    app.logger.info(f"Phone number is: {phone_number}")

    if nb_tokens >= int(MAX_TOKEN_LENGTH):
        send_message("Ta question est beaucoup trop longue.", phone_number)
        return ""
    if not incoming_msg:
        return ""
    # elif incoming_msg.startswith(("!image", "! image")):
    #     dalle_media_url = await generate_image(incoming_msg)
    #     send_message(incoming_msg, phone_number, media_url=dalle_media_url)
    #     return ""

    # Check cache for user document
    doc = cache.get(phone_number)
    users = UserCollection(collection_name)

    if doc is None:
        # If not in cache, get from database and add to cache
        doc = users.find_document("phone_number", phone_number)

        if doc is None:
            doc_id = users.add_user(phone_number)
            send_message(WELCOME_MESSAGE, phone_number)
            send_message(WELCOME_MESSAGE_GB, phone_number)

            doc = users.collection.find_one(doc_id)

    if (
        doc.get("nb_messages") >= FREE_TRIAL_LIMIT
        and doc.get("current_period_end") is None
    ):
        users.collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"is_blocked": True}},
        )

    message = [
        {
            "role": "system",
            "content": "You are a helpful assistant called WhatIA and talking either in french, spanish, italian, english or more "
            "depending on the language used to talk to you.",
        },
    ]

    if doc["is_blocked"]:
        send_message(TRIAL_END_MESSAGE_GB, phone_number)
        send_message(TRIAL_END_MESSAGE_FR, phone_number)
        return ""
    historical_messages = []
    if doc.get("history"):
        historical_messages = doc.get("history")

    historical_messages.append({"role": "user", "content": incoming_msg})

    answer = await ask_chat_conversation(message + historical_messages)
    nb_tokens += count_tokens(answer)
    answers = split_long_string(answer)
    for answer in answers:
        send_message(answer, phone_number)
    if len(historical_messages) > 4:
        del historical_messages[:2]
    historical_messages.append({"role": "assistant", "content": answer})
    users.increment_nb_tokens_messages(doc, nb_tokens)
    doc = users.update_user_history(phone_number, historical_messages)
    cache.set(phone_number, doc)

    return ""


# TODO Anonymize phone number
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data.decode("utf-8")
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )
    except ValueError:
        app.logger.error("Invalid payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        app.logger.error("Invalid signature")
        return jsonify({"error": "Invalid signature"}), 400

    event_type = event["type"]
    object_ = event["data"]["object"]
    if event_type == "checkout.session.completed":
        stripe_customer_phone = object_["customer_details"]["phone"]
    else:
        stripe_customer_id = object_["customer"]
        stripe_customer_phone = stripe.Customer.retrieve(stripe_customer_id)["phone"]

    # Initialize the UserCollection with the specified collection name
    users = UserCollection("users")

    if event_type in [
        "customer.subscription.deleted",
        "customer.subscription.paused",
    ]:
        users.delete_document({"phone_number": stripe_customer_phone})
        app.logger.info(f"User deleted from database: {stripe_customer_phone}")
    elif event_type == "customer.subscription.created":
        sub_current_period_end = object_["current_period_end"]
        _ = users.add_user(stripe_customer_phone, sub_current_period_end)
        send_message(
            ACTIVATION_MESSAGE,
            stripe_customer_phone,
        )
    elif event_type == "customer.subscription.updated":
        if object_.status in ["canceled", "unpaid"]:
            if not object_.cancel_at_period_end:
                users.delete_document({"phone_number": stripe_customer_phone})
                app.logger.info(f"User deleted from database: {stripe_customer_phone}")
            else:
                sub_current_period_end = object_["current_period_end"]
                _ = users.add_user(stripe_customer_phone, sub_current_period_end)
            send_message("Votre abonnement a pris fin.", stripe_customer_phone)
        if object_["status"] == "trialing":
            sub_current_period_end = object_["current_period_end"]
            _ = users.add_user(stripe_customer_phone, sub_current_period_end)
            send_message(
                ACTIVATION_MESSAGE,
                stripe_customer_phone,
            )
        if object_["status"] == "active":
            sub_current_period_end = object_["current_period_end"]
            _ = users.add_user(stripe_customer_phone, sub_current_period_end)
            send_message(ACTIVATION_MESSAGE, stripe_customer_phone)
    elif event_type == "checkout.session.completed":
        sub_current_period_end = datetime.datetime.utcnow()
        # Pass 7 jours
        if object_["amount_subtotal"] == 490:
            sub_current_period_end = datetime.datetime.utcnow() + datetime.timedelta(
                days=7
            )
        #     Pass 30 jours
        elif object_["amount_subtotal"] == 990:
            sub_current_period_end = datetime.datetime.utcnow() + datetime.timedelta(
                days=30
            )
        sub_current_period_end = sub_current_period_end.timestamp()
        _ = users.add_user(stripe_customer_phone, sub_current_period_end)
        send_message(
            ACTIVATION_MESSAGE,
            stripe_customer_phone,
        )
    else:
        app.logger.warning("Unhandled event type {}".format(event_type))

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    if env_name == "DEVELOPMENT":
        app.run(host="0.0.0.0", port=5000)
    elif env_name == "PROD":
        app.run(
            host="0.0.0.0",
            port=5000,
            ssl_context=(
                "/etc/letsencrypt/live/pay.whatia.fr/fullchain.pem",
                "/etc/letsencrypt/live/pay.whatia.fr/privkey.pem",
            ),
        )
