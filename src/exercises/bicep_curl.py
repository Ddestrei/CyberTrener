from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class BicepCurl(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Bicep Curl"
        self.ELBOW_EXTENDED = 160.0
        self.ELBOW_FLEXED = 95.0
        self.TRUNK_LEAN_MAX = 13.0
        self.rep_had_error = False

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        # 1. Pobieranie kątów
        raw_elbow = calculate_angle(landmarks[12], landmarks[14], landmarks[16])
        elbow_angle = raw_elbow if raw_elbow <= 180 else 360 - raw_elbow

        raw_trunk = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        trunk_angle = raw_trunk if raw_trunk <= 180 else 360 - raw_trunk

        # 2. Obliczanie odchylenia pleców
        deviation = abs(180.0 - trunk_angle)

        # Logowanie błędu w czasie rzeczywistym
        if deviation > self.TRUNK_LEAN_MAX:
            # if not self.rep_had_error:
            #     print(f">>> WYKRYTO OSZUSTWO! Odchylenie: {round(deviation, 1)}° (Kąt: {round(trunk_angle, 1)}°)")
            self.rep_had_error = True
            if "Stop swinging!" not in self.errors:
                self.add_error("Stop swinging!")

        # 3. Maszyna stanów z logowaniem przejść
        if self.state == ExerciseState.WAITING:
            if elbow_angle > self.ELBOW_EXTENDED:
                # print("--- Start powtórzenia: Ręka wyprostowana (Faza w górę) ---")
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            if elbow_angle < self.ELBOW_FLEXED:
                # print(f"--- Szczyt osiągnięty (Kąt łokcia: {round(elbow_angle, 1)}°) ---")
                if not self.rep_had_error:
                    self.reps_count += 1
                    # print(f"POWTÓRZENIE ZALICZONE! Licznik: {self.reps_count}")
                # else:
                    # print("POWTÓRZENIE ODRZUCONE: Wykryto bujanie plecami w trakcie ruchu.")
                return ExerciseState.ECCENTRIC

        elif self.state == ExerciseState.ECCENTRIC:
            # Opcjonalny print kontrolny fazy opuszczania
            if elbow_angle > self.ELBOW_EXTENDED:
                # print("--- Koniec powtórzenia: Ręka wróciła do dołu ---")
                self.rep_had_error = False
                self.errors.clear()
                return ExerciseState.CONCENTRIC

        return self.state

    def update(self, landmarks: list[dict[str, float]]):
        if landmarks:
            old_state = self.state
            self.state = self.check_conditions(landmarks)
            # Logowanie zmiany stanu dla lepszego debugowania
            # if old_state != self.state:
                # print(f"[DEBUG] Zmiana stanu: {old_state} -> {self.state}")