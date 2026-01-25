import cv2
import pytest
import os
import sys

# Path setup to ensure 'src' is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.situp import SitUp
from src.utils.smoothing import LandmarkSmoother

# Configuration: (video_path, expected_reps, description)
VIDEO_CASES = [
    ("media/test_videos/situp_perfect.mp4", 5, "Perfect form - full range of motion"),
    ("media/test_videos/situp_shallow.mp4", 0, "Partial reps - should not be counted")
]


def analyze_video(video_path):
    """
    Helper function to process a video file and return the final rep count.
    """
    detector = PoseDetector(model_complexity=1)
    situp = SitUp()

    # Use smoothing to reduce MediaPipe 'jitter' and improve tracking stability
    smoother = LandmarkSmoother(window_size=5)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = detector.detect(frame)
        if landmarks:
            # Apply temporal smoothing to the raw landmark coordinates
            smoothed_landmarks = smoother.update(landmarks)

            # Feed the stabilized data into the SitUp state machine
            if smoothed_landmarks:
                situp.update(smoothed_landmarks)

    cap.release()
    return situp.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_situp_scenarios(video_file, expected_reps, description):
    assert os.path.exists(video_file), f"Error: Video file {video_file} not found!"
    detected_reps = analyze_video(video_file)

    print(f"\nProcessing File: {video_file}")
    print(f"Description: {description}")
    print(f"Expected Reps: {expected_reps} | Detected Reps: {detected_reps}")

    assert detected_reps == expected_reps, (
        f"Test failed for {video_file}. "
        f"Expected {expected_reps} reps, but counted {detected_reps}."
    )