import cv2
import pytest
import os
import sys

# Path setup to ensure the script can access the src folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.lateral_raise import LateralRaise


def analyze_lateral_raise_dual(video_path_side, video_path_front=None):
    """
    Processes videos from one or two cameras and returns the repetition count.
    """
    # Initialize detectors for both views
    detector_side = PoseDetector(model_complexity=1)
    detector_front = PoseDetector(model_complexity=1) if video_path_front else None

    exercise = LateralRaise()

    cap_side = cv2.VideoCapture(video_path_side)
    cap_front = cv2.VideoCapture(video_path_front) if video_path_front else None

    while cap_side.isOpened():
        ret_s, frame_s = cap_side.read()
        if not ret_s:
            break

        # Detection from the side camera (mandatory)
        landmarks_s = detector_side.detect(frame_s)

        # Detection from the front camera (optional)
        landmarks_f = None
        if cap_front:
            ret_f, frame_f = cap_front.read()
            if ret_f:
                landmarks_f = detector_front.detect(frame_f)

        # Update exercise state with available landmarks
        if landmarks_s:
            exercise.update(side_landmarks=landmarks_s, front_landmarks=landmarks_f)

    cap_side.release()
    if cap_front:
        cap_front.release()

    return exercise.reps_count


def test_lateral_raise_perfect_form():
    """
    Test scenario with two cameras: 5 correct repetitions.
    """
    video_side = "media/test_videos/lateral_side_5reps.mp4"
    video_front = "media/test_videos/lateral_front_5reps.mp4"

    if not os.path.exists(video_side) or not os.path.exists(video_front):
        pytest.skip("Test video files do not exist.")

    reps = analyze_lateral_raise_dual(video_side, video_front)
    assert reps == 5


def test_lateral_raise_swinging_error():
    """
    Test error detection: torso swinging should block repetition counting.
    """
    video_side = "media/test_videos/lateral_side_swinging.mp4"

    if not os.path.exists(video_side):
        pytest.skip("Cheat video file does not exist.")

    # Even if arm movement is correct, swinging (visible from the side) should result in 0 reps
    reps = analyze_lateral_raise_dual(video_side)
    assert reps == 0


def test_lateral_raise_no_front_camera():
    """
    Test system resilience when front camera is missing (side view only).
    """
    video_side = "media/test_videos/lateral_side_3reps.mp4"

    if not os.path.exists(video_side):
        pytest.skip("Side view video file does not exist.")

    reps = analyze_lateral_raise_dual(video_side)
    assert reps == 3