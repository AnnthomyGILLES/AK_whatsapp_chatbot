import os

from flask import Flask, request, session
from twilio.rest import Client
import openai
import datetime
from flask_ngrok import run_with_ngrok
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
run_with_ngrok(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'top-secret!')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=10)

# OpenAI Chat GPT
openai.api_key = os.getenv("OPENAI_API_KEY")
completion = openai.Completion()

# Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)


# Function to send a message to the OpenAI chatbot model and return its response
def ask(message_log):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # The name of the OpenAI chatbot model to use
        messages=message_log,  # The conversation history up to this point, as a list of dictionaries
        max_tokens=1024,  # The maximum number of tokens (words or subwords) in the generated response
        stop=None,  # The stopping sequence for the generated response, if any (not used here)
        temperature=0.7,  # The "creativity" of the generated response (higher temperature = more creative)
    )

    # # Find the first response from the chatbot that has text in it (some responses may not have text)
    # for choice in response.choices:
    #     if "text" in choice:
    #         return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    reply_content = response.choices[0].message.content
    session['chat_log'].append({"role": "user", "content": f"{reply_content}"})
    return reply_content


def append_interaction_to_chat_log(question):
    session['chat_log'].append({'role': 'user', 'content': question})

def send_message(body_mess):
    message = client.messages.create(
        from_='whatsapp:+14155238886',  # With Country Code
        body=body_mess,
        to='whatsapp:+33667656197'  # With Country Code
    )
    print(message.sid)  # Print Response


@app.route('/bot', methods=['POST'])
def bot():
    if "chat_log" not in session:
        session['chat_log'] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    incoming_msg = request.values['Body'].lower()
    print(incoming_msg)

    if incoming_msg:
        append_interaction_to_chat_log(incoming_msg)
        answer = ask(session['chat_log'])
        # answer = ask('\n'.join([f"{chat['role']}: {chat['content']}" for chat in session['chat_log']]))

        send_message(answer)
    else:
        send_message("Message Cannot Be Empty!")
        print("Message Is Empty")

    return ''


if __name__ == '__main__':
    app.run()
