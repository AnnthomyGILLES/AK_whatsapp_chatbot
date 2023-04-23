import tempfile

import boto3

from utils import load_config

load_config()


def text_to_speech(text, output_format="mp3", language_code="fr-FR"):
    # Set up AWS Polly client
    client = boto3.client(
        "polly", region_name="us-west-2"
    )  # Change the region as per your requirements

    # Set up the parameters for the synthesis
    response = client.synthesize_speech(
        Text=text, OutputFormat=output_format, VoiceId="Lea", LanguageCode=language_code
    )

    # Save the audio as a temporary file
    with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as f:
        f.write(response["AudioStream"].read())
        tmp_audio_file = f.name

    return tmp_audio_file


if __name__ == "__main__":
    text = "Hello, this is a sample text to be converted to speech using AWS Polly."
    output_format = "mp3"
    language_code = "en-GB"
    tmp_audio_file = text_to_speech(text, output_format, language_code)
    print(f"The audio file has been saved to {tmp_audio_file}")
