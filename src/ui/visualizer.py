import cv2

class Visualizer:
    # Połączenia między punktami dla Pose Landmarker
    POSE_CONNECTIONS = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Ręce
        (11, 23), (12, 24), (23, 24), # Tułów
        (23, 25), (24, 26), (25, 27), (26, 28) # Nogi
    ]

    def draw_skeleton(self, image, detection_result, has_error=False):
        if not detection_result or not detection_result.pose_landmarks:
            return

        h, w, _ = image.shape
        color = (0, 0, 255) if has_error else (0, 255, 0)

        # Pobieramy punkty (tylko dla pierwszej wykrytej osoby)
        for landmarks in detection_result.pose_landmarks:
            # Rysowanie linii
            for connection in self.POSE_CONNECTIONS:
                start_pt = landmarks[connection[0]]
                end_pt = landmarks[connection[1]]
                
                if start_pt.presence > 0.5 and end_pt.presence > 0.5:
                    pt1 = (int(start_pt.x * w), int(start_pt.y * h))
                    pt2 = (int(end_pt.x * w), int(end_pt.y * h))
                    cv2.line(image, pt1, pt2, color, 3)

            # Rysowanie punktów
            for landmark in landmarks:
                if landmark.presence > 0.5:
                    px, py = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(image, (px, py), 4, (255, 255, 255), -1)

    def draw_panel(self, image, reps, exercise, errors):
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (260, 160), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        cv2.putText(image, f"{exercise}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        cv2.putText(image, f"{reps}", (15, 95), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 3)
        return image