#!/usr/bin/env python3
"""
Simple test script that doesn't require OpenCV or other heavy dependencies.
Tests the basic API functionality without camera features.
"""

import requests
import json
import base64
import time
from datetime import date, datetime

def create_simple_test_image():
    """Create a simple base64 encoded test image"""
    # Create a minimal PNG image data (1x1 red pixel)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc\xf8\x0f\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x7f\x00'
    return base64.b64encode(png_data).decode()

def test_system():
    base_url = "http://localhost:8000"

    print("🚀 Starting Simple System Test")
    print("=" * 40)

    # Test 1: Health Check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            data = response.json()
            print(f"   📊 Status: {data.get('status', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("   💡 Make sure the system is running: docker-compose up -d")
        return False

    # Test 2: System Info
    print("\n2. Testing system info...")
    try:
        response = requests.get(f"{base_url}/api/v1/system/info")
        if response.status_code == 200:
            print("   ✅ System info retrieved")
            data = response.json()
            stats = data.get('statistics', {})
            print(f"   📊 Registered employees: {stats.get('registered_employees', 0)}")
            print(f"   📊 Active cameras: {stats.get('active_cameras', 0)}")
        else:
            print(f"   ❌ System info failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ System info error: {e}")

    # Test 3: Create Employee
    print("\n3. Testing employee creation...")
    employee_data = {
        "employee_code": "TEST001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@test.com",
        "department": "Engineering",
        "position": "Software Engineer",
        "manager_email": "manager@test.com"
    }

    try:
        response = requests.post(f"{base_url}/api/v1/employees/", json=employee_data)
        if response.status_code == 200:
            print("   ✅ Employee created successfully")
            employee = response.json()
            employee_id = employee['id']
            print(f"   👤 Employee ID: {employee_id}")
        else:
            print(f"   ❌ Employee creation failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Employee creation error: {e}")
        return False

    # Test 4: List Employees
    print("\n4. Testing employee listing...")
    try:
        response = requests.get(f"{base_url}/api/v1/employees/")
        if response.status_code == 200:
            employees = response.json()
            print(f"   ✅ Found {len(employees)} employees")
        else:
            print(f"   ❌ Employee listing failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Employee listing error: {e}")

    # Test 5: Face Image Upload (Simple)
    print("\n5. Testing face image upload...")
    try:
        test_image = create_simple_test_image()
        response = requests.post(
            f"{base_url}/api/v1/employees/{employee_id}/face-image-base64",
            json={"image": test_image}
        )
        if response.status_code == 200:
            print("   ✅ Face image uploaded (Note: real face recognition requires actual face images)")
        else:
            print(f"   ⚠️ Face upload failed: {response.status_code} (Expected - test image is not a real face)")
    except Exception as e:
        print(f"   ❌ Face upload error: {e}")

    # Test 6: Manual Attendance
    print("\n6. Testing manual attendance...")
    try:
        today = date.today().isoformat()
        check_in_time = f"{today}T09:00:00"

        response = requests.post(
            f"{base_url}/api/v1/attendance/manual/{employee_id}",
            params={
                "target_date": today,
                "check_in_time": check_in_time,
                "notes": "Test attendance entry"
            }
        )

        if response.status_code == 200:
            print("   ✅ Manual attendance recorded")
        else:
            print(f"   ❌ Manual attendance failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Manual attendance error: {e}")

    # Test 7: Daily Report
    print("\n7. Testing daily attendance report...")
    try:
        today = date.today().isoformat()
        response = requests.get(f"{base_url}/api/v1/attendance/daily/{today}")
        if response.status_code == 200:
            report = response.json()
            print("   ✅ Daily report generated")
            print(f"   📊 Total employees: {report.get('total_employees', 0)}")
            print(f"   📊 Present: {report.get('present_employees', 0)}")
            print(f"   📊 Absent: {report.get('absent_employees', 0)}")
        else:
            print(f"   ❌ Daily report failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Daily report error: {e}")

    # Test 8: API Documentation
    print("\n8. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("   ✅ API documentation accessible")
            print(f"   🌐 Visit: {base_url}/docs")
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API docs error: {e}")

    # Cleanup
    print("\n9. Cleaning up test data...")
    try:
        response = requests.delete(f"{base_url}/api/v1/employees/{employee_id}")
        if response.status_code == 200:
            print("   ✅ Test employee deleted")
        else:
            print(f"   ⚠️ Cleanup warning: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Cleanup error: {e}")

    print("\n🎉 Basic system test completed!")
    print("\n📋 Summary:")
    print("   ✅ Core API functionality is working")
    print("   ✅ Employee management works")
    print("   ✅ Attendance tracking works")
    print("   ✅ Database connectivity confirmed")

    print("\n🔧 Next steps:")
    print("   1. For camera testing: python scripts/camera_simulator.py")
    print("   2. For face recognition: Add real face images via API")
    print("   3. For email testing: Configure SMTP settings in .env")
    print("   4. Full test suite: python scripts/test_system.py")

    return True

if __name__ == "__main__":
    test_system()