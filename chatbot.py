import json
import os

import chainlit as cl
import litellm
from dotenv import load_dotenv

load_dotenv()

chat_history = []

# Load existing chat history if file exists
history_file = "chat_history.json"
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        try:
            chat_history = json.load(f)
        except json.JSONDecodeError:
            chat_history = []  # File was empty or corrupted


@cl.on_message
async def on_message(message: cl.Message):
    # Append user message to history
    chat_history.append({"role": "user", "content": message.content})

    response = ""
    stream = await litellm.acompletion(
        model=os.getenv("LITELLM_MODEL"),
        messages=chat_history,
        stream=True,
        api_key=os.getenv("TOGETHER_AI_API_KEY"),
    )

    msg = cl.Message(content="")
    await msg.send()

    async for chunk in stream:
        delta = ""
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content

        response += delta
        await msg.stream_token(delta)

    # Append assistant response to history
    chat_history.append({"role": "assistant", "content": response})

    # Save updated history to file (overwrite with full updated list)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)


@cl.on_stop
async def on_stop():
    print("Saving chat history on stop...")
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)
    print("Chat history saved.")
