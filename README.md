# AgentDeck

A lightweight control deck for AI coding agents.

Connect to Codex, Claude Code, Gemini CLI and other agent runtimes from anywhere — terminal, web browser or handheld devices.

## Ongoing Phase
Connect to codex and use cardputer as a light client.

## Start up AgentDeck

- Start up Codex App Server
```
codex app-server --listen ws://0.0.0.0:8765
```

- Start up Agent Hub
```
python -m uvicorn hub.server:app --host 127.0.0.1 --port 8000
```

- Start up test client
```
python -m examples.hub_client.py
```