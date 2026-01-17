import cv2
import mediapipe as mp


class PoseDetector:
    """
    Wrapper for MediaPipe Pose detection.
    Detects body landmarks from BGR image frames.
    """
    
    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize MediaPipe Pose detector.
        https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md

        Args:
            static_image_mode: If True, treats each image independently
            model_complexity: 0, 1 or 2. Higher = more accurate but slower
            smooth_landmarks: If True, reduces jitter
            min_detection_confidence: Minimum confidence for detection (0.0 - 1.0)
            min_tracking_confidence: Minimum confidence for tracking (0.0 - 1.0)
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
    def detect(self, frame_bgr):
        """
        Detect pose landmarks from BGR frame.
        
        Args:
            frame_bgr: Input frame in BGR format (OpenCV format)
            
        Returns:
            List of landmarks with (x, y, z, visibility) or None if no pose detected
        """
        # Convert BGR to RGB (MediaPipe uses RGB)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.pose.process(frame_rgb)
        
        if results.pose_landmarks:
            # Extract normalized landmarks
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
            return landmarks
        
        return None
    
    # Manual release of resources
    def close(self):
        """Release MediaPipe resources."""
        self.pose.close()
    
    # Context manager support ('with' keyword)

    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()