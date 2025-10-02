import asyncio
import websockets

async def handler(websocket, path):
    print("[ws_server] Client connected")
    await websocket.send("Radar stream started")
    async for msg in websocket:
        print(f"[ws_server] Received: {msg}")

def start_server(host="localhost", port=8765):
    print(f"[ws_server] Starting on ws://{host}:{port}")
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(handler, host, port)
    )
    asyncio.get_event_loop().run_forever()
