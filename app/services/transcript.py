from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.academic import Enrollment
from app.models.user import Student
from app.schemas.academic import StudentRead, Transcript, TranscriptRow
from app.services.grading import calculate_gpa, score_to_grade


def build_transcript(db: Session, student: Student) -> Transcript:
    enrollments = db.scalars(
        select(Enrollment)
        .where(Enrollment.student_id == student.id)
        .options(selectinload(Enrollment.course), selectinload(Enrollment.grade))
    ).all()

    rows: list[TranscriptRow] = []
    graded: list[tuple[int, int]] = []
    for e in sorted(enrollments, key=lambda e: e.course.code):
        if e.grade is None:
            rows.append(TranscriptRow(
                course_code=e.course.code, title=e.course.title,
                credit_units=e.course.credit_units, score=None, grade=None, points=None,
            ))
            continue
        letter, points = score_to_grade(e.grade.score)
        rows.append(TranscriptRow(
            course_code=e.course.code, title=e.course.title,
            credit_units=e.course.credit_units, score=e.grade.score, grade=letter, points=points,
        ))
        graded.append((e.course.credit_units, points))

    return Transcript(
        student=StudentRead.model_validate(student),
        courses=rows,
        graded_units=sum(units for units, _ in graded),
        gpa=calculate_gpa(graded),
    )