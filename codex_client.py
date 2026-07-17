import asyncio
import json
from typing import Any, Callable, Optional
import websockets

class CodexClient:
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.ws = None
        self.connected: bool = False
        self.current_thread_id: str | None = None
        self.current_turn_id: str | None = None
        self.next_id = 1
        self.pending:dict[int, asyncio.Future] = {}
        self.handlers:list[Callable[[dict[str, Any]], None]] = []
        self.recv_task: asyncio.Task | None = None


    async def connect(self):
        if self.connected:
            return
        try:
            self.ws=await websockets.connect(self.uri)
            self.connected=True
            self.recv_task=asyncio.create_task(self._recv_loop())
            await self.initialize()
        except Exception:
            await self.close()
            raise


    async def close(self):
        ws = self.ws
        recv_task = self.recv_task
        self.connected = False

        if ws:
            try:
                await ws.close()

            except websockets.ConnectionClosed:
                pass

        if (
            recv_task is not None 
            and recv_task is not asyncio.current_task()
            and not recv_task.done()
        ):
            try:
                await asyncio.wait_for(recv_task,timeout=2.0)

            except asyncio.TimeoutError:
                recv_task.cancel()
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass

            except asyncio.CancelledError:
                pass
        
        self._fail_pending(ConnectionError("Codex Websocket connection closed."))

        self.ws = None
        self.recv_task = None
        self.current_thread_id = None
        self.current_turn_id = None
    
   
    def on_event(self, handler: Callable[[dict[str, Any]], None]):
        self.handlers.append(handler)


    async def request(self,method:str, params:dict[str, Any], timeout: float=60.0) -> dict[str, Any]:
        if self.ws is None or not self.connected:
            raise RuntimeError("Client is not connected")
        
        request_id = self.next_id
        self.next_id += 1
        future=asyncio.get_running_loop().create_future()
        self.pending[request_id] = future

        payload={
            "id": request_id,
            "method": method,
            "params": params
        }

        try:
            await self.ws.send(json.dumps(payload, ensure_ascii=False))
            return await asyncio.wait_for(future,timeout=timeout)
        
        except asyncio.TimeoutError as error:
            raise TimeoutError(f"Request timed out: {method}") from error
        
        finally:
            self.pending.pop(request_id,None)


    async def initialize(self):
        return await self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "pocket-agent",
                    "version": "1.0.0"
                }
            },
        )


    async def create_thread(
            self,
            cwd: Optional[str] = None,
            model: Optional[str] = None,
            approval_policy: Optional[str] = None,
            sandbox: Optional[str] = None,
    ) -> str:
        params: dict[str, Any] = {}

        if cwd is not None:
            params["cwd"] = cwd
        if model is not None:
            params["model"] = model
        if approval_policy is not None:
            params["approvalPolicy"] = approval_policy
        if sandbox is not None:
            params["sandbox"] = sandbox
        
        response = await self.request("thread/start", params)
        self.current_thread_id = response["result"]["thread"]["id"]
        return self.current_thread_id
    

    async def send_message(self, thread_id:str, text:str):
        response = await self.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [
                    {
                        "type": "text",
                        "text": text
                    }
                ],
            },
        )
        self.current_turn_id = response["result"]["turn"]["id"]
        return response
    

    async def interrupt_turn(self, thread_id:str):
        return await self.request(
            "turn/interrupt",
            {
                "threadId": thread_id
            },
        )
    

    async def steer_turn(self, thread_id:str, text:str):
        return await self.request(
            "turn/steer",
            {
                "threadId": thread_id,
                "input": [
                    {
                        "type": "text",
                        "text": text
                    }
                ],
            },
        )
    

    def _fail_pending(self,error:Exception):
        for future in list(self.pending.values()):
            if not future.done():
                future.set_exception(error)
        
        self.pending.clear()
    

    async def _recv_loop(self):
        ws=self.ws
        assert ws is not None

        try:
            while True:
                raw=await ws.recv()
                data=json.loads(raw)

                if "id" in data and data["id"] in self.pending:
                    request_id=data["id"]
                    future=self.pending.pop(request_id,None)

                    if future is None:
                        continue

                    if future.done():
                        continue

                    if "error" in data:
                        future.set_exception(RuntimeError(data["error"]))
                    else:
                        future.set_result(data)

                    continue

                method = data.get("method")
                if method is None:
                    continue
                
                if method == "turn/completed":
                    self.current_turn_id = None

                for handler in self.handlers:
                    try:
                        handler(data) 
                    except Exception as error:
                        print("event handler error: ", error)                                 
        
        except websockets.ConnectionClosed:
            pass

        except asyncio.CancelledError:
            raise

        except Exception as e:
            print("recv_loop error:", e)

        finally:
            self.connected = False
            if self.ws is ws:
                self.ws = None
            self.current_turn_id = None
            self._fail_pending(ConnectionError("Websocket connection closed"))