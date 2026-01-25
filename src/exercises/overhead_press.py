from typing import Optional
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class OverheadPress(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Overhead Press"
        # Vertical movement thresholds (Hip-Shoulder-Elbow angle or vertical Y-coords)
        self.ELBOW_LOCKED_MIN = 160.0  # Full extension at the top
        self.START_POSITION_MAX = 60.0  # Arms down/at shoulder level

        # Stability threshold
        self.BACK_ARCH_MAX = 25.0  # Max deviation from vertical line (side view)
        self.rep_had_error = False

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:
        """
        Analyzes OHP using side view for back arching and front/side for extension.
        """
        # 1. BACK ARCHING DETECTION (Side View)
        # Angle: Shoulder (12) -> Hip (24) -> Knee (26)
        raw_trunk = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[26])
        trunk_angle = raw_trunk if raw_trunk <= 180 else 360 - raw_trunk
        # Arching is deviation from 180 degrees
        back_arch_deviation = abs(180.0 - trunk_angle)

        if back_arch_deviation > self.BACK_ARCH_MAX:
            self.rep_had_error = True
            if "Stop arching your back!" not in self.errors:
                self.add_error("Stop arching your back!")

        # 2. ARM EXTENSION (Front view preferred for symmetry, Side view works too)
        target = front_landmarks if front_landmarks else side_landmarks
        # Use Elbow angle (Shoulder-Elbow-Wrist) or Shoulder Abduction (Hip-Shoulder-Elbow)
        # Here we use Shoulder-Elbow-Wrist to check for arm lockout (straightening)
        raw_lockout = calculate_angle(target[12], target[14], target[16])
        extension_angle = raw_lockout if raw_lockout <= 180 else 360 - raw_lockout

        # 3. STATE MACHINE LOGIC
        # WAITING: At shoulder level
        if self.state == ExerciseState.WAITING:
            if extension_angle < 90.0:  # Arms bent at shoulders
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        # CONCENTRIC: Pushing up
        elif self.state == ExerciseState.CONCENTRIC:
            if extension_angle > self.ELBOW_LOCKED_MIN:
                if not self.rep_had_error:
                    self.reps_count += 1
                return ExerciseState.ECCENTRIC

        # ECCENTRIC: Lowering the bar
        elif self.state == ExerciseState.ECCENTRIC:
            if extension_angle < 90.0:
                return ExerciseState.CONCENTRIC

        return self.state

    def update(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)