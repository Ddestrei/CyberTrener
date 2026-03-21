import cv2
import os
import sys
import pytest
from pathlib import Path
from src.processor.pose import PoseDetector


@pytest.fixture
def sample_image_path():
    """Fixture providing path to test image."""
    return Path("media/test_images/image_test_pose.jpg")


@pytest.fixture
def sample_image(sample_image_path):
    """Fixture providing loaded test image."""
    image = cv2.imread(str(sample_image_path))
    if image is None:
        pytest.skip(f"Test image not found at {sample_image_path}")
    return image


@pytest.fixture
def pose_detector():
    """Fixture providing PoseDetector instance."""
    detector = PoseDetector()
    yield detector
    detector.close()


def test_pose_detector_initialization():
    """Test that PoseDetector initializes correctly."""
    detector = PoseDetector()
    assert detector.mp_pose is not None
    assert detector.pose is not None
    detector.close()


def test_pose_detector_detects_landmarks(pose_detector, sample_image):
    """Test that PoseDetector detects 33 landmarks from image."""
    landmarks = pose_detector.detect(sample_image)
    
    assert landmarks is not None, "No pose detected in the image"
    assert len(landmarks) == 33, f"Expected 33 landmarks, got {len(landmarks)}"


def test_landmark_structure(pose_detector, sample_image):
    """Test that each landmark has correct structure."""
    landmarks = pose_detector.detect(sample_image)
    
    assert landmarks is not None
    
    for i, landmark in enumerate(landmarks):
        assert 'x' in landmark, f"Landmark {i} missing 'x' coordinate"
        assert 'y' in landmark, f"Landmark {i} missing 'y' coordinate"
        assert 'z' in landmark, f"Landmark {i} missing 'z' coordinate"
        assert 'visibility' in landmark, f"Landmark {i} missing 'visibility'"
        
        # Check that coordinates are normalized (0-1 range for x, y)
        assert 0 <= landmark['x'] <= 1, f"Landmark {i} x out of range"
        assert 0 <= landmark['y'] <= 1, f"Landmark {i} y out of range"
        assert 0 <= landmark['visibility'] <= 1, f"Landmark {i} visibility out of range"


def test_landmark_values(pose_detector, sample_image):
    """Test that landmark coordinates are reasonable values."""
    landmarks = pose_detector.detect(sample_image)
    
    assert landmarks is not None
    
    for landmark in landmarks:
        assert isinstance(landmark['x'], float)
        assert isinstance(landmark['y'], float)
        assert isinstance(landmark['z'], float)
        assert isinstance(landmark['visibility'], float)


def test_context_manager(sample_image):
    """Test that PoseDetector works as context manager."""
    with PoseDetector() as detector:
        landmarks = detector.detect(sample_image)
        assert landmarks is not None
    # Detector should be closed after exiting context


def test_no_pose_detection():
    """Test behavior with image containing no person."""
    # Create blank image
    blank_image = cv2.imread("media/test_images/blank.jpg") if Path("media/test_images/blank.jpg").exists() else None
    
    if blank_image is None:
        # Create a blank image programmatically
        import numpy as np
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    with PoseDetector() as detector:
        landmarks = detector.detect(blank_image)
        # Should return None when no pose is detected
        assert landmarks is None or len(landmarks) == 0


def test_custom_parameters():
    """Test PoseDetector with custom parameters."""
    detector = PoseDetector(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.7
    )
    assert detector.pose is not None
    detector.close()


# Keep original main function for manual testing
def main():
    """Manual test function (not run by pytest)."""
    image_path = "media/test_images/image_test_pose.jpg"
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    with PoseDetector() as detector:
        landmarks = detector.detect(image)
        
        if landmarks:
            print(f"Detected {len(landmarks)} body landmarks:\n")
            
            landmark_names = [
                "nose", "left_eye_inner", "left_eye", "left_eye_outer",
                "right_eye_inner", "right_eye", "right_eye_outer",
                "left_ear", "right_ear", "mouth_left", "mouth_right",
                "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                "left_wrist", "right_wrist", "left_pinky", "right_pinky",
                "left_index", "right_index", "left_thumb", "right_thumb",
                "left_hip", "right_hip", "left_knee", "right_knee",
                "left_ankle", "right_ankle", "left_heel", "right_heel",
                "left_foot_index", "right_foot_index"
            ]
            
            for i, landmark in enumerate(landmarks):
                name = landmark_names[i] if i < len(landmark_names) else f"landmark_{i}"
                print(f"{i:2d}. {name:20s} | "
                      f"x: {landmark['x']:.4f}, "
                      f"y: {landmark['y']:.4f}, "
                      f"z: {landmark['z']:.4f}, "
                      f"visibility: {landmark['visibility']:.4f}")
        else:
            print("No pose detected in the image.")


if __name__ == "__main__":
    main()