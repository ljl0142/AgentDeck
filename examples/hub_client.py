import asyncio
import json
import websockets

from websockets.exceptions import ConnectionClosed

from hub import protocol

async def receive_loop(ws,idle_event,stop_event):
    try:
        async for raw in ws:
            event=json.loads(raw)
            event_type=event.get("type")

            if event_type=="status.changed":
                status=event.get("status")
                print(f"\n[Event] {event}")
                if status == "idle":
                    idle_event.set()
                elif status in {"active", "connecting"}:
                    idle_event.clear()

            elif event_type=="message.delta":
                print(
                    event.get("text",""),
                    end="",
                    flush=True,
                )

            elif event_type=="command.started":
                print(f"\n[Command] {event.get('command')}")

            elif event_type=="command.completed":
                print(
                    f"\n[ExitCode]"
                    f"{event.get("exitCode")}"
                )

            elif event_type=="turn.completed":
                print(
                    f"\n[Turn] status={event.get('status')}, "
                    f"error={event.get('error')}"
                )

            elif event_type=="error":
                print(f"\n[Error] {event.get('message')}")

            else:
                print(f"\n[Event] {event}")
    
    except ConnectionClosed as exc:
        print(
            f"\n[Disconnected] Hub connection closed "
            f"(code={exc.code}, reason={exc.reason or 'unknown'})"
        )
        idle_event.set()
        stop_event.set()


async def main():
    idle_event=asyncio.Event()
    stop_event=asyncio.Event()

    try:
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            recv_task=asyncio.create_task(receive_loop(ws,idle_event,stop_event))

            try:
                while not stop_event.is_set():
                    await idle_event.wait()
                    if stop_event.is_set():
                        break
                    text=await asyncio.to_thread(input,"You> ",)
                    text=text.strip()
                    if text.lower() in {"exit","quit"}:
                        break
                    if not text:
                        continue
                    idle_event.clear()
                    await ws.send(json.dumps(protocol.message_send(text),ensure_ascii=False))

            finally:
                if not recv_task.done():
                    recv_task.cancel()

                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass
                except ConnectionClosed:
                    pass

    except ConnectionRefusedError:
        print(
            "[Connection Error] Cannot connect to Agent Hub at "
            "ws://localhost:8000/ws. Is the Hub running?"
        )
    
    except OSError as exc:
        print(f"[Connection Error] {exc}")


if __name__=="__main__":
    asyncio.run(main())

            