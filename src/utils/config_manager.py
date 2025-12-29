"""
Configuration and JSON file management.
"""
import json
import os
from pathlib import Path
from .paths import normalize_path, ensure_directory_exists


def load_json_file(filepath, default=None):
    """
    Load JSON file, return default if file doesn't exist.
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default
    """
    if default is None:
        default = {}
    
    filepath = normalize_path(filepath) if filepath else filepath
    
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def save_json_file(filepath, data):
    """
    Save data to JSON file.
    
    Args:
        filepath: Path to JSON file
        data: Data to save (must be JSON-serializable)
    """
    filepath = normalize_path(filepath)
    ensure_directory_exists(filepath)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = normalize_path(config_path)
        self.config = load_json_file(self.config_path, default=self._get_default_config())
    
    def _get_default_config(self):
        """Get default configuration."""
        return {
            "rotation": {
                "common_presets": [-90, -45, 0, 45, 90, 180],
                "adaptive_steps": [15, 5, 1, 0.5, 0.1],
                "optimization_method": "L-BFGS-B",
                "optimization_tolerance": 0.01,
                "use_pca_initial_guess": True
            },
            "ground_detection": {
                "use_learned": True,
                "use_physics": True,
                "use_ai": False,
                "confidence_threshold": 0.8,
                "learning_file": "orientation_learning.json"
            },
            "learning": {
                "enable_learning": True,
                "min_samples_for_pattern": 3
            },
            "logging": {
                "log_level": "INFO",
                "log_file": "processing_log.txt"
            },
            "debug": {
                "enabled": False,
                "log_file": "debug_log.txt",
                "save_intermediate": False,
                "verbose": False
            },
            "paths": {
                "presets_file": "rotation_presets.json",
                "ground_patterns_file": "ground_patterns.json"
            }
        }
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value
    
    def save(self):
        """Save configuration to file."""
        save_json_file(self.config_path, self.config)

