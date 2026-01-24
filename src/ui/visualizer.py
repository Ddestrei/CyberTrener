import cv2
import numpy as np

class Visualizer:
    # Połączenia między punktami dla Pose Landmarker (Topologia MediaPipe)
    POSE_CONNECTIONS = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Ręce
        (11, 23), (12, 24), (23, 24),                     # Tułów
        (23, 25), (24, 26), (25, 27), (26, 28),           # Nogi
        (27, 29), (29, 31), (28, 30), (30, 32)            # Stopy
    ]

    def draw_skeleton(self, image: np.ndarray, landmarks: list, has_error: bool = False):
        """
        Funkcja rysująca szkielet na klatce wideo.
        Args:
            image: Klatka wideo BGR (OpenCV).
            landmarks: Lista słowników [{'x':.., 'y':.., 'visibility':..}] z pose.py.
            has_error: Flaga decydująca o kolorze (Zielony=OK, Czerwony=Błąd).
        """
        if not landmarks:
            return

        h, w, _ = image.shape
        
        # Logika kolorów: (B, G, R)
        # Jeśli wykryto błąd techniki -> Czerwony, w przeciwnym razie -> Zielony.
        color = (0, 0, 255) if has_error else (0, 255, 0)
        white = (255, 255, 255)

        # 1. Rysowanie Linii (Kości)
        for connection in self.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            
            # Bezpieczeństwo: Sprawdzamy czy indeksy nie wychodzą poza zakres listy
            if start_idx >= len(landmarks) or end_idx >= len(landmarks):
                continue
            
            start_pt = landmarks[start_idx]
            end_pt = landmarks[end_idx]
            
            # Używamy .get() lub nawiasów [], ponieważ pose.py zwraca słowniki,
            # a nie obiekty klasy Landmark.
            vis1 = start_pt.get('visibility', 1.0)
            vis2 = end_pt.get('visibility', 1.0)

            # Rysujemy tylko jeśli oba punkty są wystarczająco widoczne
            if vis1 > 0.5 and vis2 > 0.5:
                # Konwersja znormalizowanych współrzędnych (0.0-1.0) na piksele
                pt1 = (int(start_pt['x'] * w), int(start_pt['y'] * h))
                pt2 = (int(end_pt['x'] * w), int(end_pt['y'] * h))
                
                cv2.line(image, pt1, pt2, color, 3)

        # 2. Rysowanie Punktów (Stawy)
        for landmark in landmarks:
            vis = landmark.get('visibility', 1.0)
            if vis > 0.5:
                px, py = int(landmark['x'] * w), int(landmark['y'] * h)
                
                # Biała kropka w środku dla lepszej widoczności
                cv2.circle(image, (px, py), 5, color, -1)
                cv2.circle(image, (px, py), 2, white, -1)

    def draw_panel(self, image: np.ndarray, reps: int, exercise_name: str, errors: list):
        """
        Rysuje półprzezroczysty panel z licznikiem powtórzeń (HUD).
        Używa cv2.addWeighted dla efektu przezroczystości.
        """
        overlay = image.copy()
        
        # Definicja panelu (Lewy górny róg): x, y, w, h
        x, y, w, h = 0, 0, 280, 150
        
        # Rysujemy czarny prostokąt na warstwie overlay
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
        
        # Alpha blending - mieszanie obrazów
        alpha = 0.6 
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        
        # Teksty informacyjne
        cv2.putText(image, exercise_name, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        cv2.putText(image, str(reps), (30, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 4)
        cv2.putText(image, "REPS", (130, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Opcjonalnie: wyświetlanie błędów
        if errors:
            cv2.putText(image, "BAD FORM!", (20, 140), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)