import socketio
import threading
import queue
import time
import dearpygui.dearpygui as dpg
from typing import Any

sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)
_incoming: "queue.Queue[dict]" = queue.Queue()

class SocketClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self._thread = None
        self._connected_evt = threading.Event()
        self._pending = []  # buffer emits until connected
        self._stop = threading.Event()

    def start(self):
        """Start the socket client in a background thread."""
        def _run():
            try:
                # try websocket first, fall back to polling if needed
                sio.connect(self.server_url, transports=["websocket", "polling"])
                # wait for events
                sio.wait()
            except Exception as e:
                print("Socket client thread stopped:", e)
            finally:
                self._connected_evt.clear()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        # small delay to allow initial connect attempt
        time.sleep(0.1)

    def stop(self):
        self._stop.set()
        try:
            sio.disconnect()
        except Exception:
            pass

    def _emit_or_buffer(self, event: str, payload: dict):
        if self._connected_evt.is_set():
            try:
                sio.emit(event, payload)
            except Exception as e:
                print("Emit failed, buffering:", e)
                self._pending.append((event, payload))
        else:
            self._pending.append((event, payload))

    def _flush_pending(self):
        while self._pending and self._connected_evt.is_set():
            event, payload = self._pending.pop(0)
            try:
                sio.emit(event, payload)
            except Exception as e:
                print("Failed flushing pending emit, re-queueing:", e)
                self._pending.insert(0, (event, payload))
                break

    def create_session(self):
        self._emit_or_buffer("create_session", {})

    def join_session(self, session_id: str):
        self._emit_or_buffer("join_session", {"session": session_id})

    def emit_op(self, session_id: str, op: dict):
        self._emit_or_buffer("op", {"session": session_id, "op": op})

    def poll(self, editor: Any):
        """
        Call this periodically on the main (DearPyGui) thread.
        Applies received ops to the local UI. Keep handlers minimal and thread-free.
        """
        while not _incoming.empty():
            msg = _incoming.get_nowait()
            if msg.get("type") == "op":
                op = msg["op"]
                typ = op.get("type")
                if typ == "add_node":
                    node_type = op.get("node_type")
                    for sub in editor.submodules:
                        if getattr(sub, "name", "") == node_type:
                            sub.initialize(parent=editor.tag)
                            break
                elif typ == "delete_node":
                    node_id = op.get("node_id")
                    try:
                        dpg.delete_item(node_id)
                    except Exception:
                        pass
                else:
                    print("Received unhandled op:", op)
            elif msg.get("type") == "session_state":
                state = msg["state"]
                print("Remote session state received (not automatically applied):", state)
            else:
                print("Unknown message:", msg)

# Socket.IO handlers put messages into the queue
@sio.event
def connect():
    print("socket connected")
    # mark connected and flush any pending emits
    try:
        SocketClient_instance = None
        # set event via stored client if available — simplistic: set global event via last-started instance
    except Exception:
        pass
    # if multiple instances exist, each will set its own event; here we set the module-level event by scanning threads
    # simpler: rely on handler below to set connected by searching active client objects when you integrate.

@sio.event
def disconnect():
    print("socket disconnected")
    # signal connection lost to any client instance by clearing events
    # actual instance event clearing is handled by thread finalizer

@sio.on("session_created")
def on_session_created(data):
    _incoming.put({"type": "session_state", "state": data})

@sio.on("session_state")
def on_session_state(data):
    _incoming.put({"type": "session_state", "state": data.get("state")})

@sio.on("op")
def on_op(data):
    _incoming.put({"type": "op", "op": data.get("op")})