import sys
import os

# Ensure src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exercises.base import ExerciseBase, ExerciseState


class MockExercise(ExerciseBase):
    """Implementation for testing the base class logic."""

    def __init__(self):
        super().__init__()
        self.name = "Mock Exercise"

    def check_conditions(self, landmarks: list[dict[str, float]]) -> ExerciseState:
        # Mock logic: value represents a virtual 'angle' or 'position'
        val = landmarks[0]['val']
        if val >= 100: return ExerciseState.WAITING
        if val <= 30: return ExerciseState.CONCENTRIC
        return ExerciseState.ECCENTRIC


def test_base_logic_counting():
    exercise = MockExercise()

    # Mock sequence representing one full rep:
    # 100 (Wait) -> 60 (Moving) -> 20 (Peak/Concentric) -> 60 (Lowering) -> 110 (Finish)
    mock_sequence = [100, 60, 20, 20, 60, 110]

    print(f"Starting test for: {exercise.name}")
    for value in mock_sequence:
        exercise.update([{'val': value}])
        print(f"Input: {value:3} | State: {exercise.state.value:10} | Reps: {exercise.reps_count}")

    # Verify DoD: The base class successfully counts the rep
    assert exercise.reps_count == 1
    print("\n✅ DoD Success: Reps counted correctly from mock data.")


if __name__ == "__main__":
    test_base_logic_counting()