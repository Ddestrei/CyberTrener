"""
WorkoutController - Central orchestrator for CyberTrener application.
Optimized with Parallel Pose Detection.
"""

import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor  # <--- NOWOŚĆ
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

import numpy as np # Dodane dla typowania

from src.processor.camera import CameraManager
from src.processor.pose import PoseDetector
from src.utils.smoothing import LandmarkSmoother
from src.exercises.base import ExerciseBase, ExerciseState
# Importy ćwiczeń (bez zmian)
from src.exercises.plank import Plank
from src.exercises.situp import SitUp
from src.exercises.bicep_curl import BicepCurl
from src.exercises.lateral_raise import LateralRaise
from src.exercises.overhead_press import OverheadPress


class WorkoutState(Enum):
    IDLE = "IDLE"
    READY = "READY"
    TRACKING = "TRACKING"
    PAUSED = "PAUSED"


@dataclass
class FrameData:
    frame: Optional[np.ndarray] = None
    landmarks: Optional[List[Dict]] = None
    is_available: bool = False


@dataclass
class WorkoutStats:
    exercise_name: str = "None"
    reps: int = 0
    state: str = "IDLE"
    exercise_state: str = "WAITING"
    errors: List[str] = field(default_factory=list)
    is_tracking: bool = False
    front_cam_online: bool = False
    side_cam_online: bool = False
    current_angle: float = 0.0  # [NEW]


EXERCISE_REGISTRY = {
    "plank": Plank,
    "sit ups": SitUp,
    "bicep curl": BicepCurl,
    "lateral raise": LateralRaise,
    "press": OverheadPress,
}

CAMERA_REQUIREMENTS = {
    "plank": {"front": False, "side": True},
    "sit ups": {"front": False, "side": True},
    "bicep curl": {"front": True, "side": True},
    "lateral raise": {"front": True, "side": False},
    "press": {"front": True, "side": True},
}


class WorkoutController:
    # TTS cooldown to prevent spam (seconds)
    TTS_COOLDOWN = 3.0
    ERROR_ANNOUNCE_COOLDOWN = 5.0

    def __init__(
            self,
            camera_manager: Optional[CameraManager] = None,
            tts_manager: Optional[Any] = None,
            command_queue: Optional[queue.Queue] = None,
    ):
        self.camera_manager = camera_manager or CameraManager()
        self.tts_manager = tts_manager
        self.command_queue = command_queue or queue.Queue()

        self.last_speach = ""
        self.last_speach_time = None

        self._detector_front = PoseDetector()
        self._detector_side = PoseDetector()

        self._smoother_front = LandmarkSmoother(window_size=5, min_visibility=0.5)
        self._smoother_side = LandmarkSmoother(window_size=5, min_visibility=0.5)

        # Thread Pool dla równoległej detekcji (2 wątki = 2 kamery)
        # max_workers=2 wystarczy, więcej nie da zysku przy 2 kamerach
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._workout_state = WorkoutState.IDLE
        self._current_exercise_name: str = "None"
        self._current_exercise: Optional[ExerciseBase] = None
        self._is_tracking = False

        self._last_tts_time: float = 0.0
        self._last_error_announce_time: float = 0.0
        self._last_announced_errors: set = set()

        self._front_cam_id: Optional[int] = None
        self._side_cam_id: Optional[int] = None
        self._single_cam_mode = False

        self._lock = threading.Lock()

    # =========================================================================
    # CAMERA MANAGEMENT
    # =========================================================================

    def start_cameras(self, front_id: int, side_id: int) -> None:
        with self._lock:
            self._front_cam_id = front_id
            self._side_cam_id = side_id
            self._single_cam_mode = (front_id == side_id)

            self.camera_manager.start_camera('front', front_id)

            if not self._single_cam_mode:
                self.camera_manager.start_camera('side', side_id)
            else:
                self.camera_manager.stop_role('side')

    def stop_cameras(self) -> None:
        self.camera_manager.stop_all()
        self._reset_smoothers()

    def _reset_smoothers(self) -> None:
        self._smoother_front.reset()
        self._smoother_side.reset()

    # =========================================================================
    # COMMAND PROCESSING (Bez zmian)
    # =========================================================================

    def process_commands(self) -> None:
        while True:
            try:
                cmd = self.command_queue.get_nowait()
                self._handle_command(cmd)
            except queue.Empty:
                break

    def _handle_command(self, cmd: str) -> None:
        cmd = cmd.lower().strip()
        with self._lock:
            if cmd in EXERCISE_REGISTRY:
                self._select_exercise(cmd)
            elif cmd == "start":
                self._start_tracking()
            elif cmd == "end":
                self._stop_tracking()
            elif cmd == "reset":
                self._reset_exercise()
            elif cmd == "next":
                self._next_exercise()
            elif cmd == "previous":
                self._previous_exercise()

    def _select_exercise(self, exercise_name: str) -> None:
        if exercise_name not in EXERCISE_REGISTRY:
            return
        exercise_class = EXERCISE_REGISTRY[exercise_name]
        self._current_exercise = exercise_class()
        self._current_exercise_name = exercise_name
        self._workout_state = WorkoutState.READY
        self._is_tracking = False
        self._reset_smoothers()
        self._speak(f"You are doing {self._current_exercise.name}")

    def _start_tracking(self) -> None:
        if self._current_exercise is None:
            self._speak("Please select an exercise first")
            return
        self._is_tracking = True
        self._workout_state = WorkoutState.TRACKING
        self._current_exercise.reset_stats()
        self._speak("Start the exercise")

    def _stop_tracking(self) -> None:
        self._is_tracking = False
        self._workout_state = WorkoutState.READY if self._current_exercise else WorkoutState.IDLE
        self._speak("Stop the exercise")

    def _reset_exercise(self) -> None:
        if self._current_exercise:
            self._current_exercise.reset_stats()
        self._last_announced_errors.clear()

    def _next_exercise(self) -> None:
        exercises = list(EXERCISE_REGISTRY.keys())
        if not exercises: return
        try:
            current_idx = exercises.index(self._current_exercise_name)
            next_idx = (current_idx + 1) % len(exercises)
        except ValueError:
            next_idx = 0
        self._select_exercise(exercises[next_idx])

    def _previous_exercise(self) -> None:
        exercises = list(EXERCISE_REGISTRY.keys())
        if not exercises: return
        try:
            current_idx = exercises.index(self._current_exercise_name)
            prev_idx = (current_idx - 1) % len(exercises)
        except ValueError:
            prev_idx = 0
        self._select_exercise(exercises[prev_idx])

    # =========================================================================
    # FRAME PROCESSING PIPELINE (ZOPTYMALIZOWANE)
    # =========================================================================

    def process_frame(self) -> Dict[str, Any]:
        # 1. Process commands
        self.process_commands()

        # 2. Parallel Processing for Cameras
        # Uruchamiamy przetwarzanie obu kamer jednocześnie
        if not self._single_cam_mode:
            # Dual Camera: Równolegle
            future_front = self._executor.submit(
                self._process_camera, 'front', self._detector_front, self._smoother_front
            )
            future_side = self._executor.submit(
                self._process_camera, 'side', self._detector_side, self._smoother_side
            )

            # Czekamy na wyniki (join)
            front_data = future_front.result()
            side_data = future_side.result()
        else:
            # Single Camera: Tylko front, side jest kopią
            front_data = self._process_camera('front', self._detector_front, self._smoother_front)
            side_data = FrameData(
                frame=front_data.frame.copy() if front_data.frame is not None else None,
                landmarks=front_data.landmarks,
                is_available=front_data.is_available
            )

        # 3. Exercise Logic
        errors = []
        exercise_state_str = "WAITING"
        angle_to_display = 0.0  # [NEW]

        if self._is_tracking and self._current_exercise:
            primary_landmarks = self._get_primary_landmarks(front_data, side_data)
            secondary_landmarks = self._get_secondary_landmarks(front_data, side_data)

            if primary_landmarks:
                self._current_exercise.update(primary_landmarks, secondary_landmarks)
                errors = self._current_exercise.errors.copy()
                exercise_state_str = self._current_exercise.state.value
                angle_to_display = getattr(self._current_exercise, 'current_angle', 0.0)
                self._announce_errors(errors)


        # 4. Build State
        stats = WorkoutStats(
            exercise_name=self._current_exercise_name,
            reps=self._current_exercise.reps_count if self._current_exercise else 0,
            state=self._workout_state.value,
            exercise_state=exercise_state_str,
            errors=errors,
            is_tracking=self._is_tracking,
            front_cam_online=front_data.is_available,
            side_cam_online=side_data.is_available,
            current_angle=angle_to_display  # [NEW]
        )

        return {
            'stats': stats,
            'front': front_data,
            'side': side_data,
        }

    def _process_camera(
            self,
            role: str,
            detector: PoseDetector,
            smoother: LandmarkSmoother
    ) -> FrameData:
        """Helper function running in a separate thread."""
        try:
            frame = self.camera_manager.get_frame(role)

            if frame is None:
                return FrameData(is_available=False)

            # Heavy lifting happens here (MediaPipe)
            raw_landmarks = detector.detect(frame)

            smoothed_landmarks = None
            if raw_landmarks:
                smoothed_landmarks = smoother.update(raw_landmarks)

            return FrameData(
                frame=frame,
                landmarks=smoothed_landmarks,
                is_available=True
            )
        except Exception as e:
            # Zabezpieczenie przed błędem w wątku
            print(f"Error processing {role} camera: {e}")
            return FrameData(is_available=False)

    def _get_primary_landmarks(self, front_data, side_data):
        if self._current_exercise_name not in CAMERA_REQUIREMENTS:
            return side_data.landmarks if side_data.landmarks else front_data.landmarks
        reqs = CAMERA_REQUIREMENTS[self._current_exercise_name]
        if reqs.get("side", False):
            return side_data.landmarks
        return front_data.landmarks

    def _get_secondary_landmarks(self, front_data, side_data):
        if self._current_exercise_name not in CAMERA_REQUIREMENTS:
            return front_data.landmarks if front_data.landmarks else None
        reqs = CAMERA_REQUIREMENTS[self._current_exercise_name]
        if reqs.get("side", False):
            return front_data.landmarks if reqs.get("front", False) else None
        return side_data.landmarks

    # =========================================================================
    # TTS & API (Bez zmian)
    # =========================================================================

    def _speak(self, text: str) -> None:
        if self.tts_manager is None: return
        if self.last_speach != text:
            #print(self.last_speach)
            self.tts_manager.add_to_queue(text)
            self.last_speach = text
            self.last_speach_time = time.time()
        else:
            #print(time.time() - self.last_speach_time)
            if time.time() - self.last_speach_time > 2:
                self.tts_manager.add_to_queue(text)
                self.last_speach_time = time.time()

    def _announce_errors(self, errors: List[str]) -> None:
        if len(errors) > 0:
            self._speak(errors[0])

    def set_exercise(self, exercise_name: str) -> bool:
        if exercise_name.lower() not in EXERCISE_REGISTRY: return False
        self._select_exercise(exercise_name.lower())
        return True

    def start(self) -> None: self._start_tracking()
    def stop(self) -> None: self._stop_tracking()
    def reset(self) -> None: self._reset_exercise()

    def get_stats(self) -> WorkoutStats:
        return WorkoutStats(
            exercise_name=self._current_exercise_name,
            reps=self._current_exercise.reps_count if self._current_exercise else 0,
            state=self._workout_state.value,
            exercise_state=self._current_exercise.state.value if self._current_exercise else "WAITING",
            errors=self._current_exercise.errors.copy() if self._current_exercise else [],
            is_tracking=self._is_tracking,
            current_angle=getattr(self._current_exercise, 'current_angle', 0.0) if self._current_exercise else 0.0  # [NEW]
        )

    def inject_command(self, command: str) -> None:
        self.command_queue.put(command)

    def cleanup(self) -> None:
        self.stop_cameras()
        self._detector_front.close()
        self._detector_side.close()
        # Shutdown thread pool
        self._executor.shutdown(wait=False)