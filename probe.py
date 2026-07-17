import asyncio
import json
import websockets


async def recv_loop(ws):
    while True:
        try:
            msg = await ws.recv()
            print("\n=== RECEIVED ===")
            try:
                print(json.dumps(json.loads(msg), indent=2))
            except:
                print(msg)
        except Exception as e:
            print("receive error:", e)
            break


async def main():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as ws:

        asyncio.create_task(recv_loop(ws))

        initialize = {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "pocket-agent",
                    "version": "0.1"
                }
            }
        }

        print("sending initialize")
        await ws.send(json.dumps(initialize))

        await asyncio.sleep(2)

        thread_start = {
            "id": 2,
            "method": "thread/start",
            "params": {}
        }

        print("sending thread/start")
        await ws.send(json.dumps(thread_start))

        while True:
            await asyncio.sleep(1)


asyncio.run(main())