import cv2
import pytest
import os
import sys

# Path setup to ensure 'src' is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.lateral_raise import LateralRaise
from src.utils.smoothing import LandmarkSmoother

# Test cases for both Front and Side views
# (video_path, expected_reps, description)
VIDEO_CASES = [
    ("media/test_videos/lateral_front_perfect.mp4", 5, "Front view - 5 clean reps"),
    ("media/test_videos/lateral_side_cheat.mp4", 0, "Side view - heavy swinging, should not count"),
    ("media/test_videos/lateral_front_partial.mp4", 0, "Front view - shallow reps, not reaching shoulder height")
]


def analyze_video(video_path):
    """
    Processes video to count reps and detect form errors for Lateral Raises.
    """
    detector = PoseDetector(model_complexity=1)
    # Using a slightly larger window for smoothing to stabilize arm movement
    smoother = LandmarkSmoother(window_size=7, min_visibility=0.5)
    lat_raise = LateralRaise()

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = detector.detect(frame)

        if landmarks:
            # Temporal smoothing is crucial here as arms move fast in lateral raises
            smoothed_landmarks = smoother.update(landmarks)

            if smoothed_landmarks:
                lat_raise.update(smoothed_landmarks)

    cap.release()
    return lat_raise.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_lateral_raise_scenarios(video_file, expected_reps, description):
    """
    Validates Lateral Raise logic against different camera angles and form qualities.
    """
    assert os.path.exists(video_file), f"Error: Video file {video_file} not found!"
    detected_reps = analyze_video(video_file)

    print(f"\nVideo: {video_file}")
    print(f"Description: {description}")
    print(f"Expected: {expected_reps} | Detected: {detected_reps}")

    assert detected_reps == expected_reps, (
        f"Failed for {video_file}. Expected {expected_reps}, got {detected_reps}."
    )