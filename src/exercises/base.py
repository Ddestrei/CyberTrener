from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class ExerciseState(Enum):
    """Possible states for the exercise state machine."""
    WAITING = "WAITING"
    CONCENTRIC = "CONCENTRIC"
    ECCENTRIC = "ECCENTRIC"


class ExerciseBase(ABC):
    """
    Abstract base class for all exercises.
    Handles state management, rep counting, and error collection.
    """

    def __init__(self):
        # Initializing fields as empty/default values
        self.name: str = ""
        self.reps_count: int = 0
        self.state: ExerciseState = ExerciseState.WAITING
        self.errors: list[str] = []

    @abstractmethod
    def check_conditions(
        self,
        side_landmarks: list[dict[str, float]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> Optional[ExerciseState]:
        """
        Analyzes landmarks and returns the suggested ExerciseState.
        Must be implemented by specific exercise classes.
        """
        pass

    def update(
        self,
        side_landmarks: Optional[list[dict[str, float]]],
        front_landmarks: Optional[list[dict[str, float]]] = None
    ) -> None:
        """
        Core state machine logic.
        Transitions: WAITING -> CONCENTRIC -> ECCENTRIC -> WAITING (Count Rep)
        """
        if not side_landmarks:
            return

        suggested_state = self.check_conditions(side_landmarks, front_landmarks)

        if suggested_state is None:
            return

        # State transition logic
        if self.state == ExerciseState.WAITING:
            if suggested_state == ExerciseState.CONCENTRIC:
                self.state = ExerciseState.CONCENTRIC

        elif self.state == ExerciseState.CONCENTRIC:
            if suggested_state == ExerciseState.ECCENTRIC:
                self.state = ExerciseState.ECCENTRIC

        elif self.state == ExerciseState.ECCENTRIC:
            if suggested_state == ExerciseState.WAITING:
                self.reps_count += 1
                self.state = ExerciseState.WAITING
                self.errors.clear()

    def add_error(self, message: str) -> None:
        """Adds a unique error message to the current list."""
        if message not in self.errors:
            self.errors.append(message)

    def reset_stats(self) -> None:
        """Resets reps, state, and errors."""
        self.reps_count = 0
        self.state = ExerciseState.WAITING
        self.errors.clear()