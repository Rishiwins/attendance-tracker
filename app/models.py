from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_code = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, nullable=False)
    position = Column(String, nullable=False)
    manager_email = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    face_image_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    attendance_records = relationship("AttendanceRecord", back_populates="employee")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    total_hours = Column(Float, default=0.0)
    break_duration = Column(Float, default=0.0)
    status = Column(String, default="present")  # present, absent, partial
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates="attendance_records")
    detection_logs = relationship("DetectionLog", back_populates="attendance_record")

class DetectionLog(Base):
    __tablename__ = "detection_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attendance_record_id = Column(String, ForeignKey("attendance_records.id"), nullable=False)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    detection_time = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float, nullable=False)
    camera_id = Column(String, nullable=False)
    detection_type = Column(String, nullable=False)  # check_in, check_out, presence
    image_path = Column(String, nullable=True)

    attendance_record = relationship("AttendanceRecord", back_populates="detection_logs")
    employee = relationship("Employee")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String, nullable=False)  # camera_service, face_recognition, email_service
    employee_id = Column(String, ForeignKey("employees.id"), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee")