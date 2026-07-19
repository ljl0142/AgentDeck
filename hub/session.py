import asyncio
import json
from typing import Any

from codex_client import CodexClient
from hub import protocol


class AgentSession:
    def __init__(self,codex_uri="ws://localhost:8765/ws"):
        self.codex=CodexClient(codex_uri)
        self.thread_id:str | None=None
        self.status="disconnected"
        self.clients:set[Any]=set()


    async def start(self) -> None:
        self.status="connecting"
        self.codex.on_event(self.handle_codex_event)
        await self.codex.connect()
        self.thread_id=await self.codex.create_thread()
        self.status="idle"


    async def stop(self) -> None:
        await self.codex.close()
        self.status="disconnected"


    async def _send(
            self,
            websocket:Any,
            payload:dict[str,Any]
    ) -> None:
        await websocket.send_json(payload)


    async def add_client(self,websocket:Any) -> None:
        self.clients.add(websocket)
        await self._send(websocket,protocol.session_ready(self.thread_id or ""))
        await self._send(websocket,protocol.status_changed(self.status))


    def remove_client(self,websocket:Any):
        self.clients.discard(websocket)


    async def send_message(self,text:str):
        if self.thread_id is None:
            raise RuntimeError("Session is not ready")
        
        if not text.strip():
            raise ValueError("Message cannot be empty")
        
        if self.status=="active":
            raise RuntimeError("Another turn is active")
        
        self.status="active"
        
        await self.broadcast(protocol.message_sent(text))
        await self.broadcast(protocol.status_changed("active"))

        try:
            await self.codex.send_message(self.thread_id,text)

        except Exception as error:
            self.status="error"

            await self.broadcast(
                protocol.error_message(
                    "CODEX_REQUEST_FAILED",
                    str(error),
                )
            )

            await self.broadcast(
                protocol.status_changed("error")
            )
            
            raise


    def handle_codex_event(self,event:dict[str,Any]):
        asyncio.create_task(self._process_codex_event(event))


    async def _process_codex_event(self,event:dict[str,Any]) -> None:
        method=event.get("method","")
        params=event.get("params",{})
        msg=params.get("msg",{})

        if method=="codex/event/agent_message_content_delta":
            delta=params.get("msg", {}).get("delta", "")
            if delta:
                await self.broadcast(protocol.message_delta(delta))

        elif method=="codex/event/exec_command_begin":
            await self.broadcast(protocol.command_started(msg.get("command")))

        elif method=="codex/event/exec_command_end":
            await self.broadcast(
                protocol.command_completed(
                    msg.get("exit_code"),
                    msg.get("output"),
                    )
                )
            
        elif method=="turn/completed":
            turn=params.get("turn",{})
            turn_status=turn.get("status","unknown")
            error=turn.get("error")
            self.status=("idle" if turn_status=="completed" else "error")
            await self.broadcast(protocol.turn_completed(turn_status,error))
            await self.broadcast(protocol.status_changed(self.status))

        elif method=="codex/event/error":
            await self.broadcast(
                protocol.error_message(
                    "CODEX_ERROR",
                    json.dumps(event,ensure_ascii=False)
                )
            )


    async def broadcast(self,payload:dict[str,Any]) -> None:
        dead_clients=[]

        for websocket in list(self.clients):
            try:
                await self._send(websocket,payload)
            except Exception:
                dead_clients.append(websocket)
        
        for websocket in dead_clients:
            self.clients.discard(websocket)


