import cv2
import threading
import time

class VideoThread(threading.Thread):
    """
    [CORE] Klasa obsługująca pobieranie obrazu w oddzielnym wątku.
    
    Zastosowanie:
    - Zapobiega zamrażaniu interfejsu (UI lag) podczas operacji I/O kamery.
    - Gwarantuje, że Backend (AI) zawsze dostaje najświeższą możliwą klatkę.
    
    Dla Backendu:
    - Metoda get_frame() zwraca czystą macierz numpy (BGR format OpenCV).
    - Obraz jest już odbity lustrzanie (cv2.flip).
    """
    def __init__(self, src=0):
        super().__init__()
        self.src = src
        # Inicjalizacja kamery
        self.capture = cv2.VideoCapture(src)
        
        # [OPTIMIZATION] Sztywne ustawienie rozdzielczości VGA (640x480).
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # [OPTIMIZATION] Bufor = 1. Zmniejsza opóźnienie (latency) do minimum.
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.online = self.capture.isOpened()
        self.frame = None
        self.stop_event = threading.Event()
        self.daemon = True # Wątek zginie razem z aplikacją

    def run(self):
        """Główna pętla wątku - komunikacja ze sprzętem."""
        while not self.stop_event.is_set() and self.online:
            ret, frame = self.capture.read()
            if ret:
                # [UX] Odbicie lustrzane
                self.frame = cv2.flip(frame, 1)
            else:
                self.online = False
                break
            # Krótka pauza, aby nie obciążać CPU na 100% (ok. 200Hz próbkowania)
            time.sleep(0.005)

    def get_frame(self):
        """
        Zwraca ostatnią klatkę (numpy array BGR) lub None.
        UWAGA: Klatka jest referencją do pamięci. Przed rysowaniem po niej 
        należy użyć .copy(), aby uniknąć błędów graficznych.
        """
        return self.frame

    def stop(self):
        self.stop_event.set()
        self.capture.release()