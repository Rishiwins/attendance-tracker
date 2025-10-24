import pytest
from fastapi.testclient import TestClient

def test_create_employee(client: TestClient, sample_employee_data):
    response = client.post("/api/v1/employees/", json=sample_employee_data)
    assert response.status_code == 200
    data = response.json()
    assert data["employee_code"] == sample_employee_data["employee_code"]
    assert data["email"] == sample_employee_data["email"]
    assert data["is_active"] is True

def test_create_employee_duplicate_code(client: TestClient, sample_employee_data):
    client.post("/api/v1/employees/", json=sample_employee_data)

    response = client.post("/api/v1/employees/", json=sample_employee_data)
    assert response.status_code == 400
    assert "Employee code already exists" in response.json()["detail"]

def test_create_employee_duplicate_email(client: TestClient, sample_employee_data):
    client.post("/api/v1/employees/", json=sample_employee_data)

    duplicate_email_data = sample_employee_data.copy()
    duplicate_email_data["employee_code"] = "EMP002"

    response = client.post("/api/v1/employees/", json=duplicate_email_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_list_employees(client: TestClient, sample_employee_data):
    client.post("/api/v1/employees/", json=sample_employee_data)

    response = client.get("/api/v1/employees/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["employee_code"] == sample_employee_data["employee_code"]

def test_get_employee_by_id(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    response = client.get(f"/api/v1/employees/{employee_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == employee_id
    assert data["employee_code"] == sample_employee_data["employee_code"]

def test_get_employee_by_code(client: TestClient, sample_employee_data):
    client.post("/api/v1/employees/", json=sample_employee_data)

    response = client.get(f"/api/v1/employees/code/{sample_employee_data['employee_code']}")
    assert response.status_code == 200
    data = response.json()
    assert data["employee_code"] == sample_employee_data["employee_code"]

def test_get_nonexistent_employee(client: TestClient):
    response = client.get("/api/v1/employees/nonexistent")
    assert response.status_code == 404
    assert "Employee not found" in response.json()["detail"]

def test_update_employee(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    update_data = {"first_name": "Jane", "position": "Senior Software Engineer"}
    response = client.put(f"/api/v1/employees/{employee_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["position"] == "Senior Software Engineer"
    assert data["last_name"] == sample_employee_data["last_name"]  # Unchanged

def test_delete_employee(client: TestClient, sample_employee_data):
    create_response = client.post("/api/v1/employees/", json=sample_employee_data)
    employee_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/employees/{employee_id}")
    assert response.status_code == 200
    assert "deactivated successfully" in response.json()["message"]

    get_response = client.get(f"/api/v1/employees/{employee_id}")
    assert get_response.json()["is_active"] is False