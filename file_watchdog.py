import os
import re
import sys
import time
import json
import logging
import threading
from daemon import BaseDaemon
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

lock = threading.Lock()
last_change = None

class UpdateFileHandler(FileSystemEventHandler):
    def __init__(self, new_key_values):
        super().__init__()

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            global last_change
            if last_change:
                if (int(time.time()) - last_change) < 5:
                    return
            global lock
            lock.acquire()
            with open(event.src_path, "r+") as file_modified:
                file_content = file_modified.read()
                for key, value in new_key_values.items():
                    file_content = re.sub(key, value, file_content)
                last_change = int(time.time())
                file_modified.seek(0)
                file_modified.write(file_content)
                file_modified.truncate()
            lock.release()

class FileUpdaterDaemon(BaseDaemon):
    def __init__(self, pid_file, directoty_path, new_key_values):
        super().__init__(pid_file)
        self.directory_path = directory_path
        self.new_key_values = new_key_values

    def run(self):
        event_handler = UpdateFileHandler(self.new_key_values)
        observer = Observer()
        observer.schedule(event_handler, self.directory_path)
        observer.daemon = True
        observer.start()

        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    daemon_action = sys.argv[2]
    directory_path = sys.argv[2]
    new_key_values = json.loads(sys.argv[3])

    daemon = FileUpdaterDaemon("/tmp/fud.pid", directory_path, new_key_values)

    if "start":
        daemon.start()
    elif "stop":
        daemon.stop()
    elif "restart":
        daemon.restart()
    else:
        print("Unkown action")
        sys.exit(2)
        
    sys.exit(0)