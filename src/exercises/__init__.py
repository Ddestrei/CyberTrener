# filepath: src/exercises/__init__.py
from src.exercises.base import ExerciseBase, ExerciseState
from src.exercises.plank import Plank
from src.exercises.situp import SitUp
from src.exercises.bicep_curl import BicepCurl
from src.exercises.lateral_raise import LateralRaise
from src.exercises.overhead_press import OverheadPress

# Registry mapping voice-friendly names to classes
EXERCISE_REGISTRY: dict[str, type[ExerciseBase]] = {
    "plank": Plank,
    "sit-ups": SitUp,
    "situps": SitUp,  # alias
    "bicep curl": BicepCurl,
    "bicep curls": BicepCurl,  # alias
    "curls": BicepCurl,  # alias
    "lateral raise": LateralRaise,
    "lateral raises": LateralRaise,  # alias
    "overhead press": OverheadPress,
    "ohp": OverheadPress,  # alias
    "press": OverheadPress,  # alias
}

# Camera requirements per exercise (for validation)
CAMERA_REQUIREMENTS: dict[str, dict] = {
    "plank": {"required": ["side"], "optional": ["front"]},
    "sit-ups": {"required": ["side"], "optional": []},
    "bicep curl": {"required": ["side"], "optional": ["front"]},
    "lateral raise": {"required": ["front", "side"], "optional": []},
    "overhead press": {"required": ["front", "side"], "optional": []},
}

def get_exercise(name: str) -> ExerciseBase | None:
    """Factory function to create exercise instance by name."""
    name = name.lower().strip()
    if name in EXERCISE_REGISTRY:
        return EXERCISE_REGISTRY[name]()
    return None

def list_exercises() -> list[str]:
    """Return list of unique exercise names (no aliases)."""
    unique = set()
    for name, cls in EXERCISE_REGISTRY.items():
        # Use class name as unique identifier
        if cls.__name__ not in [c.__name__ for c in unique]:
            unique.add(cls)
    return [cls.__name__.lower() for cls in unique]