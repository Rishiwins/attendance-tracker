import logging
from typing import List, Dict, Optional
import base64
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """
    Lite version of face recognition service without OpenCV dependencies.
    This is for testing the API functionality without heavy CV libraries.
    """

    def __init__(self):
        self.known_face_employee_ids: List[str] = []
        self.tolerance = settings.FACE_RECOGNITION_TOLERANCE
        self.model = settings.FACE_DETECTION_MODEL
        self.encodings_file = Path("data/face_encodings.txt")
        self.encodings_file.parent.mkdir(exist_ok=True)
        self._load_encodings()

    def _load_encodings(self) -> None:
        """Load saved face employee IDs from file"""
        try:
            if self.encodings_file.exists():
                with open(self.encodings_file, 'r') as f:
                    self.known_face_employee_ids = [line.strip() for line in f.readlines()]
                logger.info(f"Loaded {len(self.known_face_employee_ids)} registered employees")
        except Exception as e:
            logger.error(f"Error loading face registrations: {e}")
            self.known_face_employee_ids = []

    def _save_encodings(self) -> None:
        """Save face employee IDs to file"""
        try:
            with open(self.encodings_file, 'w') as f:
                for employee_id in self.known_face_employee_ids:
                    f.write(f"{employee_id}\n")
            logger.info(f"Saved {len(self.known_face_employee_ids)} registered employees")
        except Exception as e:
            logger.error(f"Error saving face registrations: {e}")

    def encode_face_from_image(self, image_data: bytes) -> Optional[str]:
        """Simulate face encoding from image bytes (returns dummy encoding)"""
        try:
            # For lite version, just simulate successful encoding
            if len(image_data) > 100:  # Basic validation
                return "dummy_face_encoding"
            return None
        except Exception as e:
            logger.error(f"Error encoding face from image: {e}")
            return None

    def encode_face_from_base64(self, base64_image: str) -> Optional[str]:
        """Simulate face encoding from base64 image"""
        try:
            image_data = base64.b64decode(base64_image)
            return self.encode_face_from_image(image_data)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    def register_employee_face(self, employee_id: str, image_data: bytes) -> bool:
        """Register a new employee's face (simulation)"""
        try:
            face_encoding = self.encode_face_from_image(image_data)

            if face_encoding is None:
                logger.error(f"Could not extract face encoding for employee {employee_id}")
                return False

            if employee_id not in self.known_face_employee_ids:
                self.known_face_employee_ids.append(employee_id)
                logger.info(f"Added new face registration for employee {employee_id}")
            else:
                logger.info(f"Updated face registration for employee {employee_id}")

            self._save_encodings()
            return True

        except Exception as e:
            logger.error(f"Error registering employee face: {e}")
            return False

    def recognize_faces_in_frame(self, frame) -> List[Dict]:
        """Simulate face recognition in a frame"""
        try:
            # For lite version, simulate finding one random registered employee
            if self.known_face_employee_ids:
                # Simulate recognizing the first registered employee
                employee_id = self.known_face_employee_ids[0]

                recognized_faces = [{
                    'employee_id': employee_id,
                    'confidence': 0.85,  # Simulated confidence
                    'location': {
                        'top': 100,
                        'right': 200,
                        'bottom': 200,
                        'left': 100
                    }
                }]
                return recognized_faces

            return []

        except Exception as e:
            logger.error(f"Error recognizing faces: {e}")
            return []

    def remove_employee_face(self, employee_id: str) -> bool:
        """Remove an employee's face registration"""
        try:
            if employee_id in self.known_face_employee_ids:
                self.known_face_employee_ids.remove(employee_id)
                self._save_encodings()
                logger.info(f"Removed face registration for employee {employee_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing employee face: {e}")
            return False

    def get_registered_employees(self) -> List[str]:
        """Get list of registered employee IDs"""
        return self.known_face_employee_ids.copy()

    def draw_faces_on_frame(self, frame, recognized_faces: List[Dict]):
        """Simulate drawing faces on frame (returns original frame)"""
        # For lite version, just return the original frame
        # In full version, this would use OpenCV to draw bounding boxes
        logger.info(f"Would draw {len(recognized_faces)} faces on frame")
        return frame