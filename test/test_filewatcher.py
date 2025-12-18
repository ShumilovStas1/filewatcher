import shutil
import time
from queue import Queue

from src.filewatcher import FileWatcher
from src.filewatcher import Event

def test_file_creation(tmp_path):
    q: Queue[Event] = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    with open(tmp_path / "testfile.txt", "w") as f:
        pass
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events: list[Event] = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "created"
    assert events[0].src_path == str(tmp_path / "testfile.txt")


def test_dir_creation(tmp_path):
    q: Queue = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    (tmp_path / "new_dir").mkdir()
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "created"
    assert events[0].src_path == str(tmp_path / "new_dir")

def test_file_modification(tmp_path):
    with open(tmp_path / "modified.txt", "w") as f:
        pass
    q: Queue = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()

    with open(tmp_path / "modified.txt", "a") as f:
        f.write("test")
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "modified"
    assert events[0].src_path == str(tmp_path / "modified.txt")

def test_file_deletion(tmp_path):
    with open(tmp_path / "to_delete.txt", "w") as f:
        pass
    q: Queue = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    (tmp_path / "to_delete.txt").unlink()
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "deleted"
    assert events[0].src_path == str(tmp_path / "to_delete.txt")

def test_dir_deletion(tmp_path):
    (tmp_path / "to_delete_dir").mkdir()
    q: Queue = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    (tmp_path / "to_delete_dir").rmdir()
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events: list[Event] = list(q.queue)
    print("Events:", events)
    assert len(events) == 1
    assert events[0].type == "deleted"
    assert events[0].src_path == str(tmp_path / "to_delete_dir")

def test_file_move(tmp_path):
    (tmp_path / "2").mkdir()
    (tmp_path / "1").mkdir()
    with open(tmp_path / "1/to_move.txt", "w") as f:
        pass
    q: Queue[Event] = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    shutil.move(tmp_path / "1/to_move.txt", tmp_path /"2/to_move.txt")
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "moved"
    assert events[0].src_path == str(tmp_path / "1/to_move.txt")
    assert events[0].dest_path == str(tmp_path / "2/to_move.txt")

def test_dir_move(tmp_path):
    (tmp_path / "2").mkdir()
    (tmp_path / "1").mkdir()
    q: Queue = Queue()
    watcher = FileWatcher(q, [tmp_path])
    watcher.start()
    shutil.move(tmp_path / "2", tmp_path /"1")
    wait_for_events(q, expected_count=1)
    watcher.stop()
    events = list(q.queue)
    assert len(events) == 1
    assert events[0].type == "moved"
    assert events[0].src_path == str(tmp_path / "2")
    assert events[0].dest_path == str(tmp_path / "1/2")

# def test_dir_change_permissions(tmp_path):
#     os.mkdir(tmp_path / "perm_dir")
#     q: Queue = Queue()
#     watcher = Watcher(q, [tmp_path])
#     watcher.start()
#     os.chmod(tmp_path / "perm_dir", 0o777)
#     wait_for_events(q, expected_count=1)
#     watcher.stop()
#     events = list(q.queue)
#     assert len(events) == 1
#     assert isinstance(events[0], DirModifiedEvent)


def wait_for_events(queue, expected_count, timeout=2.0):
    start = time.time()
    while time.time() - start < timeout:
        if queue.qsize() >= expected_count:
            return
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for {expected_count} events")

