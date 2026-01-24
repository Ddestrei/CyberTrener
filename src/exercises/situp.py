from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class SitUp(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Sit-up"
        # PROGI DOPASOWANE DO TWOICH LOGÓW:
        self.THRESHOLD_SITTING = 110.0  # Góra (Siad) - w logach masz > 120
        self.THRESHOLD_LYING = 50.0  # Dół (Leżenie) - w logach masz < 30

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        # Normalizacja do kąta wewnętrznego
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle
        print(f"DEBUG | State: {self.state.name} | Normalized Angle: {angle:.2f}")

        # Logika maszyny stanów dopasowana do Twojego nagrania:
        if self.state == ExerciseState.WAITING:
            # Zaczynamy test, gdy kąt jest wysoki (siedzisz lub zaczynasz ruch)
            if angle > self.THRESHOLD_SITTING:
                return ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            # Schodzisz w dół do leżenia
            if angle < self.THRESHOLD_LYING:
                return ExerciseState.ECCENTRIC

        elif self.state == ExerciseState.ECCENTRIC:
            # Wracasz w górę do siadu
            if angle > self.THRESHOLD_SITTING:
                self.reps_count += 1
                return ExerciseState.CONCENTRIC

        return self.state

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle
        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(angle, 1),
            "state": self.state.value
        }