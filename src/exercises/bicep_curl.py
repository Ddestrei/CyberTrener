from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class BicepCurl(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Bicep Curl"
        # Elbow thresholds
        self.ELBOW_EXTENDED = 160.0  # Arm straight
        self.ELBOW_FLEXED = 40.0  # Arm fully curled
        # Trunk threshold (Cheating)
        self.TRUNK_LEAN_MAX = 15.0  # Maximum degrees of leaning back from vertical

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Monitors Elbow (Shoulder-Elbow-Wrist) and Trunk angle.
        """
        # Right arm: Shoulder (12), Elbow (14), Wrist (16)
        elbow_angle = calculate_angle(landmarks[12], landmarks[14], landmarks[16])

        # Trunk lean: Shoulder (12), Hip (24), and a vertical reference point
        # For simplicity, we can check the angle between Shoulder-Hip and the vertical axis
        # Or more simply: Angle between Ear(8)-Shoulder(12)-Hip(24)
        trunk_angle = calculate_angle(landmarks[8], landmarks[12], landmarks[24])

        # Check for cheating (leaning back)
        # Assuming 180 is straight, if user leans back, the angle changes significantly
        if abs(180 - trunk_angle) > self.TRUNK_LEAN_MAX:
            self.add_error("Stop swinging! Keep your back straight.")
            # We don't change the state, but the error will stay in self.errors
            # which we can use to invalidate the rep during the state transition.

        # State Machine for Rep Counting
        if self.state == ExerciseState.WAITING:
            if elbow_angle > self.ELBOW_EXTENDED:
                return ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            if elbow_angle < self.ELBOW_FLEXED:
                return ExerciseState.ECCENTRIC

        elif self.state == ExerciseState.ECCENTRIC:
            if elbow_angle > self.ELBOW_EXTENDED:
                # ONLY COUNT IF NO ERRORS WERE DETECTED IN THIS CYCLE
                if not self.errors:
                    self.reps_count += 1
                self.errors.clear()  # Reset errors for next rep
                return ExerciseState.CONCENTRIC

        return self.state

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        elbow_angle = calculate_angle(landmarks[12], landmarks[14], landmarks[16])
        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "elbow_angle": round(elbow_angle, 1),
            "status": "Cheating Detected" if self.errors else "Good Form",
            "errors": self.errors
        }