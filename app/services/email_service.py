import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import date, datetime
from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

        template_dir = Path(__file__).parent.parent / "templates"
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            return None

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email with optional attachments"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())

                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)

            server = self._create_smtp_connection()
            if not server:
                return False

            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_daily_attendance_report(
        self,
        manager_email: str,
        attendance_summary: Dict,
        report_date: date
    ) -> bool:
        """Send daily attendance report to manager"""
        try:
            template = self.jinja_env.get_template('daily_attendance_report.html')

            html_content = template.render(
                attendance_summary=attendance_summary,
                report_date=report_date,
                company_name="Your Company"
            )

            subject = f"Daily Attendance Report - {report_date.strftime('%B %d, %Y')}"

            return self.send_email(
                to_emails=[manager_email],
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Failed to send daily attendance report: {e}")
            return False

    def send_eod_summary_to_managers(self, attendance_data: List[Dict]) -> bool:
        """Send EOD summary to all managers"""
        try:
            manager_groups = {}

            for employee_data in attendance_data:
                manager_email = employee_data.get('manager_email')
                if manager_email:
                    if manager_email not in manager_groups:
                        manager_groups[manager_email] = []
                    manager_groups[manager_email].append(employee_data)

            success_count = 0
            for manager_email, employees in manager_groups.items():
                if self.send_manager_eod_report(manager_email, employees):
                    success_count += 1

            logger.info(f"Sent EOD reports to {success_count}/{len(manager_groups)} managers")
            return success_count == len(manager_groups)

        except Exception as e:
            logger.error(f"Failed to send EOD summaries: {e}")
            return False

    def send_manager_eod_report(
        self,
        manager_email: str,
        employee_attendance: List[Dict]
    ) -> bool:
        """Send EOD report to a specific manager"""
        try:
            template = self.jinja_env.get_template('manager_eod_report.html')

            today = date.today()
            present_employees = [emp for emp in employee_attendance if emp['status'] in ['present', 'partial']]
            absent_employees = [emp for emp in employee_attendance if emp['status'] == 'absent']
            late_employees = [emp for emp in employee_attendance if emp.get('is_late', False)]

            html_content = template.render(
                manager_email=manager_email,
                report_date=today,
                total_employees=len(employee_attendance),
                present_count=len(present_employees),
                absent_count=len(absent_employees),
                late_count=len(late_employees),
                employee_attendance=employee_attendance,
                present_employees=present_employees,
                absent_employees=absent_employees,
                late_employees=late_employees,
                company_name="Your Company"
            )

            subject = f"End of Day Attendance Report - {today.strftime('%B %d, %Y')}"

            return self.send_email(
                to_emails=[manager_email],
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Failed to send manager EOD report to {manager_email}: {e}")
            return False

    def send_employee_attendance_alert(
        self,
        employee_email: str,
        employee_name: str,
        alert_type: str,
        details: Dict
    ) -> bool:
        """Send attendance alert to employee"""
        try:
            template = self.jinja_env.get_template('employee_attendance_alert.html')

            html_content = template.render(
                employee_name=employee_name,
                alert_type=alert_type,
                details=details,
                company_name="Your Company"
            )

            subject_map = {
                'late_arrival': 'Late Arrival Alert',
                'early_departure': 'Early Departure Alert',
                'missing_checkout': 'Missing Check-out Alert',
                'insufficient_hours': 'Insufficient Working Hours Alert'
            }

            subject = subject_map.get(alert_type, 'Attendance Alert')

            return self.send_email(
                to_emails=[employee_email],
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Failed to send attendance alert to {employee_email}: {e}")
            return False

    def send_system_alert(
        self,
        admin_emails: List[str],
        alert_type: str,
        message: str,
        details: Optional[Dict] = None
    ) -> bool:
        """Send system alert to administrators"""
        try:
            template = self.jinja_env.get_template('system_alert.html')

            html_content = template.render(
                alert_type=alert_type,
                message=message,
                details=details or {},
                timestamp=datetime.now(),
                company_name="Your Company"
            )

            subject = f"System Alert: {alert_type}"

            return self.send_email(
                to_emails=admin_emails,
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
            return False