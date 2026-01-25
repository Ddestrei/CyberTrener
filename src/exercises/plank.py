from typing import Optional
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle

class Plank(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Plank"
        # Thresholds from Issue requirements
        self.PERFECT_ANGLE = 180.0
        self.SAG_THRESHOLD = 165.0
        self.PIKE_THRESHOLD = 195.0

    def check_conditions(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:
        """
        Plank is a static hold, so we mostly stay in CONCENTRIC (active) state.
        Uses side camera landmarks to monitor hip alignment.
        """
        # Right side landmarks by default for side-view: Shoulder (12), Hip (24), Ankle (28)
        angle = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[28])

        self.errors.clear()
        if angle < self.SAG_THRESHOLD:
            self.add_error("Sagging hips")
        elif angle > self.PIKE_THRESHOLD:
            self.add_error("Hips too high")

        # Static exercises stay in active state during the hold
        return ExerciseState.CONCENTRIC

    def get_feedback(self, side_landmarks: list[dict[str, float]]) -> dict:
        """Returns structured feedback based on side view landmarks."""
        angle = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[28])

        status = "Good Form"
        severity = 0  # 0: OK, 1: Warning, 2: Critical
        error_type = None

        if angle < self.SAG_THRESHOLD:
            status = "Sagging"
            error_type = "Hips too low"
            severity = 2
        elif angle > self.PIKE_THRESHOLD:
            status = "Piked"
            error_type = "Hips too high"
            severity = 1

        return {
            "exercise": self.name,
            "status": status,
            "angle": round(angle, 1),
            "error_type": error_type,
            "severity": severity
        }

    def update(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """
        Updates the plank state based on dual camera input.
        """
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)