import openai
from openai import AsyncOpenAI

client = AsyncOpenAI()
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 60


@sleep_and_retry
@limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
async def ask_chat_conversation(prompt, max_tokens=500):
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=prompt,
            max_tokens=max_tokens,
            stop=None,
            temperature=0.7,
            stream=False,
        )
        reply_content = response.choices[0].message.content
        return reply_content
    except openai.RateLimitError as e:
        print("[Log] Rate limit reached")
