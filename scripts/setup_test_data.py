#!/usr/bin/env python3
"""
Setup test data for the attendance tracking system.
This script creates sample employees, cameras, and attendance records for testing.
"""

import requests
import json
import base64
from datetime import date, datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw

class TestDataSetup:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.created_employees = []
        self.created_cameras = []

    def create_test_face_image(self, name="Test", color=(100, 150, 200)):
        """Create a simple test face image with name"""
        img = Image.new('RGB', (200, 200), color=color)
        draw = ImageDraw.Draw(img)

        # Draw a simple face
        # Head circle
        draw.ellipse([50, 30, 150, 130], fill=(220, 180, 140), outline=(0, 0, 0), width=2)

        # Eyes
        draw.ellipse([70, 60, 85, 75], fill=(0, 0, 0))
        draw.ellipse([115, 60, 130, 75], fill=(0, 0, 0))

        # Nose
        draw.ellipse([95, 85, 105, 95], fill=(200, 160, 120))

        # Mouth
        draw.arc([80, 100, 120, 120], 0, 180, fill=(0, 0, 0), width=2)

        # Add name
        draw.text((60, 150), name, fill=(0, 0, 0))

        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()

    def create_employee(self, employee_data, face_image=None):
        """Create an employee with optional face image"""
        try:
            # Create employee
            response = self.session.post(
                f"{self.base_url}/api/v1/employees/",
                json=employee_data
            )

            if response.status_code != 200:
                print(f"❌ Failed to create employee {employee_data['employee_code']}: {response.text}")
                return None

            employee = response.json()
            self.created_employees.append(employee['id'])
            print(f"✅ Created employee: {employee['employee_code']} - {employee['first_name']} {employee['last_name']}")

            # Upload face image if provided
            if face_image:
                base64_image = base64.b64encode(face_image).decode()
                face_response = self.session.post(
                    f"{self.base_url}/api/v1/employees/{employee['id']}/face-image-base64",
                    json={"image": base64_image}
                )

                if face_response.status_code == 200:
                    print(f"✅ Uploaded face image for {employee['employee_code']}")
                else:
                    print(f"⚠️ Failed to upload face image for {employee['employee_code']}")

            return employee

        except Exception as e:
            print(f"❌ Error creating employee: {e}")
            return None

    def create_camera(self, camera_data):
        """Create a camera"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/cameras/",
                json=camera_data
            )

            if response.status_code != 200:
                print(f"❌ Failed to create camera {camera_data['name']}: {response.text}")
                return None

            camera = response.json()
            self.created_cameras.append(camera['id'])
            print(f"✅ Created camera: {camera['name']} at {camera['location']}")

            return camera

        except Exception as e:
            print(f"❌ Error creating camera: {e}")
            return None

    def create_attendance_record(self, employee_id, target_date, check_in_time, check_out_time=None, notes=None):
        """Create an attendance record"""
        try:
            params = {
                "target_date": target_date.isoformat(),
                "check_in_time": check_in_time.isoformat(),
                "notes": notes or f"Test data for {target_date}"
            }

            if check_out_time:
                params["check_out_time"] = check_out_time.isoformat()

            response = self.session.post(
                f"{self.base_url}/api/v1/attendance/manual/{employee_id}",
                params=params
            )

            if response.status_code == 200:
                print(f"✅ Created attendance record for {target_date}")
                return True
            else:
                print(f"❌ Failed to create attendance record: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating attendance record: {e}")
            return False

    def setup_sample_employees(self):
        """Create sample employees"""
        print("👥 Creating sample employees...")

        employees = [
            {
                "employee_code": "EMP001",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@company.com",
                "department": "Engineering",
                "position": "Software Engineer",
                "manager_email": "manager@company.com"
            },
            {
                "employee_code": "EMP002",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@company.com",
                "department": "Engineering",
                "position": "Senior Software Engineer",
                "manager_email": "manager@company.com"
            },
            {
                "employee_code": "EMP003",
                "first_name": "Mike",
                "last_name": "Johnson",
                "email": "mike.johnson@company.com",
                "department": "Marketing",
                "position": "Marketing Manager",
                "manager_email": "director@company.com"
            },
            {
                "employee_code": "EMP004",
                "first_name": "Sarah",
                "last_name": "Williams",
                "email": "sarah.williams@company.com",
                "department": "HR",
                "position": "HR Specialist",
                "manager_email": "hr-director@company.com"
            },
            {
                "employee_code": "EMP005",
                "first_name": "David",
                "last_name": "Brown",
                "email": "david.brown@company.com",
                "department": "Engineering",
                "position": "DevOps Engineer",
                "manager_email": "manager@company.com"
            }
        ]

        colors = [
            (100, 150, 200),  # Blue
            (200, 100, 150),  # Pink
            (150, 200, 100),  # Green
            (200, 150, 100),  # Orange
            (150, 100, 200)   # Purple
        ]

        created_employees = []
        for i, emp_data in enumerate(employees):
            face_image = self.create_test_face_image(
                emp_data['first_name'],
                colors[i % len(colors)]
            )
            employee = self.create_employee(emp_data, face_image)
            if employee:
                created_employees.append(employee)

        return created_employees

    def setup_sample_cameras(self):
        """Create sample cameras"""
        print("📹 Creating sample cameras...")

        cameras = [
            {
                "name": "Main Entrance",
                "location": "Ground Floor - Main Entrance",
                "url": "http://localhost:8080/video"
            },
            {
                "name": "Office Floor 1",
                "location": "First Floor - Open Office",
                "url": "http://localhost:8081/video"
            },
            {
                "name": "Meeting Room",
                "location": "Second Floor - Conference Room A",
                "url": "http://localhost:8082/video"
            }
        ]

        created_cameras = []
        for cam_data in cameras:
            camera = self.create_camera(cam_data)
            if camera:
                created_cameras.append(camera)

        return created_cameras

    def setup_sample_attendance_data(self, employees):
        """Create sample attendance data for the last week"""
        print("📊 Creating sample attendance data...")

        if not employees:
            print("⚠️ No employees available for attendance data")
            return

        # Create attendance for the last 7 days
        for i in range(7):
            target_date = date.today() - timedelta(days=i)

            for employee in employees:
                # Skip some days randomly to simulate absences
                import random
                if random.random() < 0.1:  # 10% absence rate
                    continue

                # Generate realistic check-in times (8:30 - 9:30 AM)
                check_in_hour = random.randint(8, 9)
                check_in_minute = random.randint(0, 59)
                if check_in_hour == 9 and check_in_minute > 30:
                    check_in_minute = 30

                check_in_time = datetime.combine(
                    target_date,
                    datetime.min.time().replace(hour=check_in_hour, minute=check_in_minute)
                )

                # Generate check-out times (5:00 - 7:00 PM)
                check_out_hour = random.randint(17, 19)
                check_out_minute = random.randint(0, 59)

                check_out_time = datetime.combine(
                    target_date,
                    datetime.min.time().replace(hour=check_out_hour, minute=check_out_minute)
                )

                self.create_attendance_record(
                    employee['id'],
                    target_date,
                    check_in_time,
                    check_out_time,
                    f"Sample data for {target_date}"
                )

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("🧹 Cleaning up test data...")

        # Delete employees
        for employee_id in self.created_employees:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/employees/{employee_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted employee {employee_id}")
                else:
                    print(f"❌ Failed to delete employee {employee_id}")
            except Exception as e:
                print(f"❌ Error deleting employee {employee_id}: {e}")

        # Delete cameras
        for camera_id in self.created_cameras:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/cameras/{camera_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted camera {camera_id}")
                else:
                    print(f"❌ Failed to delete camera {camera_id}")
            except Exception as e:
                print(f"❌ Error deleting camera {camera_id}: {e}")

    def run_setup(self):
        """Run the complete test data setup"""
        print("🚀 Setting up test data for Attendance Tracking System")
        print("=" * 60)

        try:
            # Check if system is running
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code != 200:
                print("❌ System is not running. Please start it first.")
                return False

            print("✅ System is running")

            # Create sample data
            employees = self.setup_sample_employees()
            cameras = self.setup_sample_cameras()
            self.setup_sample_attendance_data(employees)

            print("\n🎉 Test data setup completed!")
            print(f"   - Created {len(employees)} employees")
            print(f"   - Created {len(cameras)} cameras")
            print("   - Created sample attendance records")

            print("\n💡 Next steps:")
            print("   1. Test the API endpoints")
            print("   2. Check the attendance reports")
            print("   3. Start the camera simulator")
            print("   4. Run the test suite")

            return True

        except Exception as e:
            print(f"❌ Error during setup: {e}")
            return False

def main():
    import sys

    print("Test Data Setup for Attendance Tracking System")
    print("=" * 50)

    setup = TestDataSetup()

    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        setup.cleanup_test_data()
    else:
        success = setup.run_setup()
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()