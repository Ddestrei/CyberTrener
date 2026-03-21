import queue
import threading
import time

from src.audio.listener import ExerciseListener
from src.audio.speaker import TextToSpeechManager


class StateManager(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.is_plank = 0
        self.is_sit_ups = 0
        self.is_bicep_curl = 0
        self.is_lateral_raise = 0
        self.is_press = 0
        self.is_start = 0
        self.is_end = 0
        self.is_reset = 0
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.last_spoken_word = "Brak"
        self.reps = 0
        self.is_tracking = False
        self.tts_manager = TextToSpeechManager()
        self.listener = ExerciseListener(self.queue)
        self.listener.start()

    def update_word(self, word):
        self.last_spoken_word = word

    def run(self):
        while True:
            cmd = self.queue.get()
            with self.lock:
                if cmd in ["plank", "sit ups", "bicep curl", "lateral raise", "press"]:
                    self.last_spoken_word = cmd
                    if cmd == "plank":
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a plank exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.is_plank = 1
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 0
                    elif cmd == "sit ups":
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a sit ups exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.is_plank = 0
                        self.is_sit_ups = 1
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 0
                    elif cmd == "bicep curl":
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a bicep curl exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 1
                        self.is_lateral_raise = 0
                        self.is_press = 0
                    elif cmd == "lateral raise":
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a lateral raise exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 1
                        self.is_press = 0
                    elif cmd == "press":
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a overhead press exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 1

                elif cmd == "start":
                    self.reps = 0
                    self.listener.sleep = 1
                    self.tts_manager.add_to_queue('Start the exercise')
                    time.sleep(10)
                    self.listener.sleep = 0
                    self.is_tracking = True

                elif cmd == "end":
                    self.listener.sleep = 1
                    self.tts_manager.add_to_queue('Stop the exercise')
                    time.sleep(10)
                    self.listener.sleep = 0
                    self.is_tracking = False

                elif cmd == "reset":
                    self.reps = 0
                    self.is_reset = 1

                elif cmd == "previous":
                    if self.is_plank:
                        self.is_plank = 0
                        self.is_press = 1
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a press exercise')
                        self.last_spoken_word = 'press'
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_sit_ups:
                        self.is_sit_ups = 0
                        self.is_plank = 1
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a plank exercise')
                        self.last_spoken_word = 'plank'
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_bicep_curl:
                        self.is_bicep_curl = 0
                        self.is_sit_ups = 1
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a sit ups exercise')
                        self.last_spoken_word = 'sit ups'
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_lateral_raise:
                        self.is_lateral_raise = 0
                        self.is_bicep_curl = 1
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a bicep curl exercise')
                        self.last_spoken_word = 'bicep curl'
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_press:
                        self.is_press = 0
                        self.is_lateral_raise = 1
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a lateral raise exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                        self.last_spoken_word = 'lateral raise'

                elif cmd == "next":
                    if self.is_plank:
                        self.is_plank = 0
                        self.is_sit_ups = 1
                        self.last_spoken_word = 'sit ups'
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a sit ups exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_sit_ups:
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 1
                        self.last_spoken_word = 'bicep curl'
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a bicep curl exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_bicep_curl:
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 1
                        self.last_spoken_word = 'lateral raise'
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a lateral raise exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_lateral_raise:
                        self.is_lateral_raise = 0
                        self.is_press = 1
                        self.last_spoken_word = 'press'
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a overhead press exercise')
                        time.sleep(10)
                        self.listener.sleep = 0
                    elif self.is_press:
                        self.is_press = 0
                        self.is_plank = 1
                        self.last_spoken_word = 'plank'
                        self.listener.sleep = 1
                        self.tts_manager.add_to_queue('You are doing a plank exercise')
                        time.sleep(10)
                        self.listener.sleep = 0