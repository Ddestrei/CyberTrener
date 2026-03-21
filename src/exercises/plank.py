import time
from typing import Optional, Tuple, Dict
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class Plank(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Plank"

        # --- PROGI (Side View) ---
        self.SAG_THRESHOLD = 165.0  # Biodra za nisko
        self.PIKE_THRESHOLD = 195.0  # Biodra za wysoko

        # --- LOGIKA CZASU ---
        self.last_second_timestamp: Optional[float] = None

    def _get_side_landmarks(self, landmarks: list[dict[str, float]]) -> Tuple[Dict, Dict, Dict]:
        """Automatyczne wykrywanie strony (lewa/prawa)."""
        left_vis = (landmarks[11]['visibility'] + landmarks[23]['visibility'] + landmarks[27]['visibility']) / 3
        right_vis = (landmarks[12]['visibility'] + landmarks[24]['visibility'] + landmarks[28]['visibility']) / 3

        if left_vis > right_vis:
            return landmarks[11], landmarks[23], landmarks[27]
        else:
            return landmarks[12], landmarks[24], landmarks[28]

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:

        shoulder, hip, ankle = self._get_side_landmarks(side_landmarks)
        angle = calculate_angle(shoulder, hip, ankle)

        self.errors.clear()

        # Walidacja pozycji
        if angle < self.SAG_THRESHOLD:
            self.add_error("Hips too low!")
        elif angle > self.PIKE_THRESHOLD:
            self.add_error("Hips too high!")

        # Stan aktywny (CONCENTRIC) jeśli użytkownik jest w pozycji poziomej
        if 130 < angle < 230:
            return ExerciseState.CONCENTRIC

        return ExerciseState.WAITING

    def update(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        if not side_landmarks:
            self.last_second_timestamp = None
            return

        # 1. Sprawdź warunki i błędy
        self.state = self.check_conditions(side_landmarks, front_landmarks)

        # 2. Logika timestampów
        # Nabijamy repy (sekundy) tylko gdy:
        # - Jesteśmy w stanie aktywnym
        # - Nie ma żadnych błędów technicznych
        if self.state == ExerciseState.CONCENTRIC and not self.errors:
            current_time = time.time()

            # Jeśli to pierwsza klatka poprawnego trzymania, zainicjuj timestamp
            if self.last_second_timestamp is None:
                self.last_second_timestamp = current_time

            # Sprawdź czy od ostatniego zapisanego repa (sekundy) minęła co najmniej 1 sekunda
            elif current_time - self.last_second_timestamp >= 1.0:
                self.reps_count += 1
                # Aktualizujemy timestamp na obecny, by zacząć odliczać kolejną sekundę
                self.last_second_timestamp = current_time
        else:
            # RESET TIMESTAMP: jeśli jest błąd lub użytkownik przerwał ćwiczenie,
            # zerujemy licznik czasu dla obecnej sekundy (ale reps_count zostaje).
            self.last_second_timestamp = None

    def reset_stats(self) -> None:
        """Reset wszystkiego przy nowej sesji."""
        super().reset_stats()
        self.last_second_timestamp = None