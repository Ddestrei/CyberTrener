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

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Plank is a static hold, so we mostly stay in CONCENTRIC (active) state.
        We use this method to trigger error collection.
        """
        # Right side landmarks by default for side-view
        # Shoulder: 12, Hip: 24, Ankle: 28
        angle = calculate_angle(landmarks[12], landmarks[24], landmarks[28])

        self.errors.clear()
        if angle < self.SAG_THRESHOLD:
            self.add_error("Sagging hips")
        elif angle > self.PIKE_THRESHOLD:
            self.add_error("Hips too high")

        return ExerciseState.CONCENTRIC

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        """Returns structured feedback with error type and severity."""
        angle = calculate_angle(landmarks[12], landmarks[24], landmarks[28])

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