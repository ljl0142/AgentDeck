import asyncio
import json
from codex_client import CodexClient

def print_event(event):
    method=event.get("method")

    if method:
        print("\nMETHOD: ", method)
    
    if method in {
        "codex/event/agent_message",
        "codex/event/agent_message_content_delta",
        "codex/event/exec_command_begin",
        "codex/event/exec_command_end",
        "turn/completed",
        "thread/status/changed",
    }:
        print(json.dumps(event, indent=2, ensure_ascii=False))


async def main():
    client = CodexClient("ws://localhost:8765/ws")

    client.on_event(print_event)

    await client.connect()
    thread_id=await client.create_thread()
    print("THREAD: ", thread_id)

    await client.send_message(thread_id, "Hello, world!")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())