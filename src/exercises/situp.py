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

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Analyzes the hip angle and manages the exercise state machine.
        Key landmarks: 12 (Shoulder), 24 (Hip), 26 (Knee).
        """
        # Calculate the internal angle at the hip joint
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])

        # Normalize the angle to 0-180 degree range
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        # Optional debug logging for development
        # print(f"DEBUG | State: {self.state.name} | Angle: {angle:.2f}")

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

                # Transition back to search for the lying position
                # This prevents duplicate counting during the same movement cycle
                return ExerciseState.CONCENTRIC

        return self.state

    def update(self, landmarks: list[dict[str, float]]):
        """
        Core update method called by tests and the application loop.
        Processes landmarks to determine state changes.
        """
        if landmarks:
            self.state = self.check_conditions(landmarks)

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        """
        Returns structured data for the UI and feedback modules.
        """
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(angle, 1),
            "state": self.state.value
        }