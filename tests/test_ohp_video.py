import cv2
import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.overhead_press import OverheadPress


def analyze_ohp_dual(video_path_side, video_path_front=None):
    detector_side = PoseDetector(model_complexity=1)
    detector_front = PoseDetector(model_complexity=1) if video_path_front else None
    exercise = OverheadPress()

    cap_side = cv2.VideoCapture(video_path_side)
    cap_front = cv2.VideoCapture(video_path_front) if video_path_front else None

    while cap_side.isOpened():
        ret_s, frame_s = cap_side.read()
        if not ret_s: break

        lms_s = detector_side.detect(frame_s)
        lms_f = None

        if cap_front:
            ret_f, frame_f = cap_front.read()
            if ret_f:
                lms_f = detector_front.detect(frame_f)

        if lms_s:
            exercise.update(side_landmarks=lms_s, front_landmarks=lms_f)

    cap_side.release()
    if cap_front: cap_front.release()
    return exercise.reps_count, exercise.errors


def test_ohp_perfect_form():
    """Test 3 clean reps with full extension and no arching."""
    v_side = "media/test_videos/ohp_side_perfect.mp4"
    v_front = "media/test_videos/ohp_front_perfect.mp4"

    if not os.path.exists(v_side): pytest.skip("Video missing")

    reps, errors = analyze_ohp_dual(v_side, v_front)
    assert reps == 3
    assert len(errors) == 0


def test_ohp_back_arch_error():
    """Test that arching back prevents rep counting and triggers error."""
    v_side = "media/test_videos/ohp_side_arching.mp4"

    if not os.path.exists(v_side): pytest.skip("Video missing")

    reps, errors = analyze_ohp_dual(v_side)
    assert "Stop arching your back!" in errors
    assert reps == 0