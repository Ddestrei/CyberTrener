import cv2
import threading
import time
import atexit
import glob
import re
import os
import platform  # [NOWOŚĆ] Biblioteka do wykrywania systemu operacyjnego

# [LOCK] Globalna blokada sprzętowa.
# Zapobiega sytuacji "Device Busy" (Linux) oraz konfliktom dostępu (Windows),
# gdy dwa wątki próbują jednocześnie inicjalizować kamerę.
hardware_lock = threading.Lock()

# Sprawdzamy system raz przy starcie aplikacji.
# Pozwala to na dobranie odpowiedniego sterownika (backendu) OpenCV.
IS_WINDOWS = (platform.system() == 'Windows')

class VideoThread(threading.Thread):
    """
    Klasa wątku obsługującego ciągły odczyt z kamery w tle.
    Działa niezależnie od głównej pętli UI, co zapobiega zacinaniu się interfejsu.
    """
    def __init__(self, src, name="Camera"):
        super().__init__()
        self.src = src  # ID urządzenia (np. 0, 1)
        self.name = name
        self.capture = None
        self.frame = None
        self.online = False
        self.error_msg = None 
        self._stop_event = threading.Event()
        self.daemon = True # Wątek zginie automatycznie po zamknięciu aplikacji

    def run(self):
        """Główna pętla wątku: inicjalizacja i pobieranie klatek."""
        with hardware_lock:
            # [CROSS-PLATFORM] Dobór backendu wideo
            if IS_WINDOWS:
                print(f"[{self.name}] Inicjalizacja CAM {self.src} (Windows DSHOW)...")
                # Na Windows najszybszym i najnowszym standardem jest DirectShow
                backend = cv2.CAP_DSHOW
            else:
                print(f"[{self.name}] Inicjalizacja /dev/video{self.src} (Linux V4L2)...")
                # Na Linux (Arch/Ubuntu) standardem jest Video4Linux2
                backend = cv2.CAP_V4L2

            # Próba otwarcia kamery z wybranym sterownikiem
            self.capture = cv2.VideoCapture(self.src, backend)
            
            # [PERFORMANCE] Konfiguracja strumienia wideo.
            # 1. Wymuszenie rozdzielczości VGA (640x480).
            #    Dwie kamery HD na jednym kontrolerze USB często przekraczają przepustowość.
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            
            # 2. [LATENCY] Ustawienie bufora na 1 klatkę.
            #    Kluczowe ustawienie! Mówimy sterownikowi, aby nie kolejkował starych klatek.
            #    Dzięki temu zawsze widzimy obraz "na żywo", a nie z opóźnieniem.
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.capture.isOpened():
                self.error_msg = "Nie można otworzyć (Zajęta/Brak)"
                print(f"[{self.name}] BŁĄD: {self.error_msg}")
                
                # Hint tylko dla użytkowników Linuxa (Windows nie używa modprobe)
                if not IS_WINDOWS and self.src >= 2:
                    print(f"[{self.name}] HINT: Sprawdź v4l2loopback (exclusive_caps=1)")
                
                self.online = False
                return

            self.online = True
            self.error_msg = None
            print(f"[{self.name}] START (Online).")

        # Pętla odczytu (działa dopóki nie zatrzymamy wątku)
        while not self._stop_event.is_set():
            if not self.capture.isOpened():
                self.online = False
                break
            
            ret, frame = self.capture.read()
            if ret:
                # Odbicie lustrzane (Mirror) - bardziej naturalne dla użytkownika
                self.frame = cv2.flip(frame, 1)
            else:
                # Krótki odpoczynek jeśli brak klatki (np. kamera się inicjalizuje)
                time.sleep(0.01)
            
            # [CPU SAVER] Mikro-sleep, aby wątek nie zużywał 100% rdzenia CPU
            time.sleep(0.005)

        self._release()

    def _release(self):
        """Bezpieczne zwalnianie zasobów kamery."""
        with hardware_lock:
            if self.capture and self.capture.isOpened():
                self.capture.release()
            self.online = False
            print(f"[{self.name}] Zatrzymano.")

    def get_frame(self, resize_width=None):
        """
        Zwraca kopię ostatniej klatki.
        Obsługuje skalowanie (resize) PRZED wysłaniem do UI, co drastycznie zwiększa FPS.
        """
        if self.frame is not None:
            f = self.frame.copy()
            if resize_width:
                # Skalowanie z zachowaniem proporcji (Aspect Ratio)
                h, w = f.shape[:2]
                aspect = h / w
                new_h = int(resize_width * aspect)
                f = cv2.resize(f, (resize_width, new_h), interpolation=cv2.INTER_NEAREST)
            return f
        return None

    def stop(self):
        """Sygnał zatrzymania wątku."""
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout=1.0)
        # Fallback: wymuszenie zwolnienia zasobów jeśli wątek wisi
        if self.capture and self.capture.isOpened():
            self._release()

class CameraManager:
    """
    Zarządca (Manager) obsługujący kamery na różnych systemach operacyjnych.
    Powinien być używany jako Singleton (jedna instancja na aplikację).
    """
    def __init__(self):
        self.active_threads = {} # Słownik aktywnych wątków: {'front': Thread, ...}
        atexit.register(self.stop_all) # Gwarancja sprzątania przy zamknięciu programu

    def passive_scan(self):
        """
        [DISCOVERY] Wykrywanie dostępnych kamer.
        Zachowanie różni się w zależności od systemu dla bezpieczeństwa.
        """
        print(f"[Manager] Skanowanie ({platform.system()})...")
        self.stop_all() # Reset przed skanowaniem
        time.sleep(0.5)
        
        candidates = []

        if IS_WINDOWS:
            # [WINDOWS] Skanowanie portów w pętli na Windowsie często zawiesza OpenCV.
            # Bezpieczniej jest udostępnić użytkownikowi zakres ID 0-3.
            # Użytkownik metodą prób i błędów wybierze właściwą kamerę.
            candidates = [0, 1, 2, 3]
        else:
            # [LINUX] Możemy bezpiecznie sprawdzić pliki w /dev/video*
            try:
                files = sorted(glob.glob('/dev/video*'))
                for f in files:
                    if os.access(f, os.R_OK):
                        match = re.search(r'video(\d+)', f)
                        if match:
                            candidates.append(int(match.group(1)))
            except Exception:
                candidates = [0, 1, 2]

            # Fallback: zawsze dodajemy typowe porty dla OBS/DroidCam (np. 20)
            for force_id in [0, 1, 2, 20]:
                if force_id not in candidates and os.path.exists(f"/dev/video{force_id}"):
                    candidates.append(force_id)

        candidates = sorted(list(set(candidates)))
        print(f"[Manager] Dostępne sloty: {candidates}")
        return candidates

    def start_camera(self, role, src):
        """Uruchamia kamerę (src) dla danej roli (role)."""
        curr = self.active_threads.get(role)
        
        # Jeśli wątek już działa poprawnie - nie restartujemy go
        if curr and curr.is_alive() and curr.src == src and curr.online:
            return

        # Jeśli zmiana źródła - zatrzymujemy stary wątek
        if curr:
            curr.stop()
        
        # Start nowego wątku
        t = VideoThread(src, role)
        t.start()
        self.active_threads[role] = t
        time.sleep(0.2) # Czas na inicjalizację sprzętu

    def get_frame(self, role, resize_width=None):
        t = self.active_threads.get(role)
        if t and t.online:
            return t.get_frame(resize_width)
        return None
    
    def get_status(self, role):
        """Zwraca komunikat błędu, jeśli kamera nie działa."""
        t = self.active_threads.get(role)
        if t and not t.online and t.error_msg:
            return t.error_msg
        return None

    def stop_role(self, role):
        """Zatrzymuje kamerę tylko dla jednej roli (np. Side)."""
        t = self.active_threads.get(role)
        if t:
            t.stop()
            del self.active_threads[role]

    def stop_all(self):
        """Zatrzymuje wszystkie aktywne kamery."""
        # [FIX] Kopiujemy listę wartości, aby uniknąć błędu
        # "RuntimeError: dictionary changed size during iteration"
        threads_to_stop = list(self.active_threads.values())
        
        for t in threads_to_stop:
            t.stop()
        
        self.active_threads.clear()