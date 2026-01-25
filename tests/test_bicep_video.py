import cv2
import pytest
import os
import sys

# Ensure the 'src' directory is accessible for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.bicep_curl import BicepCurl
from src.utils.smoothing import LandmarkSmoother

# Test configurations: (video_path, expected_reps, description)
VIDEO_CASES = [
    ("media/test_videos/bicep_perfect.mp4", 5, "Clean reps - no swinging"),
    ("media/test_videos/bicep_cheat.mp4", 1, "Cheating by leaning back - should not count"),
    ("media/test_videos/bicep_partial.mp4", 1, "Partial movement - should not count")
]


def analyze_video(video_path):
    """
    Core processing function: Runs pose detection and exercise logic on a video file.
    """
    detector = PoseDetector(model_complexity=1)
    # Initialize smoother to handle MediaPipe jitter and filter low-confidence points
    smoother = LandmarkSmoother(window_size=5, min_visibility=0.5)
    curl = BicepCurl()

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Extract raw pose landmarks from the current frame
        landmarks = detector.detect(frame)

        if landmarks:
            # Apply temporal smoothing to stabilize landmark positions
            smoothed_landmarks = smoother.update(landmarks)

            if smoothed_landmarks:
                # Update the exercise state machine with stabilized data
                curl.update(smoothed_landmarks)

    cap.release()
    return curl.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_bicep_curl_scenarios(video_file, expected_reps, description):
    """
    Integration test to verify rep counting and error detection across different scenarios.
    """
    assert os.path.exists(video_file), f"Error: Video file {video_file} not found!"
    detected_reps = analyze_video(video_file)

    print(f"\nProcessing: {video_file} | Scenario: {description}")
    print(f"Expected: {expected_reps} | Detected: {detected_reps}")

    # Verify that the logic correctly counts reps or rejects cheated movements
    assert detected_reps == expected_reps