import cv2
import pytest
import os
import sys

# Path setup to ensure 'src' is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processor.pose import PoseDetector
from src.exercises.plank import Plank
from src.utils.smoothing import LandmarkSmoother  # 1. Importujemy smoother

# Configuration: List of tuples (video_path, expected_status)
VIDEO_CASES = [
    ("media/test_videos/plank_correct.mp4", "Good Form"),
    ("media/test_videos/plank_sagging.mp4", "Sagging"),
    ("media/test_videos/plank_piked.mp4", "Piked")
]


def analyze_video(video_path):
    """
    Helper function: processes video and collects status statistics.
    """
    detector = PoseDetector(model_complexity=1)
    plank = Plank()
    # 2. Inicjalizacja smoothera.
    # Dla planku window_size=5-10 jest idealne, bo to ćwiczenie statyczne.
    smoother = LandmarkSmoother(window_size=8)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return None

    stats = {
        "Good Form": 0,
        "Sagging": 0,
        "Piked": 0,
        "total_frames": 0
    }

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = detector.detect(frame)
        if landmarks:
            # 3. Wygładzanie punktów (redukcja drżenia kończyn na wideo)
            smoothed_landmarks = smoother.update(landmarks)

            if smoothed_landmarks:
                # 4. Przekazujemy wygładzone dane do logiki planku
                plank.update(smoothed_landmarks)
                feedback = plank.get_feedback(smoothed_landmarks)
                status = feedback["status"]

                if status in stats:
                    stats[status] += 1
                    stats["total_frames"] += 1

    cap.release()
    return stats


@pytest.mark.parametrize("video_file, expected_status", VIDEO_CASES)
def test_plank_scenarios(video_file, expected_status):
    """
    Automated Test Case to verify the effectiveness of form detection.
    """
    # 1. Verify file existence
    assert os.path.exists(video_file), f"Error: Video file {video_file} not found!"

    # 2. Perform Video Analysis
    results = analyze_video(video_file)
    assert results is not None, f"Error: Could not open video {video_file}"
    assert results["total_frames"] > 0, f"Error: No pose landmarks detected in {video_file}"

    # 3. Calculate success rate (percentage of frames matching expected status)
    success_rate = (results[expected_status] / results["total_frames"]) * 100

    print(f"\nProcessing File: {video_file}")
    print(f"Expected: {expected_status} | Detected Accuracy: {success_rate:.2f}%")

    # 4. Assertion: Test passes if expected status dominates (> 50% of frames)
    # You can adjust this threshold based on your video quality (e.g., transitions)
    assert success_rate > 50, (
        f"Test failed for {video_file}. "
        f"Expected {expected_status}, but only detected it in {success_rate:.2f}% of frames."
    )


if __name__ == "__main__":
    # If run directly, print a summary report for available videos
    print("--- Plank Logic Video Test Report ---")
    for video, status in VIDEO_CASES:
        if os.path.exists(video):
            res = analyze_video(video)
            rate = (res[status] / res["total_frames"]) * 100
            print(f"File: {video:30} | Match: {rate:5.1f}% for status '{status}'")
        else:
            print(f"File: {video:30} | Status: NOT FOUND")