# create.py
import asyncio
import configparser
import os
from pathlib import Path

import aiohttp
import openai
from dotenv import load_dotenv
from loguru import logger
from openai.error import RateLimitError
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 30
MAX_TOKENS = 400

ENV = os.getenv("ENV_WHATIA", "DEVELOPMENT")
config = configparser.ConfigParser()
config_file_path = Path(__file__).resolve().parent.parent / "config.ini"
config.read(config_file_path)
env_path = Path(__file__).resolve().parent.parent / config[ENV]["ENV_FILE_PATH"]

load_dotenv(dotenv_path=env_path)


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
