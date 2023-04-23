import configparser
import os
import re
from pathlib import Path
from urllib.request import urlopen

import tiktoken
from dotenv import load_dotenv
from mutagen.mp3 import MP3

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def count_tokens(phrase):
    n = encoding.encode(phrase)
    return len(n)


def get_audio_duration(url):
    audio_file = urlopen(url)
    audio = MP3(audio_file)
    duration = audio.info.length
    return duration


def load_config(env_name="DEVELOPMENT"):
    ENV = os.getenv("ENV_WHATIA", env_name)

    # Read the configuration file
    config = configparser.ConfigParser()
    config_file_path = Path(__file__).resolve().parent / "config.ini"
    config.read(config_file_path)

    env_path = Path(__file__).resolve().parent / config[ENV]["ENV_FILE_PATH"]

    load_dotenv(dotenv_path=env_path)
    return config


def split_long_string(text, max_len=1200):
    """
    Split a long string into a list of strings of maximum length `max_len`.

    Args:
        text (str): The input text to be split.
        max_len (int, optional): The maximum length of each chunk. Defaults to 1200.

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
