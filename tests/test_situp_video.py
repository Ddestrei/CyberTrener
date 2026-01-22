import cv2
import pytest
import os
import sys

# Path setup to ensure 'src' is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.situp import SitUp

# Configuration: (video_path, expected_reps, description)
VIDEO_CASES = [
    ("assets/videos/situp_perfect.mp4", 5, "Perfect form - full range of motion"),
    ("assets/videos/situp_shallow.mp4", 0, "Partial reps - should not be counted")
]


def analyze_video(video_path):
    """
    Helper function: processes video and returns final rep count.
    """
    detector = PoseDetector(model_complexity=1)
    situp = SitUp()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = detector.detect(frame)
        if landmarks:
            situp.update(landmarks)

    cap.release()
    return situp.reps_count


@pytest.mark.parametrize("video_file, expected_reps, description", VIDEO_CASES)
def test_situp_scenarios(video_file, expected_reps, description):
    """
    Automated Test Case to verify rep counting and ROM validation.
    """
    # 1. Verify file existence
    assert os.path.exists(video_file), f"Error: Video file {video_file} not found!"

    # 2. Perform Video Analysis
    detected_reps = analyze_video(video_file)

    print(f"\nProcessing File: {video_file}")
    print(f"Description: {description}")
    print(f"Expected Reps: {expected_reps} | Detected Reps: {detected_reps}")

    # 3. Assertion: Detected reps must match expected reps exactly
    assert detected_reps == expected_reps, (
        f"Test failed for {video_file}. "
        f"Expected {expected_reps} reps, but counted {detected_reps}."
    )


if __name__ == "__main__":
    # Quick report when running script directly
    print("--- Sit-up Logic Video Test Report ---")
    for video, reps, desc in VIDEO_CASES:
        if os.path.exists(video):
            detected = analyze_video(video)
            status = "PASS" if detected == reps else "FAIL"
            print(f"[{status}] File: {video:30} | Found: {detected}/{reps} reps ({desc})")
        else:
            print(f"[MISSING] File: {video:30}")