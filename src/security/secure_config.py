"""
Secure configuration management with environment variable support.
Prevents hardcoded secrets and supports .env files.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

from .validators import validate_config_file_path


logger = logging.getLogger(__name__)


class SecureConfig:
    """
    Secure configuration manager that loads from:
    1. Environment variables (highest priority)
    2. .env file
    3. config.json file
    4. Defaults (lowest priority)
    """
    
    # Environment variable names for sensitive data
    ENV_VAR_PREFIX = "OA_"
    
    # Sensitive keys that should NEVER be in config.json
    SENSITIVE_KEYS = {
        'ai_api_key',
        'api_key',
        'api_secret',
        'password',
        'token',
        'secret',
        'credentials'
    }
    
    def __init__(self, config_path: Optional[Path] = None, env_file: Optional[Path] = None):
        """
        Initialize secure configuration.
        
        Args:
            config_path: Path to config.json
            env_file: Path to .env file (default: .env in current directory)
        """
        self.config_path = config_path or Path("config.json")
        self.env_file = env_file or Path(".env")
        
        # Load configuration
        self._config = self._load_config()
        
        # Audit for hardcoded secrets
        self._audit_secrets()
    
    def _load_dotenv(self):
        """Load environment variables from .env file."""
        if not DOTENV_AVAILABLE:
            logger.warning(
                "python-dotenv not available. "
                "Install with: pip install python-dotenv"
            )
            return
        
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment variables from {self.env_file}")
        else:
            logger.debug(f".env file not found: {self.env_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from multiple sources with priority.
        
        Returns:
            Merged configuration dictionary
        """
        # Load .env first (lowest priority for structure, highest for secrets)
        self._load_dotenv()
        
        # Load config.json
        config = {}
        if self.config_path.exists():
            try:
                validated_path = validate_config_file_path(self.config_path)
                with open(validated_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {validated_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {self.config_path}: {e}")
                config = self._get_default_config()
        else:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            config = self._get_default_config()
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to config.
        
        Environment variable format: OA_SECTION_KEY=value
        Example: OA_GROUND_DETECTION_AI_API_KEY=sk-...
        
        Args:
            config: Base configuration
            
        Returns:
            Configuration with env overrides applied
        """
        # Special handling for sensitive values
        ai_api_key = os.getenv(f"{self.ENV_VAR_PREFIX}AI_API_KEY")
        if ai_api_key:
            if "ground_detection" not in config:
                config["ground_detection"] = {}
            config["ground_detection"]["ai_api_key"] = ai_api_key
            logger.info("Loaded AI API key from environment variable")
        
        # Check for debug mode override
        debug_enabled = os.getenv(f"{self.ENV_VAR_PREFIX}DEBUG")
        if debug_enabled:
            if "debug" not in config:
                config["debug"] = {}
            config["debug"]["enabled"] = debug_enabled.lower() in ('true', '1', 'yes')
        
        # Check for log level override
        log_level = os.getenv(f"{self.ENV_VAR_PREFIX}LOG_LEVEL")
        if log_level:
            if "logging" not in config:
                config["logging"] = {}
            config["logging"]["log_level"] = log_level.upper()
        
        return config
    
    def _audit_secrets(self):
        """
        Audit configuration for hardcoded secrets.
        Logs warnings if sensitive values are found in config file.
        """
        def check_dict(d: dict, path: str = ""):
            """Recursively check dictionary for secrets."""
            for key, value in d.items():
                full_path = f"{path}.{key}" if path else key
                
                # Check if key is sensitive
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    if isinstance(value, str) and value and value != "":
                        logger.warning(
                            f"SECURITY: Sensitive key '{full_path}' has a non-empty value in config file. "
                            f"Move to environment variable: {self.ENV_VAR_PREFIX}{key.upper()}"
                        )
                
                # Recurse into nested dicts
                if isinstance(value, dict):
                    check_dict(value, full_path)
        
        check_dict(self._config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "rotation": {
                "common_presets": [-90, -45, 0, 45, 90, 180],
                "adaptive_steps": [15, 5, 1, 0.5, 0.1],
                "optimization_method": "L-BFGS-B",
                "optimization_tolerance": 0.01,
                "use_pca_initial_guess": True,
                "fast_mode": False
            },
            "ground_detection": {
                "use_learned": True,
                "use_physics": True,
                "use_ai": False,
                "ai_provider": "openai",
                "ai_api_key": "",  # Should be set via environment variable
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
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Supports dot notation for nested keys: "rotation.common_presets"
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value (in memory only).
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def save(self, path: Optional[Path] = None):
        """
        Save configuration to file (excluding sensitive values).
        
        Args:
            path: Path to save to (default: self.config_path)
        """
        path = path or self.config_path
        
        # Create sanitized config (remove sensitive values)
        sanitized = self._sanitize_config(self._config)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(sanitized, f, indent=2)
            logger.info(f"Saved configuration to {path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive values from configuration.
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Sanitized configuration
        """
        sanitized = {}
        
        for key, value in config.items():
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                # Replace with empty string
                sanitized[key] = ""
            elif isinstance(value, dict):
                # Recurse into nested dicts
                sanitized[key] = self._sanitize_config(value)
            else:
                sanitized[key] = value
        
        return sanitized


def get_secure_config(config_path: Optional[Path] = None, 
                      env_file: Optional[Path] = None) -> SecureConfig:
    """
    Get a secure configuration instance.
    
    Args:
        config_path: Path to config.json
        env_file: Path to .env file
        
    Returns:
        SecureConfig instance
    """
    return SecureConfig(config_path, env_file)

