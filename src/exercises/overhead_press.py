from typing import Optional, Tuple, Dict
import math
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class OverheadPress(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Overhead Press"

        # --- PROGI RUCHU (Shoulder Abduction/Elevation) ---
        # 0 stopni - ręka wzdłuż tułowia, 160-180 stopni - ręka pionowo nad głową
        self.ANGLE_START = 80.0  # Start: dłonie/łokcie na wysokości barków
        self.ANGLE_START_TRIGGER = 100.0
        self.ANGLE_PEAK = 150.0  # Szczyt: wyprostowane ręce nad głową

        # --- PROGI BŁĘDÓW ---
        self.MAX_BACK_ARCH = 20.0  # Max odchylenie tułowia w tył (kamera boczna)
        self.MIN_ELBOW_EXTENSION = 160.0  # Progiem "blokady" łokcia na szczycie
        self.MAX_SPINE_LATERAL = 10.0  # Przechył na boki (kamera przednia)

        self.rep_had_error = False
        self.current_shoulder_angle = 0.0

    def _get_arm_landmarks(self, landmarks: list[dict[str, float]]) -> Tuple[str, Dict, Dict, Dict, Dict, Dict]:
        """Wykrywa aktywną stronę na podstawie widoczności."""
        left_vis = (landmarks[11]['visibility'] + landmarks[13]['visibility'] + landmarks[15]['visibility']) / 3
        right_vis = (landmarks[12]['visibility'] + landmarks[14]['visibility'] + landmarks[16]['visibility']) / 3

        if left_vis > right_vis:
            return "left", landmarks[11], landmarks[13], landmarks[15], landmarks[23], landmarks[25]
        else:
            return "right", landmarks[12], landmarks[14], landmarks[16], landmarks[24], landmarks[26]

    def _calculate_vertical_angle(self, p1: Dict, p2: Dict) -> float:
        """Oblicza kąt od pionu (używane do detekcji wygięcia pleców)."""
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)

    def _check_side_errors(self, shoulder, hip):
        """Kamera boczna: wykrywanie nadmiernego wygięcia kręgosłupa w tył."""
        # W OHP przy wyciskaniu ludzie często wypychają biodra do przodu i klatkę do góry
        # Tułów (Bark -> Biodro) odchyla się wtedy od pionu w tył.
        torso_angle = self._calculate_vertical_angle(shoulder, hip)

        # Jeśli kąt jest ujemny i przekracza próg (zależnie od ustawienia kamery bocznej)
        # Przyjmujemy abs(), by wykryć odchylenie w dowolną stronę od pionu
        if abs(torso_angle) > self.MAX_BACK_ARCH:
            self.rep_had_error = True
            self.add_error("Don't lean back too much! Brace your core.")

    def _check_front_errors(self, front_landmarks: list[dict], elbow_angle: float):
        """Kamera przednia: symetria i stabilność."""
        l_shoulder, r_shoulder = front_landmarks[11], front_landmarks[12]
        l_hip, r_hip = front_landmarks[23], front_landmarks[24]

        # 1. Przechył boczny kręgosłupa
        mid_shoulder = {'x': (l_shoulder['x'] + r_shoulder['x']) / 2, 'y': (l_shoulder['y'] + r_shoulder['y']) / 2}
        mid_hip = {'x': (l_hip['x'] + r_hip['x']) / 2, 'y': (l_hip['y'] + r_hip['y']) / 2}

        spine_lean = abs(self._calculate_vertical_angle(mid_shoulder, mid_hip))
        if spine_lean > self.MAX_SPINE_LATERAL:
            self.rep_had_error = True
            self.add_error("Keep your body centered!")
        print(f"elbow angle {elbow_angle}")
        # 2. Niepełny wyprost łokcia w fazie szczytowej
        if self.state == ExerciseState.CONCENTRIC and self.current_shoulder_angle > self.ANGLE_PEAK:
            if elbow_angle < self.MIN_ELBOW_EXTENSION:
                self.rep_had_error = True
                self.add_error("Lock out your elbows at the top!")

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:

        # 1. Pobranie punktów
        side_name, shoulder, elbow, wrist, hip, knee = self._get_arm_landmarks(side_landmarks)

        # 2. Obliczenie głównego kąta - wznos ramienia (Hip -> Shoulder -> Elbow)
        # W OHP ręka idzie od poziomu barków (~90st) do pełnego pionu (~180st)
        self.current_shoulder_angle = calculate_angle(hip, shoulder, elbow)

        # Normalizacja kąta do 180 stopni (MediaPipe/Geometry fix)
        if self.current_shoulder_angle > 180:
            self.current_shoulder_angle = 360 - self.current_shoulder_angle

        # Kąt w łokciu do sprawdzania lockoutu
        elbow_angle = calculate_angle(shoulder, elbow, wrist)

        # 3. SPRAWDZANIE BŁĘDÓW (tylko w trakcie ruchu)
        if self.state != ExerciseState.WAITING or self.reps_count != 0:
            self._check_side_errors(shoulder, hip)
            if front_landmarks:
                self._check_front_errors(front_landmarks, elbow_angle)

        # 4. MASZYNA STANÓW
        # STAN: WAITING (Sztanga/Hantle przy barkach)
        if self.state == ExerciseState.WAITING:
            if self.current_shoulder_angle < self.ANGLE_START:
                self.errors.clear()
                self.rep_had_error = False

            if self.current_shoulder_angle > self.ANGLE_START_TRIGGER:
                return ExerciseState.CONCENTRIC

        # STAN: CONCENTRIC (Wyciskanie w górę)
        elif self.state == ExerciseState.CONCENTRIC:
            if self.current_shoulder_angle > self.ANGLE_PEAK:
                return ExerciseState.ECCENTRIC

            # Błąd - opuszczenie przed końcem ruchu
            if self.current_shoulder_angle < self.ANGLE_START:
                self.add_error("Full range of motion! Press higher.")
                return ExerciseState.WAITING

        # STAN: ECCENTRIC (Opuszczanie do barków)
        elif self.state == ExerciseState.ECCENTRIC:
            if self.current_shoulder_angle < self.ANGLE_START:
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