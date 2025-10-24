from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from app.database import engine, Base
from app.api import employees, attendance
from app.services.face_recognition_service_lite import FaceRecognitionService
from app.services.attendance_service import AttendanceService
from app.services.email_service import EmailService
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

face_service = FaceRecognitionService()
attendance_service = AttendanceService()
email_service = EmailService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Attendance Tracking System (Lite Mode)...")

    Base.metadata.create_all(bind=engine)

    logger.info("System started successfully (without camera support)")

    yield

    logger.info("System shutdown complete")

app = FastAPI(
    title="Employee Attendance Tracking System (Lite)",
    description="Employee attendance tracking API - Lite version without camera support",
    version="1.0.0-lite",
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

@app.get("/")
def read_root():
    return {
        "message": "Employee Attendance Tracking System (Lite Mode)",
        "version": "1.0.0-lite",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "This is the lite version without camera and OpenCV support"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "connected",
            "face_recognition": "simulated",
            "camera_manager": "disabled",
            "mode": "lite"
        }
    }

@app.get("/api/v1/system/info")
def get_system_info():
    """Get system information"""
    registered_employees = face_service.get_registered_employees()

    return {
        "system_name": "Employee Attendance Tracking System (Lite)",
        "version": "1.0.0-lite",
        "environment": settings.ENVIRONMENT,
        "mode": "lite",
        "statistics": {
            "registered_employees": len(registered_employees),
            "active_cameras": 0,
            "face_recognition_tolerance": settings.FACE_RECOGNITION_TOLERANCE,
            "face_detection_model": settings.FACE_DETECTION_MODEL
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)