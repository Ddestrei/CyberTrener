import queue
import threading
from src.audio.listener import ExerciseListener


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

        self.listener = ExerciseListener(self.queue)
        self.listener.start()

    def update_word(self, word):
        self.last_spoken_word = word

    def run(self):
        while True:
            cmd = self.queue.get()
            with (self.lock):
                if cmd in ["plank", "sit ups", "bicep curl", "lateral raise", "press"]:
                    self.last_spoken_word = cmd
                    if cmd == "plank":
                        self.is_plank = 1
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 0
                        pass
                    elif cmd == "sit ups":
                        self.is_plank = 0
                        self.is_sit_ups = 1
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 0
                        pass
                    elif cmd == "bicep curl":
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 1
                        self.is_lateral_raise = 0
                        self.is_press = 0
                        pass
                    elif cmd == "lateral raise":
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 1
                        self.is_press = 0
                        pass
                    elif cmd == "press":
                        self.is_plank = 0
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 0
                        self.is_press = 1
                        pass

                elif cmd == "start" and self.last_spoken_word != "Brak":
                    self.is_tracking = True

                elif cmd == "end":
                    self.is_tracking = False

                elif cmd == "reset":
                    self.reps = 0

                elif cmd == "previous":
                    if self.is_plank:
                        self.is_plank = 0
                        self.is_press = 1
                        self.last_spoken_word = 'press'
                    elif self.is_sit_ups:
                        self.is_sit_ups = 0
                        self.is_plank = 1
                        self.last_spoken_word = 'plank'
                    elif self.is_bicep_curl:
                        self.is_bicep_curl = 0
                        self.is_sit_ups = 1
                        self.last_spoken_word = 'sit ups'
                    elif self.is_lateral_raise:
                        self.is_lateral_raise = 0
                        self.is_bicep_curl = 1
                        self.last_spoken_word = 'bicep curl'
                    elif self.is_press:
                        self.is_press = 0
                        self.is_lateral_raise = 1
                        self.last_spoken_word = 'lateral raise'

                elif cmd == "next":
                    if self.is_plank:
                        self.is_plank = 0
                        self.is_sit_ups = 1
                        self.last_spoken_word = 'sit ups'
                    if self.is_sit_ups:
                        self.is_sit_ups = 0
                        self.is_bicep_curl = 1
                        self.last_spoken_word = 'bicep curl'
                    if self.is_bicep_curl:
                        self.is_bicep_curl = 0
                        self.is_lateral_raise = 1
                        self.last_spoken_word = 'lateral raise'
                    if self.is_lateral_raise:
                        self.is_lateral_raise = 0
                        self.is_press = 1
                        self.last_spoken_word = 'press'
                    if self.is_press:
                        self.is_press = 0
                        self.is_plank = 1
                        self.last_spoken_word = 'plank'