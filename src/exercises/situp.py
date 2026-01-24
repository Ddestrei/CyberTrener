from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class SitUp(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Sit-up"
        # Progi kątowe oparte na Twoich logach:
        # Siad (Góra) to ok. 128 stopni, Leżenie (Dół) to ok. 20 stopni.
        self.THRESHOLD_SITTING = 110.0
        self.THRESHOLD_LYING = 50.0

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        """
        Analizuje kąt biodra i zarządza maszyną stanów.
        Punkty: 12 (Ramię), 24 (Biodro), 26 (Kolano).
        """
        # Obliczamy kąt w biodrze
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        # Normalizacja do zakresu 0-180
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        # DEBUG (opcjonalnie odkomentuj, by widzieć logi w konsoli)
        # print(f"DEBUG | State: {self.state.name} | Angle: {angle:.2f}")

        # LOGIKA MASZYNY STANÓW

        # 1. Startujemy lub szukamy ponownego położenia się (Faza CONCENTRIC)
        if self.state == ExerciseState.WAITING or self.state == ExerciseState.CONCENTRIC:
            if angle < self.THRESHOLD_LYING:
                # Użytkownik leży - przechodzimy do fazy oczekiwania na podniesienie (ECCENTRIC)
                return ExerciseState.ECCENTRIC

        # 2. Faza podnoszenia się (Faza ECCENTRIC)
        elif self.state == ExerciseState.ECCENTRIC:
            if angle > self.THRESHOLD_SITTING:
                # ZALICZENIE POWTÓRZENIA
                self.reps_count += 1
                # KLUCZ: Wracamy do stanu CONCENTRIC (szukania leżenia).
                # To blokuje ponowne zliczenie w tej samej fazie ruchu!
                return ExerciseState.CONCENTRIC

        return self.state

    def update(self, landmarks: list[dict[str, float]]):
        """
        Główna metoda aktualizująca stan ćwiczenia, wywoływana w testach i aplikacji.
        """
        if landmarks:
            self.state = self.check_conditions(landmarks)

    def get_feedback(self, landmarks: list[dict[str, float]]) -> dict:
        """
        Zwraca dane do wyświetlenia w UI.
        """
        raw_angle = calculate_angle(landmarks[12], landmarks[24], landmarks[26])
        angle = raw_angle if raw_angle <= 180 else 360 - raw_angle

        return {
            "exercise": self.name,
            "reps": self.reps_count,
            "angle": round(angle, 1),
            "state": self.state.value
        }