from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class SitUp(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Sit-up"
        # Thresholds for sit-up phases
        self.THRESHOLD_DOWN = 160.0  # Lying down (Start/End)
        self.THRESHOLD_UP = 60.0  # Fully up (Peak)

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Monitors the Hip angle (Shoulder-Hip-Knee).
        """
        # Right side: Shoulder (12), Hip (24), Knee (26)
        # Using right side as default for side-view video
        angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])

        # State Machine Logic
        if self.state == ExerciseState.WAITING:
            if angle > self.THRESHOLD_DOWN:
                return ExerciseState.CONCENTRIC  # Ready to start or just started

        elif self.state == ExerciseState.CONCENTRIC:
            if angle < self.THRESHOLD_UP:
                return ExerciseState.ECCENTRIC  # Reached the top

        elif self.state == ExerciseState.ECCENTRIC:
            if angle > self.THRESHOLD_DOWN:
                self.reps_count += 1
                return ExerciseState.CONCENTRIC  # Finished rep and ready for next

        return self.state

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(angle, 1),
            "state": self.state.value
        }