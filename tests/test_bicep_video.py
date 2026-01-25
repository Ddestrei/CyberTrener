import cv2
import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.bicep_curl import BicepCurl
from src.utils.smoothing import LandmarkSmoother

VIDEO_CASES = [
    ("media/test_videos/bicep_perfect.mp4", 5, "Clean reps - no swinging"),
    ("media/test_videos/bicep_cheat.mp4", 1, "Cheating by leaning back - should not count"),
    ("media/test_videos/bicep_partial.mp4", 1, "Partial movement - should not count")
]


def analyze_video(video_path):
    detector = PoseDetector(model_complexity=1)
    smoother = LandmarkSmoother(window_size=5, min_visibility=0.5)
    curl = BicepCurl()
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = detector.detect(frame)

        if landmarks:
            smoothed_landmarks = smoother.update(landmarks)

            if smoothed_landmarks:
                curl.update(smoothed_landmarks)

    cap.release()
    return curl.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_bicep_curl_scenarios(video_file, expected_reps, description):
    assert os.path.exists(video_file), f"Plik {video_file} nie istnieje!"
    detected_reps = analyze_video(video_file)

    print(f"\nWideo: {video_file} | Opis: {description}")
    print(f"Oczekiwano: {expected_reps} | Wykryto: {detected_reps}")

    assert detected_reps == expected_reps