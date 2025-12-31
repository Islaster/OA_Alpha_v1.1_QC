#!/usr/bin/env python3
"""
Quick test script to run the GUI application locally in Python.
This allows you to test changes before compiling.

Usage:
    python3 test_local.py
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for required dependencies
missing_deps = []
try:
    import PySide6
except ImportError:
    missing_deps.append("PySide6")

try:
    import requests
except ImportError:
    missing_deps.append("requests")

try:
    from cryptography.fernet import Fernet
except ImportError:
    missing_deps.append("cryptography")

try:
    import dotenv
except ImportError:
    missing_deps.append("python-dotenv")

if missing_deps:
    print("❌ Missing required dependencies:")
    for dep in missing_deps:
        print(f"   - {dep}")
    print("\n📦 Install them with:")
    print(f"   pip install {' '.join(missing_deps)}")
    print("\n   Or install all requirements:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Check if gui_new.py exists
if not os.path.exists("gui_new.py"):
    print("❌ gui_new.py not found!")
    print("   Make sure you're running this from the project root directory.")
    sys.exit(1)

# Check for config.json
if not os.path.exists("config.json"):
    print("⚠️  Warning: config.json not found")
    print("   The app may use default configuration.")

# Check for .env file (optional)
if not os.path.exists(".env"):
    print("⚠️  Warning: .env file not found")
    print("   License validation may not work without API keys.")
    print("   Copy env.example to .env and fill in your values.")

print("✅ All checks passed!")
print("🚀 Starting application...")
print("=" * 60)

# Import and run the main application
try:
    from gui_new import main
    sys.exit(main())
except KeyboardInterrupt:
    print("\n\n👋 Application stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

