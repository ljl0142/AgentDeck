from typing import Any

#WEB -> HUB
def message_send(text:str) -> dict[str,Any]:
    return {
        "type":"message.send",
        "text":text,
    }


def status_get() -> dict[str,Any]:
    return {
        "type":"status.get",
    }


def ping() -> dict[str,Any]:
    return {
        "type":"ping",
    }

#HUB -> WEB
def session_ready(thread_id:str) -> dict[str,Any]:
    return {
        "type":"session.ready",
        "threadId":thread_id,
    }


def status_changed(status:str) -> dict[str,Any]:
    return {
        "type":"status.changed",
        "status":status,
    }


def message_delta(text:str) -> dict[str,Any]:
    return {
        "type":"message.delta",
        "text":text,
    }


def command_started(command:Any) -> dict[str,Any]:
    return {
        "type":"command.started",
        "command":command
    }


def command_completed(
        exit_code: int | None,
        output:str
) -> dict[str,Any]:
    return {
        "type":"command.completed",
        "exitCode":exit_code,
        "output":output,
    }


def turn_completed(
        status:str,
        error:Any=None,
) -> dict[str,Any]:
    return {
        "type":"turn.completed",
        "status":status,
        "error":error,
    }


def error_message(
        code:str,
        message:str,
) -> dict[str,Any]:
    return {
        "type":"error",
        "code":code,
        "message":message,
    }
