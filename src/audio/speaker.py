# Source - https://stackoverflow.com/a
# Posted by Sachin Hosmani
# Retrieved 2026-01-18, License - CC BY-SA 4.0

import threading
import queue
import subprocess
import time
import os
import sys

class TextToSpeechManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def add_to_queue(self, phrase):
        self.queue.put(phrase)

    def _process_queue(self):
        while True:
            phrase = self.queue.get()
            if phrase is None:
                break
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "speak.py")

            subprocess.call([sys.executable, script_path,phrase])
            self.queue.task_done()

    def stop(self):
        self.queue.put(None)
        self.thread.join()

if __name__ == "__main__":
    tts_manager = TextToSpeechManager()

    # add stuff you want spoken into the queue
    tts_manager.add_to_queue("Hello, this is the first message.")
    tts_manager.add_to_queue("Here's the second message.")
    tts_manager.add_to_queue("And finally, the third message.")

    # Simulate some other work in parallel
    for i in range(50):
        print(f"Main program doing work {i+1}...")
        time.sleep(1)

    tts_manager.stop()
