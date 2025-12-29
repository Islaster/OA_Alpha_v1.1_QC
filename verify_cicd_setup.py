#!/usr/bin/env python3
"""
CI/CD Setup Verification Script
Checks that all required files and configurations are in place.
"""
import sys
import os
from pathlib import Path
import json

def print_status(message, status):
    """Print status with color."""
    symbols = {"✓": "✓", "✗": "✗", "⚠": "⚠"}
    colors = {
        "✓": "\033[92m",  # Green
        "✗": "\033[91m",  # Red
        "⚠": "\033[93m",  # Yellow
        "reset": "\033[0m"
    }
    symbol = symbols.get(status, status)
    color = colors.get(status, "")
    reset = colors["reset"]
    print(f"{color}{symbol}{reset} {message}")

def check_file_exists(filepath, required=True):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print_status(f"Found: {filepath}", "✓")
        return True
    else:
        status = "✗" if required else "⚠"
        print_status(f"Missing: {filepath}", status)
        return False

def check_directory_exists(dirpath):
    """Check if a directory exists."""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        print_status(f"Found directory: {dirpath}", "✓")
        return True
    else:
        print_status(f"Missing directory: {dirpath}", "✗")
        return False

def check_pyproject_toml():
    """Verify pyproject.toml configuration."""
    if not Path("pyproject.toml").exists():
        print_status("pyproject.toml not found", "✗")
        return False
    
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    checks = {
        "[tool.pyapp]": "PyApp configuration",
        "entry-point": "Entry point defined",
        "[tool.pyarmor]": "PyArmor configuration",
        "[project]": "Project metadata",
    }
    
    all_ok = True
    for key, description in checks.items():
        if key in content:
            print_status(f"pyproject.toml: {description}", "✓")
        else:
            print_status(f"pyproject.toml: Missing {description}", "✗")
            all_ok = False
    
    return all_ok

def check_workflow_file():
    """Verify GitHub Actions workflow."""
    workflow_path = ".github/workflows/release.yml"
    if not Path(workflow_path).exists():
        print_status("GitHub Actions workflow not found", "✗")
        return False
    
    with open(workflow_path, "r") as f:
        content = f.read()
    
    checks = {
        "PYARMOR_LICENSE": "PyArmor license secret reference",
        "matrix:": "Build matrix strategy",
        "pip-audit": "Security audit step",
        "pyarmor gen": "Code obfuscation step",
        "actions/upload-artifact": "Artifact upload",
    }
    
    all_ok = True
    for key, description in checks.items():
        if key in content:
            print_status(f"Workflow: {description}", "✓")
        else:
            print_status(f"Workflow: Missing {description}", "⚠")
            all_ok = False
    
    return all_ok

def check_entry_points():
    """Check entry point files."""
    entry_points = {
        "gui_new.py": "GUI entry point",
        "main_processor.py": "CLI entry point",
    }
    
    all_ok = True
    for filepath, description in entry_points.items():
        if Path(filepath).exists():
            print_status(f"{description}: {filepath}", "✓")
        else:
            print_status(f"{description}: {filepath} not found", "✗")
            all_ok = False
    
    return all_ok

def check_requirements():
    """Check requirements files."""
    req_files = {
        "requirements.txt": True,
        "requirements-security.txt": True,
    }
    
    all_ok = True
    for filepath, required in req_files.items():
        if Path(filepath).exists():
            print_status(f"Requirements: {filepath}", "✓")
            
            # Check for key packages
            with open(filepath, "r") as f:
                content = f.read().lower()
            
            if filepath == "requirements-security.txt":
                expected = ["python-dotenv", "cryptography"]
                for pkg in expected:
                    if pkg in content:
                        print_status(f"  Contains {pkg}", "✓")
                    else:
                        print_status(f"  Missing {pkg}", "✗")
                        all_ok = False
        else:
            status = "✗" if required else "⚠"
            print_status(f"Requirements: {filepath} not found", status)
            if required:
                all_ok = False
    
    return all_ok

def check_security_files():
    """Check security-related files."""
    files = {
        "env.example": "Environment template",
        ".gitignore": "Git ignore file",
        ".safety-policy.yml": "Safety policy",
    }
    
    all_ok = True
    for filepath, description in files.items():
        if Path(filepath).exists():
            print_status(f"{description}: {filepath}", "✓")
        else:
            print_status(f"{description}: {filepath} not found", "⚠")
    
    # Check .gitignore contents
    if Path(".gitignore").exists():
        with open(".gitignore", "r") as f:
            content = f.read()
        
        required_entries = [".env", "*.log", "__pycache__", "venv"]
        for entry in required_entries:
            if entry in content:
                print_status(f"  .gitignore contains {entry}", "✓")
            else:
                print_status(f"  .gitignore missing {entry}", "⚠")
    
    return all_ok

def check_documentation():
    """Check documentation files."""
    docs = {
        "README_GITHUB_CICD.md": False,
        "CICD_QUICKSTART.md": False,
        "CICD_CHEATSHEET.md": False,
        "SECURITY.md": False,
    }
    
    for filepath, required in docs.items():
        if Path(filepath).exists():
            print_status(f"Documentation: {filepath}", "✓")
        else:
            status = "✗" if required else "⚠"
            print_status(f"Documentation: {filepath} not found", status)

def check_src_structure():
    """Check source code structure."""
    expected_dirs = [
        "src/core",
        "src/io",
        "src/optimization",
        "src/gui",
        "src/security",
        "src/utils",
        "src/learning",
        "src/positioning",
    ]
    
    all_ok = True
    for dirpath in expected_dirs:
        if Path(dirpath).exists():
            print_status(f"Module: {dirpath}", "✓")
        else:
            print_status(f"Module: {dirpath} not found", "✗")
            all_ok = False
    
    return all_ok

def main():
    """Main verification function."""
    print("\n" + "="*60)
    print("  CI/CD SETUP VERIFICATION")
    print("="*60 + "\n")
    
    results = {}
    
    print("🔍 Checking GitHub Actions Workflow...")
    results['workflow'] = check_directory_exists(".github/workflows")
    results['workflow'] &= check_file_exists(".github/workflows/release.yml")
    results['workflow'] &= check_workflow_file()
    print()
    
    print("🔍 Checking Package Configuration...")
    results['package'] = check_file_exists("pyproject.toml")
    results['package'] &= check_pyproject_toml()
    print()
    
    print("🔍 Checking Entry Points...")
    results['entry_points'] = check_entry_points()
    print()
    
    print("🔍 Checking Requirements...")
    results['requirements'] = check_requirements()
    print()
    
    print("🔍 Checking Security Files...")
    results['security'] = check_security_files()
    print()
    
    print("🔍 Checking Documentation...")
    check_documentation()
    print()
    
    print("🔍 Checking Source Structure...")
    results['structure'] = check_src_structure()
    print()
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for category, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print_status(f"{category.upper()}: {status}", "✓" if passed else "✗")
    
    print("\n" + "="*60)
    
    if all_passed:
        print_status("✓ All critical checks passed!", "✓")
        print_status("Ready to push to GitHub and trigger CI/CD build", "✓")
        print("\nNext steps:")
        print("  1. Add PYARMOR_LICENSE to GitHub Secrets")
        print("  2. git push origin main")
        print("  3. Check Actions tab for build progress")
        return 0
    else:
        print_status("✗ Some checks failed", "✗")
        print("\nPlease fix the issues above before pushing to GitHub.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

