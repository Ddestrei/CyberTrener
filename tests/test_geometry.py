import pytest
import math
from src.utils.geometry import (
    calculate_angle,
    calculate_distance
)

# Note: The Y axis in Mediapipe is faced downwards.
# Which means, that angles grow clockwise, not counter-clockwise.

class TestCalculateAngle:
    """Test 2D angle calculation using atan2."""
    
    def test_right_angle_90_degrees(self):
        """Test that a right angle returns 90 degrees."""
        # Right angle: horizontal-vertical
        point_a = {'x': 0.0, 'y': 0.5}  # Left
        point_b = {'x': 0.5, 'y': 0.5}  # Center (vertex)
        point_c = {'x': 0.5, 'y': 0.0}  # Up
        
        angle = calculate_angle(point_a, point_b, point_c)
        assert abs(angle - 90.0) < 0.1, f"Expected ~90°, got {angle}°"
    
    def test_straight_line_180_degrees(self):
        """Test that a straight line returns 180 degrees."""
        point_a = {'x': 0.0, 'y': 0.5}
        point_b = {'x': 0.5, 'y': 0.5}
        point_c = {'x': 1.0, 'y': 0.5}
        
        angle = calculate_angle(point_a, point_b, point_c)
        assert abs(angle - 180.0) < 0.1, f"Expected ~180°, got {angle}°"
    
    def test_acute_angle_45_degrees(self):
        """Test a 45-degree angle."""
        point_a = {'x': 1.0, 'y': 0.5}
        point_b = {'x': 0.5, 'y': 0.5}

        # Calculate C at 45 degrees relative to horizontal right
        # Y is inverted in MediaPipe coordinate system (see note at the top)
        point_c = {
            'x': 0.5 + 0.5 * math.cos(math.radians(45)), 
            'y': 0.5 + 0.5 * math.sin(math.radians(45)) # +sin = down
        }

        angle = calculate_angle(point_a, point_b, point_c)
        assert abs(angle - 45.0) < 1.0, f"Expected ~45°, got {angle}°"
    
    def test_zero_angle(self):
        """Test that aligned points return 0 or 360 degrees."""
        point_a = {'x': 1.0, 'y': 0.5} # Right of B
        point_b = {'x': 0.5, 'y': 0.5}
        point_c = {'x': 0.8, 'y': 0.5} # Also right of B
        
        angle = calculate_angle(point_a, point_b, point_c)
        # Should be close to 0 or 360
        assert angle < 1.0 or angle > 359.0, f"Expected ~0°/360°, got {angle}°"
    
    def test_270_degrees(self):
        """Test 270-degree angle (useful for arm down position)."""
        point_a = {'x': 0.0, 'y': 0.5}
        point_b = {'x': 0.5, 'y': 0.5}
        point_c = {'x': 0.5, 'y': 1.0}  # Down
        
        angle = calculate_angle(point_a, point_b, point_c)
        assert abs(angle - 270.0) < 0.1, f"Expected ~270°, got {angle}°"


class TestCalculateDistance:
    """Test 2D distance calculations."""
    
    def test_horizontal_distance(self):
        """Test distance between horizontally aligned points."""
        point_a = {'x': 0.0, 'y': 0.5}
        point_b = {'x': 0.3, 'y': 0.5}
        
        distance = calculate_distance(point_a, point_b)
        assert abs(distance - 0.3) < 0.01, f"Expected ~0.3, got {distance}"
    
    def test_vertical_distance(self):
        """Test distance between vertically aligned points."""
        point_a = {'x': 0.5, 'y': 0.0}
        point_b = {'x': 0.5, 'y': 0.4}
        
        distance = calculate_distance(point_a, point_b)
        assert abs(distance - 0.4) < 0.01, f"Expected ~0.4, got {distance}"
    
    def test_diagonal_distance(self):
        """Test diagonal distance (Pythagorean theorem)."""
        point_a = {'x': 0.0, 'y': 0.0}
        point_b = {'x': 0.3, 'y': 0.4}
        
        distance = calculate_distance(point_a, point_b)
        expected = math.sqrt(0.3**2 + 0.4**2)  # 0.5
        assert abs(distance - expected) < 0.01, f"Expected ~{expected}, got {distance}"
    
    def test_zero_distance(self):
        """Test distance between same point."""
        point_a = {'x': 0.5, 'y': 0.5}
        point_b = {'x': 0.5, 'y': 0.5}
        
        distance = calculate_distance(point_a, point_b)
        assert distance < 0.01, f"Expected ~0, got {distance}"


@pytest.mark.parametrize("angle_deg,expected", [
    (0, 0),
    (45, 45),
    (90, 90),
    (135, 135),
    (180, 180),
])
def test_various_angles(angle_deg, expected):
    """Parametric test for various angles."""
    # Create points forming the desired angle
    point_a = {'x': 1.0, 'y': 0.5}
    point_b = {'x': 0.5, 'y': 0.5}
    
    # Calculate point C based on desired angle
    # '+sin' to generate clockwise angle due to Y-axis direction (see note at the top)
    angle_rad = math.radians(angle_deg)
    point_c = {
        'x': 0.5 + 0.5 * math.cos(angle_rad),
        'y': 0.5 + 0.5 * math.sin(angle_rad)
    }
    
    angle = calculate_angle(point_a, point_b, point_c)
    assert abs(angle - expected) < 2.0, f"Expected ~{expected}°, got {angle}°"