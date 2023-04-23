import configparser
import os
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


def split_long_string(long_string, substring_size=1599):
    return [
        long_string[i : i + substring_size]
        for i in range(0, len(long_string), substring_size)
    ]
