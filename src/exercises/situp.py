from typing import Optional
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class SitUp(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Sit-up"
        # Angular thresholds based on hip flexion
        # Upright (Sitting) is roughly > 110 degrees, Lying down is < 50 degrees
        self.THRESHOLD_SITTING = 110.0
        self.THRESHOLD_LYING = 50.0

    def check_conditions(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:
        """
        Analyzes the hip angle and manages the exercise state machine.
        Uses side view as the primary source for hip flexion.
        Key landmarks: 12 (Shoulder), 24 (Hip), 26 (Knee).
        """
        # Calculate the internal angle at the hip joint using side view
        raw_angle = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[26])

        # Normalize the angle to 0-180 degree range
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        # Waiting for the user to reach the starting position (lying down)
        if self.state == ExerciseState.WAITING or self.state == ExerciseState.CONCENTRIC:
            if angle < self.THRESHOLD_LYING:
                # User reached the floor; transition to waiting for the lifting phase
                return ExerciseState.ECCENTRIC

        # Tracking the upward movement (lifting torso)
        elif self.state == ExerciseState.ECCENTRIC:
            if angle > self.THRESHOLD_SITTING:
                # SUCCESS: One rep completed when torso is fully upright
                self.reps_count += 1
                return ExerciseState.CONCENTRIC

        return self.state

    def update(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """
        Core update method. Processes landmarks to determine state changes.
        """
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)

    def get_feedback(self, side_landmarks: list[dict[str, float]]) -> dict:
        """
        Returns structured data for the UI based on side view landmarks.
        """
        raw_angle = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[26])
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(angle, 1),
            "state": self.state.value
        }