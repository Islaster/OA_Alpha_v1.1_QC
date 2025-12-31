"""
Lemon Squeezy API integration for license validation and payments.
"""
import os
import requests
import hashlib
import platform
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LemonSqueezyClient:
    """
    Client for interacting with Lemon Squeezy API.
    """
    
    BASE_URL = "https://api.lemonsqueezy.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Lemon Squeezy client.
        
        Args:
            api_key: Lemon Squeezy API key (optional - only needed for private endpoints)
        """
        # Try to load from environment
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = api_key or os.getenv("LEMONSQUEEZY_API_KEY")
        self.store_id = os.getenv("LEMONSQUEEZY_STORE_ID")
        self.product_id = os.getenv("LEMONSQUEEZY_PRODUCT_ID")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json"
        })
        
        # Only add Authorization header if API key is provided
        # (Public endpoints like activate/validate don't need it)
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def validate_license(self, license_key: str, instance_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a license key.
        
        Note: This is a PUBLIC endpoint that doesn't require API authentication.
        Uses form data (not JSON) as per Lemon Squeezy API spec.
        
        Args:
            license_key: The license key to validate
            instance_name: Optional instance identifier (machine ID)
            
        Returns:
            dict: Validation response with license details
        """
        url = f"{self.BASE_URL}/licenses/validate"
        
        payload = {
            "license_key": license_key
        }
        
        if instance_name:
            payload["instance_name"] = instance_name
        
        headers = {
            "Accept": "application/json"
        }
        
        try:
            # Use data= (form-encoded) not json= as per Lemon Squeezy spec
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "valid": False,
                "error": str(e),
                "license_key": {
                    "status": "inactive"
                }
            }
    
    def activate_license(self, license_key: str, instance_name: str) -> Dict[str, Any]:
        """
        Activate a license for a specific instance (device).
        
        Note: This is a PUBLIC endpoint that doesn't require API authentication.
        Uses form data (not JSON) as per Lemon Squeezy API spec.
        
        Args:
            license_key: The license key to activate
            instance_name: Machine/instance identifier (friendly name)
            
        Returns:
            dict: Activation response with 'activated' boolean and 'instance' object
            Example success response:
            {
                "activated": true,
                "license_key": {...},
                "instance": {
                    "id": "abc123",
                    "name": "MacBook-Pro",
                    ...
                }
            }
        """
        url = f"{self.BASE_URL}/licenses/activate"
        
        payload = {
            "license_key": license_key,
            "instance_name": instance_name
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        try:
            # Use data= (form-encoded) not json= as per Lemon Squeezy spec
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            
            # Log response details for debugging
            if response.status_code != 200:
                logger.warning(f"License activation returned status {response.status_code}")
                try:
                    error_data = response.json()
                    logger.debug(f"Activation error response: {error_data}")
                    # Extract error message from response if available
                    error_msg = error_data.get("error", {}).get("message", str(response.status_code))
                    if error_msg:
                        return {
                            "activated": False,
                            "error": f"{response.status_code} Client Error: {error_msg}",
                            "status_code": response.status_code,
                            "response": error_data
                        }
                except ValueError:
                    # Response is not JSON
                    logger.debug(f"Activation error response (non-JSON): {response.text[:500]}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("License activation request timed out")
            return {
                "activated": False,
                "error": "Request timed out. Please check your internet connection."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"License activation failed: {e}", exc_info=True)
            return {
                "activated": False,
                "error": str(e)
            }
    
    def deactivate_license(self, license_key: str, instance_id: str) -> Dict[str, Any]:
        """
        Deactivate a license for a specific instance.
        
        IMPORTANT: Requires instance_id (not instance_name)!
        The instance_id is returned when you activate and must be stored locally.
        
        Note: This is a PUBLIC endpoint that doesn't require API authentication.
        Uses form data (not JSON) as per Lemon Squeezy API spec.
        
        Args:
            license_key: The license key to deactivate
            instance_id: Instance ID returned from activation (e.g., "abc123")
            
        Returns:
            dict: Deactivation response with 'deactivated' boolean
        """
        url = f"{self.BASE_URL}/licenses/deactivate"
        
        payload = {
            "license_key": license_key,
            "instance_id": instance_id  # NOTE: Uses instance_id, not instance_name!
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        try:
            # Use data= (form-encoded) not json= as per Lemon Squeezy spec
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "deactivated": False,
                "error": str(e)
            }
    
    def get_customer_portal_url(self, customer_id: str) -> Optional[str]:
        """
        Get customer portal URL for managing subscription.
        
        Args:
            customer_id: Lemon Squeezy customer ID
            
        Returns:
            str: Portal URL or None if error
        """
        url = f"{self.BASE_URL}/customers/{customer_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("attributes", {}).get("urls", {}).get("customer_portal")
        except requests.exceptions.RequestException:
            return None


class LicenseValidator:
    """
    High-level license validation and management.
    """
    
    def __init__(self, client: Optional[LemonSqueezyClient] = None):
        """
        Initialize license validator.
        
        Args:
            client: LemonSqueezyClient instance (creates new if None)
        """
        self.client = client or LemonSqueezyClient()
        self._machine_id = None
    
    @property
    def machine_id(self) -> str:
        """
        Get unique machine identifier (friendly name).
        
        Returns:
            str: Device name like "MacBook-Pro" or "DESKTOP-Windows"
        """
        if self._machine_id is None:
            # Create friendly device name (as per gruntWAVE spec)
            self._machine_id = f"{platform.node()}-{platform.system()}"
        return self._machine_id
    
    def check_license(self, license_key: str) -> tuple[bool, str, Dict[str, Any]]:
        """
        Check if license is valid and activate if needed.
        
        Args:
            license_key: License key to check
            
        Returns:
            tuple: (is_valid, status_message, full_response_data)
                   full_response_data includes 'instance_id' if activated
        """
        if not license_key or not license_key.strip():
            return False, "No license key provided", {}
        
        # Try to activate (this also validates)
        result = self.client.activate_license(license_key, self.machine_id)
        
        if result.get("error"):
            return False, f"Error: {result['error']}", result
        
        # Check if activation was successful
        if result.get("activated"):
            instance_id = result.get("instance", {}).get("id")
            return True, "License activated successfully", {
                "instance_id": instance_id,
                "instance_name": self.machine_id,
                "license_data": result.get("license_key", {})
            }
        else:
            # Not activated - check why
            license_data = result.get("license_key", {})
            meta = result.get("meta", {})
            
            # If already activated on this machine
            if meta.get("instance_id"):
                return True, "License already active on this device", {
                    "instance_id": meta.get("instance_id"),
                    "license_data": license_data
                }
            
            return False, "Activation failed", result
    
    def get_license_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed license information.
        
        Args:
            license_key: License key to check
            
        Returns:
            dict: License information or None
        """
        result = self.client.validate_license(license_key)
        
        if result.get("valid"):
            license_data = result.get("license_key", {})
            return {
                "status": license_data.get("status"),
                "key": license_data.get("key"),
                "activation_limit": license_data.get("activation_limit"),
                "activation_usage": license_data.get("activation_usage"),
                "expires_at": license_data.get("expires_at"),
                "customer_name": license_data.get("customer_name"),
                "customer_email": license_data.get("customer_email"),
            }
        return None
    
    def is_trial_or_premium(self, license_key: Optional[str] = None) -> str:
        """
        Check if user is on trial or has premium license.
        
        Args:
            license_key: License key to check (None for trial)
            
        Returns:
            str: "trial", "premium", or "invalid"
        """
        if not license_key:
            return "trial"
        
        is_valid, _, _ = self.check_license(license_key)
        return "premium" if is_valid else "invalid"


def test_license_validation():
    """Test function for license validation."""
    print("🍋 Lemon Squeezy License Validation Test\n")
    
    # Check if API key is configured
    api_key = os.getenv("LEMONSQUEEZY_API_KEY")
    if not api_key:
        print("❌ LEMONSQUEEZY_API_KEY not found in environment")
        print("   Please set it in your .env file")
        return
    
    print(f"✓ API Key found: {api_key[:20]}...")
    print(f"✓ Store ID: {os.getenv('LEMONSQUEEZY_STORE_ID')}")
    print(f"✓ Product ID: {os.getenv('LEMONSQUEEZY_PRODUCT_ID')}")
    print()
    
    # Initialize validator
    try:
        validator = LicenseValidator()
        print(f"✓ Machine ID: {validator.machine_id}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize validator: {e}")
        return
    
    # Test with a license key
    print("Enter a license key to test (or press Enter to skip):")
    license_key = input("> ").strip()
    
    if license_key:
        print("\nValidating license...")
        is_valid, message, data = validator.check_license(license_key)
        
        if is_valid:
            print(f"✅ {message}")
            print("\nLicense Details:")
            info = validator.get_license_info(license_key)
            if info:
                for key, value in info.items():
                    print(f"  • {key}: {value}")
        else:
            print(f"❌ {message}")
    else:
        print("\n✓ Running in trial mode (no license)")
    
    print("\n🎉 Test complete!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    test_license_validation()

