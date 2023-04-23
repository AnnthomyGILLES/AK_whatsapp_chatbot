import os
from pathlib import Path

from dotenv import load_dotenv

from audio import utils

load_dotenv(dotenv_path=Path("..", ".env"))


def audio_to_text(media_url):
    # Create header with authorization along with content-type
    header = {
        "authorization": os.getenv("ASSEMBLYAI_API_KEY"),
        "content-type": "application/json",
    }
    # upload_url = utils.upload_file("audio.mp3", header)
    upload_url = {"upload_url": media_url}

    # Request a transcription
    transcript_response = utils.request_transcript(upload_url, header)

    # Create a polling endpoint that will let us check when the transcription is complete
    polling_endpoint = utils.make_polling_endpoint(transcript_response)

    # Wait until the transcription is complete
    utils.wait_for_completion(polling_endpoint, header)

    # Request the paragraphs of the transcript
    paragraphs = utils.get_paragraphs(polling_endpoint, header)

    return paragraphs[0]["text"]


if __name__ == "__main__":
    res = audio_to_text(media_url=None)
