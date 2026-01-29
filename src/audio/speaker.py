import threading
import queue
import pyttsx3 

class TextToSpeechManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def add_to_queue(self, phrase):
        if phrase:
            self.queue.put(phrase)

    def _process_queue(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 140)
            engine.setProperty('volume', 1.0)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)
        except Exception as e:
            print(f"[TTS] Błąd inicjalizacji silnika: {e}")
            return

        while True:
            phrase = self.queue.get()
            if phrase is None:
                break

            try:
                engine.say(phrase)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS] Błąd odtwarzania: {e}")

            self.queue.task_done()

    def stop(self):
        self.queue.put(None)
        self.thread.join()