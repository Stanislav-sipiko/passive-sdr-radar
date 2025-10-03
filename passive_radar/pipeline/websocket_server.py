# passive_radar/tools/ws_client.py
import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://raspberrypi:8765"  # адрес твоего WebSocket сервера

async def listen():
    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL}")
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                ts = datetime.utcnow().isoformat()
                print(f"[{ts}] Track received: {data}")
                
                # Пишем в файл
                with open("tracks.log", "a", encoding="utf-8") as f:
                    f.write(f"{ts} {json.dumps(data)}\n")

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by server")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(listen())
