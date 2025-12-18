import logging
import os

from watchdog.events import FileSystemEventHandler, \
    DirModifiedEvent, FileModifiedEvent, DirDeletedEvent, FileDeletedEvent, DirCreatedEvent, \
    FileCreatedEvent, DirMovedEvent, FileMovedEvent, FileSystemEvent
from watchdog.observers import Observer
from queue import Queue, Full

log = logging.getLogger(__name__)

class Event:
    def __init__(self,
                 event_type: str,
                 root_path: str,
                 src_path: str,
                 is_dir: bool,
                 dest_path: str | None = None):
        self.event_type = event_type
        self.root_path = root_path
        self.src_path = src_path
        self.is_dir = is_dir
        self.dest_path = dest_path

    def to_dict(self):
        event_dict = {
            "type": self.event_type,
            "root_path": self.root_path,
            "src_path": self.src_path,
            "is_dir": self.is_dir
        }
        if self.dest_path:
            event_dict["dest_path"] = self.dest_path
        return event_dict

    def __str__(self):
        return f"type: {self.event_type}, src_path: {self.src_path}, is_dir: {self.is_dir}"
    __repr__ = __str__

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, queue: Queue, root_path: str):
        self.queue = queue
        self.root_path = root_path

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        log.info(f"Moving detected: {event}")
        self._put_event(event, "moved")

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        log.info(f"Creation detected: {event}")
        self._put_event(event, "created")

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        log.info(f"Deletion detected: {event}")
        self._put_event(event, "deleted")

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            log.info(f"Modification detected: {event}")
            self._put_event(event, "modified")

    def _put_event(self, event: FileSystemEvent, event_type: str):
        src_rel_path = os.path.relpath(event.src_path, self.root_path)
        dest_rel_path = None
        if event.dest_path:
            dest_rel_path = os.path.relpath(event.dest_path, self.root_path)
        try:
            event_obj = Event(event_type=event_type, src_path=src_rel_path,
                              is_dir=event.is_directory, dest_path=dest_rel_path, root_path=self.root_path)
            self.queue.put(event_obj, timeout=0.2)
        except Full:
            log.warning(f"Event queue is full, dropping event {event}")



class FileWatcher:
    def __init__(self, queue: Queue[Event], path_list: list[str]):
        self.path_list = path_list
        self.queue = queue
        self.observer: Observer | None = None

    def start(self):
        log.info(f"Starting watcher on paths: {self.path_list}")
        self.observer = Observer()
        self.observer.daemon = True
        for valid_path in self.path_list:
            self.observer.schedule(FileEventHandler(self.queue, valid_path), valid_path, recursive=True)
        self.observer.start()

    def stop(self):
        log.info("Stopping watcher...")
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def get_dirs(self):
        return list(self.path_list)