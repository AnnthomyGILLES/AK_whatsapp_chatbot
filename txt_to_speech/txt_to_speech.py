import configparser
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

ENV = os.getenv("ENV_WHATIA", "DEVELOPMENT")
config = configparser.ConfigParser()
config_file_path = Path(__file__).resolve().parent.parent / "config.ini"

config.read(config_file_path)

env_path = Path(__file__).resolve().parent.parent / config[ENV]["ENV_FILE_PATH"]

load_dotenv(dotenv_path=env_path)

# aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
# aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if __name__ == "__main__":
    # Set up AWS Polly client
    client = boto3.client(
        "polly", region_name="us-west-2"
    )  # Change the region as per your requirements

    # Specify the text to be converted to speech
    text = "Hello, this is a sample text to be converted to speech using AWS Polly."

    # Set up the parameters for the synthesis
    response = client.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId="Joanna",  # Change the voice as per your requirements
    )
    print(response)
