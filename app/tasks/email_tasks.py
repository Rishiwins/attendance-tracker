from celery import current_task
from datetime import date, datetime
import logging

from app.tasks.celery_app import celery_app
from app.services.email_service import EmailService
from app.services.attendance_service import AttendanceService
from app.database import SessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def send_daily_eod_reports(self):
    """Send end-of-day reports to all managers"""
    try:
        db = SessionLocal()
        email_service = EmailService()
        attendance_service = AttendanceService()

        today = date.today()
        attendance_summary = attendance_service.get_attendance_summary(today, db)

        success = email_service.send_eod_summary_to_managers(
            attendance_summary['attendance_details']
        )

        db.close()

        if success:
            logger.info("EOD reports sent successfully")
            return {"status": "success", "message": "EOD reports sent successfully"}
        else:
            logger.error("Failed to send some EOD reports")
            return {"status": "partial", "message": "Some EOD reports failed to send"}

    except Exception as e:
        logger.error(f"Error sending EOD reports: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True)
def send_attendance_alert(self, employee_email: str, employee_name: str, alert_type: str, details: dict):
    """Send attendance alert to employee"""
    try:
        email_service = EmailService()

        success = email_service.send_employee_attendance_alert(
            employee_email=employee_email,
            employee_name=employee_name,
            alert_type=alert_type,
            details=details
        )

        if success:
            logger.info(f"Attendance alert sent to {employee_email}")
            return {"status": "success", "message": "Alert sent successfully"}
        else:
            logger.error(f"Failed to send attendance alert to {employee_email}")
            return {"status": "error", "message": "Failed to send alert"}

    except Exception as e:
        logger.error(f"Error sending attendance alert: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True)
def send_daily_report_to_admin(self, target_date: str):
    """Send daily attendance report to admin"""
    try:
        db = SessionLocal()
        email_service = EmailService()
        attendance_service = AttendanceService()

        report_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        attendance_summary = attendance_service.get_attendance_summary(report_date, db)

        success = email_service.send_daily_attendance_report(
            manager_email="admin@company.com",  # This should come from settings
            attendance_summary=attendance_summary,
            report_date=report_date
        )

        db.close()

        if success:
            logger.info(f"Daily report sent for {target_date}")
            return {"status": "success", "message": "Daily report sent successfully"}
        else:
            logger.error(f"Failed to send daily report for {target_date}")
            return {"status": "error", "message": "Failed to send daily report"}

    except Exception as e:
        logger.error(f"Error sending daily report: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True)
def send_system_alert(self, alert_type: str, message: str, details: dict = None):
    """Send system alert to administrators"""
    try:
        email_service = EmailService()

        admin_emails = ["admin@company.com"]  # This should come from settings

        success = email_service.send_system_alert(
            admin_emails=admin_emails,
            alert_type=alert_type,
            message=message,
            details=details
        )

        if success:
            logger.info(f"System alert sent: {alert_type}")
            return {"status": "success", "message": "System alert sent successfully"}
        else:
            logger.error(f"Failed to send system alert: {alert_type}")
            return {"status": "error", "message": "Failed to send system alert"}

    except Exception as e:
        logger.error(f"Error sending system alert: {e}")
        return {"status": "error", "message": str(e)}