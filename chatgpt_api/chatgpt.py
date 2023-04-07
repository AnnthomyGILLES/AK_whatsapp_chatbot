import aiohttp
import openai
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 30
MAX_TOKENS = 400


async def ask_chat_conversation(message_log):
    """
    Send a message to the GPT-3.5-turbo model and return the generated response.
    This function is rate limited according to the specified limits.

    Args:
        message_log (list): A list of message dictionaries containing the conversation history.

    Returns:
        str: The content of the generated message.
    """
    async with aiohttp.ClientSession() as session:

        @sleep_and_retry
        @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
        async def request():
            try:
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=message_log,
                    max_tokens=MAX_TOKENS,
                    stop=None,
                    temperature=0.7,
                )

                reply_content = response.choices[0].message.content

                return reply_content
            except RateLimitError:
                print("[Log] Rate limit reached")

        return await request()


async def ask_prompt(prompt):
    """
    Send a prompt to the text-davinci-002 model and return the generated response.
    This function is rate limited according to the specified limits.

    Args:
        prompt (str): The prompt to send to the model.

    Returns:
        str: The generated text response.
    """
    async with aiohttp.ClientSession() as session:

        @sleep_and_retry
        @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
        async def request():
            try:
                response = await openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.7,
                )

                reply_content = response.choices[0].text

                return reply_content
            except RateLimitError:
                print("[Log] Rate limit reached")

        return await request()
