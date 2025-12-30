#!/usr/bin/env python3
"""
Test script for Lemon Squeezy API integration.
Updated to match official gruntWAVE spec.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.licensing import LemonSqueezyClient, LicenseValidator, LicenseStorage


def test_activation():
    """Test license activation flow."""
    print("\n" + "="*70)
    print("🔑 LICENSE ACTIVATION TEST")
    print("="*70)
    
    validator = LicenseValidator()
    storage = LicenseStorage()
    
    print(f"\n💻 Device: {validator.machine_id}")
    print(f"📁 Storage: {storage.storage_dir}")
    
    # Check if already activated
    if storage.is_activated():
        print("\n✅ License already activated locally!")
        data = storage.load_license()
        print(f"   License Key: {data.get('license_key')[:20]}...")
        print(f"   Instance ID: {data.get('instance_id')}")
        print(f"   Device: {data.get('instance_name')}")
        
        print("\nWould you like to deactivate? (y/n)")
        if input("> ").strip().lower() == 'y':
            test_deactivation(storage)
        return
    
    # Get license key
    print("\n📝 Enter your license key:")
    license_key = input("> ").strip()
    
    if not license_key:
        print("❌ No license key provided")
        return
    
    # Activate
    print("\n🔄 Activating...")
    is_valid, message, data = validator.check_license(license_key)
    
    if is_valid:
        print(f"✅ {message}")
        
        # Save to storage
        instance_id = data.get("instance_id")
        if instance_id:
            storage.save_license(
                license_key=license_key,
                instance_id=instance_id,
                instance_name=validator.machine_id,
                additional_data={
                    "license_data": data.get("license_data", {})
                }
            )
            print(f"\n💾 Saved locally!")
            print(f"   Instance ID: {instance_id}")
        else:
            print("\n⚠️  No instance_id returned (might already be activated)")
    else:
        print(f"❌ {message}")
        if data:
            print(f"\n   Details: {data}")


def test_deactivation(storage: LicenseStorage):
    """Test license deactivation."""
    print("\n" + "="*70)
    print("🔓 LICENSE DEACTIVATION TEST")
    print("="*70)
    
    # Load stored license
    data = storage.load_license()
    if not data:
        print("\n❌ No license found locally")
        return
    
    license_key = data.get("license_key")
    instance_id = data.get("instance_id")
    
    if not instance_id:
        print("\n❌ No instance_id found (required for deactivation)")
        return
    
    print(f"\n📋 Current License:")
    print(f"   Key: {license_key[:20]}...")
    print(f"   Instance ID: {instance_id}")
    print(f"   Device: {data.get('instance_name')}")
    
    print("\n⚠️  This will deactivate the license on this device.")
    print("You can then activate it on another machine.")
    print("\nConfirm deactivation? (yes/no)")
    
    if input("> ").strip().lower() != 'yes':
        print("❌ Cancelled")
        return
    
    # Deactivate
    print("\n🔄 Deactivating...")
    client = LemonSqueezyClient()
    result = client.deactivate_license(license_key, instance_id)
    
    if result.get("deactivated"):
        print("✅ License deactivated successfully!")
        storage.clear_license()
        print("💾 Cleared local storage")
        print("\n✨ You can now activate this license on another machine")
    else:
        print(f"❌ Deactivation failed: {result.get('error', 'Unknown error')}")


def main():
    """Main test function."""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*18 + "🍋 LEMON SQUEEZY LICENSE TEST" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    # Load environment
    load_dotenv()
    
    # Check config
    api_key = os.getenv("LEMONSQUEEZY_API_KEY")
    if not api_key:
        print("\n❌ LEMONSQUEEZY_API_KEY not found in .env")
        return 1
    
    print(f"\n✅ API Key configured")
    print(f"✅ Store ID: {os.getenv('LEMONSQUEEZY_STORE_ID')}")
    print(f"✅ Product ID: {os.getenv('LEMONSQUEEZY_PRODUCT_ID')}")
    
    # Run test
    try:
        test_activation()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*70)
    print("✅ Test complete!")
    print("="*70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

