from queue import Queue
from threading import Thread
import socketio

from .filewatcher import FileWatcher, Event
import logging


log = logging.getLogger(__name__)

def register_event_handlers(sio: socketio.Server, watcher: FileWatcher):
    @sio.event
    def connect(sid, environ):
        log.info(f"Client connected: {sid}")
        sio.emit("dirs", to=sid, data=watcher.get_dirs())

    @sio.event
    def disconnect(sid):
        log.info(f"Client disconnected: {sid}")

    @sio.event
    def message(sid, data):
        log.info(f"Message from {sid}: {data}")
        sio.emit('reply', f"Received: {data}", to=sid)

def create_app(watch_dirs: list[str]) -> dict:
    sio = socketio.Server(async_mode='threading', cors_allowed_origins='*')
    app = socketio.WSGIApp(sio)

    fs_queue: Queue[Event] = Queue(maxsize=1000)
    watcher = FileWatcher(fs_queue, watch_dirs)

    register_event_handlers(sio, watcher)

    def event_sender():
        while True:
            event: Event= fs_queue.get()
            log.info(f"sending broadcast event: {event}")
            sio.emit("fs_event", event.to_dict())

    def start_event_sender_worker():
        Thread(target=event_sender, daemon=True).start()

    return {
        "app": app,
        "sio": sio,
        "watcher": watcher,
        "fs_queue": fs_queue,
        "start_background_worker": start_event_sender_worker
    }


