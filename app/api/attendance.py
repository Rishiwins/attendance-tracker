from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models import AttendanceRecord, Employee
from app.schemas import AttendanceRecord as AttendanceRecordSchema, AttendanceSummary, DailyReport
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["attendance"])

attendance_service = AttendanceService()

@router.get("/daily/{target_date}", response_model=DailyReport)
def get_daily_attendance(
    target_date: date,
    db: Session = Depends(get_db)
):
    """Get daily attendance report"""
    summary = attendance_service.get_attendance_summary(target_date, db)

    attendance_summaries = []
    for detail in summary['attendance_details']:
        attendance_summaries.append(AttendanceSummary(
            employee_id=detail['employee_id'],
            employee_name=detail['employee_name'],
            date=target_date,
            check_in_time=detail['check_in_time'],
            check_out_time=detail['check_out_time'],
            total_hours=detail['total_hours'],
            status=detail['status']
        ))

    return DailyReport(
        date=target_date,
        total_employees=summary['total_employees'],
        present_employees=summary['present_employees'],
        absent_employees=summary['absent_employees'],
        late_employees=summary['late_employees'],
        attendance_records=attendance_summaries
    )

@router.get("/employee/{employee_id}")
def get_employee_attendance_history(
    employee_id: str,
    start_date: date = Query(..., description="Start date for attendance history"),
    end_date: date = Query(..., description="End date for attendance history"),
    db: Session = Depends(get_db)
):
    """Get attendance history for specific employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    attendance_records = attendance_service.get_employee_attendance_history(
        employee_id, start_date, end_date, db
    )

    return {
        "employee_id": employee_id,
        "employee_name": employee.full_name,
        "start_date": start_date,
        "end_date": end_date,
        "attendance_records": attendance_records
    }

@router.post("/manual/{employee_id}")
def mark_manual_attendance(
    employee_id: str,
    target_date: date,
    check_in_time: Optional[datetime] = None,
    check_out_time: Optional[datetime] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Manually mark attendance for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not check_in_time and not check_out_time:
        raise HTTPException(
            status_code=400,
            detail="At least one of check_in_time or check_out_time must be provided"
        )

    if check_in_time and check_out_time and check_out_time <= check_in_time:
        raise HTTPException(
            status_code=400,
            detail="Check-out time must be after check-in time"
        )

    attendance_record = attendance_service.mark_manual_attendance(
        employee_id=employee_id,
        target_date=target_date,
        check_in_time=check_in_time,
        check_out_time=check_out_time,
        notes=notes,
        db=db
    )

    if not attendance_record:
        raise HTTPException(status_code=400, detail="Failed to mark attendance")

    return {
        "message": "Attendance marked successfully",
        "attendance_record": attendance_record
    }

@router.get("/summary/{target_date}")
def get_attendance_summary(
    target_date: date,
    db: Session = Depends(get_db)
):
    """Get detailed attendance summary for a date"""
    summary = attendance_service.get_attendance_summary(target_date, db)
    return summary

@router.get("/weekly-report")
def get_weekly_attendance_report(
    start_date: date = Query(..., description="Start date of the week"),
    db: Session = Depends(get_db)
):
    """Get weekly attendance report"""
    end_date = start_date + timedelta(days=6)

    weekly_data = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_summary = attendance_service.get_attendance_summary(current_date, db)
        weekly_data.append(daily_summary)

    all_employees = db.query(Employee).filter(Employee.is_active == True).all()

    employee_weekly_summary = {}
    for employee in all_employees:
        employee_data = {
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'department': employee.department,
            'daily_records': [],
            'total_hours': 0.0,
            'total_days_present': 0,
            'total_days_absent': 0,
            'late_days': 0
        }

        for daily_data in weekly_data:
            employee_detail = next(
                (detail for detail in daily_data['attendance_details']
                 if detail['employee_id'] == employee.id),
                None
            )

            if employee_detail:
                employee_data['daily_records'].append(employee_detail)
                if employee_detail['status'] in ['present', 'partial']:
                    employee_data['total_days_present'] += 1
                    employee_data['total_hours'] += employee_detail['total_hours']
                else:
                    employee_data['total_days_absent'] += 1

                if employee_detail['is_late']:
                    employee_data['late_days'] += 1

        employee_weekly_summary[employee.id] = employee_data

    return {
        'start_date': start_date,
        'end_date': end_date,
        'daily_summaries': weekly_data,
        'employee_weekly_summary': employee_weekly_summary
    }

@router.get("/monthly-report")
def get_monthly_attendance_report(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    db: Session = Depends(get_db)
):
    """Get monthly attendance report"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    all_employees = db.query(Employee).filter(Employee.is_active == True).all()

    monthly_summary = {}
    for employee in all_employees:
        attendance_records = attendance_service.get_employee_attendance_history(
            employee.id, start_date, end_date, db
        )

        total_hours = sum(record.total_hours for record in attendance_records)
        present_days = len([r for r in attendance_records if r.status in ['present', 'partial']])
        absent_days = len([r for r in attendance_records if r.status == 'absent'])

        monthly_summary[employee.id] = {
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'department': employee.department,
            'total_working_days': (end_date - start_date).days + 1,
            'present_days': present_days,
            'absent_days': absent_days,
            'total_hours': total_hours,
            'average_hours_per_day': total_hours / max(present_days, 1),
            'attendance_records': attendance_records
        }

    return {
        'year': year,
        'month': month,
        'start_date': start_date,
        'end_date': end_date,
        'monthly_summary': monthly_summary
    }

@router.delete("/{attendance_id}")
def delete_attendance_record(
    attendance_id: str,
    db: Session = Depends(get_db)
):
    """Delete an attendance record"""
    attendance_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.id == attendance_id
    ).first()

    if not attendance_record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(attendance_record)
    db.commit()

    return {"message": "Attendance record deleted successfully"}