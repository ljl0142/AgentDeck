import asyncio
import json
import websockets
from  datetime import datetime

SERVER_URI = "ws://localhost:8765"
LOG_FILE = "log.jsonl"

thread_id = None
seen_methods = set()

def save_raw_message(msg: str):
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "raw": msg,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")

async def recv_loop(ws):
    global thread_id, seen_methods
    while True:
        try:
            msg = await ws.recv()
            save_raw_message(msg)

            try:
                data=json.loads(msg)
                print(json.dumps(data, indent=2))
            except Exception:
                print("\n=== RAW RECEIVED ===")
                print(msg)
                continue

            if "method" in data:
                seen_methods.add(data["method"])
                print("\nMETHOD:", data["method"])
                print("SEEN METHODS:", sorted(seen_methods))

            if data.get("id") == 2 and "result" in data:
                thread = data["result"].get("thread")
                if thread and "id" in thread:
                    thread_id = thread["id"]
                    print("\n=== THREAD CREATED ===")
                    print(thread_id)

            if data.get("id") == 3:
                print("\n=== TURN START RESPONSE ===")
                print(json.dumps(data, indent=2, ensure_ascii=False))

            if "error" in data:
                print("\n=== ERROR ===")
                print(json.dumps(data, indent=2, ensure_ascii=False))


        except Exception as e:
            print("receive error:", e)
            break

async def main():
    global thread_id
    async with websockets.connect(SERVER_URI) as ws:
        asyncio.create_task(recv_loop(ws))

        initialize = {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "pocketagent",
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

        await asyncio.sleep(2)

        while thread_id is None:
            await asyncio.sleep(0.5)

        print("Using_thread:", thread_id)

        turn_start = {
            "id": 3,
            "method": "turn/start",
            "params": {
                "threadId": thread_id,
                "input": [
                    {
                        "type": "text",
                        "text": "view the working directory and list the files in it"
                    }
                ]
            }
        }

        print("sending turn/start")
        await ws.send(json.dumps(turn_start))

        while True:
            await asyncio.sleep(1)

asyncio.run(main())