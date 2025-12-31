"""
Local storage for license data.
Stores license key and instance_id securely.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class LicenseStorage:
    """
    Handles local storage of license information.
    """
    
    def __init__(self, app_name: str = "OA_OrientationAutomator"):
        """
        Initialize license storage.
        
        Args:
            app_name: Application name for storage directory
        """
        self.app_name = app_name
        self.storage_dir = self._get_storage_dir()
        self.license_file = self.storage_dir / "license.json"
        
        # Ensure directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_storage_dir(self) -> Path:
        """
        Get platform-specific storage directory.
        
        Returns:
            Path: Storage directory path
        """
        if os.name == 'nt':  # Windows
            base = Path(os.getenv('APPDATA', ''))
        elif os.name == 'posix':  # macOS/Linux
            if 'darwin' in os.sys.platform:  # macOS
                base = Path.home() / 'Library' / 'Application Support'
            else:  # Linux
                base = Path.home() / '.local' / 'share'
        else:
            base = Path.home()
        
        return base / self.app_name
    
    def save_license(self, license_key: str, instance_id: str, 
                    instance_name: str, additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save license information locally.
        
        Args:
            license_key: The license key
            instance_id: Instance ID from Lemon Squeezy activation
            instance_name: Friendly device name
            additional_data: Optional additional data to store
            
        Returns:
            bool: True if saved successfully
        """
        data = {
            "license_key": license_key,
            "instance_id": instance_id,
            "instance_name": instance_name,
            "activated": True
        }
        
        if additional_data:
            data.update(additional_data)
        
        try:
            with open(self.license_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set file permissions (read/write for owner only)
            if os.name != 'nt':
                os.chmod(self.license_file, 0o600)
            
            return True
        except Exception as e:
            logger.error(f"Error saving license: {e}", exc_info=True)
            return False
    
    def load_license(self) -> Optional[Dict[str, Any]]:
        """
        Load license information from local storage.
        
        Returns:
            dict: License data or None if not found
        """
        if not self.license_file.exists():
            return None
        
        try:
            with open(self.license_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading license: {e}", exc_info=True)
            return None
    
    def clear_license(self) -> bool:
        """
        Clear stored license information.
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error clearing license: {e}", exc_info=True)
            return False
    
    def is_activated(self) -> bool:
        """
        Check if a license is currently activated.
        
        Returns:
            bool: True if activated
        """
        data = self.load_license()
        return data is not None and data.get("activated", False)
    
    def get_instance_id(self) -> Optional[str]:
        """
        Get stored instance ID.
        
        Returns:
            str: Instance ID or None
        """
        data = self.load_license()
        return data.get("instance_id") if data else None
    
    def get_license_key(self) -> Optional[str]:
        """
        Get stored license key.
        
        Returns:
            str: License key or None
        """
        data = self.load_license()
        return data.get("license_key") if data else None

