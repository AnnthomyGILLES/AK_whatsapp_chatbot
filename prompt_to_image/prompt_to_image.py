import asyncio
import os

import aiohttp
import openai
from loguru import logger
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits

from utils import load_config

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 30
MAX_TOKENS = 400

load_config()

openai.api_key = os.getenv("OPENAI_API_KEY")


async def generate_image(prompt):
    async with aiohttp.ClientSession() as session:

        @sleep_and_retry
        @limits(calls=MAX_CALLS_PER_MINUTE, period=ONE_MINUTE)
        async def request():
            try:
                response = openai.Image.create(
                    prompt=prompt,
                    n=1,
                    size="256x256",
                )

                reply_content = response["data"][0]["url"]

                return reply_content
            except RateLimitError:
                logger.error(f"rate limit reached for DALL-E")

        return await request()


async def main():
    PROMPT = "An eco-friendly computer from the 90s in the style of vaporwave"
    response = await generate_image(PROMPT)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
