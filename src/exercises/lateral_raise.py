from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle

class LateralRaise(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Lateral Raise"

        # Movement thresholds adjusted based on test video analysis
        self.ARMS_DOWN = 30.0      # Starting position (arms at sides)
        self.ARMS_UP_MIN = 80.0    # Minimum height for a valid rep
        self.ARMS_UP_MAX = 120.0   # Maximum height to prevent incorrect exercise detection
        self.TRUNK_STABILITY_LIMIT = 22.0  # Max allowed torso deviation (swinging)

        self.rep_had_error = False

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        # 1. Angle Calculation
        # Arm angle: Hip (24) -> Shoulder (12) -> Elbow (14)
        raw_arm_angle = calculate_angle(landmarks[24], landmarks[12], landmarks[14])
        arm_angle = raw_arm_angle if raw_arm_angle <= 180 else 360 - raw_arm_angle

        # Trunk angle: Shoulder (12) -> Hip (24) -> Knee (26)
        raw_trunk = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        trunk_angle = raw_trunk if raw_trunk <= 180 else 360 - raw_trunk
        trunk_deviation = abs(180.0 - trunk_angle)

        # 2. Continuous Form Validation
        # Flag the rep if the user swings their torso beyond the stability limit
        if trunk_deviation > self.TRUNK_STABILITY_LIMIT:
            self.rep_had_error = True
            if "Don't use momentum!" not in self.errors:
                self.add_error("Don't use momentum!")

        # 3. State Machine Logic
        if self.state == ExerciseState.WAITING:
            if arm_angle < self.ARMS_DOWN:
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            # Check if the arms reached the valid peak range
            if arm_angle > self.ARMS_UP_MIN:
                if arm_angle < self.ARMS_UP_MAX:
                    # Increment count only if no form errors occurred during the phase
                    if not self.rep_had_error:
                        self.reps_count += 1
                    return ExerciseState.ECCENTRIC
                else:
                    # Reset if arms go beyond realistic lateral raise range
                    return ExerciseState.WAITING

        elif self.state == ExerciseState.ECCENTRIC:
            # Reset error flag and return to concentric search once arms are lowered
            if arm_angle < self.ARMS_DOWN:
                self.rep_had_error = False
                return ExerciseState.CONCENTRIC

        return self.state

    def update(self, landmarks: list[dict[str, float]]):
        """
        Main entry point to update exercise state per frame.
        """
        if landmarks:
            self.state = self.check_conditions(landmarks)