"""
Rotation utilities and conversions.
"""
import math
from mathutils import Euler


def degrees_to_radians(degrees):
    """Convert degrees tuple to radians tuple."""
    return tuple(math.radians(d) for d in degrees)


def radians_to_degrees(radians):
    """Convert radians tuple or Euler to degrees tuple."""
    if isinstance(radians, Euler):
        radians = tuple(radians)
    return tuple(math.degrees(r) for r in radians)


def apply_rotation(obj, rotation_euler):
    """Apply rotation to an object."""
    obj.rotation_euler = rotation_euler


def normalize_angle(angle_deg):
    """Normalize angle to -180 to 180 range."""
    while angle_deg > 180:
        angle_deg -= 360
    while angle_deg < -180:
        angle_deg += 360
    return angle_deg


def euler_to_matrix(euler):
    """Convert Euler rotation to 4x4 matrix."""
    if not isinstance(euler, Euler):
        euler = Euler(euler, 'XYZ')
    return euler.to_matrix().to_4x4()


def matrix_to_euler(matrix):
    """Convert 4x4 matrix to Euler rotation."""
    return matrix.to_euler('XYZ')

