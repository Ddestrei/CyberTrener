from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class OverheadPress(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Overhead Press"
        # Rep counting thresholds (Wrist relative to Shoulder/Ear)
        self.THRESHOLD_START = 160.0  # Arms down (bar at shoulder level)
        self.THRESHOLD_TOP = 40.0  # Arms fully extended up
        # Safety threshold (Back arching)
        # Angle between Ear-Shoulder-Hip or Shoulder-Hip-Knee
        self.ARCH_THRESHOLD = 15.0

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Monitors arm extension and lumbar arching.
        """
        # 1. Rep Counting Logic (Right side: Shoulder 12, Elbow 14, Wrist 16)
        # Using angle for simplicity, but height (Y-coordinate) could also work
        arm_angle = calculate_angle(landmarks[12], landmarks[14], landmarks[16])

        # 2. Back Arch Detection (Ear 8, Shoulder 12, Hip 24)
        # A straight line should be near 180 degrees
        body_angle = calculate_angle(landmarks[8], landmarks[12], landmarks[24])

        if abs(180 - body_angle) > self.ARCH_THRESHOLD:
            self.add_error("Back arching detected! Core tight.")

        # State Machine
        if self.state == ExerciseState.WAITING:
            if arm_angle > self.THRESHOLD_START:
                return ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            if arm_angle < self.THRESHOLD_TOP:
                return ExerciseState.ECCENTRIC

        elif self.state == ExerciseState.ECCENTRIC:
            if arm_angle > self.THRESHOLD_START:
                if not self.errors:
                    self.reps_count += 1
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        return self.state

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "status": "Danger: Arching" if self.errors else "Good Form",
            "errors": self.errors
        }