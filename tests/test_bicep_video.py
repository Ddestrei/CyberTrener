import cv2
import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.bicep_curl import BicepCurl

VIDEO_CASES = [
    ("assets/videos/bicep_perfect.mp4", 5, "Clean reps - no swinging"),
    ("assets/videos/bicep_cheat.mp4", 0, "Cheating by leaning back - should not count"),
    ("assets/videos/bicep_partial.mp4", 0, "Partial movement - should not count")
]


def analyze_video(video_path):
    detector = PoseDetector(model_complexity=1)
    curl = BicepCurl()
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        landmarks = detector.detect(frame)
        if landmarks:
            curl.update(landmarks)
    cap.release()
    return curl.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_bicep_curl_scenarios(video_file, expected_reps, description):
    assert os.path.exists(video_file), f"File {video_file} missing!"
    detected_reps = analyze_video(video_file)

    print(f"\nVideo: {video_file} | Desc: {description}")
    print(f"Expected: {expected_reps} | Detected: {detected_reps}")

    assert detected_reps == expected_reps