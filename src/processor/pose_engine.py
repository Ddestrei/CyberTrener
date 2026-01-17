import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2

class PoseEngineV2:
    def __init__(self, model_path='pose_landmarker.task'):
        # 1. Konfiguracja opcji
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO, # Zoptymalizowane pod wideo
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # 2. Tworzenie detektora
        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.last_timestamp_ms = 0

    def process_frame(self, frame):
        # MediaPipe Tasks wymaga klatki w formacie Image i timestampu w milisekundach
        timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)
        
        # Zapobieganie błędom przy identycznych timestampach
        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = timestamp_ms

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Wykrywanie
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)
        return detection_result

    def close(self):
        self.detector.close()