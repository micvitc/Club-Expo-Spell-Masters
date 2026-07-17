import asyncio
import websockets
import json

async def listen_to_gestures():
    url = "ws://127.0.0.1:8000/ws"
    try:
        async with websockets.connect(url) as ws:
            while True:
                response = await ws.recv()
                data = json.loads(response)
                
                gesture = data.get("gesture")
                accuracy = data.get("accuracy")
                
                if gesture != "None":
                    print(f"{gesture} [{accuracy}%]")
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(listen_to_gestures())