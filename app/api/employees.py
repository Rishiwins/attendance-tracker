from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
from io import BytesIO

from app.database import get_db
from app.models import Employee
from app.schemas import Employee as EmployeeSchema, EmployeeCreate, EmployeeUpdate
try:
    from app.services.face_recognition_service import FaceRecognitionService
except ImportError:
    from app.services.face_recognition_service_lite import FaceRecognitionService

router = APIRouter(prefix="/employees", tags=["employees"])

face_service = FaceRecognitionService()

@router.post("/", response_model=EmployeeSchema)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """Create a new employee"""
    db_employee = db.query(Employee).filter(
        Employee.employee_code == employee.employee_code
    ).first()
    if db_employee:
        raise HTTPException(status_code=400, detail="Employee code already exists")

    db_employee = db.query(Employee).filter(Employee.email == employee.email).first()
    if db_employee:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_employee = Employee(**employee.dict(exclude={'face_image'}))
    db.add(db_employee)
    db.flush()

    if employee.face_image:
        try:
            image_data = base64.b64decode(employee.face_image)
            success = face_service.register_employee_face(db_employee.id, image_data)
            if not success:
                db.rollback()
                raise HTTPException(status_code=400, detail="Failed to register face")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Invalid face image: {str(e)}")

    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/", response_model=List[EmployeeSchema])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all employees"""
    query = db.query(Employee)
    if active_only:
        query = query.filter(Employee.is_active == True)

    employees = query.offset(skip).limit(limit).all()
    return employees

@router.get("/{employee_id}", response_model=EmployeeSchema)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    """Get employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.get("/code/{employee_code}", response_model=EmployeeSchema)
def get_employee_by_code(employee_code: str, db: Session = Depends(get_db)):
    """Get employee by employee code"""
    employee = db.query(Employee).filter(
        Employee.employee_code == employee_code
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.put("/{employee_id}", response_model=EmployeeSchema)
def update_employee(
    employee_id: str,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update employee information"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_update.dict(exclude_unset=True)

    if 'email' in update_data:
        existing_employee = db.query(Employee).filter(
            Employee.email == update_data['email'],
            Employee.id != employee_id
        ).first()
        if existing_employee:
            raise HTTPException(status_code=400, detail="Email already in use")

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee

@router.delete("/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    """Delete employee (soft delete)"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.is_active = False
    face_service.remove_employee_face(employee_id)

    db.commit()
    return {"message": "Employee deactivated successfully"}

@router.post("/{employee_id}/face-image")
def upload_face_image(
    employee_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload or update employee face image"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_data = file.file.read()
        success = face_service.register_employee_face(employee_id, image_data)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to process face image")

        return {"message": "Face image uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@router.post("/{employee_id}/face-image-base64")
def upload_face_image_base64(
    employee_id: str,
    face_image: dict,
    db: Session = Depends(get_db)
):
    """Upload face image as base64"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        image_data = base64.b64decode(face_image['image'])
        success = face_service.register_employee_face(employee_id, image_data)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to process face image")

        return {"message": "Face image uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@router.get("/{employee_id}/face-registered")
def check_face_registered(employee_id: str, db: Session = Depends(get_db)):
    """Check if employee has face registered"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    registered_employees = face_service.get_registered_employees()
    is_registered = employee_id in registered_employees

    return {
        "employee_id": employee_id,
        "face_registered": is_registered
    }