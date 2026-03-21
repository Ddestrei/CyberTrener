from collections import deque
from typing import Dict, List, Optional

class LandmarkSmoother:
    def __init__(self, window_size: int = 5, min_visibility: float = 0.5):
        """
        Smooths landmark positions using a moving average filter.
        
        Args:
            window_size: Number of frames to average (default: 5).
                        Balance between smoothness and latency.
            min_visibility: Minimum visibility threshold to process landmark (default: 0.5)
        """
        self.window_size = window_size
        self.min_visibility = min_visibility
        # Dictionary storing history for each landmark
        # Key: landmark index (int)
        # Value: deque of dicts with {'x', 'y', 'z'}
        self._history: Dict[int, deque] = {}

    def update(self, current_landmarks: Optional[List[Dict[str, float]]]) -> Optional[List[Dict[str, float]]]:
        """
        Process raw landmarks and return smoothed data.
        
        Args:
            current_landmarks: List of landmark dicts from PoseDetector
        
        Returns:
            Smoothed landmarks in the same format, or None if input is None
        """
        if not current_landmarks:
            return current_landmarks

        smoothed_landmarks = []
        
        for idx, landmark in enumerate(current_landmarks):
            visibility = landmark.get('visibility', 0.0) # for safety
            
            # Initialize buffer for new landmark
            if idx not in self._history:
                self._history[idx] = deque(maxlen=self.window_size)
            
            # If landmark is visible, add to history
            if visibility >= self.min_visibility:
                self._history[idx].append({
                    'x': landmark['x'],
                    'y': landmark['y'],
                    'z': landmark['z']
                })
            
                # Calculate smoothed position
                smoothed_landmark = self._calculate_average(self._history[idx], landmark)
                smoothed_landmarks.append(smoothed_landmark)

            else:
                # If not visible, clear history and use original landmark
                self._history[idx].clear()
                smoothed_landmarks.append(landmark)
            
        return smoothed_landmarks

    def _calculate_average(self, history_deque: deque, original_landmark: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate arithmetic mean from buffer.
        
        Args:
            history_deque: Buffer of recent landmark positions
            original_landmark: Original landmark data (for fallback and visibility)
        
        Returns:
            Smoothed landmark dict with averaged x, y, z and original visibility
        """
        count = len(history_deque)
        if count == 0:
            # No history - return original landmark
            return original_landmark.copy()

        sum_x = sum(point['x'] for point in history_deque)
        sum_y = sum(point['y'] for point in history_deque)
        sum_z = sum(point['z'] for point in history_deque)
            
        return {
            'x': sum_x / count,
            'y': sum_y / count,
            'z': sum_z / count,
            'visibility': original_landmark.get('visibility', 0.0) # for safety
        }

    def reset(self):
        """Clear all history buffers. Useful when switching between exercises or users."""
        self._history.clear()