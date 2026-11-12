from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import Lecturer, Student  # noqa: F401


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    credit_units: Mapped[int] = mapped_column()
    lecturer_id: Mapped[int | None] = mapped_column(ForeignKey("lecturers.id", ondelete="SET NULL"))

    lecturer: Mapped["Lecturer | None"] = relationship(back_populates="courses")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))

    student: Mapped[Student] = relationship(back_populates="enrollments")
    course: Mapped[Course] = relationship(back_populates="enrollments")
    grade: Mapped["Grade | None"] = relationship(back_populates="enrollment", uselist=False)


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (CheckConstraint("score >= 0 AND score <= 100", name="ck_score_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), unique=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    enrollment: Mapped[Enrollment] = relationship(back_populates="grade")