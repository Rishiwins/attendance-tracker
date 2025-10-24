import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient

def test_get_daily_attendance_empty(client: TestClient):
    today = date.today()
    response = client.get(f"/api/v1/attendance/daily/{today}")
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == today.isoformat()
    assert data["total_employees"] == 0
    assert data["present_employees"] == 0
    assert data["absent_employees"] == 0

def test_get_attendance_summary(client: TestClient):
    today = date.today()
    response = client.get(f"/api/v1/attendance/summary/{today}")
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "total_employees" in data
    assert "attendance_details" in data

def test_mark_manual_attendance(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    today = date.today()
    check_in_time = "2024-01-01T09:00:00"

    response = client.post(
        f"/api/v1/attendance/manual/{employee_id}",
        params={
            "target_date": today.isoformat(),
            "check_in_time": check_in_time,
            "notes": "Manual entry"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"]

def test_mark_manual_attendance_invalid_employee(client: TestClient):
    today = date.today()
    check_in_time = "2024-01-01T09:00:00"

    response = client.post(
        "/api/v1/attendance/manual/nonexistent",
        params={
            "target_date": today.isoformat(),
            "check_in_time": check_in_time
        }
    )

    assert response.status_code == 404
    assert "Employee not found" in response.json()["detail"]

def test_mark_manual_attendance_no_times(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    today = date.today()

    response = client.post(
        f"/api/v1/attendance/manual/{employee_id}",
        params={"target_date": today.isoformat()}
    )

    assert response.status_code == 400
    assert "At least one of check_in_time or check_out_time must be provided" in response.json()["detail"]

def test_get_employee_attendance_history(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    start_date = "2024-01-01"
    end_date = "2024-01-31"

    response = client.get(
        f"/api/v1/attendance/employee/{employee_id}",
        params={"start_date": start_date, "end_date": end_date}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == employee_id
    assert "attendance_records" in data

def test_get_employee_attendance_history_invalid_dates(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    start_date = "2024-01-31"
    end_date = "2024-01-01"

    response = client.get(
        f"/api/v1/attendance/employee/{employee_id}",
        params={"start_date": start_date, "end_date": end_date}
    )

    assert response.status_code == 400
    assert "End date must be after start date" in response.json()["detail"]

def test_get_weekly_attendance_report(client: TestClient):
    start_date = "2024-01-01"

    response = client.get(
        "/api/v1/attendance/weekly-report",
        params={"start_date": start_date}
    )

    assert response.status_code == 200
    data = response.json()
    assert "start_date" in data
    assert "end_date" in data
    assert "daily_summaries" in data
    assert len(data["daily_summaries"]) == 7

def test_get_monthly_attendance_report(client: TestClient):
    response = client.get(
        "/api/v1/attendance/monthly-report",
        params={"year": 2024, "month": 1}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2024
    assert data["month"] == 1
    assert "monthly_summary" in data

def test_get_monthly_attendance_report_invalid_month(client: TestClient):
    response = client.get(
        "/api/v1/attendance/monthly-report",
        params={"year": 2024, "month": 13}
    )

    assert response.status_code == 400
    assert "Month must be between 1 and 12" in response.json()["detail"]