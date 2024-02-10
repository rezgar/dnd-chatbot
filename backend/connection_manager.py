from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
import uuid
from dnd_session_chat import DnDSessionChat
import asyncio
import uvicorn
from dotenv import load_dotenv, find_dotenv
import openai
import os

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[DnDSessionChat] = []

    async def connect(self, autogen_chat: DnDSessionChat):
        await autogen_chat.websocket.accept()
        print(f"autogen_chat {autogen_chat.chat_id} connected")
        self.active_connections.append(autogen_chat)

    async def disconnect(self, autogen_chat: DnDSessionChat):
        autogen_chat.client_receive_queue.put_nowait("DO_FINISH")
        print(f"autogen_chat {autogen_chat.chat_id} disconnected")
        self.active_connections.remove(autogen_chat)