import uvicorn
import asyncio
import time
from fastapi import FastAPI, WebSocket
from connection_manager import ConnectionManager
from dnd_session_chat import DnDSessionChat

dnd_session = DnDSessionChat(chat_id=1)

async def process_messages(chat: DnDSessionChat):
  while True:
      message = await chat.client_receive_queue.get()
      if message and message == "DO_FINISH":
          chat.client_receive_queue.task_done()
          break
      
      if message and message.endswith('Your turn!'):
         response = input()
         await chat.client_sent_queue.put(response)
      
      # TODO: Process reply

      chat.client_receive_queue.task_done()
      await asyncio.sleep(0.05)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(asyncio.wait([
       dnd_session.start(),
       process_messages(dnd_session)
    ]))