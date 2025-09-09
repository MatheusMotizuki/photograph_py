import uuid
import asyncio
from fastapi import FastAPI
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, static_files={})
app.mount("/", socket_app)

# In-memory sessions: {session_id: {"state": {...}, "ops": [...]}}
SESSIONS: dict = {}

@sio.event
async def connect(sid, environ):
    print(f"[connect] Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[disconnect] Client disconnected: {sid}")
    # try remove from any session mapping
    try:
        sock_sess = await sio.get_session(sid)
        session_id = sock_sess.get("session")
        if session_id and session_id in SESSIONS:
            if sid in SESSIONS[session_id].get("clients", []):
                SESSIONS[session_id]["clients"].remove(sid)
                print(f"[disconnect] Removed {sid} from session {session_id} clients")
    except Exception:
        pass

def _print_sessions_debug():
    print(f"[SESSIONS] total={len(SESSIONS)}")
    for s, data in SESSIONS.items():
        clients = data.get("clients", [])
        nodes = data.get("state", {}).get("nodes", [])
        links = data.get("state", {}).get("links", [])
        print(f" - session {s}: clients={clients} nodes={len(nodes)} links={len(links)}")

@sio.event
async def create_session(sid, data):
    print(f"[create_session] Requested by {sid} with data: {data}")
    session_id = str(uuid.uuid4())[:8]
    SESSIONS[session_id] = {"state": {"nodes": [], "links": []}, "ops": [], "clients": []}
    print(f"[create_session] Created session {session_id}, initial state: {SESSIONS[session_id]['state']}")
    await sio.save_session(sid, {"session": session_id})
    print(f"[create_session] Saved socket session for {sid} -> {session_id}")
    await sio.enter_room(sid, session_id)

    SESSIONS[session_id].setdefault("clients", [])
    if sid not in SESSIONS[session_id]["clients"]:
        SESSIONS[session_id]["clients"].append(sid)

    print(f"[create_session] {sid} entered room {session_id}")
    await sio.emit("session_created", {"session": session_id, "state": SESSIONS[session_id]["state"]}, to=sid)
    print(f"[create_session] Emitted session_created to {sid} for {session_id}")
    _print_sessions_debug()

@sio.event
async def join_session(sid, data):
    session_id = data.get("session")
    print(f"[join_session] {sid} trying to join session: {session_id}")
    if session_id not in SESSIONS:
        print(f"[join_session] session not found: {session_id}")
        await sio.emit("error", {"msg": "session_not_found"}, to=sid)
        return
    await sio.save_session(sid, {"session": session_id})
    print(f"[join_session] Saved socket session for {sid} -> {session_id}")
    await sio.enter_room(sid, session_id)

    SESSIONS[session_id].setdefault("clients", [])
    if sid not in SESSIONS[session_id]["clients"]:
        SESSIONS[session_id]["clients"].append(sid)

    print(f"[join_session] {sid} entered room {session_id}")
    # send current state only to new joiner
    await sio.emit("session_state", {"session": session_id, "state": SESSIONS[session_id]["state"]}, to=sid)
    print(f"[join_session] Sent session_state to {sid} for {session_id}")
    await sio.emit("peer_joined", {"sid": sid}, room=session_id, skip_sid=sid)
    print(f"[join_session] Notified peers in {session_id} about {sid}")
    print(f"[join_session] {sid} joined {session_id}")
    _print_sessions_debug()

@sio.event
async def op(sid, data):
    """
    Generic operation broadcast.
    Expected `data` shape:
      { "session": "<id>", "op": {"type":"add_node", ...} }
    """
    session_id = data.get("session")
    print(f"[op] Received from {sid}: session={session_id}, op={data.get('op')}")
    if session_id not in SESSIONS:
        print(f"[op] session not found: {session_id}")
        await sio.emit("error", {"msg": "session_not_found"}, to=sid)
        return
    op = data.get("op")

    # Update session state based on operation type
    if op.get("type") == "add_node":
        node_data = {
            "id": op.get("node_id"),
            "type": op.get("node_type"),
            "position": op.get("position", [0, 0])
        }
        SESSIONS[session_id]["state"]["nodes"].append(node_data)
        print(f"[op] Added node to session {session_id}: {node_data}")
    elif op.get("type") == "link_created":
        # store descriptors (node_tag/index) so peers can resolve locally
        link_data = {
            "source": op.get("source"),
            "target": op.get("target"),
            "id": op.get("link_id"),
        }
        SESSIONS[session_id]["state"]["links"].append(link_data)
        print(f"[op] Added link to session {session_id}: {link_data}")
    elif op.get("type") == "link_deleted":
        # Remove link from state
        links = SESSIONS[session_id]["state"]["links"]
        SESSIONS[session_id]["state"]["links"] = [l for l in links if l.get("id") != op.get("link_id")]
        print(f"[op] Removed link from session {session_id}: {op.get('link_id')}")
    elif op.get("type") == "delete_node":
        # Remove node and associated links
        node_id = op.get("node_id")
        nodes = SESSIONS[session_id]["state"]["nodes"]
        links = SESSIONS[session_id]["state"]["links"]
        SESSIONS[session_id]["state"]["nodes"] = [n for n in nodes if n.get("id") != node_id]
        SESSIONS[session_id]["state"]["links"] = [l for l in links if l.get("source") != node_id and l.get("target") != node_id]
        print(f"[op] Removed node from session {session_id}: {node_id}")

    # persist op for simple history (naive)
    SESSIONS[session_id]["ops"].append(op)
    print(f"[op] Appended op to session {session_id}. Total ops: {len(SESSIONS[session_id]['ops'])}")
    # broadcast to others in room
    await sio.emit("op", {"op": op}, room=session_id, skip_sid=sid)
    print(f"[op] Broadcast op to room {session_id}, skipped sender {sid}")
    _print_sessions_debug()

# lightweight HTTP endpoint (optional) to list sessions
@app.get("/sessions")
async def list_sessions():
    print(f"[HTTP] /sessions requested, returning {len(SESSIONS)} sessions")
    return {"sessions": list(SESSIONS.keys())}

@app.get("/sessions_with_clients")
async def list_sessions_with_clients():
    """Return sessions with connected client IDs (for debug)."""
    return {
        sid: {
            "state": SESSIONS[sid]["state"],
            "ops": len(SESSIONS[sid]["ops"]),
            "clients": list(SESSIONS[sid].get("clients", []))
        } for sid in SESSIONS
    }