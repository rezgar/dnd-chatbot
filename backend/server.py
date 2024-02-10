import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket
from connection_manager import ConnectionManager
from dnd_session_chat import DnDSessionChat

app = FastAPI()
app.autogen_chat = {}
manager = ConnectionManager()

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    try:
        autogen_chat = DnDSessionChat(chat_id=chat_id, websocket=websocket)
        await manager.connect(autogen_chat)
        data = await autogen_chat.websocket.receive_text()
        future_calls = asyncio.gather(send_to_client(autogen_chat), receive_from_client(autogen_chat))
        await autogen_chat.start(data)
        print("DO_FINISHED")
    except Exception as e:
        print("ERROR", str(e))
    finally:
        try:
            await manager.disconnect(autogen_chat)
        except:
            pass
        
    async def send_to_client(autogen_chat: DnDSessionChat):
      while True:
          reply = await autogen_chat.client_receive_queue.get()
          if reply and reply == "DO_FINISH":
              autogen_chat.client_receive_queue.task_done()
              break
          await autogen_chat.websocket.send_text(reply)
          autogen_chat.client_receive_queue.task_done()
          await asyncio.sleep(0.05)

    async def receive_from_client(autogen_chat: DnDSessionChat):
      while True:
          data = await autogen_chat.websocket.receive_text()
          if data and data == "DO_FINISH":
              await autogen_chat.client_receive_queue.put("DO_FINISH")
              await autogen_chat.client_sent_queue.put("DO_FINISH")
              break
          await autogen_chat.client_sent_queue.put(data)
          await asyncio.sleep(0.05)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)