from typing import Optional, Tuple, Dict
import math
from src.exercises.base import ExerciseBase, ExerciseState
from src.utils.geometry import calculate_angle


class BicepCurl(ExerciseBase):
    def __init__(self):
        super().__init__()
        self.name = "Bicep Curl"

        # --- PROGI RUCHU (ROM) ---
        self.ANGLE_START = 160.0  # Ręka wyprostowana (dół)
        self.ANGLE_START_TRIGGER = 130
        self.ANGLE_PEAK = 20.0  # Pełne zgięcie (góra) - dociągnięcie

        # --- PROGI BŁĘDÓW (SIDE VIEW) ---
        self.MAX_TORSO_SWING = 10.0  # Max odchylenie pleców od pionu
        self.MAX_ELBOW_DRIFT = 20.0  # Max ucieczka łokcia (przód/tył)

        # --- PROGI BŁĘDÓW (FRONT VIEW) ---
        self.MAX_SPINE_LATERAL = 10.0
        self.MAX_ELBOW_FLARE = 20.0
        self.MAX_WRIST_ALIGNMENT = 15.0

        self.rep_had_error = False
        self.current_elbow_angle = 180.0

    def _get_arm_landmarks(self, landmarks: list[dict[str, float]]) -> Tuple[str, Dict, Dict, Dict, Dict, Dict]:
        """
        Automatycznie wykrywa, która ręka ćwiczy (bazując na widoczności).
        Zwraca: (side_name, shoulder, elbow, wrist, hip, knee)
        """
        # Left: 11, 13, 15 | Right: 12, 14, 16
        left_vis = (landmarks[11]['visibility'] + landmarks[13]['visibility'] + landmarks[15]['visibility']) / 3
        right_vis = (landmarks[12]['visibility'] + landmarks[14]['visibility'] + landmarks[16]['visibility']) / 3

        if left_vis > right_vis:
            return "left", landmarks[11], landmarks[13], landmarks[15], landmarks[23], landmarks[25]
        else:
            return "right", landmarks[12], landmarks[14], landmarks[16], landmarks[24], landmarks[26]

    def _calculate_vertical_angle(self, p1: Dict, p2: Dict) -> float:
        """
        Oblicza kąt odchylenia odcinka P1->P2 od idealnego pionu.
        Wynik w stopniach (wartość bezwzględna).
        """
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        # W MediaPipe Y rośnie w dół. Atan2(dx, dy) zwróci kąt względem osi Y (pionu).
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)

    def _check_side_errors(self, shoulder, elbow, hip):
        """Analiza błędów z kamery bocznej."""

        # 1. ŁOKIEĆ PRZÓD/TYŁ (Elbow Drift)
        # Sprawdzamy kąt ramienia (Bark -> Łokieć) względem pionu.
        # Łokieć powinien być "zakotwiczony" pod barkiem.
        upper_arm_angle = self._calculate_vertical_angle(shoulder, elbow)

        # Jeśli odchylenie jest zbyt duże (czy to w przód, czy w tył)
        if abs(upper_arm_angle) > self.MAX_ELBOW_DRIFT:
            self.rep_had_error = True
            # print("Keep elbow fixed under shoulder!")
            # Możemy uściślić komunikat w przyszłości, sprawdzając znak kąta
            self.add_error("Keep elbow fixed under shoulder!")

        # 2. BUJANIE PLECAMI (Torso Swing)
        # Kąt tułowia (Bark -> Biodro) względem pionu.
        torso_angle = abs(self._calculate_vertical_angle(shoulder, hip))

        # print(f"torso_angle {torso_angle}")
        if torso_angle > self.MAX_TORSO_SWING:
            self.rep_had_error = True
            self.add_error("Keep back straight!")

    def _check_front_errors(self, front_landmarks: list[dict], active_side: str):
        """Analiza błędów z kamery przedniej."""

        l_shoulder, r_shoulder = front_landmarks[11], front_landmarks[12]
        l_hip, r_hip = front_landmarks[23], front_landmarks[24]

        # Obliczamy szerokość barków jako jednostkę referencyjną
        shoulder_width = abs(l_shoulder['x'] - r_shoulder['x'])

        # 1. KRĘGOSŁUP LEWO/PRAWO
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
            if "Don't lean sideways!" not in self.errors:
                self.add_error("Don't lean sideways!")

        # Ustalenie punktów dla aktywnej ręki
        if active_side == "left":
            active_shoulder = l_shoulder
            active_elbow = front_landmarks[13]
            active_wrist = front_landmarks[15]
        else:
            active_shoulder = r_shoulder
            active_elbow = front_landmarks[14]
            active_wrist = front_landmarks[16]

        # 2. ŁOKIEĆ NA BOKI (Flare) - Kąt ramienia
        flare_angle = abs(self._calculate_vertical_angle(active_shoulder, active_elbow))
        if flare_angle > self.MAX_ELBOW_FLARE:
            self.rep_had_error = True
            if "Don't flare elbow out!" not in self.errors:
                self.add_error("Don't flare elbow out!")

        # 3. LINIA NADGARSTEK-ŁOKIEĆ (POPRAWIONE)
        # Zamiast kąta pionowego, sprawdzamy odchylenie w osi X.
        # Nadgarstek nie powinien być dalej od łokcia niż 20% szerokości barków.

        wrist_elbow_diff_x = abs(active_elbow['x'] - active_wrist['x'])
        max_allowed_deviation = shoulder_width * 0.20  # 20% szerokości barków

        # Sprawdzamy błąd tylko jeśli ręka nie jest na samym szczycie (tam dłonie schodzą się do barków)
        if wrist_elbow_diff_x > max_allowed_deviation:
            self.rep_had_error = True
            # Wypisujemy wartość dla debugowania (możesz usunąć printa później)
            print(f"Wrist drift: {wrist_elbow_diff_x:.3f} > {max_allowed_deviation:.3f}")

            if "Keep wrist aligned!" not in self.errors:
                self.add_error("Keep wrist aligned!")

    def check_conditions(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> ExerciseState:

        # 1. Pobranie punktów
        side_name, shoulder, elbow, wrist, hip, knee = self._get_arm_landmarks(side_landmarks)

        # 2. Obliczenie głównego kąta (zgięcie łokcia)
        raw_angle = calculate_angle(shoulder, elbow, wrist)
        self.current_elbow_angle = raw_angle if raw_angle <= 180 else 360 - raw_angle
        print(f"current_elbow_angle {self.current_elbow_angle}")

        # 3. SPRAWDZANIE BŁĘDÓW (tylko gdy ćwiczymy, nie w spoczynku)
        if self.state != ExerciseState.WAITING or self.reps_count != 0:
            self._check_side_errors(shoulder, elbow, hip)

            if front_landmarks:
                self._check_front_errors(front_landmarks, side_name)

        # 4. MASZYNA STANÓW
        # STAN: WAITING (Ręka na dole)
        if self.state == ExerciseState.WAITING:
            # Reset błędów przy pełnym wyproście
            if self.current_elbow_angle > self.ANGLE_START:
                self.errors.clear()
                self.rep_had_error = False

            if self.current_elbow_angle < self.ANGLE_START_TRIGGER:
                return ExerciseState.CONCENTRIC

        # STAN: CONCENTRIC (Ruch w górę)
        elif self.state == ExerciseState.CONCENTRIC:
            # A. SUKCES - Dociągnięcie (< 60 stopni)
            print(f"{self.current_elbow_angle}")
            if self.current_elbow_angle < self.ANGLE_PEAK:
                return ExerciseState.ECCENTRIC

            if self.current_elbow_angle > self.ANGLE_START:
                # print("Full range of motion! Pull higher")
                self.add_error("Full range of motion! Pull higher")
                return ExerciseState.WAITING

        # STAN: ECCENTRIC (Ruch w dół)
        elif self.state == ExerciseState.ECCENTRIC:
            # Powrót na dół
            if self.current_elbow_angle > self.ANGLE_START:
                if not self.rep_had_error:
                    self.reps_count += 1
                return ExerciseState.WAITING

        return self.state

    def update(
            self,
            side_landmarks: list[dict[str, float]],
            front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """Entry point dla managera."""
        if side_landmarks:
            self.state = self.check_conditions(side_landmarks, front_landmarks)