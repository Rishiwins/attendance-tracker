import cv2
import asyncio
import logging
from typing import Dict, List, Optional, Callable
import numpy as np
from datetime import datetime
import threading
import queue
import time

from app.config import settings
from app.services.face_recognition_service import FaceRecognitionService

logger = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, camera_id: str, url: str, face_recognition_service: FaceRecognitionService):
        self.camera_id = camera_id
        self.url = url
        self.face_recognition_service = face_recognition_service
        self.cap = None
        self.is_running = False
        self.thread = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.last_frame = None
        self.last_recognition_time = 0
        self.recognition_interval = 2.0  # Recognize faces every 2 seconds
        self.on_face_detected: Optional[Callable] = None

    def start(self):
        """Start the camera stream"""
        if self.is_running:
            return

        try:
            # Handle different camera URL types
            if self.url.isdigit():
                # Webcam index (0, 1, 2, etc.)
                self.cap = cv2.VideoCapture(int(self.url))
            elif self.url.startswith(('http://', 'https://', 'rtsp://')):
                # IP camera or network stream
                self.cap = cv2.VideoCapture(self.url)
            else:
                # File path or other format
                self.cap = cv2.VideoCapture(self.url)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id} at {self.url}")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            # For webcams, set resolution
            if self.url.isdigit():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

            logger.info(f"Started camera stream {self.camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error starting camera {self.camera_id}: {e}")
            return False

    def stop(self):
        """Stop the camera stream"""
        self.is_running = False

        if self.thread:
            self.thread.join(timeout=5)

        if self.cap:
            self.cap.release()

        logger.info(f"Stopped camera stream {self.camera_id}")

    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning(f"Failed to read frame from camera {self.camera_id}")
                    time.sleep(0.1)
                    continue

                self.last_frame = frame.copy()

                if not self.frame_queue.full():
                    self.frame_queue.put(frame)

                current_time = time.time()
                if current_time - self.last_recognition_time >= self.recognition_interval:
                    self._process_frame_for_recognition(frame)
                    self.last_recognition_time = current_time

                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                logger.error(f"Error in capture loop for camera {self.camera_id}: {e}")
                time.sleep(1)

    def _process_frame_for_recognition(self, frame: np.ndarray):
        """Process frame for face recognition"""
        try:
            recognized_faces = self.face_recognition_service.recognize_faces_in_frame(frame)

            if recognized_faces and self.on_face_detected:
                detection_data = {
                    'camera_id': self.camera_id,
                    'timestamp': datetime.utcnow(),
                    'faces': recognized_faces,
                    'frame': frame
                }
                self.on_face_detected(detection_data)

        except Exception as e:
            logger.error(f"Error processing frame for recognition: {e}")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the camera"""
        return self.last_frame

    def get_frame_from_queue(self) -> Optional[np.ndarray]:
        """Get frame from the queue (non-blocking)"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def is_alive(self) -> bool:
        """Check if camera stream is alive"""
        return self.is_running and self.thread and self.thread.is_alive()

class CameraManager:
    def __init__(self, face_recognition_service: FaceRecognitionService):
        self.face_recognition_service = face_recognition_service
        self.cameras: Dict[str, CameraStream] = {}
        self.detection_callbacks: List[Callable] = []

    def add_camera(self, camera_id: str, url: str) -> bool:
        """Add a new camera to the system"""
        try:
            if camera_id in self.cameras:
                logger.warning(f"Camera {camera_id} already exists")
                return False

            camera_stream = CameraStream(camera_id, url, self.face_recognition_service)
            camera_stream.on_face_detected = self._on_face_detected

            if camera_stream.start():
                self.cameras[camera_id] = camera_stream
                logger.info(f"Added camera {camera_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error adding camera {camera_id}: {e}")
            return False

    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the system"""
        try:
            if camera_id not in self.cameras:
                return False

            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            logger.info(f"Removed camera {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}")
            return False

    def start_all_cameras(self):
        """Start all configured cameras"""
        for camera_id, url in enumerate(settings.camera_url_list):
            self.add_camera(f"camera_{camera_id}", url)

    def stop_all_cameras(self):
        """Stop all cameras"""
        for camera_id in list(self.cameras.keys()):
            self.remove_camera(camera_id)

    def _on_face_detected(self, detection_data: Dict):
        """Handle face detection from any camera"""
        for callback in self.detection_callbacks:
            try:
                callback(detection_data)
            except Exception as e:
                logger.error(f"Error in detection callback: {e}")

    def add_detection_callback(self, callback: Callable):
        """Add a callback for face detection events"""
        self.detection_callbacks.append(callback)

    def remove_detection_callback(self, callback: Callable):
        """Remove a detection callback"""
        if callback in self.detection_callbacks:
            self.detection_callbacks.remove(callback)

    def get_camera_status(self) -> Dict[str, Dict]:
        """Get status of all cameras"""
        status = {}
        for camera_id, camera_stream in self.cameras.items():
            status[camera_id] = {
                'is_alive': camera_stream.is_alive(),
                'url': camera_stream.url,
                'last_frame_available': camera_stream.last_frame is not None
            }
        return status

    def get_camera_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get latest frame from specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_latest_frame()
        return None

    def get_all_camera_frames(self) -> Dict[str, np.ndarray]:
        """Get latest frames from all cameras"""
        frames = {}
        for camera_id, camera_stream in self.cameras.items():
            frame = camera_stream.get_latest_frame()
            if frame is not None:
                frames[camera_id] = frame
        return frames

    def restart_camera(self, camera_id: str) -> bool:
        """Restart a specific camera"""
        if camera_id not in self.cameras:
            return False

        url = self.cameras[camera_id].url
        self.remove_camera(camera_id)
        return self.add_camera(camera_id, url)

    def get_active_cameras(self) -> List[str]:
        """Get list of active camera IDs"""
        return [
            camera_id for camera_id, camera_stream in self.cameras.items()
            if camera_stream.is_alive()
        ]