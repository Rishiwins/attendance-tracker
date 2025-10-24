#!/usr/bin/env python3
"""
Test script to verify full mode with OpenCV and face recognition works.
"""

import sys
import subprocess

def test_opencv_import():
    """Test if OpenCV can be imported"""
    try:
        import cv2
        print(f"✅ OpenCV imported successfully - Version: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False

def test_face_recognition_import():
    """Test if face_recognition can be imported"""
    try:
        import face_recognition
        print("✅ face_recognition imported successfully")
        return True
    except ImportError as e:
        print(f"❌ face_recognition import failed: {e}")
        return False

def test_webcam_access():
    """Test if webcam can be accessed"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ Webcam access successful")
                cap.release()
                return True
            else:
                print("⚠️ Webcam opened but couldn't read frame")
                cap.release()
                return False
        else:
            print("⚠️ Webcam not accessible (may not be available)")
            return False
    except Exception as e:
        print(f"❌ Webcam test failed: {e}")
        return False

def test_face_recognition_functionality():
    """Test basic face recognition functionality"""
    try:
        import face_recognition
        import numpy as np
        from PIL import Image

        # Create a simple test image (black square)
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Try to find face locations (should return empty list for black image)
        face_locations = face_recognition.face_locations(test_image)
        print(f"✅ Face detection test completed - Found {len(face_locations)} faces (expected 0)")
        return True
    except Exception as e:
        print(f"❌ Face recognition functionality test failed: {e}")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("🧪 Testing Full Mode Dependencies")
    print("=" * 40)

    results = []

    print("1. Testing OpenCV...")
    results.append(test_opencv_import())

    print("\n2. Testing face_recognition...")
    results.append(test_face_recognition_import())

    print("\n3. Testing webcam access...")
    results.append(test_webcam_access())

    print("\n4. Testing face recognition functionality...")
    results.append(test_face_recognition_functionality())

    print("\n" + "=" * 40)
    print(f"Results: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("🎉 All tests passed! Full mode is ready!")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

def main():
    """Main test function"""
    print("Full Mode Dependency Test")
    print("=" * 50)

    success = test_dependencies()

    if success:
        print("\n✅ Full mode is ready!")
        print("You can now use:")
        print("  docker-compose up -d")
        sys.exit(0)
    else:
        print("\n❌ Full mode needs fixes")
        print("Use lite mode instead:")
        print("  docker-compose -f docker-compose.lite.yml up -d")
        sys.exit(1)

if __name__ == "__main__":
    main()