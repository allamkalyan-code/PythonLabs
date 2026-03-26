import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        await ws.send(json.dumps({"type": "message", "content": "SUPER SECRET KEYWORD"}))
        try:
            while True:
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print("RECV:", resp)
        except asyncio.TimeoutError:
            print("timeout")

asyncio.run(test())
