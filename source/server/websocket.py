import uuid
import asyncio
from fastapi import FastAPI
import socketio

# ...existing code...
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, static_files={})
app.mount("/", socket_app)

# In-memory sessions: {session_id: {"state": {...}, "ops": [...]}}
SESSIONS: dict = {}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def create_session(sid, data):
    session_id = str(uuid.uuid4())[:8]
    SESSIONS[session_id] = {"state": {"nodes": [], "links": []}, "ops": []}
    await sio.save_session(sid, {"session": session_id})
    await sio.enter_room(sid, session_id)
    await sio.emit("session_created", {"session": session_id, "state": SESSIONS[session_id]["state"]}, to=sid)
    print(f"Session created: {session_id} by {sid}")

@sio.event
async def join_session(sid, data):
    session_id = data.get("session")
    if session_id not in SESSIONS:
        await sio.emit("error", {"msg": "session_not_found"}, to=sid)
        return
    await sio.save_session(sid, {"session": session_id})
    await sio.enter_room(sid, session_id)
    # send current state only to new joiner
    await sio.emit("session_state", {"session": session_id, "state": SESSIONS[session_id]["state"]}, to=sid)
    await sio.emit("peer_joined", {"sid": sid}, room=session_id, skip_sid=sid)
    print(f"{sid} joined {session_id}")

@sio.event
async def op(sid, data):
    """
    Generic operation broadcast.
    Expected `data` shape:
      { "session": "<id>", "op": {"type":"add_node", ...} }
    """
    session_id = data.get("session")
    if session_id not in SESSIONS:
        await sio.emit("error", {"msg": "session_not_found"}, to=sid)
        return
    op = data.get("op")
    # persist op for simple history (naive)
    SESSIONS[session_id]["ops"].append(op)
    # broadcast to others in room
    await sio.emit("op", {"op": op}, room=session_id, skip_sid=sid)

# lightweight HTTP endpoint (optional) to list sessions
@app.get("/sessions")
async def list_sessions():
    return {"sessions": list(SESSIONS.keys())}