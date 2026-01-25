from typing import Optional
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class BicepCurl(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Bicep Curl"
        # Movement thresholds
        self.ELBOW_EXTENDED = 160.0
        self.ELBOW_FLEXED = 95.0
        # Trunk stability threshold (deviation from 180 degrees)
        self.TRUNK_LEAN_MAX = 13.0
        self.rep_had_error = False

    def check_conditions(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> Optional[ExerciseState]:
        # 1. Angle Retrieval
        # Elbow angle: Shoulder (12) -> Elbow (14) -> Wrist (16)
        raw_elbow = calculate_angle(side_landmarks[12], side_landmarks[14], side_landmarks[16])
        elbow_angle = raw_elbow if raw_elbow <= 180 else 360 - raw_elbow

        # Trunk angle: Shoulder (12) -> Hip (24) -> Knee (26)
        raw_trunk = calculate_angle(side_landmarks[12], side_landmarks[24], side_landmarks[26])
        trunk_angle = raw_trunk if raw_trunk <= 180 else 360 - raw_trunk

        # 2. Back Deviation Calculation
        # Measures how much the torso leans away from a straight vertical line (180°)
        deviation = abs(180.0 - trunk_angle)

        # Cheating detection (Swinging/Leaning)
        if deviation > self.TRUNK_LEAN_MAX:
            self.rep_had_error = True
            if "Stop swinging!" not in self.errors:
                self.add_error("Stop swinging!")

        # 3. State Machine Logic
        # WAITING: Initial state, looking for a full arm extension to start
        if self.state == ExerciseState.WAITING:
            if elbow_angle > self.ELBOW_EXTENDED:
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        # CONCENTRIC: Upward phase (curling the weight)
        elif self.state == ExerciseState.CONCENTRIC:
            if elbow_angle < self.ELBOW_FLEXED:
                # Rep is counted at the peak of the contraction if no cheating was detected
                if not self.rep_had_error:
                    self.reps_count += 1
                return ExerciseState.ECCENTRIC

        # ECCENTRIC: Downward phase (lowering the weight)
        elif self.state == ExerciseState.ECCENTRIC:
            if elbow_angle > self.ELBOW_EXTENDED:
                # Reset error flags once the arm is fully extended again
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        return self.state

    def update(
        self,
        side_landmarks: Optional[list[dict[str, float]]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """
        Main entry point called per frame to update the exercise state.
        Uses original logic by assigning state directly from check_conditions.
        """
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)