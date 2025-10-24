# Upgrade to Full Mode with Camera Support

This guide explains how to upgrade from lite mode to full mode with real face recognition and camera support.

## Current Status

✅ **Lite Mode Working**: Basic API functionality without OpenCV
🔧 **Full Mode**: Real face recognition with cameras (requires setup)

## Option 1: Local Development (Recommended)

For development and testing with your local machine's camera:

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install System Dependencies (macOS)

```bash
# Install OpenCV dependencies
brew install cmake
brew install dlib

# For better camera support
brew install ffmpeg
```

### 3. Install System Dependencies (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
    python3-dev \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev
```

### 4. Run Locally

```bash
# Set environment variables
export CAMERA_URLS="0"  # Use default webcam

# Start the application
uvicorn app.main:app --reload
```

## Option 2: Docker with Pre-built Image

Use a pre-built Docker image with OpenCV support:

### 1. Alternative Dockerfile

Create `Dockerfile.opencv`:

```dockerfile
# Use a base image with OpenCV pre-installed
FROM jjanzic/docker-python3-opencv:latest

WORKDIR /app

# Install additional dependencies
RUN pip install --no-cache-dir dlib face-recognition

COPY requirements-lite.txt .
RUN pip install --no-cache-dir -r requirements-lite.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build and Run

```bash
docker build -f Dockerfile.opencv -t attendance-full .
docker run -p 8000:8000 --device=/dev/video0 attendance-full
```

## Option 3: Use External OpenCV Container

Run OpenCV processing in a separate container:

### 1. Create docker-compose.opencv.yml

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: attendance_db
      POSTGRES_USER: attendance_user
      POSTGRES_PASSWORD: attendance_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  opencv_processor:
    image: jjanzic/docker-python3-opencv:latest
    volumes:
      - ./app/services:/app/services
      - ./data:/app/data
    working_dir: /app
    command: python services/camera_processor.py

  attendance_app:
    build:
      dockerfile: Dockerfile.lite
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://attendance_user:attendance_password@postgres:5432/attendance_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - opencv_processor

volumes:
  postgres_data:
```

## Camera Configuration

### Webcam Support

```bash
# Use built-in webcam
CAMERA_URLS="0"

# Use external USB camera
CAMERA_URLS="1"

# Multiple cameras
CAMERA_URLS="0,1,2"
```

### IP Camera Support

```bash
# HTTP streaming camera
CAMERA_URLS="http://192.168.1.100:8080/video"

# RTSP camera
CAMERA_URLS="rtsp://admin:password@192.168.1.100:554/stream"

# Multiple IP cameras
CAMERA_URLS="http://cam1/video,http://cam2/video"
```

### Mixed Configuration

```bash
# Webcam + IP cameras
CAMERA_URLS="0,http://192.168.1.100:8080/video,1"
```

## Testing Full Mode

### 1. Test Dependencies

```bash
python scripts/test_full_mode.py
```

### 2. Test Camera Access

```bash
# Test default webcam
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera OK:' if cap.isOpened() else 'Camera Failed')"
```

### 3. Test Face Recognition

```bash
# Run the camera simulator
python scripts/camera_simulator.py

# In another terminal, test the system
python scripts/test_system.py
```

## Production Deployment

### Cloud Deployment

For cloud deployment without local cameras:

1. **Use IP cameras** connected to your network
2. **Configure camera URLs** in environment variables
3. **Deploy with Docker** using the lite version
4. **Add camera support** through external streaming services

### On-Premises Deployment

For on-premises with local cameras:

1. **Use local installation** (Option 1)
2. **Configure camera devices** in Docker
3. **Set up camera permissions** for Docker containers

## Troubleshooting

### Common Issues

**Camera Permission Denied**
```bash
# Add user to video group (Linux)
sudo usermod -a -G video $USER

# Run Docker with privileged mode
docker run --privileged ...
```

**OpenCV Import Error**
```bash
# Install system dependencies
sudo apt install libgl1-mesa-glx libglib2.0-0

# Or use headless version
pip install opencv-python-headless
```

**dlib Compilation Error**
```bash
# Install cmake and build tools
sudo apt install cmake build-essential

# Use conda instead of pip
conda install dlib
```

## Performance Optimization

### For Better Performance

1. **Use GPU acceleration** (if available)
2. **Reduce camera resolution** in settings
3. **Adjust recognition tolerance** for speed vs accuracy
4. **Use multiple worker processes**

### Configuration

```bash
# Environment variables for optimization
FACE_RECOGNITION_TOLERANCE=0.7  # Higher = faster, less accurate
FACE_DETECTION_MODEL=cnn        # CNN for GPU, hog for CPU
CAMERA_FPS=15                   # Lower FPS for better performance
```

## Current Functionality

**✅ Working in Lite Mode:**
- Employee management API
- Manual attendance tracking
- Database operations
- Email notifications
- Comprehensive testing

**🔧 Full Mode Adds:**
- Real-time camera feeds
- Automatic face detection
- Face recognition matching
- Live video streaming
- Automatic attendance recording

The system is production-ready in lite mode and can be upgraded to full mode when camera infrastructure is available.