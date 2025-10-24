# Employee Attendance Tracking System

A production-ready employee attendance tracking system using real-time camera detection and face recognition technology.

## Features

- **Real-time Face Detection & Recognition**: Uses OpenCV and face_recognition library
- **Automated Attendance Tracking**: Automatic check-in/check-out detection
- **Office Hours Calculation**: Tracks working hours, breaks, and overtime
- **Email Notifications**: Daily EOD reports sent to managers
- **REST API**: Comprehensive API for all operations
- **Multi-camera Support**: Support for multiple camera feeds
- **Dashboard Interface**: Web-based admin interface
- **Production Ready**: Docker containerization with proper logging and monitoring

## Architecture

### Core Components

1. **Face Recognition Service**: Handles face detection, encoding, and recognition
2. **Camera Service**: Manages multiple camera streams and real-time processing
3. **Attendance Service**: Calculates working hours and attendance status
4. **Email Service**: Automated email notifications and reports
5. **REST API**: FastAPI-based endpoints for all operations
6. **Database**: PostgreSQL with SQLAlchemy ORM
7. **Task Queue**: Celery with Redis for async operations

### Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Cache/Queue**: Redis, Celery
- **Computer Vision**: OpenCV, face_recognition
- **Email**: SMTP with Jinja2 templates
- **Deployment**: Docker, Docker Compose

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if running locally)
- Redis (if running locally)

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd assignment
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the system:
```bash
docker-compose up -d
```

4. Access the API:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up database:
```bash
# Create PostgreSQL database
createdb attendance_db

# Run migrations
alembic upgrade head
```

3. Start services:
```bash
# Start Redis
redis-server

# Start the application
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/attendance_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Camera Settings
CAMERA_URLS=http://camera1:8080/video,http://camera2:8080/video

# Face Recognition
FACE_RECOGNITION_TOLERANCE=0.6
FACE_DETECTION_MODEL=hog

# Notifications
ADMIN_EMAIL=admin@company.com
MANAGER_EMAIL=manager@company.com
```

## API Usage

### Employee Management

```bash
# Create employee
curl -X POST "http://localhost:8000/api/v1/employees/" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_code": "EMP001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@company.com",
    "department": "Engineering",
    "position": "Software Engineer",
    "manager_email": "manager@company.com"
  }'

# Upload face image
curl -X POST "http://localhost:8000/api/v1/employees/{employee_id}/face-image" \
  -F "file=@face_image.jpg"

# List employees
curl "http://localhost:8000/api/v1/employees/"
```

### Attendance Management

```bash
# Get daily attendance
curl "http://localhost:8000/api/v1/attendance/daily/2024-01-01"

# Get employee attendance history
curl "http://localhost:8000/api/v1/attendance/employee/{employee_id}?start_date=2024-01-01&end_date=2024-01-31"

# Mark manual attendance
curl -X POST "http://localhost:8000/api/v1/attendance/manual/{employee_id}" \
  -d "target_date=2024-01-01&check_in_time=2024-01-01T09:00:00"
```

### Camera Management

```bash
# List cameras
curl "http://localhost:8000/api/v1/cameras/"

# Get camera status
curl "http://localhost:8000/api/v1/cameras/{camera_id}/status"

# Get live camera feed
curl "http://localhost:8000/api/v1/cameras/{camera_id}/stream"
```

## System Features

### Attendance Tracking

- **Automatic Detection**: Face recognition triggers check-in/check-out
- **Break Tracking**: Detects when employees are away from their desk
- **Working Hours**: Calculates total hours, breaks, and overtime
- **Late Arrival Detection**: Flags employees arriving after office hours
- **Manual Override**: Ability to manually mark attendance

### Email Notifications

- **Daily EOD Reports**: Sent to managers at end of day
- **Attendance Alerts**: Notifications for late arrivals, early departures
- **System Alerts**: Technical issue notifications for administrators
- **Custom Templates**: HTML email templates with company branding

### Face Recognition

- **Multiple Face Support**: Can handle multiple people in frame
- **Confidence Scoring**: Adjustable recognition threshold
- **Face Enrollment**: Easy employee face registration
- **Real-time Processing**: Live face detection and recognition

### Monitoring & Logging

- **Comprehensive Logging**: Structured logging with rotation
- **Health Checks**: System component status monitoring
- **Performance Metrics**: Camera feed status, recognition accuracy
- **Error Handling**: Graceful error handling and recovery

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Production Deployment

### Docker Deployment

1. Update production configuration in `.env`
2. Build and deploy:

```bash
docker-compose -f docker-compose.yml up -d
```

### Security Considerations

- Change default secret keys
- Use strong database passwords
- Configure HTTPS/TLS termination
- Restrict camera access to internal network
- Regular security updates

### Performance Optimization

- Adjust face recognition tolerance for accuracy vs speed
- Configure camera resolution for optimal performance
- Use Redis clustering for high availability
- Database connection pooling
- Load balancing for multiple instances

## Troubleshooting

### Common Issues

1. **Camera Connection Failed**
   - Check camera URL and network connectivity
   - Verify camera supports the specified format
   - Check firewall settings

2. **Face Recognition Not Working**
   - Ensure proper lighting conditions
   - Check face image quality during enrollment
   - Adjust recognition tolerance settings

3. **Email Notifications Not Sending**
   - Verify SMTP credentials
   - Check firewall/network restrictions
   - Ensure proper email templates exist

4. **Database Connection Issues**
   - Verify database credentials
   - Check network connectivity
   - Ensure database server is running

### Logs Location

- Application logs: `logs/attendance_system.log`
- Docker logs: `docker-compose logs -f attendance_app`

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation at `/docs` endpoint