from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- students ----
class StudentCreate(BaseModel):
    user_id: int
    matric_number: str = Field(min_length=3, max_length=30)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    department: str | None = Field(default=None, max_length=100)


class StudentUpdate(BaseModel):
    matric_number: str | None = Field(default=None, min_length=3, max_length=30)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    department: str | None = Field(default=None, max_length=100)


class StudentRead(ORMModel):
    id: int
    user_id: int
    matric_number: str
    first_name: str
    last_name: str
    department: str | None


# ---- lecturers ----
class LecturerCreate(BaseModel):
    user_id: int
    staff_id: str = Field(min_length=2, max_length=30)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class LecturerRead(ORMModel):
    id: int
    user_id: int
    staff_id: str
    first_name: str
    last_name: str


# ---- courses ----
class CourseCreate(BaseModel):
    code: str = Field(min_length=3, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    credit_units: int = Field(gt=0, le=10)
    lecturer_id: int | None = None

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    credit_units: int | None = Field(default=None, gt=0, le=10)
    lecturer_id: int | None = None


class CourseRead(ORMModel):
    id: int
    code: str
    title: str
    credit_units: int
    lecturer_id: int | None


# ---- registration and grades ----
class EnrollmentRead(ORMModel):
    id: int
    student_id: int
    course_id: int


class GradeIn(BaseModel):
    score: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class GradeRead(BaseModel):
    student_id: int
    course_id: int
    score: Decimal
    grade: str
    points: int


# ---- transcript ----
class TranscriptRow(BaseModel):
    course_code: str
    title: str
    credit_units: int
    score: Decimal | None
    grade: str | None
    points: int | None


class Transcript(BaseModel):
    student: StudentRead
    courses: list[TranscriptRow]
    graded_units: int
    gpa: Decimal | None