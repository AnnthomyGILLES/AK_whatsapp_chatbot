import aiohttp
import openai
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 60


@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
async def ask_chat_conversation(prompt, max_tokens=300):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=max_tokens,
            stop=None,
            temperature=0.7,
            stream=False,
        )
        reply_content = response.choices[0].message.content
        return reply_content
    except RateLimitError:
        print("[Log] Rate limit reached")


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
                    max_tokens=MAX_TOKENS,
                    temperature=0.7,
                    stream=False,
                )

                reply_content = response.choices[0].text

                return reply_content
            except RateLimitError:
                print("[Log] Rate limit reached")

        return await request()
