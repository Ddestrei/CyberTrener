from typing import Optional
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class LateralRaise(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Lateral Raise"
        # Angular thresholds
        self.ARMS_DOWN = 30.0  # Starting position (arms at sides)
        self.ARMS_UP_MIN = 80.0  # Minimum height for a valid repetition
        self.ARMS_UP_MAX = 120.0  # Maximum height (to prevent shrugging/overhead movement)
        self.TRUNK_STABILITY_LIMIT = 22.0  # Maximum allowed torso swing (side view)

        self.rep_had_error = False

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:
        """
        Analyzes movement using the side camera as the primary source for stability
        and the front camera (if available) for measuring arm elevation height.
        """
        # 1. TRUNK STABILITY (Best visible from the side)
        # Angle: Shoulder (12) -> Hip (24) -> Knee (26)
        raw_trunk = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[26])
        trunk_angle = raw_trunk if raw_trunk <= 180 else 360 - raw_trunk
        trunk_deviation = abs(180.0 - trunk_angle)

        if trunk_deviation > self.TRUNK_STABILITY_LIMIT:
            self.rep_had_error = True
            if "Stop swinging your body!" not in self.errors:
                self.add_error("Stop swinging your body!")

        # 2. ARM ELEVATION (Prefer front view if available, otherwise use side view)
        target_landmarks = front_landmarks if front_landmarks else side_landmarks

        # Angle: Hip (24) -> Shoulder (12) -> Elbow (14)
        raw_arm = calculate_angle(target_landmarks[24], target_landmarks[12], target_landmarks[14])
        arm_angle = raw_arm if raw_arm <= 180 else 360 - raw_arm

        # 3. STATE MACHINE LOGIC (Consistent with BicepCurl)
        # WAITING: Waiting for arms to be lowered to start the concentric phase
        if self.state == ExerciseState.WAITING:
            if arm_angle < self.ARMS_DOWN:
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        # CONCENTRIC: Lifting phase - count repetition at the peak
        elif self.state == ExerciseState.CONCENTRIC:
            if arm_angle > self.ARMS_UP_MIN:
                if arm_angle < self.ARMS_UP_MAX:
                    # Increment rep count only if no technical errors were detected
                    if not self.rep_had_error:
                        self.reps_count += 1
                    return ExerciseState.ECCENTRIC
                else:
                    # If arms went too high, reset to WAITING without counting the rep
                    return ExerciseState.WAITING

        # ECCENTRIC: Lowering phase - looking for extension to start over
        elif self.state == ExerciseState.ECCENTRIC:
            if arm_angle < self.ARMS_DOWN:
                self.rep_had_error = False
                self.errors.clear()
                # Return directly to searching for the lifting phase (consistent with BicepCurl)
                return ExerciseState.CONCENTRIC

        return self.state

    def update(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """
        Main update method. Directly assigns the state to bypass
        the automatic logic from the base class.
        """
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)