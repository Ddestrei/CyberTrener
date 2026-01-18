import cv2
import sys
import os
import time

# --- FIX IMPORTÓW ---
# Musimy dodać główny folder projektu do ścieżki Pythona, 
# żeby skrypt widział folder 'src', mimo że jest w folderze 'tests'.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.ui.visualizer import Visualizer

# --- KONFIGURACJA ---
# Wpisz tutaj nazwę swojego pliku wideo. 
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATH = os.path.join(CURRENT_DIR, "test.mp4")

def main():
    # 1. Sprawdź czy plik istnieje
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ BŁĄD: Nie znaleziono pliku: {VIDEO_PATH}")
        print("Upewnij się, że ścieżka jest dobra.")
        return

    # 2. Inicjalizacja
    cap = cv2.VideoCapture(VIDEO_PATH)
    pose_detector = PoseDetector()
    visualizer = Visualizer()

    print("🟢 Start testu wideo. Naciśnij 'q', aby wyjść.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Koniec filmu. Zapętlam...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Opcjonalnie: Zmniejsz wideo, jeśli jest w 4K i muli
        # frame = cv2.resize(frame, (1280, 720))

        # 3. Detekcja
        landmarks = pose_detector.detect(frame)

        # 4. Rysowanie
        # is_bad_form=False (zielony), zmien na True żeby przetestować czerwony
        visualizer.draw_skeleton(frame, landmarks, has_error=False) 

        # 5. Wyświetlanie (Zwykłe okno OpenCV, nie Streamlit)
        cv2.imshow('Test Wideo - CyberTrener', frame)

        # Spowolnienie, żeby nie leciało za szybko (dopasowanie do ~30 FPS)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    pose_detector.close()

if __name__ == "__main__":
    main()