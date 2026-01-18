import math
from typing import Dict


def calculate_angle(point_a: Dict[str, float], point_b: Dict[str, float], point_c: Dict[str, float]) -> float:
    """
    Calculate the angle at point B formed by points A-B-C.
    
    Uses atan2 to get the full 360-degree range, which helps distinguish
    between "up" and "down" states in exercise tracking.
    
    Args:
        point_a: First point with 'x', 'y' coordinates (e.g., shoulder)
        point_b: Vertex point (angle is calculated here) (e.g., elbow)
        point_c: Third point with 'x', 'y' coordinates (e.g., wrist)
        
    Returns:
        float: Angle in degrees (0.0-360.0)
        
    Example:
        >>> shoulder = {'x': 0.5, 'y': 0.3}
        >>> elbow = {'x': 0.6, 'y': 0.5}
        >>> wrist = {'x': 0.7, 'y': 0.3}
        >>> angle = calculate_angle(shoulder, elbow, wrist)
    """
    # Vector from B to A
    ba_x = point_a['x'] - point_b['x']
    ba_y = point_a['y'] - point_b['y']
    
    # Vector from B to C
    bc_x = point_c['x'] - point_b['x']
    bc_y = point_c['y'] - point_b['y']
    
    # Calculate angles using atan2
    # In MediaPipe, Y-axis increases downwards
    angle_ba = math.atan2(ba_y, ba_x)
    angle_bc = math.atan2(bc_y, bc_x)
    
    # Calculate the angle difference
    angle_diff = angle_bc - angle_ba
    
    # Convert to degrees and normalize to 0-360 range
    angle_degrees = math.degrees(angle_diff)
    
    # Normalize to 0-360 if negative
    if angle_degrees < 0:
        angle_degrees += 360.0
        
    return angle_degrees


def calculate_distance(point_a: Dict[str, float], point_b: Dict[str, float]) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        point_a: First point with 'x', 'y' coordinates
        point_b: Second point with 'x', 'y' coordinates
        
    Returns:
        float: Distance between points
    """
    dx = point_b['x'] - point_a['x']
    dy = point_b['y'] - point_a['y']
    
    distance = math.sqrt(dx**2 + dy**2)
    
    return distance
