import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from hub.session import AgentSession
from hub import protocol


session=AgentSession("ws://localhost:8765/ws")


@asynccontextmanager
async def lifespan(app:FastAPI):
    await session.start()

    try:
        yield

    finally:
        await session.stop()


app=FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "ok":session.status != "disconnected",
        "status":session.status,
        "threadId":session.thread_id,
        "clients":len(session.clients),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept()
    await session.add_client(websocket)

    try:
        while True:
            message=await websocket.receive_json()
            message_type=message.get("type")
            if message_type=="message.send":
                text=message.get("text","")
                try:
                    await session.send_message(text)
                except ValueError as error:
                    await websocket.send_json(
                        protocol.error_message(
                            "INVALID_MESSAGE",
                            str(error),
                        )
                    )
                except RuntimeError as error:
                    await websocket.send_json(
                        protocol.error_message(
                            "SESSION_BUSY",
                            str(error),
                        )
                    )

            elif message_type=="status.get":
                await websocket.send_json(
                    protocol.status_changed(session.status)
                )

            elif message_type=="ping":
                await websocket.send_json(protocol.ping())

            else:
                await websocket.send_json(
                    protocol.error_message(
                        "UNKNOWN_MESSAGE",
                        f"Unknown type: {message_type}"
                    )
                )
                
    except WebSocketDisconnect:
        pass

    finally:
        session.remove_client(websocket)
