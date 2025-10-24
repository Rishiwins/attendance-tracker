import pytest
import numpy as np
from unittest.mock import Mock, patch
from app.services.face_recognition_service import FaceRecognitionService

class TestFaceRecognitionService:
    def setup_method(self):
        """Set up test fixtures"""
        self.face_service = FaceRecognitionService()

    def test_initialization(self):
        """Test service initialization"""
        assert self.face_service.tolerance == 0.6
        assert self.face_service.model == "hog"
        assert isinstance(self.face_service.known_face_encodings, list)
        assert isinstance(self.face_service.known_face_employee_ids, list)

    def test_get_registered_employees_empty(self):
        """Test getting registered employees when none exist"""
        employees = self.face_service.get_registered_employees()
        assert isinstance(employees, list)

    @patch('app.services.face_recognition_service.face_recognition')
    def test_encode_face_from_image_success(self, mock_face_recognition):
        """Test successful face encoding from image"""
        mock_face_recognition.face_locations.return_value = [(0, 100, 100, 0)]
        mock_face_recognition.face_encodings.return_value = [np.array([1, 2, 3, 4])]

        image_data = b"fake_image_data"
        encoding = self.face_service.encode_face_from_image(image_data)

        assert encoding is not None
        assert isinstance(encoding, np.ndarray)

    @patch('app.services.face_recognition_service.face_recognition')
    def test_encode_face_from_image_no_faces(self, mock_face_recognition):
        """Test face encoding when no faces are found"""
        mock_face_recognition.face_locations.return_value = []

        image_data = b"fake_image_data"
        encoding = self.face_service.encode_face_from_image(image_data)

        assert encoding is None

    @patch('app.services.face_recognition_service.face_recognition')
    def test_register_employee_face_success(self, mock_face_recognition):
        """Test successful employee face registration"""
        mock_face_recognition.face_locations.return_value = [(0, 100, 100, 0)]
        mock_face_recognition.face_encodings.return_value = [np.array([1, 2, 3, 4])]

        employee_id = "emp123"
        image_data = b"fake_image_data"

        success = self.face_service.register_employee_face(employee_id, image_data)

        assert success is True
        assert employee_id in self.face_service.known_face_employee_ids

    @patch('app.services.face_recognition_service.face_recognition')
    def test_register_employee_face_failure(self, mock_face_recognition):
        """Test employee face registration failure"""
        mock_face_recognition.face_locations.return_value = []

        employee_id = "emp123"
        image_data = b"fake_image_data"

        success = self.face_service.register_employee_face(employee_id, image_data)

        assert success is False
        assert employee_id not in self.face_service.known_face_employee_ids

    @patch('app.services.face_recognition_service.face_recognition')
    def test_recognize_faces_in_frame(self, mock_face_recognition):
        """Test face recognition in frame"""
        mock_face_recognition.face_locations.return_value = [(0, 100, 100, 0)]
        mock_face_recognition.face_encodings.return_value = [np.array([1, 2, 3, 4])]
        mock_face_recognition.compare_faces.return_value = [True]
        mock_face_recognition.face_distance.return_value = [0.3]

        self.face_service.known_face_encodings = [np.array([1, 2, 3, 4])]
        self.face_service.known_face_employee_ids = ["emp123"]

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        recognized_faces = self.face_service.recognize_faces_in_frame(frame)

        assert len(recognized_faces) == 1
        assert recognized_faces[0]["employee_id"] == "emp123"
        assert recognized_faces[0]["confidence"] > 0

    def test_remove_employee_face(self):
        """Test removing employee face"""
        employee_id = "emp123"
        self.face_service.known_face_employee_ids = [employee_id]
        self.face_service.known_face_encodings = [np.array([1, 2, 3, 4])]

        success = self.face_service.remove_employee_face(employee_id)

        assert success is True
        assert employee_id not in self.face_service.known_face_employee_ids
        assert len(self.face_service.known_face_encodings) == 0

    def test_remove_nonexistent_employee_face(self):
        """Test removing face for non-existent employee"""
        success = self.face_service.remove_employee_face("nonexistent")
        assert success is False