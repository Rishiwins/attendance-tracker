# Testing Guide - Employee Attendance Tracking System

This guide will help you test the attendance tracking system to verify all components are working correctly.

## Quick Test Setup

### 1. Start the System

```bash
# Option A: Using Docker (Recommended)
docker-compose up -d

# Option B: Local Development
# Start PostgreSQL and Redis first, then:
uvicorn app.main:app --reload
```

### 2. Verify System Health

```bash
# Check if API is running
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00",
  "components": {
    "database": "connected",
    "face_recognition": "active",
    "camera_manager": "active",
    "active_cameras": 0,
    "total_cameras": 0
  }
}
```

## Step-by-Step Testing

### Phase 1: API Testing

#### 1. Test Employee Management

```bash
# Create a test employee
curl -X POST "http://localhost:8000/api/v1/employees/" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_code": "TEST001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@test.com",
    "department": "Engineering",
    "position": "Software Engineer",
    "manager_email": "manager@test.com"
  }'

# List employees
curl http://localhost:8000/api/v1/employees/

# Get employee by code
curl http://localhost:8000/api/v1/employees/code/TEST001
```

#### 2. Test Attendance Management

```bash
# Get today's attendance (should be empty initially)
curl "http://localhost:8000/api/v1/attendance/daily/$(date +%Y-%m-%d)"

# Mark manual attendance for testing
EMPLOYEE_ID="<employee_id_from_previous_step>"
curl -X POST "http://localhost:8000/api/v1/attendance/manual/$EMPLOYEE_ID" \
  -d "target_date=$(date +%Y-%m-%d)&check_in_time=$(date +%Y-%m-%d)T09:00:00&notes=Test+entry"

# Check attendance again
curl "http://localhost:8000/api/v1/attendance/daily/$(date +%Y-%m-%d)"
```

### Phase 2: Face Recognition Testing

#### 1. Upload Face Image

```bash
# Upload a test face image (you'll need a photo file)
EMPLOYEE_ID="<your_employee_id>"
curl -X POST "http://localhost:8000/api/v1/employees/$EMPLOYEE_ID/face-image" \
  -F "file=@test_face.jpg"

# Or upload base64 encoded image
curl -X POST "http://localhost:8000/api/v1/employees/$EMPLOYEE_ID/face-image-base64" \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image_data_here"}'

# Check if face is registered
curl "http://localhost:8000/api/v1/employees/$EMPLOYEE_ID/face-registered"
```

### Phase 3: Camera Testing

Since you might not have physical cameras, we'll test with a simulated camera or webcam.

#### 1. Add a Test Camera

```bash
# Add a camera (using webcam or IP camera)
curl -X POST "http://localhost:8000/api/v1/cameras/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "location": "Test Location",
    "url": "0"
  }'

# Note: url "0" uses default webcam, or use "http://your-ip-camera-url"
```

#### 2. Test Camera Functions

```bash
# List cameras
curl http://localhost:8000/api/v1/cameras/

# Get camera status
CAMERA_ID="<camera_id_from_previous_step>"
curl "http://localhost:8000/api/v1/cameras/$CAMERA_ID/status"

# Get a frame from camera (should return image)
curl "http://localhost:8000/api/v1/cameras/$CAMERA_ID/frame" --output test_frame.jpg

# Get frame with face detection overlay
curl "http://localhost:8000/api/v1/cameras/$CAMERA_ID/frame-with-detection" --output detected_frame.jpg
```

## Automated Testing Scripts

### Test Script 1: Basic API Tests

Run the automated test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_employees.py -v
pytest tests/test_attendance.py -v
pytest tests/test_face_recognition.py -v
```

### Test Script 2: System Integration Test

Use our comprehensive testing scripts:

```bash
# Quick system check
./scripts/quick_test.sh

# Comprehensive system test
python scripts/test_system.py

# Setup sample test data
python scripts/setup_test_data.py

# Start camera simulator
python scripts/camera_simulator.py
```

## Complete Testing Workflow

### 1. Start the System

```bash
# Using Docker (Recommended)
docker-compose up -d

# Wait for services to start
sleep 10

# Check system health
curl http://localhost:8000/health
```

### 2. Run Quick Tests

```bash
# Run basic API tests
./scripts/quick_test.sh
```

### 3. Setup Test Data

```bash
# Create sample employees, cameras, and attendance
python scripts/setup_test_data.py
```

### 4. Start Camera Simulator

```bash
# In a new terminal, start the camera simulator
python scripts/camera_simulator.py

# This will:
# - Simulate a camera feed at http://localhost:8080/video
# - Show simulated employee presence/absence
# - Allow manual control of employee detection
```

### 5. Test Face Recognition

```bash
# Add the simulated camera to the system
curl -X POST "http://localhost:8000/api/v1/cameras/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simulator Camera",
    "location": "Test Location",
    "url": "http://localhost:8080/video"
  }'

# Check camera status
curl "http://localhost:8000/api/v1/cameras/system/status"

# Get live feed with face detection
curl "http://localhost:8000/api/v1/cameras/<camera_id>/frame-with-detection" --output detected_frame.jpg
```

### 6. Test Email Notifications

```bash
# Configure email settings in .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
MANAGER_EMAIL=manager@company.com

# Restart the system to pick up email settings
docker-compose restart

# Test email task (requires Celery worker)
python -c "
from app.tasks.email_tasks import send_daily_eod_reports
result = send_daily_eod_reports.delay()
print('Email task queued:', result.id)
"
```

### 7. Run Comprehensive Tests

```bash
# Run the full test suite
python scripts/test_system.py

# Run unit tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

## Expected Test Results

### Successful Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00",
  "components": {
    "database": "connected",
    "face_recognition": "active",
    "camera_manager": "active",
    "active_cameras": 1,
    "total_cameras": 1
  }
}
```

### Successful Employee Creation
```json
{
  "id": "uuid-here",
  "employee_code": "TEST001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@test.com",
  "department": "Engineering",
  "position": "Software Engineer",
  "manager_email": "manager@test.com",
  "is_active": true,
  "face_image_path": null,
  "created_at": "2024-01-01T10:00:00"
}
```

### Successful Attendance Report
```json
{
  "date": "2024-01-01",
  "total_employees": 5,
  "present_employees": 4,
  "absent_employees": 1,
  "late_employees": 1,
  "attendance_records": [
    {
      "employee_id": "uuid",
      "employee_name": "John Doe",
      "date": "2024-01-01",
      "check_in_time": "2024-01-01T09:00:00",
      "check_out_time": "2024-01-01T17:30:00",
      "total_hours": 8.5,
      "status": "present"
    }
  ]
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. System Not Responding
```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs attendance_app

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Connect to database manually
docker-compose exec postgres psql -U attendance_user -d attendance_db
```

#### 3. Camera Issues
```bash
# Check camera simulator
python scripts/camera_simulator.py

# Test camera URL directly
curl http://localhost:8080/

# Check camera status in system
curl http://localhost:8000/api/v1/cameras/system/status
```

#### 4. Face Recognition Issues
```bash
# Check if face encodings are saved
ls -la data/face_encodings.pkl

# Check face registration status
curl "http://localhost:8000/api/v1/employees/<employee_id>/face-registered"
```

#### 5. Email Issues
```bash
# Check Celery worker status
docker-compose logs celery_worker

# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('SMTP connection successful')
"
```

## Performance Testing

### Load Testing
```bash
# Install Apache Bench
apt-get install apache2-utils

# Test API endpoints
ab -n 100 -c 10 http://localhost:8000/health
ab -n 50 -c 5 http://localhost:8000/api/v1/employees/
```

### Memory and CPU Usage
```bash
# Monitor container resources
docker stats

# Check system resource usage
top -p $(pgrep -f uvicorn)
```

## Cleanup

```bash
# Remove test data
python scripts/setup_test_data.py --cleanup

# Stop and remove containers
docker-compose down -v

# Remove test images
rm -f test_frame.jpg detected_frame.jpg
```

## API Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Video Streaming URLs

When camera simulator is running:
- Status page: http://localhost:8080/
- Video stream: http://localhost:8080/video
- Single frame: http://localhost:8080/frame
