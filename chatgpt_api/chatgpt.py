import aiohttp
import openai
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 60


@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
async def ask_chat_conversation(prompt, max_tokens=350):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
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
