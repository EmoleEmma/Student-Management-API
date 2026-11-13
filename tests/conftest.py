from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.academic import Course
from app.models.user import Lecturer, Role, Student, User

PASSWORD = "Password123"

TEST_URL = settings.test_database_url
assert TEST_URL and TEST_URL.rsplit("/", 1)[-1].endswith("_test"), (
    "Set TEST_DATABASE_URL in .env to a database whose name ends with _test"
)

engine = create_engine(TEST_URL)
SessionForTests = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _override_get_db():
    db = SessionForTests()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


# ---------- data helpers ----------
def make_user(email: str, role: Role = Role.STUDENT) -> int:
    with SessionForTests() as db:
        user = User(email=email, hashed_password=hash_password(PASSWORD), role=role)
        db.add(user)
        db.commit()
        return user.id


def make_student(email: str, matric: str) -> int:
    with SessionForTests() as db:
        user = User(email=email, hashed_password=hash_password(PASSWORD), role=Role.STUDENT)
        student = Student(matric_number=matric, first_name="Test", last_name=matric, user=user)
        db.add(student)
        db.commit()
        return student.id


def make_lecturer(email: str, staff_id: str) -> int:
    with SessionForTests() as db:
        user = User(email=email, hashed_password=hash_password(PASSWORD), role=Role.LECTURER)
        lecturer = Lecturer(staff_id=staff_id, first_name="Dr", last_name=staff_id, user=user)
        db.add(lecturer)
        db.commit()
        return lecturer.id


def make_course(code: str, units: int, lecturer_id: int | None) -> int:
    with SessionForTests() as db:
        course = Course(code=code, title=f"{code} title", credit_units=units, lecturer_id=lecturer_id)
        db.add(course)
        db.commit()
        return course.id


# ---------- fixtures ----------
@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def login(client):
    def _login(email: str) -> dict:
        r = client.post("/auth/login", data={"username": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login


@pytest.fixture
def deactivate():
    def _deactivate(email: str) -> None:
        with SessionForTests() as db:
            db.execute(update(User).where(User.email == email).values(is_active=False))
            db.commit()

    return _deactivate


@pytest.fixture
def world():
    """admin@test.com, lec1/lec2, s1/s2 (all with password Password123), courses c1 (lec1) and c2 (lec2)."""
    make_user("admin@test.com", Role.ADMIN)
    lec1 = make_lecturer("lec1@test.com", "STF001")
    lec2 = make_lecturer("lec2@test.com", "STF002")
    s1 = make_student("s1@test.com", "MAT001")
    s2 = make_student("s2@test.com", "MAT002")
    c1 = make_course("CSC101", 3, lec1)
    c2 = make_course("CSC102", 2, lec2)
    return SimpleNamespace(lec1=lec1, lec2=lec2, s1=s1, s2=s2, c1=c1, c2=c2)