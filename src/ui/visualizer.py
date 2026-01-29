import cv2
import numpy as np

class Visualizer:
    # Point connections for Pose Landmarker (MediaPipe Topology)
    POSE_CONNECTIONS = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Arms
        (11, 23), (12, 24), (23, 24),                     # Torso
        (23, 25), (24, 26), (25, 27), (26, 28),           # Legs
        (27, 29), (29, 31), (28, 30), (30, 32)            # Feet
    ]

    def draw_skeleton(self, image: np.ndarray, landmarks: list, has_error: bool = False):
        """Draws the skeleton with color coding for errors."""
        if not landmarks: 
            return
            
        h, w = image.shape[:2]
        color = (0, 0, 255) if has_error else (0, 255, 0)
        white = (255, 255, 255)

        def get_attr(pt, key):
            return pt.get(key, 0.0) if isinstance(pt, dict) else getattr(pt, key, 0.0)

        for connection in self.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx >= len(landmarks) or end_idx >= len(landmarks): 
                continue
                
            start_pt, end_pt = landmarks[start_idx], landmarks[end_idx]
            if get_attr(start_pt, 'visibility') > 0.5 and get_attr(end_pt, 'visibility') > 0.5:
                pt1 = (int(get_attr(start_pt, 'x') * w), int(get_attr(start_pt, 'y') * h))
                pt2 = (int(get_attr(end_pt, 'x') * w), int(get_attr(end_pt, 'y') * h))
                cv2.line(image, pt1, pt2, color, 3)

        for landmark in landmarks:
            if get_attr(landmark, 'visibility') > 0.5:
                px, py = int(get_attr(landmark, 'x') * w), int(get_attr(landmark, 'y') * h)
                cv2.circle(image, (px, py), 5, color, -1)
                cv2.circle(image, (px, py), 2, white, -1)

    def draw_panel(self, image: np.ndarray, reps: float, exercise_name: str, errors: list, angle: float = 0.0):
        """
        Draws the information HUD. 
        Includes a placeholder for the joint angle.
        """
        if image is None or image.size == 0: 
            return

        overlay = image.copy()
        x, y, w, h = 0, 0, 300, 180 
        
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        if exercise_name.lower() == "plank":
            total_seconds = int(reps)
            main_text = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
            label_text = "TIME"
        else:
            main_text = str(int(reps))
            label_text = "REPS"

        # 1. Exercise Name
        cv2.putText(image, exercise_name.title(), (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # 2. Main Value (Counter)
        cv2.putText(image, main_text, (25, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
        
        # dynamic label positioning
        text_size = cv2.getTextSize(main_text, cv2.FONT_HERSHEY_SIMPLEX, 2.0, 4)[0]
        label_x = 25 + text_size[0] + 15
        cv2.putText(image, label_text, (label_x, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 3. [PLACEHOLDER] Current Angle
        angle_text = f"CURRENT ANGLE: {angle:.1f} DEG"
        cv2.putText(image, angle_text, (20, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # 4. Error Display
        if errors:
            error_text = errors[0] if isinstance(errors[0], str) else "BAD FORM!"
            cv2.putText(image, error_text, (20, 165), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)