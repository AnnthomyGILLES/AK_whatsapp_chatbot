import asyncio
from pathlib import Path

import openai
import pytest
from dotenv import load_dotenv

from chatgpt_api.chatgpt import ask_chat_conversation

load_dotenv(dotenv_path=Path("..", ".env.development"))
# OpenAI Chat GPT
openai.api_key = "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"


@pytest.mark.asyncio
async def test_ask_chat_conversation_multiple_calls():
    message_logs = [
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
        ],
        [
            {"role": "user", "content": "What's the weather like today?"},
            {"role": "assistant", "content": "I'm sorry, I don't know."},
        ],
        [
            {"role": "user", "content": "Can you tell me a joke?"},
            {
                "role": "assistant",
                "content": "Sure! Why did the chicken cross the road?",
            },
        ],
    ]

    responses = await asyncio.gather(
        *(ask_chat_conversation(log) for log in message_logs)
    )

    assert len(responses) == len(message_logs)

    for response in responses:
        assert response is not None
        assert len(response) > 0
