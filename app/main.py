from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.database import engine, Base
from app.api import employees, attendance, cameras
from app.services.attendance_service import AttendanceService
from app.services.email_service import EmailService
from app.config import settings

# Set up logging first
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import OpenCV dependencies, fall back to lite mode if not available
try:
    import cv2
    import face_recognition
    from app.services.camera_service import CameraManager
    from app.services.face_recognition_service import FaceRecognitionService
    FULL_MODE = True
    print("OpenCV and face_recognition detected - running in FULL MODE")
except ImportError as e:
    from app.services.face_recognition_service_lite import FaceRecognitionService
    FULL_MODE = False
    print(f"OpenCV/face_recognition not available ({e}) - running in LITE MODE")

face_service = FaceRecognitionService()
if FULL_MODE:
    camera_manager = CameraManager(face_service)
else:
    camera_manager = None
attendance_service = AttendanceService()
email_service = EmailService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Attendance Tracking System...")

    Base.metadata.create_all(bind=engine)

    def on_face_detected(detection_data):
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            attendance_service.process_face_detection(detection_data, db)
        except Exception as e:
            logger.error(f"Error processing face detection: {e}")
        finally:
            db.close()

    if FULL_MODE and camera_manager:
        camera_manager.add_detection_callback(on_face_detected)
        camera_manager.start_all_cameras()
    else:
        logger.info("Camera functionality disabled - running in lite mode")

    logger.info("System started successfully")

    yield

    logger.info("Shutting down system...")
    if FULL_MODE and camera_manager:
        camera_manager.stop_all_cameras()
    logger.info("System shutdown complete")

app = FastAPI(
    title="Employee Attendance Tracking System",
    description="Real-time employee attendance tracking using face recognition",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(cameras.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "Employee Attendance Tracking System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    system_status = camera_manager.get_camera_status()
    active_cameras = camera_manager.get_active_cameras()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "connected",
            "face_recognition": "active",
            "camera_manager": "active",
            "active_cameras": len(active_cameras),
            "total_cameras": len(system_status)
        }
    }

@app.get("/api/v1/system/info")
def get_system_info():
    """Get system information"""
    registered_employees = face_service.get_registered_employees()
    active_cameras = camera_manager.get_active_cameras()

    return {
        "system_name": "Employee Attendance Tracking System",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "statistics": {
            "registered_employees": len(registered_employees),
            "active_cameras": len(active_cameras),
            "face_recognition_tolerance": settings.FACE_RECOGNITION_TOLERANCE,
            "face_detection_model": settings.FACE_DETECTION_MODEL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)