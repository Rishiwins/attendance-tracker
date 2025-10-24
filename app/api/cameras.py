from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import cv2
import io
from PIL import Image

from app.database import get_db
from app.models import Camera
from app.schemas import Camera as CameraSchema, CameraCreate
from app.services.camera_service import CameraManager
from app.services.face_recognition_service import FaceRecognitionService

router = APIRouter(prefix="/cameras", tags=["cameras"])

face_service = FaceRecognitionService()
camera_manager = CameraManager(face_service)

@router.post("/", response_model=CameraSchema)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db)
):
    """Create a new camera"""
    db_camera = db.query(Camera).filter(Camera.url == camera.url).first()
    if db_camera:
        raise HTTPException(status_code=400, detail="Camera URL already exists")

    db_camera = Camera(**camera.dict())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)

    success = camera_manager.add_camera(db_camera.id, camera.url)
    if not success:
        db.delete(db_camera)
        db.commit()
        raise HTTPException(status_code=400, detail="Failed to initialize camera")

    return db_camera

@router.get("/", response_model=List[CameraSchema])
def list_cameras(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all cameras"""
    query = db.query(Camera)
    if active_only:
        query = query.filter(Camera.is_active == True)

    cameras = query.all()
    return cameras

@router.get("/{camera_id}", response_model=CameraSchema)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    """Get camera by ID"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.put("/{camera_id}/toggle")
def toggle_camera(camera_id: str, db: Session = Depends(get_db)):
    """Toggle camera active status"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.is_active:
        success = camera_manager.remove_camera(camera_id)
        if success:
            camera.is_active = False
    else:
        success = camera_manager.add_camera(camera_id, camera.url)
        if success:
            camera.is_active = True

    if not success:
        raise HTTPException(status_code=400, detail="Failed to toggle camera")

    db.commit()
    return {"message": f"Camera {'activated' if camera.is_active else 'deactivated'} successfully"}

@router.delete("/{camera_id}")
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    """Delete camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera_manager.remove_camera(camera_id)
    db.delete(camera)
    db.commit()

    return {"message": "Camera deleted successfully"}

@router.get("/{camera_id}/status")
def get_camera_status(camera_id: str, db: Session = Depends(get_db)):
    """Get camera status"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    status = camera_manager.get_camera_status()
    camera_status = status.get(camera_id, {
        'is_alive': False,
        'url': camera.url,
        'last_frame_available': False
    })

    return {
        'camera_id': camera_id,
        'name': camera.name,
        'location': camera.location,
        'is_active': camera.is_active,
        'status': camera_status
    }

@router.get("/{camera_id}/frame")
def get_camera_frame(camera_id: str, db: Session = Depends(get_db)):
    """Get latest frame from camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    frame = camera_manager.get_camera_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="No frame available")

    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()

    return StreamingResponse(
        io.BytesIO(frame_bytes),
        media_type="image/jpeg"
    )

@router.get("/{camera_id}/frame-with-detection")
def get_camera_frame_with_detection(camera_id: str, db: Session = Depends(get_db)):
    """Get latest frame from camera with face detection overlay"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    frame = camera_manager.get_camera_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="No frame available")

    recognized_faces = face_service.recognize_faces_in_frame(frame)

    frame_with_faces = face_service.draw_faces_on_frame(frame, recognized_faces)

    _, buffer = cv2.imencode('.jpg', frame_with_faces)
    frame_bytes = buffer.tobytes()

    return StreamingResponse(
        io.BytesIO(frame_bytes),
        media_type="image/jpeg"
    )

@router.get("/{camera_id}/stream")
def get_camera_stream(camera_id: str, db: Session = Depends(get_db)):
    """Get live video stream from camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    def generate_stream():
        while True:
            frame = camera_manager.get_camera_frame(camera_id)
            if frame is not None:
                recognized_faces = face_service.recognize_faces_in_frame(frame)
                frame_with_faces = face_service.draw_faces_on_frame(frame, recognized_faces)

                _, buffer = cv2.imencode('.jpg', frame_with_faces)
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/{camera_id}/restart")
def restart_camera(camera_id: str, db: Session = Depends(get_db)):
    """Restart camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    success = camera_manager.restart_camera(camera_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to restart camera")

    return {"message": "Camera restarted successfully"}

@router.get("/system/status")
def get_all_cameras_status(db: Session = Depends(get_db)):
    """Get status of all cameras"""
    cameras = db.query(Camera).all()
    system_status = camera_manager.get_camera_status()

    camera_statuses = []
    for camera in cameras:
        status = system_status.get(camera.id, {
            'is_alive': False,
            'url': camera.url,
            'last_frame_available': False
        })

        camera_statuses.append({
            'camera_id': camera.id,
            'name': camera.name,
            'location': camera.location,
            'url': camera.url,
            'is_active': camera.is_active,
            'is_alive': status['is_alive'],
            'last_frame_available': status['last_frame_available']
        })

    return {
        'total_cameras': len(cameras),
        'active_cameras': len([c for c in cameras if c.is_active]),
        'alive_cameras': len([s for s in camera_statuses if s['is_alive']]),
        'camera_details': camera_statuses
    }