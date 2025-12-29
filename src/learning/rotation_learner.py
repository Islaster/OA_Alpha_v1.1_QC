"""
Learning system for rotation presets.
Stores successful rotations and identifies patterns.

Mac-compatible version with cross-platform support.
"""
import os
import json
from collections import defaultdict
from src.utils.config_manager import load_json_file, save_json_file


class RotationLearner:
    def __init__(self, presets_file="rotation_presets.json"):
        self.presets_file = presets_file
        self.presets_data = load_json_file(presets_file, default={})
        
        # Ensure required keys exist
        if "rotations" not in self.presets_data:
            self.presets_data["rotations"] = {}
        if "patterns" not in self.presets_data:
            self.presets_data["patterns"] = {}
        if "statistics" not in self.presets_data:
            self.presets_data["statistics"] = {}
    
    def save_rotation(self, object_name, object_type, rotation_degrees, bbox_reduction):
        """
        Save a successful rotation.
        
        Args:
            object_name: Name of the object
            object_type: Type/category of object
            rotation_degrees: Tuple of (x, y, z) rotation in degrees
            bbox_reduction: Percentage reduction in bounding box volume
        """
        key = f"{object_type}:{object_name}"
        
        if key not in self.presets_data["rotations"]:
            self.presets_data["rotations"][key] = []
        
        entry = {
            "rotation": list(rotation_degrees),
            "bbox_reduction": bbox_reduction,
            "timestamp": __import__("time").time()
        }
        
        self.presets_data["rotations"][key].append(entry)
        
        # Update statistics
        self._update_statistics(rotation_degrees, bbox_reduction)
        
        # Save to file
        self.save()
        print(f"  [Learning] Saved rotation for {object_name}: {rotation_degrees}")
    
    def forget_object(self, object_name, object_type):
        """
        Remove learned data for a specific object.
        
        Args:
            object_name: Name of the object
            object_type: Type/category of object
            
        Returns:
            bool: True if data was removed, False if not found
        """
        key = f"{object_type}:{object_name}"
        found = False
        
        # Remove from rotations
        if key in self.presets_data["rotations"]:
            del self.presets_data["rotations"][key]
            found = True
            
        # Remove from patterns if present
        if key in self.presets_data.get("patterns", {}):
            del self.presets_data["patterns"][key]
            found = True
            
        if found:
            self.save()
            
        return found
    
    def get_presets_for_object(self, object_name, object_type):
        """
        Get learned presets for an object.
        
        Args:
            object_name: Name of the object
            object_type: Type/category of object
            
        Returns:
            list: List of rotation tuples in degrees, sorted by success rate
        """
        key = f"{object_type}:{object_name}"
        
        if key in self.presets_data["rotations"]:
            rotations = self.presets_data["rotations"][key]
            # Sort by bbox_reduction (best first)
            rotations.sort(key=lambda x: x["bbox_reduction"], reverse=True)
            return [tuple(r["rotation"]) for r in rotations]
        
        return []
    
    def get_common_presets(self, min_samples=3):
        """
        Get commonly successful rotation presets across all objects.
        
        Args:
            min_samples: Minimum number of successful uses to include
            
        Returns:
            list: List of rotation tuples in degrees
        """
        # Count occurrences of each rotation
        rotation_counts = defaultdict(int)
        
        for key, rotations in self.presets_data["rotations"].items():
            for entry in rotations:
                rot_key = tuple(entry["rotation"])
                rotation_counts[rot_key] += 1
        
        # Filter by minimum samples and sort by frequency
        common = [
            rot for rot, count in rotation_counts.items()
            if count >= min_samples
        ]
        common.sort(key=lambda r: rotation_counts[r], reverse=True)
        
        return common
    
    def _update_statistics(self, rotation_degrees, bbox_reduction):
        """Update global statistics."""
        rot_key = str(rotation_degrees)
        
        if rot_key not in self.presets_data["statistics"]:
            self.presets_data["statistics"][rot_key] = {
                "count": 0,
                "total_reduction": 0,
                "avg_reduction": 0
            }
        
        stats = self.presets_data["statistics"][rot_key]
        stats["count"] += 1
        stats["total_reduction"] += bbox_reduction
        stats["avg_reduction"] = stats["total_reduction"] / stats["count"]
    
    def save(self):
        """Save presets to file."""
        save_json_file(self.presets_file, self.presets_data)
    
    def get_patterns(self):
        """Get identified patterns in successful rotations."""
        return self.presets_data.get("patterns", {})

