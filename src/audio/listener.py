import sounddevice as sd
import speech_recognition as sr
import numpy as np
import threading
import queue
import json

# Spróbuj zaimportować Vosk, jeśli jest dostępny
try:
    from vosk import Model, KaldiRecognizer

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


class ExerciseListener(threading.Thread):
    def __init__(self, command_queue, keywords):
        super().__init__(daemon=True)
        self.command_queue = command_queue
        self.sample_rate = 16000  # <--- Definiujemy atrybut na samym początku
        self.keywords = keywords

        if not self.check_microphone():
            print("!!! OSTRZEŻENIE: Nie wykryto podłączonego mikrofonu !!!")
        else:
            print("Mikrofon wykryty i gotowy.")

        # Próba załadowania modelu Vosk (offline)
        self.model_loaded = False
        if VOSK_AVAILABLE:
            try:
                # Folder 'model' musi być w tym samym katalogu co skrypt
                self.vosk_model = Model("vosk-model-small-en-us-0.15")
                self.recognizer = KaldiRecognizer(self.vosk_model, self.sample_rate)
                self.model_loaded = True
                print("Załadowano silnik offline (Vosk).")
            except Exception as e:
                print(f"Vosk niezaładowany (brak folderu 'model'). Używam Google API. Info: {e}")

    def check_microphone(self):
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        return len(input_devices) > 0

    def run(self):
        # Używamy sounddevice do przechwytywania dźwięku
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               dtype='int16', channels=1) as stream:
            print("Nasłuchiwanie komend...")

            while True:
                data, overflow = stream.read(8000)
                if overflow:
                    continue

                if self.model_loaded:
                    # Logika OFFLINE (Vosk)
                    if self.recognizer.AcceptWaveform(bytes(data)):
                        result = json.loads(self.recognizer.Result())
                        self.process_text(result.get("text", ""))
                else:
                    # Logika ONLINE (Google Fallback)
                    # Konwersja na format akceptowany przez SpeechRecognition
                    audio_data = sr.AudioData(bytes(data), self.sample_rate, 2)
                    try:
                        # Uwaga: Google może być wolniejsze przy krótkich blokach
                        r = sr.Recognizer()
                        text = r.recognize_google(audio_data, language="en-US").lower()
                        self.process_text(text)
                    except:
                        pass

    def process_text(self, text):
        if not text:
            return

        print(f"Słyszę: {text}")
        for cmd in self.keywords:
            if cmd in text:
                print(f"Wyryto komendę: {cmd}")
                self.command_queue.put(cmd)
                break
            else:
                if 'brass' in text or 'bless' in text or 'grass' in text:
                    print(f"Wyryto komendę: press")
                    self.command_queue.put("press")
                    break
                if 'bike' in text or 'bites' in text or 'bicep' in text or 'cover' in text or 'cutter' in text or 'curl' in text:
                    print(f"Wyryto komendę: bicep curl")
                    self.command_queue.put("bicep curl")
                    break
                if 'thoughts' in text or 'starved' in text or 'dart' in text or 'thought' in text or 'dogs' in text or 'solved' in text:
                    print(f"Wyryto komendę: start")
                    self.command_queue.put("start")
                    break
                if 'and' in text:
                    print(f"Wyryto komendę: end")
                    self.command_queue.put("end")
                    break
                if 'previews' in text or 'reviews' in text:
                    print(f"Wyryto komendę: previous")
                    self.command_queue.put("previous")
                    break
                if 'assets' in text or 'price' in text:
                    print(f"Wyryto komendę: reset")
                    self.command_queue.put("reset")
                    break
                if 'black' in text or 'blanc' in text or 'blank' in text or 'long' in text or 'blog' in text or 'flunk' in text or 'plum' in text or 'flung' in text \
                        or 'plunk' in text or 'wrong' in text or 'plug' in text:
                    print(f"Wyryto komendę: plank")
                    self.command_queue.put("plank")
                    break
                if 'ups' in text or 'adopts' in text or 'ducks' in text or 'dubs' in text:
                    print(f"Wyryto komendę: sit ups")
                    self.command_queue.put("sit ups")
                    break
                if 'rice' in text or 'rise' in text or 'lott' in text or 'local' in text or 'eye' in text:
                    print(f"Wyryto komendę: lateral raise")
                    self.command_queue.put("lateral raise")
                    break


# --- Przykład użycia ---
class Listener(threading.Thread):
    def __init__(self, commands, functions):
        super().__init__(daemon=True)
        self.commands = commands
        self.functions = functions
        self.q = queue.Queue()
        listener = ExerciseListener(self.q, keywords=commands)
        listener.start()

    def run(self):
        try:
            while True:
                if not self.q.empty():
                    command = self.q.get()
                    index = self.commands.index(command)
                    func = self.functions[index]
                    func()
                    print(f"Przetwarzanie w aplikacji głównej: {command}")
        except KeyboardInterrupt:
            print("Zamykanie...")
