import os
from mistralai import Mistral
from fastapi.responses import JSONResponse
from chainlit.auth import create_jwt
from chainlit.server import app
import chainlit as cl
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from chainlit.user import User
from chainlit.server import _authenticate_user
from chainlit.utils import mount_chainlit


origins = [
    "https://pluto-chat.netlify.app",
    "http://localhost:5173" 
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Credentials"],
)

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
settings = {
    "model":"mistral-small-latest",
    "max_tokens":1000,
    "temperature":0.5,
}

@app.get("/custom-auth")
async def custom_auth():
    # Verify the user's identity with custom logic.
    token = create_jwt(cl.User(identifier="Test User"))
    return JSONResponse({"token": token})

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set(
        "message_history",
        [{"role": "assistant", "content": "You are a helpful assistant. Your name is Pluto."}],
    )
    await cl.Message(content="Hello!! I'm Pluto assistant. How can I help you?").send()


@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = client.chat.stream(
        messages=message_history, stream=True, **settings
    )

    for part in stream:
        if token := part.data.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()