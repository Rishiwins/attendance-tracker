#!/usr/bin/env python3
"""
Comprehensive system test script for the attendance tracking system.
This script tests all major components and workflows.
"""

import requests
import json
import time
import base64
from datetime import date, datetime
from io import BytesIO
from PIL import Image
import numpy as np

class AttendanceSystemTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.employee_id = None
        self.camera_id = None

    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print(f"{status}: {test_name} - {message}")

    def test_health_check(self):
        """Test system health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_create_employee(self):
        """Test employee creation"""
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
            response = self.session.post(
                f"{self.base_url}/api/v1/employees/",
                json=employee_data
            )

            if response.status_code == 200:
                data = response.json()
                self.employee_id = data["id"]
                self.log_test("Create Employee", True, f"Employee ID: {self.employee_id}")
                return True
            else:
                self.log_test("Create Employee", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Employee", False, str(e))
            return False

    def test_list_employees(self):
        """Test listing employees"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/employees/")

            if response.status_code == 200:
                data = response.json()
                self.log_test("List Employees", True, f"Found {len(data)} employees")
                return True
            else:
                self.log_test("List Employees", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("List Employees", False, str(e))
            return False

    def create_test_face_image(self):
        """Create a simple test face image"""
        # Create a simple test image (not a real face, but will test the upload mechanism)
        img = Image.new('RGB', (200, 200), color='lightblue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()

    def test_face_upload(self):
        """Test face image upload"""
        if not self.employee_id:
            self.log_test("Face Upload", False, "No employee ID available")
            return False

        try:
            # Create test image
            image_data = self.create_test_face_image()
            base64_image = base64.b64encode(image_data).decode()

            response = self.session.post(
                f"{self.base_url}/api/v1/employees/{self.employee_id}/face-image-base64",
                json={"image": base64_image}
            )

            if response.status_code == 200:
                self.log_test("Face Upload", True, "Face image uploaded successfully")
                return True
            else:
                self.log_test("Face Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Face Upload", False, str(e))
            return False

    def test_manual_attendance(self):
        """Test manual attendance marking"""
        if not self.employee_id:
            self.log_test("Manual Attendance", False, "No employee ID available")
            return False

        try:
            today = date.today().isoformat()
            check_in_time = f"{today}T09:00:00"

            response = self.session.post(
                f"{self.base_url}/api/v1/attendance/manual/{self.employee_id}",
                params={
                    "target_date": today,
                    "check_in_time": check_in_time,
                    "notes": "Test attendance entry"
                }
            )

            if response.status_code == 200:
                self.log_test("Manual Attendance", True, "Attendance marked successfully")
                return True
            else:
                self.log_test("Manual Attendance", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Manual Attendance", False, str(e))
            return False

    def test_daily_attendance_report(self):
        """Test daily attendance report"""
        try:
            today = date.today().isoformat()
            response = self.session.get(f"{self.base_url}/api/v1/attendance/daily/{today}")

            if response.status_code == 200:
                data = response.json()
                self.log_test("Daily Report", True, f"Total employees: {data.get('total_employees', 0)}")
                return True
            else:
                self.log_test("Daily Report", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Daily Report", False, str(e))
            return False

    def test_create_camera(self):
        """Test camera creation"""
        camera_data = {
            "name": "Test Camera",
            "location": "Test Location",
            "url": "0"  # Use default webcam
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/cameras/",
                json=camera_data
            )

            if response.status_code == 200:
                data = response.json()
                self.camera_id = data["id"]
                self.log_test("Create Camera", True, f"Camera ID: {self.camera_id}")
                return True
            else:
                self.log_test("Create Camera", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Camera", False, str(e))
            return False

    def test_camera_status(self):
        """Test camera status check"""
        if not self.camera_id:
            self.log_test("Camera Status", False, "No camera ID available")
            return False

        try:
            response = self.session.get(f"{self.base_url}/api/v1/cameras/{self.camera_id}/status")

            if response.status_code == 200:
                data = response.json()
                self.log_test("Camera Status", True, f"Camera active: {data.get('is_active', False)}")
                return True
            else:
                self.log_test("Camera Status", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Camera Status", False, str(e))
            return False

    def test_system_info(self):
        """Test system information endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/system/info")

            if response.status_code == 200:
                data = response.json()
                stats = data.get('statistics', {})
                self.log_test("System Info", True,
                    f"Registered employees: {stats.get('registered_employees', 0)}, "
                    f"Active cameras: {stats.get('active_cameras', 0)}")
                return True
            else:
                self.log_test("System Info", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Info", False, str(e))
            return False

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")

        # Delete test employee
        if self.employee_id:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/employees/{self.employee_id}")
                if response.status_code == 200:
                    print("✅ Test employee deleted")
                else:
                    print(f"❌ Failed to delete employee: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting employee: {e}")

        # Delete test camera
        if self.camera_id:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/cameras/{self.camera_id}")
                if response.status_code == 200:
                    print("✅ Test camera deleted")
                else:
                    print(f"❌ Failed to delete camera: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting camera: {e}")

    def run_all_tests(self):
        """Run comprehensive system test"""
        print("🚀 Starting Attendance System Tests\n")

        # Core system tests
        tests = [
            self.test_health_check,
            self.test_system_info,
            self.test_create_employee,
            self.test_list_employees,
            self.test_face_upload,
            self.test_manual_attendance,
            self.test_daily_attendance_report,
            self.test_create_camera,
            self.test_camera_status,
        ]

        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests

        # Print summary
        print("\n📊 Test Summary:")
        print("=" * 50)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        if passed == total:
            print("\n🎉 All tests passed! System is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above for details.")

        return passed == total

def main():
    print("Employee Attendance Tracking System - Test Suite")
    print("=" * 60)

    # Check if system is running
    tester = AttendanceSystemTester()

    try:
        success = tester.run_all_tests()

        # Cleanup test data
        tester.cleanup()

        if success:
            print("\n✅ System test completed successfully!")
            exit(0)
        else:
            print("\n❌ System test completed with failures!")
            exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.cleanup()
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        tester.cleanup()
        exit(1)

if __name__ == "__main__":
    main()