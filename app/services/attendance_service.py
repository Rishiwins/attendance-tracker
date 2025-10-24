from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import Employee, AttendanceRecord, DetectionLog
from app.schemas import AttendanceRecordCreate, DetectionLogCreate
from app.database import get_db

logger = logging.getLogger(__name__)

class AttendanceService:
    def __init__(self):
        self.office_start_time = time(9, 0)  # 9:00 AM
        self.office_end_time = time(18, 0)   # 6:00 PM
        self.late_threshold_minutes = 15     # Late if check-in after 9:15 AM
        self.minimum_hours = 8.0             # Minimum working hours
        self.break_time_threshold = 30       # Minutes away considered as break

    def process_face_detection(self, detection_data: Dict, db: Session) -> Optional[DetectionLog]:
        """Process face detection and update attendance"""
        try:
            camera_id = detection_data['camera_id']
            timestamp = detection_data['timestamp']
            faces = detection_data['faces']

            for face in faces:
                employee_id = face['employee_id']
                confidence = face['confidence']

                if employee_id == "Unknown" or confidence < 0.7:
                    continue

                employee = db.query(Employee).filter(Employee.id == employee_id).first()
                if not employee or not employee.is_active:
                    continue

                attendance_record = self._get_or_create_attendance_record(
                    employee_id, timestamp.date(), db
                )

                detection_type = self._determine_detection_type(
                    attendance_record, timestamp
                )

                detection_log = DetectionLog(
                    attendance_record_id=attendance_record.id,
                    employee_id=employee_id,
                    detection_time=timestamp,
                    confidence_score=confidence,
                    camera_id=camera_id,
                    detection_type=detection_type
                )

                db.add(detection_log)

                self._update_attendance_record(
                    attendance_record, detection_log, timestamp, db
                )

                db.commit()

                logger.info(f"Processed detection for employee {employee_id}: {detection_type}")
                return detection_log

        except Exception as e:
            logger.error(f"Error processing face detection: {e}")
            db.rollback()
            return None

    def _get_or_create_attendance_record(
        self, employee_id: str, record_date: date, db: Session
    ) -> AttendanceRecord:
        """Get existing or create new attendance record for employee and date"""
        attendance_record = db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date == record_date
            )
        ).first()

        if not attendance_record:
            attendance_record = AttendanceRecord(
                employee_id=employee_id,
                date=record_date,
                status="absent"
            )
            db.add(attendance_record)
            db.flush()

        return attendance_record

    def _determine_detection_type(
        self, attendance_record: AttendanceRecord, timestamp: datetime
    ) -> str:
        """Determine if this is check-in, check-out, or presence detection"""
        if not attendance_record.check_in_time:
            return "check_in"

        if attendance_record.check_out_time:
            last_detection_time = max(
                attendance_record.check_in_time,
                attendance_record.check_out_time
            )
        else:
            last_detection_time = attendance_record.check_in_time

        time_since_last = (timestamp - last_detection_time).total_seconds() / 60

        if time_since_last > self.break_time_threshold:
            if not attendance_record.check_out_time:
                return "check_out"
            else:
                return "check_in"  # Return from break

        return "presence"

    def _update_attendance_record(
        self,
        attendance_record: AttendanceRecord,
        detection_log: DetectionLog,
        timestamp: datetime,
        db: Session
    ):
        """Update attendance record based on detection"""
        if detection_log.detection_type == "check_in":
            if not attendance_record.check_in_time:
                attendance_record.check_in_time = timestamp
                attendance_record.status = "present"
            else:
                attendance_record.check_in_time = timestamp

        elif detection_log.detection_type == "check_out":
            attendance_record.check_out_time = timestamp

        self._calculate_working_hours(attendance_record, db)

    def _calculate_working_hours(self, attendance_record: AttendanceRecord, db: Session):
        """Calculate total working hours and breaks"""
        if not attendance_record.check_in_time:
            return

        if attendance_record.check_out_time:
            total_time = attendance_record.check_out_time - attendance_record.check_in_time
            total_hours = total_time.total_seconds() / 3600

            break_duration = self._calculate_break_duration(attendance_record, db)

            attendance_record.total_hours = max(0, total_hours - break_duration)
            attendance_record.break_duration = break_duration

            if attendance_record.total_hours >= self.minimum_hours:
                attendance_record.status = "present"
            else:
                attendance_record.status = "partial"
        else:
            now = datetime.utcnow()
            if now.date() == attendance_record.date:
                working_time = now - attendance_record.check_in_time
                attendance_record.total_hours = working_time.total_seconds() / 3600

    def _calculate_break_duration(
        self, attendance_record: AttendanceRecord, db: Session
    ) -> float:
        """Calculate total break duration based on detection gaps"""
        detection_logs = db.query(DetectionLog).filter(
            DetectionLog.attendance_record_id == attendance_record.id
        ).order_by(DetectionLog.detection_time).all()

        if len(detection_logs) < 2:
            return 0.0

        total_break_time = 0.0
        last_detection_time = detection_logs[0].detection_time

        for detection_log in detection_logs[1:]:
            gap_minutes = (detection_log.detection_time - last_detection_time).total_seconds() / 60

            if gap_minutes > self.break_time_threshold:
                total_break_time += (gap_minutes - self.break_time_threshold) / 60

            last_detection_time = detection_log.detection_time

        return total_break_time

    def get_daily_attendance(self, target_date: date, db: Session) -> List[AttendanceRecord]:
        """Get attendance records for a specific date"""
        return db.query(AttendanceRecord).filter(
            AttendanceRecord.date == target_date
        ).all()

    def get_employee_attendance_history(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
        db: Session
    ) -> List[AttendanceRecord]:
        """Get attendance history for an employee"""
        return db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            )
        ).order_by(AttendanceRecord.date).all()

    def get_attendance_summary(self, target_date: date, db: Session) -> Dict:
        """Get attendance summary for a date"""
        all_employees = db.query(Employee).filter(Employee.is_active == True).all()
        attendance_records = self.get_daily_attendance(target_date, db)

        attendance_dict = {record.employee_id: record for record in attendance_records}

        present_count = 0
        absent_count = 0
        late_count = 0
        partial_count = 0

        attendance_details = []

        for employee in all_employees:
            attendance_record = attendance_dict.get(employee.id)

            if attendance_record:
                status = attendance_record.status
                check_in_time = attendance_record.check_in_time
                is_late = (
                    check_in_time and
                    check_in_time.time() > time(
                        self.office_start_time.hour,
                        self.office_start_time.minute + self.late_threshold_minutes
                    )
                )

                if status == "present":
                    present_count += 1
                    if is_late:
                        late_count += 1
                elif status == "partial":
                    partial_count += 1
                    if is_late:
                        late_count += 1
                else:
                    absent_count += 1

                attendance_details.append({
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'employee_code': employee.employee_code,
                    'department': employee.department,
                    'check_in_time': check_in_time,
                    'check_out_time': attendance_record.check_out_time,
                    'total_hours': attendance_record.total_hours,
                    'status': status,
                    'is_late': is_late
                })
            else:
                absent_count += 1
                attendance_details.append({
                    'employee_id': employee.id,
                    'employee_name': employee.full_name,
                    'employee_code': employee.employee_code,
                    'department': employee.department,
                    'check_in_time': None,
                    'check_out_time': None,
                    'total_hours': 0.0,
                    'status': 'absent',
                    'is_late': False
                })

        return {
            'date': target_date,
            'total_employees': len(all_employees),
            'present_employees': present_count,
            'absent_employees': absent_count,
            'partial_employees': partial_count,
            'late_employees': late_count,
            'attendance_details': attendance_details
        }

    def mark_manual_attendance(
        self,
        employee_id: str,
        target_date: date,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Optional[AttendanceRecord]:
        """Manually mark attendance for an employee"""
        try:
            attendance_record = self._get_or_create_attendance_record(
                employee_id, target_date, db
            )

            if check_in_time:
                attendance_record.check_in_time = check_in_time
            if check_out_time:
                attendance_record.check_out_time = check_out_time
            if notes:
                attendance_record.notes = notes

            self._calculate_working_hours(attendance_record, db)
            db.commit()

            logger.info(f"Manual attendance marked for employee {employee_id} on {target_date}")
            return attendance_record

        except Exception as e:
            logger.error(f"Error marking manual attendance: {e}")
            db.rollback()
            return None