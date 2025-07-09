#!/usr/bin/env python3
"""
Test script for image processing functionality.
This script can be run independently to test OCR and image processing capabilities.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_image_processor_import():
    """Test that the image processor can be imported."""
    try:
        from capper_ranks.services.image_processor import ImageProcessor, image_processor
        print("✅ Successfully imported ImageProcessor")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ImageProcessor: {e}")
        print("Make sure you have installed the required dependencies:")
        print("pip install Pillow pytesseract requests")
        return False

def test_tesseract_installation():
    """Test if tesseract is available."""
    try:
        import pytesseract
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract is installed (version: {version})")
        return True
    except Exception as e:
        print(f"❌ Tesseract not available: {e}")
        print("Please install tesseract:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def test_pillow_installation():
    """Test if Pillow is available."""
    try:
        from PIL import Image
        print(f"✅ Pillow is installed (version: {Image.__version__})")
        return True
    except ImportError as e:
        print(f"❌ Pillow not available: {e}")
        print("Please install Pillow: pip install Pillow")
        return False

def test_requests_installation():
    """Test if requests is available."""
    try:
        import requests
        print(f"✅ Requests is installed (version: {requests.__version__})")
        return True
    except ImportError as e:
        print(f"❌ Requests not available: {e}")
        print("Please install requests: pip install requests")
        return False

def test_image_processor_creation():
    """Test creating an ImageProcessor instance."""
    try:
        from capper_ranks.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        print("✅ Successfully created ImageProcessor instance")
        return True
    except Exception as e:
        print(f"❌ Failed to create ImageProcessor: {e}")
        return False

def test_ocr_text_cleaning():
    """Test OCR text cleaning functionality."""
    try:
        from capper_ranks.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        
        # Test dirty OCR text
        dirty_text = """
        Shohei Ohtani | Over 1.5 Total Bases
        Aaron Judge 0ver 0.5 Home Runs
        
        
        """
        
        cleaned = processor._clean_ocr_text(dirty_text)
        print(f"✅ OCR text cleaning works:")
        print(f"   Original: {repr(dirty_text)}")
        print(f"   Cleaned: {repr(cleaned)}")
        return True
    except Exception as e:
        print(f"❌ OCR text cleaning failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Image Processing Test Suite ===\n")
    
    tests = [
        ("Image Processor Import", test_image_processor_import),
        ("Tesseract Installation", test_tesseract_installation),
        ("Pillow Installation", test_pillow_installation),
        ("Requests Installation", test_requests_installation),
        ("Image Processor Creation", test_image_processor_creation),
        ("OCR Text Cleaning", test_ocr_text_cleaning),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! Image processing is ready to use.")
    else:
        print("⚠️  Some tests failed. Please install missing dependencies.")
        print("\nTo install all dependencies:")
        print("pip install -r requirements.txt")
        print("\nTo install tesseract:")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")

if __name__ == '__main__':
    main() 