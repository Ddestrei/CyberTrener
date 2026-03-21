from typing import Optional, Tuple, Dict
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class SitUp(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Sit-up"

        # --- PROGI KĄTOWE ---
        # 180 stopni = płasko
        # 90 stopni = pionowo

        self.ANGLE_LYING = 120.0        # Granica leżenia (reset błędów)
        self.ANGLE_START_TRIGGER = 100.0 # Moment, w którym uznajemy, że user zaczął ćwiczyć
        self.ANGLE_FULL_REP = 60.0      # Cel - pełne zgięcie (według Twojego życzenia)

        # --- PROGI STÓP ---
        self.FEET_LIFT_THRESHOLD = -0.05

        self.rep_had_error = False
        self.current_hip_angle = 180.0

    def _get_best_side_landmarks(self, landmarks: list[dict[str, float]]) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Wybiera stronę o lepszej widoczności i zwraca:
        (Shoulder, Hip, Knee, Ankle)
        """
        # Lewa: 11, 23, 25, 27 | Prawa: 12, 24, 26, 28
        left_vis = (landmarks[11]['visibility'] + landmarks[23]['visibility'] + landmarks[25]['visibility']) / 3
        right_vis = (landmarks[12]['visibility'] + landmarks[24]['visibility'] + landmarks[26]['visibility']) / 3

        if left_vis > right_vis:
            return landmarks[11], landmarks[23], landmarks[25], landmarks[27]  # Left side
        else:
            return landmarks[12], landmarks[24], landmarks[26], landmarks[28]  # Right side

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:

        # 1. Pobranie punktów i kąta
        shoulder, hip, knee, ankle = self._get_best_side_landmarks(side_landmarks)

        raw_angle = calculate_angle(shoulder, hip, knee)
        self.current_hip_angle = raw_angle if raw_angle <= 180 else 360 - raw_angle
        # 2. Sprawdzenie stóp (zawsze aktywne w tle)
        knee_hip_diff = ankle['y'] - hip['y']

        # Jeśli jesteśmy w trakcie ćwiczenia (nie leżymy), sprawdzaj stopy
        if self.state != ExerciseState.WAITING:
            if knee_hip_diff < self.FEET_LIFT_THRESHOLD:
                self.rep_had_error = True
                self.add_error("Keep feet on ground!")

        # 3. MASZYNA STANÓW

        # --- STAN 1: WAITING (Leżenie) ---
        if self.state == ExerciseState.WAITING:
            # Jeśli user leży (> 150), czyścimy błędy zgodnie z prośbą
            if self.current_hip_angle > self.ANGLE_LYING:
                self.errors.clear()
                self.rep_had_error = False

            # TRIGGER: Jeśli kąt spadnie poniżej 130 -> ZACZYNAMY ĆWICZENIE
            if self.current_hip_angle < self.ANGLE_START_TRIGGER:
                return ExerciseState.CONCENTRIC

        # --- STAN 2: CONCENTRIC (Ruch w górę) ---
        elif self.state == ExerciseState.CONCENTRIC:

            # A. SUKCES: Osiągnięto pełny zakres (< 60 stopni)
            if self.current_hip_angle < self.ANGLE_FULL_REP:
                return ExerciseState.ECCENTRIC

            # B. PORAŻKA (Niepełny ruch):
            # User nie dobił do 60, a wrócił już do leżenia (> 150)
            if self.current_hip_angle > self.ANGLE_LYING:
                self.add_error("Incomplete rep! Go deeper")
                self.rep_had_error = True
                # Wracamy do waitingu bez zaliczenia
                return ExerciseState.WAITING

        # --- STAN 3: ECCENTRIC (Powrót po sukcesie) ---
        elif self.state == ExerciseState.ECCENTRIC:

            # Czekamy na powrót do leżenia
            if self.current_hip_angle > self.ANGLE_LYING:
                # Zliczamy tylko jeśli nie było błędu ze stopami
                if not self.rep_had_error:
                    self.reps_count += 1
                return ExerciseState.WAITING

        return self.state

    def update(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)

    def get_feedback(self, side_landmarks: list[dict[str, float]]) -> dict:
        """
        Zwraca dane do wyświetlenia w UI (Visualizer).
        """
        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(self.current_hip_angle, 1),
            "state": self.state.value,
            "errors": self.errors
        }