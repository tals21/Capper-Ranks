#!/usr/bin/env python3
"""
Installation script for image processing dependencies.
This script helps users install and configure the required dependencies for OCR functionality.
"""

import subprocess
import sys
import platform
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def install_python_dependencies():
    """Install Python dependencies for image processing."""
    print("\n=== Installing Python Dependencies ===")
    
    dependencies = [
        "Pillow",
        "pytesseract", 
        "requests"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def install_tesseract():
    """Install Tesseract OCR based on the operating system."""
    print("\n=== Installing Tesseract OCR ===")
    
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        return run_command("brew install tesseract", "Installing Tesseract via Homebrew")
    
    elif system == "linux":
        # Try to detect the distribution
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    return run_command("sudo apt-get update && sudo apt-get install -y tesseract-ocr", 
                                     "Installing Tesseract via apt-get")
                elif 'fedora' in content or 'rhel' in content or 'centos' in content:
                    return run_command("sudo dnf install -y tesseract", 
                                     "Installing Tesseract via dnf")
                else:
                    print("⚠️  Unsupported Linux distribution. Please install Tesseract manually:")
                    print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr")
                    print("   Fedora/RHEL: sudo dnf install tesseract")
                    return False
        except FileNotFoundError:
            print("⚠️  Could not detect Linux distribution. Please install Tesseract manually.")
            return False
    
    elif system == "windows":
        print("⚠️  Windows detected. Please install Tesseract manually:")
        print("   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. Install to default location (C:\\Program Files\\Tesseract-OCR)")
        print("   3. Add to PATH environment variable")
        return False
    
    else:
        print(f"⚠️  Unsupported operating system: {system}")
        return False

def verify_installation():
    """Verify that all dependencies are properly installed."""
    print("\n=== Verifying Installation ===")
    
    # Test Python imports
    try:
        import PIL
        print("✅ Pillow imported successfully")
    except ImportError:
        print("❌ Pillow not available")
        return False
    
    try:
        import pytesseract
        print("✅ pytesseract imported successfully")
    except ImportError:
        print("❌ pytesseract not available")
        return False
    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError:
        print("❌ requests not available")
        return False
    
    # Test Tesseract availability
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract available (version: {version})")
    except Exception as e:
        print(f"❌ Tesseract not available: {e}")
        return False
    
    # Test image processor
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from capper_ranks.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        print("✅ ImageProcessor created successfully")
    except Exception as e:
        print(f"❌ ImageProcessor creation failed: {e}")
        return False
    
    return True

def main():
    """Main installation function."""
    print("=== Capper-Ranks Image Processing Installation ===")
    print("This script will install the required dependencies for image-based pick detection.\n")
    
    # Check if running in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment.")
        print("   Consider creating a virtual environment first:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print()
    
    # Install dependencies
    if not install_python_dependencies():
        print("\n❌ Failed to install Python dependencies")
        return False
    
    if not install_tesseract():
        print("\n❌ Failed to install Tesseract")
        print("Please install Tesseract manually and run the verification script:")
        print("python scripts/test_image_processing.py")
        return False
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Installation verification failed")
        return False
    
    print("\n🎉 Installation completed successfully!")
    print("\nNext steps:")
    print("1. Test the installation: python scripts/test_image_processing.py")
    print("2. Run the bot: python -m capper_ranks.bot")
    print("\nThe bot will now automatically detect picks from both text and images in tweets.")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 