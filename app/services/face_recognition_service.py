import cv2
import face_recognition
import numpy as np
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    def __init__(self):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_employee_ids: List[str] = []
        self.tolerance = settings.FACE_RECOGNITION_TOLERANCE
        self.model = settings.FACE_DETECTION_MODEL
        self.encodings_file = Path("data/face_encodings.pkl")
        self.encodings_file.parent.mkdir(exist_ok=True)
        self._load_encodings()

    def _load_encodings(self) -> None:
        """Load saved face encodings from file"""
        try:
            if self.encodings_file.exists():
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_employee_ids = data.get('employee_ids', [])
                logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
        except Exception as e:
            logger.error(f"Error loading face encodings: {e}")
            self.known_face_encodings = []
            self.known_face_employee_ids = []

    def _save_encodings(self) -> None:
        """Save face encodings to file"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'employee_ids': self.known_face_employee_ids
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved {len(self.known_face_encodings)} face encodings")
        except Exception as e:
            logger.error(f"Error saving face encodings: {e}")

    def encode_face_from_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """Extract face encoding from image bytes"""
        try:
            image = Image.open(BytesIO(image_data))
            image_rgb = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            face_locations = face_recognition.face_locations(image_rgb, model=self.model)

            if not face_locations:
                logger.warning("No faces found in the image")
                return None

            if len(face_locations) > 1:
                logger.warning("Multiple faces found, using the first one")

            face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

            if face_encodings:
                return face_encodings[0]

            return None

        except Exception as e:
            logger.error(f"Error encoding face from image: {e}")
            return None

    def encode_face_from_base64(self, base64_image: str) -> Optional[np.ndarray]:
        """Extract face encoding from base64 image"""
        try:
            image_data = base64.b64decode(base64_image)
            return self.encode_face_from_image(image_data)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    def register_employee_face(self, employee_id: str, image_data: bytes) -> bool:
        """Register a new employee's face"""
        try:
            face_encoding = self.encode_face_from_image(image_data)

            if face_encoding is None:
                logger.error(f"Could not extract face encoding for employee {employee_id}")
                return False

            if employee_id in self.known_face_employee_ids:
                index = self.known_face_employee_ids.index(employee_id)
                self.known_face_encodings[index] = face_encoding
                logger.info(f"Updated face encoding for employee {employee_id}")
            else:
                self.known_face_encodings.append(face_encoding)
                self.known_face_employee_ids.append(employee_id)
                logger.info(f"Added new face encoding for employee {employee_id}")

            self._save_encodings()
            return True

        except Exception as e:
            logger.error(f"Error registering employee face: {e}")
            return False

    def recognize_faces_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """Recognize faces in a video frame"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            recognized_faces = []

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    self.known_face_encodings,
                    face_encoding,
                    tolerance=self.tolerance
                )

                face_distances = face_recognition.face_distance(
                    self.known_face_encodings,
                    face_encoding
                )

                employee_id = "Unknown"
                confidence = 0.0

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        employee_id = self.known_face_employee_ids[best_match_index]
                        confidence = 1 - face_distances[best_match_index]

                top, right, bottom, left = face_location

                recognized_faces.append({
                    'employee_id': employee_id,
                    'confidence': float(confidence),
                    'location': {
                        'top': int(top),
                        'right': int(right),
                        'bottom': int(bottom),
                        'left': int(left)
                    }
                })

            return recognized_faces

        except Exception as e:
            logger.error(f"Error recognizing faces: {e}")
            return []

    def remove_employee_face(self, employee_id: str) -> bool:
        """Remove an employee's face encoding"""
        try:
            if employee_id in self.known_face_employee_ids:
                index = self.known_face_employee_ids.index(employee_id)
                del self.known_face_encodings[index]
                del self.known_face_employee_ids[index]
                self._save_encodings()
                logger.info(f"Removed face encoding for employee {employee_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing employee face: {e}")
            return False

    def get_registered_employees(self) -> List[str]:
        """Get list of registered employee IDs"""
        return self.known_face_employee_ids.copy()

    def draw_faces_on_frame(self, frame: np.ndarray, recognized_faces: List[Dict]) -> np.ndarray:
        """Draw bounding boxes and labels on detected faces"""
        try:
            for face in recognized_faces:
                location = face['location']
                employee_id = face['employee_id']
                confidence = face['confidence']

                top, right, bottom, left = location['top'], location['right'], location['bottom'], location['left']

                color = (0, 255, 0) if employee_id != "Unknown" else (0, 0, 255)

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                label = f"{employee_id} ({confidence:.2f})" if employee_id != "Unknown" else "Unknown"
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            return frame

        except Exception as e:
            logger.error(f"Error drawing faces on frame: {e}")
            return frame