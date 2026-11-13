from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.deps import AdminUser, DbSession
from app.models.user import Lecturer, Role, User
from app.schemas.academic import LecturerCreate, LecturerRead

router = APIRouter(prefix="/lecturers", tags=["lecturers"])


@router.post("", response_model=LecturerRead, status_code=201)
def create_lecturer(payload: LecturerCreate, db: DbSession, _: AdminUser):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.role == Role.ADMIN:
        raise HTTPException(409, "Admin accounts cannot be lecturers")
    if user.student is not None or user.lecturer is not None:
        raise HTTPException(409, "User already has a profile")
    if db.scalar(select(Lecturer).where(Lecturer.staff_id == payload.staff_id)):
        raise HTTPException(409, "Staff ID already exists")
    user.role = Role.LECTURER
    lecturer = Lecturer(**payload.model_dump())
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return lecturer


@router.get("", response_model=list[LecturerRead])
def list_lecturers(
    db: DbSession,
    _: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    stmt = select(Lecturer).order_by(Lecturer.last_name, Lecturer.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()