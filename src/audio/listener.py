import sounddevice as sd
import speech_recognition as sr
import threading
import queue
import json
import time

# Spróbuj zaimportować Vosk, jeśli jest dostępny
try:
    from vosk import Model, KaldiRecognizer

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


class ExerciseListener(threading.Thread):
    def __init__(self,command_queue):
        super().__init__(daemon=True)
        self.queue = command_queue
        self.sleep = 0
        self.commands = [
            "start", "end", "next", "previous", "reset", "plank", "sit ups", "bicep curl", "lateral raise", "press"
        ]

        self.sample_rate = 16000  # <--- Definiujemy atrybut na samym początku

        if not self.check_microphone():
            print("!!! OSTRZEŻENIE: Nie wykryto podłączonego mikrofonu !!!")
        else:
            print("Mikrofon wykryty i gotowy.")

        if VOSK_AVAILABLE:
            try:
                self.vosk_model = Model("src/audio/vosk-model-small-en-us-0.15")

                # 2. OPTYMALIZACJA: Tworzymy filtr gramatyczny
                # Vosk będzie teraz ignorował słowa spoza tej listy (oraz [unk] dla nieznanych)
                grammar = json.dumps(self.commands + ["[unk]"])
                self.recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate, grammar)

                self.model_loaded = True
                print("Załadowano silnik offline z ograniczoną gramatyką.")
            except Exception as e:
                print(f"Błąd ładowania modelu: {e}")
                self.model_loaded = False

    def check_microphone(self):
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        return len(input_devices) > 0

    def run(self):
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               dtype='int16', channels=1) as stream:
            print("Nasłuchiwanie (tylko zdefiniowane komendy)...")
            while True:
                if self.sleep:
                    time.sleep(0.1)
                    continue

                data, _ = stream.read(4000)
                if self.model_loaded:
                    if self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "")

                        # Ponieważ mamy gramatykę, text będzie ALBO pusty,
                        # ALBO będzie zawierał dokładnie jedną z naszych komend.
                        if text in self.commands:
                            print(f"Wyryto komendę: {text}")
                            self.queue.put(text)

    def process_text(self, text):
        if not text:
            return
        print(f"Słyszę: {text}")
        for cmd in self.commands:
            if cmd in text:
                print(f"Wyryto komendę: {cmd}")
                return cmd
            else:
                if 'brass' in text or 'bless' in text or 'grass' in text:
                    print(f"Wyryto komendę: press")
                    return "press"
                if 'bike' in text or 'bites' in text or 'bicep' in text or 'cover' in text or 'cutter' in text or 'curl' in text:
                    print(f"Wyryto komendę: bicep curl")
                    return "bicep curl"
                if 'thoughts' in text or 'starved' in text or 'dart' in text or 'thought' in text or 'dogs' in text or 'solved' in text:
                    print(f"Wyryto komendę: start")
                    return "start"
                if 'and' in text:
                    print(f"Wyryto komendę: end")
                    return "end"
                if 'previews' in text or 'reviews' in text:
                    print(f"Wyryto komendę: previous")
                    return "previous"
                if 'assets' in text or 'price' in text:
                    print(f"Wyryto komendę: reset")
                    return "reset"
                if 'black' in text or 'blanc' in text or 'blank' in text or 'long' in text or 'blog' in text or 'flunk' in text or 'plum' in text or 'flung' in text \
                        or 'plunk' in text or 'wrong' in text or 'plug' in text:
                    print(f"Wyryto komendę: plank")
                    return 'plank'
                if 'ups' in text or 'adopts' in text or 'ducks' in text or 'dubs' in text:
                    print(f"Wyryto komendę: sit ups")
                    return 'sit ups'
                if 'rice' in text or 'rise' in text or 'lott' in text or 'local' in text or 'eye' in text:
                    print(f"Wyryto komendę: lateral raise")
                    return "lateral raise"
        return None


