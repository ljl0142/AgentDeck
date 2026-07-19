import json
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from hub.session import AgentSession
from hub import protocol


session=AgentSession("ws://localhost:8765/ws")

AGENTDECK_TOKEN=os.getenv("AGENTDECK_TOKEN")
if not AGENTDECK_TOKEN:
    raise RuntimeError("AGENTDECK_TOKEN environment variable is not set")


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
    authenticated=False

    try:
        while True:
            message=await websocket.receive_json()
            message_type=message.get("type")

            if not authenticated:
                if message_type!="auth.login":
                    await websocket.send_json(
                        protocol.error_message(
                            "AUTH_REQUIRED",
                            "Authentication is required",
                        )
                    )
                    continue

                token=message.get("token")

                if not isinstance(token,str) or not token:
                    await websocket.send_json(
                        protocol.error_message(
                             "INVALID_MESSAGE",
                            "token must be a non-empty string",
                        )
                    )
                    continue

                if not secrets.compare_digest(token,AGENTDECK_TOKEN):
                    await websocket.send_json(
                        protocol.error_message(
                            "AUTH_FAILED",
                            "Invalid token",
                        )
                    )
                    await websocket.close(code=1008,reason="Authentication failed")
                    return
                
                authenticated=True

                await websocket.send_json(protocol.auth_ready())
                await session.add_client(websocket)

                continue

            if message_type=="auth.login":    
                await websocket.send_json(
                    protocol.error_message(
                        "ALREADY_AUTHENTICATED",
                        "Client is already authenticated",
                    )
                )

            elif message_type=="message.send":
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
                await websocket.send_json(protocol.pong())

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
        if authenticated:
            session.remove_client(websocket)
