import asyncio
from codex_client import CodexClient

async def main():
    client=CodexClient("ws://localhost:8765/ws")
    turn_finished=asyncio.Event()

    def handle_event(event):
        method=event.get("method")

        if method == "codex/event/agent_message_content_delta":
            delta=(
                event.get("params", {})
                .get("msg", {})
                .get("delta", "")
            )
            print(delta, end="", flush=True)
        
        elif method == "turn/completed":
            params=event.get("params", {})
            turn=params.get("turn", {})
            if turn.get("status")=="failed":
                error=turn.get("error")
                print(f"\n[Turn failed] {error}")
            print()
            turn_finished.set()

        elif method == "codex/event/exec_command_begin":
            msg=event.get("params",{}).get("msg",{})
            command=msg.get("command","")
            print(f"\n[Command] {command}")

        elif method == "codex/event/exec_command_end":
            msg=event.get("params",{}).get("msg",{})
            output=msg.get("output","")
            exit_code=msg.get("exit_code")
            print(f"\n[Exit Code] {exit_code}")

            if output:
                print(output)
        
        elif method == "codex/event/error":
            print(f"\n[Codex Error] {event}")
        
    client.on_event(handle_event)
    
    try:
        await client.connect()
        thread_id=await client.create_thread()
        print("Connected.")
        print("Thread: ",thread_id)
        print("Type 'exit' to quit.")

        while True:
            text=await asyncio.to_thread(input, "You> ")
            text=text.strip()

            if not text:
                continue

            if text.lower() in {"exit", "quit"}:
                break

            turn_finished.clear()
            print("Codex> ", end="", flush=True)

            try:
                await client.send_message(thread_id, text)
                await asyncio.wait_for(turn_finished.wait(), timeout=300.0)
            
            except asyncio.TimeoutError:
                print(
                    "\n[Turn Timeout] "
                    "No turn/completed event received."
                      )
            
            except Exception as error:
                print(f"\n[Request failed] {error}")
    
    finally:
        await client.close()
        print("Disconnected.")


if __name__=="__main__":
    asyncio.run(main())
