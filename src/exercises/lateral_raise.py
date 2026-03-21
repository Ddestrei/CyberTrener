from typing import Optional, Tuple, Dict
import math
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class LateralRaise(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Lateral Raise"

        # --- PROGI RUCHU (Shoulder Abduction) ---
        # 0 stopni to ręka pionowo w dół, 90 stopni to ręka równolegle do podłogi
        self.ANGLE_START = 20.0  # Ręce przy tułowiu
        self.ANGLE_START_TRIGGER = 35.0
        self.ANGLE_PEAK = 80.0  # Minimalna wysokość wznosu (szczyt)
        self.ANGLE_TOO_HIGH = 115

        # --- PROGI BŁĘDÓW ---
        self.MAX_TORSO_SWING = 12.0  # Bujanie przód-tył (kamera boczna)
        self.MAX_ELBOW_BENT = 150.0  # Jeśli kąt w łokciu < 150, ręka jest zbyt zgięta
        self.MAX_SPINE_LATERAL = 10.0  # Przechylanie się na boki (kamera przednia)

        self.rep_had_error = False
        self.current_abduction_angle = 0.0

    def _get_arm_landmarks(self, landmarks: list[dict[str, float]]) -> Tuple[str, Dict, Dict, Dict, Dict, Dict]:
        """Wykrywa aktywną stronę na podstawie widoczności (podobnie jak w bicep curl)."""
        left_vis = (landmarks[11]['visibility'] + landmarks[13]['visibility'] + landmarks[15]['visibility']) / 3
        right_vis = (landmarks[12]['visibility'] + landmarks[14]['visibility'] + landmarks[16]['visibility']) / 3

        if left_vis > right_vis:
            # Lewa strona: Bark(11), Łokieć(13), Nadgarstek(15), Biodro(23), Kolano(25)
            return "left", landmarks[11], landmarks[13], landmarks[15], landmarks[23], landmarks[25]
        else:
            # Prawa strona: Bark(12), Łokieć(14), Nadgarstek(16), Biodro(24), Kolano(26)
            return "right", landmarks[12], landmarks[14], landmarks[16], landmarks[24], landmarks[26]

    def _calculate_vertical_angle(self, p1: Dict, p2: Dict) -> float:
        """Kąt od pionu (z Twojej implementacji bicep_curl)."""
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)

    def _check_side_errors(self, shoulder, hip):
        """Kamera boczna: wykrywanie bujania tułowiem (momentum)."""
        torso_angle = abs(self._calculate_vertical_angle(shoulder, hip))
        if torso_angle > self.MAX_TORSO_SWING:
            self.rep_had_error = True
            self.add_error("Don't swing! Keep torso still.")

    def _check_front_errors(self, front_landmarks: list[dict], active_side: str, elbow_angle: float):
        """Kamera przednia: stabilność kręgosłupa i zgięcie łokcia."""

        # 1. Stabilność kręgosłupa (identycznie jak w curl)
        l_shoulder, r_shoulder = front_landmarks[11], front_landmarks[12]
        l_hip, r_hip = front_landmarks[23], front_landmarks[24]

        mid_shoulder_x = (l_shoulder['x'] + r_shoulder['x']) / 2
        mid_shoulder_y = (l_shoulder['y'] + r_shoulder['y']) / 2
        mid_hip_x = (l_hip['x'] + r_hip['x']) / 2
        mid_hip_y = (l_hip['y'] + r_hip['y']) / 2

        spine_lean = abs(self._calculate_vertical_angle(
            {'x': mid_shoulder_x, 'y': mid_shoulder_y},
            {'x': mid_hip_x, 'y': mid_hip_y}
        ))

        if spine_lean > self.MAX_SPINE_LATERAL:
            self.rep_had_error = True
            self.add_error("Keep your spine vertical!")

        # 2. Zbyt mocno zgięte łokcie (T-Rex arms)
        # W lateral raise dopuszczalne jest lekkie ugięcie, ale nie "pompowanie" łokciami
        if elbow_angle < self.MAX_ELBOW_BENT:
            self.rep_had_error = True
            self.add_error("Keep arms straighter!")

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:

        # 1. Pobranie punktów
        side_name, shoulder, elbow, wrist, hip, knee = self._get_arm_landmarks(side_landmarks)

        # 2. Obliczenie kątów
        # Główny kąt: Odwiedzenie barku (Hip -> Shoulder -> Elbow)
        # Używamy calculate_angle, żeby sprawdzić jak wysoko są łokcie względem tułowia
        self.current_abduction_angle = calculate_angle(hip, shoulder, elbow)

        if self.current_abduction_angle > 180:
            self.current_abduction_angle = 360 -self.current_abduction_angle

        print(f"current_abduction_angle {self.current_abduction_angle}")
        # Pomocniczy kąt: Zgięcie łokcia (Shoulder -> Elbow -> Wrist) do walidacji techniki
        elbow_angle = calculate_angle(shoulder, elbow, wrist)

        # 3. SPRAWDZANIE BŁĘDÓW
        if self.state != ExerciseState.WAITING or self.reps_count != 0:
            self._check_side_errors(shoulder, hip)
            if front_landmarks:
                self._check_front_errors(front_landmarks, side_name, elbow_angle)

        if self.current_abduction_angle > self.ANGLE_TOO_HIGH:
            self.add_error("Arms are too high!")
            self.rep_had_error = True
            return ExerciseState.WAITING

        # 4. MASZYNA STANÓW
        # STAN: WAITING (Ręce w dole)
        if self.state == ExerciseState.WAITING:
            if self.current_abduction_angle < self.ANGLE_START:
                self.errors.clear()
                self.rep_had_error = False

            if self.current_abduction_angle > self.ANGLE_START_TRIGGER:
                return ExerciseState.CONCENTRIC

        # STAN: CONCENTRIC (Ruch w górę)
        elif self.state == ExerciseState.CONCENTRIC:
            # Sukces - osiągnięcie poziomu barków
            if self.current_abduction_angle > self.ANGLE_PEAK:
                return ExerciseState.ECCENTRIC

            # Błąd - powrót na dół przed osiągnięciem góry
            if self.current_abduction_angle < self.ANGLE_START:
                self.add_error("Go higher! Parallel to the floor.")
                return ExerciseState.WAITING

        # STAN: ECCENTRIC (Ruch w dół)
        elif self.state == ExerciseState.ECCENTRIC:
            if self.current_abduction_angle < self.ANGLE_START:
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