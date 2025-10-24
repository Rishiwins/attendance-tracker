from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

class EmployeeBase(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    position: str
    manager_email: EmailStr

class EmployeeCreate(EmployeeBase):
    face_image: Optional[str] = None  # Base64 encoded image

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    position: Optional[str] = None
    manager_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    id: str
    is_active: bool
    face_image_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AttendanceRecordBase(BaseModel):
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: float = 0.0
    break_duration: float = 0.0
    status: str = "present"
    notes: Optional[str] = None

class AttendanceRecordCreate(AttendanceRecordBase):
    employee_id: str

class AttendanceRecord(AttendanceRecordBase):
    id: str
    employee_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DetectionLogBase(BaseModel):
    employee_id: str
    confidence_score: float
    camera_id: str
    detection_type: str
    image_path: Optional[str] = None

class DetectionLogCreate(DetectionLogBase):
    attendance_record_id: str

class DetectionLog(DetectionLogBase):
    id: str
    attendance_record_id: str
    detection_time: datetime

    class Config:
        from_attributes = True

class CameraBase(BaseModel):
    name: str
    location: str
    url: str

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: str
    is_active: bool
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AttendanceSummary(BaseModel):
    employee_id: str
    employee_name: str
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: float = 0.0
    status: str

class DailyReport(BaseModel):
    date: date
    total_employees: int
    present_employees: int
    absent_employees: int
    late_employees: int
    attendance_records: List[AttendanceSummary]

class FaceRecognitionResult(BaseModel):
    employee_id: str
    confidence: float
    location: dict