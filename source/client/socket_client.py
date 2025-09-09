import socketio
import threading
import queue
import time
import dearpygui.dearpygui as dpg
from typing import Any, Optional
from source.nodes.core import update, Link

sio = socketio.Client(reconnection=True, logger=False, engineio_logger=False)
_incoming: "queue.Queue[dict]" = queue.Queue()

# Keep a reference to the most recently started client so the sio handlers
# can mark it connected/disconnected and flush pending emits.
CURRENT_CLIENT: Optional["SocketClient"] = None

class SocketClient:
    def __init__(self, server_url: str = "http://192.168.1.90:8000"):
        self.server_url = server_url
        self._thread = None
        self._connected_evt = threading.Event()
        self._pending = []  # buffer emits until connected
        self._stop = threading.Event()

    def start(self):
        """Start the socket client in a background thread."""
        global CURRENT_CLIENT
        CURRENT_CLIENT = self
        print(f"[SocketClient] Starting client, connecting to {self.server_url}...")

        def _run():
            try:
                # try websocket first, fall back to polling if needed
                print("[SocketClient._run] Attempting sio.connect()")
                sio.connect(self.server_url, transports=["websocket", "polling"])
                print("[SocketClient._run] sio.connect() returned, entering sio.wait()")
                # wait for events
                sio.wait()
                print("[SocketClient._run] sio.wait() finished")
            except Exception as e:
                print("[SocketClient._run] Socket client thread stopped with exception:", e)
            finally:
                self._connected_evt.clear()
                print("[SocketClient._run] Connection event cleared, thread exiting")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        # small delay to allow initial connect attempt
        time.sleep(0.1)
        print("[SocketClient] Background thread started")

    def stop(self):
        global CURRENT_CLIENT
        print("[SocketClient] Stopping client...")
        self._stop.set()
        if CURRENT_CLIENT is self:
            CURRENT_CLIENT = None
        try:
            sio.disconnect()
            print("[SocketClient] sio.disconnect() called")
        except Exception as e:
            print("[SocketClient] Exception on disconnect:", e)

    def _emit_or_buffer(self, event: str, payload: dict):
        if self._connected_evt.is_set():
            try:
                print(f"[SocketClient] Emitting event '{event}' with payload: {payload}")
                sio.emit(event, payload)
            except Exception as e:
                print("[SocketClient] Emit failed, buffering:", e)
                self._pending.append((event, payload))
                print(f"[SocketClient] Buffered event '{event}' (pending count={len(self._pending)})")
        else:
            self._pending.append((event, payload))
            print(f"[SocketClient] Not connected: buffered event '{event}' (pending count={len(self._pending)})")

    def _flush_pending(self):
        if not self._pending:
            print("[SocketClient] No pending emits to flush")
            return
        print(f"[SocketClient] Flushing {len(self._pending)} pending emits...")
        while self._pending and self._connected_evt.is_set():
            event, payload = self._pending.pop(0)
            try:
                print(f"[SocketClient] Flushing event '{event}' with payload: {payload}")
                sio.emit(event, payload)
            except Exception as e:
                print("[SocketClient] Failed flushing pending emit, re-queueing:", e)
                self._pending.insert(0, (event, payload))
                break
        print(f"[SocketClient] Flush complete (remaining pending={len(self._pending)})")

    def create_session(self):
        print("[SocketClient] create_session() called")
        self._emit_or_buffer("create_session", {})

    def join_session(self, session_id: str):
        print(f"[SocketClient] join_session() called with session_id={session_id}")
        self._emit_or_buffer("join_session", {"session": session_id})

    def emit_op(self, session_id: str, op: dict):
        print(f"[SocketClient] emit_op() called for session={session_id} op={op}")
        self._emit_or_buffer("op", {"session": session_id, "op": op})

    def poll(self, editor: Any):
        """
        Call this periodically on the main (DearPyGui) thread.
        Applies received ops to the local UI. Keep handlers minimal and thread-free.
        """
        # Debug: Check if polling is being called
        queue_size = _incoming.qsize()
        if queue_size > 0:
            print(f"[SocketClient.poll] Called with {queue_size} messages in queue")

        processed = 0
        while not _incoming.empty():
            msg = _incoming.get_nowait()
            processed += 1
            print(f"[SocketClient.poll] Processing message {processed}: {msg}")
            if msg.get("type") == "session_created":
                # Store session ID in editor
                editor.session_id = msg.get("session_id")
                # Also store for operations
                editor.current_session_id = msg.get("session_id")
                print(f"[SocketClient.poll] Session created with ID: {editor.session_id}")
                # Show the session created dialog
                try:
                    editor._show_session_created_dialog()
                except Exception as e:
                    print(f"[SocketClient.poll] Failed to show session dialog: {e}")
            elif msg.get("type") == "op":
                op = msg["op"]
                typ = op.get("type")
                print(f"[SocketClient.poll] Processing op type='{typ}' op={op} (received_by={msg.get('received_by')})")
                if typ == "add_node":
                    node_type = op.get("node_type")
                    node_id = op.get("node_id")
                    pos = op.get("position")
                    for sub in editor.submodules:
                        if getattr(sub, "name", "") == node_type:
                            print(f"[SocketClient.poll] Initializing submodule for node_type='{node_type}' with node_id={node_id} pos={pos}")
                            try:
                                created = sub.initialize(parent=editor.tag, node_tag=node_id, pos=pos)
                                print(f"[SocketClient.poll] Created node (from op): {created}")
                            except TypeError:
                                created = sub.initialize(parent=editor.tag)
                                print(f"[SocketClient.poll] Fallback created node (from op): {created}")
                            break
                elif typ == "link_created":
                    src = op.get("source")
                    dst = op.get("target")
                    created_link = None
                    if isinstance(src, dict) and isinstance(dst, dict):
                        try:
                            def _resolve_endpoint(desc):
                                node_tag = desc.get("node")
                                idx = desc.get("index", 0)
                                # try direct existence
                                if not dpg.does_item_exist(node_tag):
                                    # try find by alias if needed
                                    for item in dpg.get_all_items():
                                        try:
                                            if dpg.get_item_alias(item) == node_tag:
                                                node_tag = item
                                                break
                                        except Exception:
                                            continue
                                if not dpg.does_item_exist(node_tag):
                                    raise RuntimeError(f"Node {desc.get('node')} not found locally")
                                children = dpg.get_item_info(node_tag)["children"][1]
                                if idx >= len(children):
                                    raise RuntimeError(f"Attribute index {idx} out of range for node {node_tag}")
                                return children[idx]

                            src_attr = _resolve_endpoint(src)
                            dst_attr = _resolve_endpoint(dst)
                            created_link = dpg.add_node_link(src_attr, dst_attr, parent=editor.tag)
                            update.node_links.append(Link(source=src_attr, target=dst_attr, id=int(created_link)))
                            print(f"[SocketClient.poll] Created remote link: {src} -> {dst} (attrs {src_attr}->{dst_attr})")
                        except Exception as e:
                            print(f"[SocketClient.poll] Failed to create remote link from descriptors {src} -> {dst}: {e}")
                    else:
                        print(f"[SocketClient.poll] Unexpected link payload shape: src={src} dst={dst}")

                elif typ == "link_deleted":
                    link_id = op.get("link_id")
                    if link_id:
                        try:
                            dpg.delete_item(link_id)
                            print(f"[SocketClient.poll] Deleted remote link: {link_id}")
                        except Exception as e:
                            print(f"[SocketClient.poll] Failed to delete remote link: {e}")
                elif typ == "delete_node":
                    node_id = op.get("node_id")
                    print(f"[SocketClient.poll] Deleting node id={node_id}")
                    # Resolve canonical id to actual item
                    target_item = node_id
                    if not dpg.does_item_exist(target_item):
                        # try find by alias
                        found = None
                        for item in dpg.get_all_items():
                            try:
                                if dpg.get_item_alias(item) == node_id:
                                    found = item
                                    break
                            except Exception:
                                continue
                        if found:
                            target_item = found

                    # Delete the item if exists
                    try:
                        if dpg.does_item_exist(target_item):
                            dpg.delete_item(target_item)
                            print(f"[SocketClient.poll] Deleted remote node item: {target_item}")
                        else:
                            print(f"[SocketClient.poll] Remote node {node_id} not present locally")
                    except Exception as e:
                        print(f"[SocketClient.poll] Exception deleting node {node_id}: {e}")

                    # Remove links referencing that node from local update.node_links
                    removed = []
                    for l in update.node_links[:]:
                        try:
                            src_parent = dpg.get_item_info(l.source)["parent"]
                        except Exception:
                            src_parent = None
                        try:
                            tgt_parent = dpg.get_item_info(l.target)["parent"]
                        except Exception:
                            tgt_parent = None

                        # compare with resolved target_item or alias
                        if src_parent == target_item or tgt_parent == target_item:
                            try:
                                dpg.delete_item(l.id)
                            except Exception:
                                pass
                            update.node_links.remove(l)
                            removed.append(l)
                    if removed:
                        print(f"[SocketClient.poll] Removed remote links due to node delete: {removed}")
                    # update path/output after structural change
                    try:
                        update.update_path()
                        update.update_output()
                    except Exception:
                        pass
                else:
                    print("[SocketClient.poll] Received unhandled op:", op)
            elif msg.get("type") == "session_state":
                state = msg["state"]
                print("[SocketClient.poll] Remote session state received (not automatically applied):", state)
                # Apply nodes from session state
                if "nodes" in state:
                    for node_data in state["nodes"]:
                        node_type = node_data.get("type")
                        node_id = node_data.get("id")
                        pos = node_data.get("position")
                        for sub in editor.submodules:
                            if getattr(sub, "name", "") == node_type:
                                print(f"[SocketClient.poll] Recreating node from session state: {node_type} id={node_id} pos={pos}")
                                try:
                                    created = sub.initialize(parent=editor.tag, node_tag=node_id, pos=pos)
                                    print(f"[SocketClient.poll] sub.initialize returned: {created}")
                                except TypeError:
                                    created = sub.initialize(parent=editor.tag)
                                    print(f"[SocketClient.poll] fallback initialize returned: {created}")
                                break

                # Apply links from session state
                if "links" in state:
                    for link_data in state["links"]:
                        source = link_data.get("source")
                        target = link_data.get("target")
                        if source and target:
                            try:
                                dpg.add_node_link(source, target, parent=editor.tag)
                                print(f"[SocketClient.poll] Recreated link from session state: {source} -> {target}")
                            except Exception as e:
                                print(f"[SocketClient.poll] Failed to recreate link from session state: {e}")
            else:
                print("[SocketClient.poll] Unknown message:", msg)
        if processed:
            print(f"[SocketClient.poll] Processed {processed} messages")

# Socket.IO handlers put messages into the queue
@sio.event
def connect():
    print("[sio] socket connected")
    try:
        # print our client id (socket sid) for debugging
        try:
            print(f"[sio] client sid = {sio.sid}")
        except Exception:
            print("[sio] client sid unavailable")
        if CURRENT_CLIENT is not None:
            # mark connected and flush any pending emits
            CURRENT_CLIENT._connected_evt.set()
            # flush pending emits immediately on connect
            CURRENT_CLIENT._flush_pending()
            print("[sio] marked CURRENT_CLIENT connected and flushed pending emits")
    except Exception as e:
        print("[sio] connect handler exception:", e)

@sio.event
def disconnect():
    print("[sio] socket disconnected")
    try:
        if CURRENT_CLIENT is not None:
            CURRENT_CLIENT._connected_evt.clear()
            print("[sio] cleared CURRENT_CLIENT connected event")
    except Exception as e:
        print("[sio] disconnect handler exception:", e)

@sio.on("session_created")
def on_session_created(data):
    print("[sio] on_session_created received:", data)
    session_id = data.get("session")
    # Store session ID for the editor
    _incoming.put({"type": "session_created", "session_id": session_id, "state": data.get("state")})

@sio.on("session_state")
def on_session_state(data):
    print("[sio] on_session_state received:", data)
    _incoming.put({"type": "session_state", "state": data.get("state")})

@sio.on("op")
def on_op(data):
    # include who received it (our sid) for easier debugging
    try:
        my_sid = getattr(sio, "sid", None)
    except Exception:
        my_sid = None
    print(f"[sio] on_op received (delivered to sid={my_sid}): {data}")
    print(f"[sio] Adding op to incoming queue: {data.get('op')}")
    print(f"[sio] Queue size before adding: {_incoming.qsize()}")
    _incoming.put({"type": "op", "op": data.get("op"), "received_by": my_sid})
    print(f"[sio] Queue size after adding: {_incoming.qsize()}")