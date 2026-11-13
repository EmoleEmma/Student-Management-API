# Student Management API

[![CI](https://github.com/EmoleEmma/Student-Management-API/actions/workflows/ci.yml/badge.svg)](https://github.com/EmoleEmma/Student-Management-API/actions/workflows/ci.yml)

> Establish a strong backend/software-engineering foundation using a realistic academic management system.

## Background

This project is a REST API for managing students, lecturers, courses, course registration, grades and transcripts, with JWT authentication and role-based access control (ADMIN, LECTURER, STUDENT).

It was built as a **production-style learning project**. A university records system was chosen deliberately: the domain is familiar, so the attention goes to engineering fundamentals rather than to understanding the business. It also contains the authorization problems that real systems face, such as a student who must see only their own results, and a lecturer who may grade only the courses assigned to them.

What the project is meant to demonstrate:

- A layered, modular structure (routers, schemas, models, services) that stays testable
- Database design with migrations instead of ad-hoc table creation
- Secure authentication, and authorization at both the role level and the object level
- Input validation and one consistent error format
- Automated unit, integration and API tests, including security tests for role boundaries
- Continuous integration against a real PostgreSQL database

## Features

- Student, lecturer and course management with search and pagination
- Course registration and removal by students
- Grade entry by assigned lecturers, with automatic letter grade and grade points
- Transcripts with credit-weighted GPA on a 5.0 scale
- Registration and login with Argon2 password hashing and JWT access tokens
- Interactive OpenAPI documentation at `/docs`
- Seed data for development

## Tech stack

Python 3.14, FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, pwdlib (Argon2), PyJWT, pytest, GitHub Actions. Docker is planned.

## Architecture

```
app/
  core/        config, security (hashing, JWT), dependencies (auth guards), error handlers
  db/          SQLAlchemy base and session
  models/      ORM models (users, students, lecturers, courses, enrollments, grades)
  schemas/     Pydantic request/response models
  routers/     HTTP endpoints, grouped by resource
  services/    business rules with no HTTP concerns (grading, transcripts, access checks)
  main.py      application entry point
alembic/       database migrations
scripts/       create_admin.py, seed.py
tests/         unit, API and security tests
docs/          ER diagram
```

Routers handle HTTP and call services for business rules. Rules such as the grading scale and GPA calculation live in `services/` so they can be unit-tested without a web request.

## Database

See the full [ER diagram](docs/er-diagram.md).

```mermaid
erDiagram
    USERS ||--o| STUDENTS : "has profile"
    USERS ||--o| LECTURERS : "has profile"
    LECTURERS |o--o{ COURSES : teaches
    STUDENTS ||--o{ ENROLLMENTS : registers
    COURSES ||--o{ ENROLLMENTS : has
    ENROLLMENTS ||--o| GRADES : receives
```

Credentials and role live in `users`. Students and lecturers are one-to-one profile tables, so login data is kept separate from academic data.

## Roles and permissions

| Action | ADMIN | LECTURER | STUDENT |
|---|:---:|:---:|:---:|
| Register / log in | yes | yes | yes |
| Create, update, delete students and courses | yes | no | no |
| Create lecturer profiles, assign lecturers to courses | yes | no | no |
| List courses and view a course | yes | yes | yes |
| List students | all | only students in own courses | no |
| View a student | any | only students in own courses | only self |
| View a course roster | any | own courses only | no |
| Enter or change grades | any course | own courses only | no |
| Register for / drop a course | no | no | yes (self) |
| View a transcript | any | no | only self |

## Business rules and assumptions

- **Grading scale (5.0):** 70-100 = A (5), 60-69 = B (4), 50-59 = C (3), 45-49 = D (2), 40-44 = E (1), 0-39 = F (0).
- **GPA:** sum of (credit units x grade points) divided by total credit units, counting graded courses only, rounded half-up to 2 decimals. A student with no graded courses has a GPA of `null`.
- **Registration:** a student cannot register for the same course twice, and cannot drop a course once it has a grade.
- **Grades:** one grade per registration. Entering a grade again overwrites the previous one.
- **Accounts:** anyone can self-register, and always as STUDENT. An admin then attaches a student profile, or creates a lecturer profile (which promotes the account to LECTURER). The first ADMIN is created with `scripts/create_admin.py`, and no endpoint can create admins.
- **Deleting:** a course with registered students cannot be deleted. Deleting a student removes their profile and registrations but keeps their login account.

## Getting started

### Prerequisites

Python 3.14 (3.12+ should work) and PostgreSQL 16 or newer.

### Setup

```bash
git clone https://github.com/EmoleEmma/Student-Management-API.git
cd Student-Management-API

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create the databases (one for development, one for tests):

```sql
CREATE DATABASE student_api;
CREATE DATABASE student_api_test;
```

Copy `.env.example` to `.env` and fill it in (see the table below), then:

```bash
alembic upgrade head              # create the tables
python scripts/seed.py            # optional: demo data
python scripts/create_admin.py    # optional: create your own admin
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API documentation.

### Environment variables

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `DATABASE_URL` | yes | | e.g. `postgresql+psycopg://user:password@localhost:5432/student_api` |
| `SECRET_KEY` | yes | | Signs JWTs. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | Access token lifetime |
| `ALGORITHM` | no | `HS256` | JWT signing algorithm |
| `ENVIRONMENT` | no | `development` | Set to `production` to make `seed.py` refuse to run |
| `TEST_DATABASE_URL` | for tests | | Database used by pytest. The name must end in `_test` |

### Demo accounts (after `python scripts/seed.py`)

All use the password `Password123`. These are for local development only.

| Role | Email |
|---|---|
| ADMIN | `admin@school.test` |
| LECTURER | `lecturer1@school.test`, `lecturer2@school.test` |
| STUDENT | `student1@school.test` to `student5@school.test` |

## API overview

Full details and a try-it-out interface are at `/docs`. Protected endpoints expect `Authorization: Bearer <token>`.

| Resource | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login` |
| Users | `GET /users/me` |
| Students | `POST /students`, `GET /students?q=`, `GET /students/me`, `GET /students/me/transcript`, `GET /students/{id}`, `GET /students/{id}/transcript`, `PATCH /students/{id}`, `DELETE /students/{id}` |
| Lecturers | `POST /lecturers`, `GET /lecturers` |
| Courses | `POST /courses`, `GET /courses?q=`, `GET /courses/mine`, `GET /courses/{id}`, `PATCH /courses/{id}`, `DELETE /courses/{id}`, `GET /courses/{id}/students` |
| Registration | `POST /courses/{id}/register`, `DELETE /courses/{id}/register` |
| Grades | `PUT /courses/{id}/students/{student_id}/grade` |

Example (bash):

```bash
# log in (form-encoded) and keep the token
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1@school.test&password=Password123"

# read your transcript
curl http://127.0.0.1:8000/students/me/transcript \
  -H "Authorization: Bearer <access_token>"
```

### Error format

Every error uses the same shape:

```json
{ "error": { "code": "not_found", "message": "Course not found" } }
```

Validation errors (`422`) add a `details` list naming each invalid field. Internal errors return a generic `500` message and never expose stack traces or SQL.

## Testing

```bash
python -m pytest -v
```

The tests run against the database in `TEST_DATABASE_URL`, and refuse to start unless its name ends in `_test`. The suite covers unit tests for grading rules, API tests for each workflow, and security tests for role boundaries: unauthenticated access (401), wrong role (403), ownership checks (a student viewing another student, a lecturer grading another lecturer's course), and deactivated accounts.

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) starts a PostgreSQL container, applies the migrations, checks that the migrations match the models, and runs the full test suite on every push and pull request.

## Security notes

- Passwords are hashed with Argon2 and never stored or returned in plain text.
- Response schemas are separate from database models, so password hashes cannot be serialized.
- A user's role is read from the database on every request, not trusted from the token, so changes take effect immediately.
- Authorization is enforced at the role level and the object level.
- Login returns the same error for an unknown email and a wrong password.
- All database access goes through the ORM with bound parameters.
- Unhandled errors log only the exception type, because database error text can contain sensitive values.

## Known limitations and roadmap

Not implemented yet: Docker setup, refresh tokens, password reset and email verification, rate limiting, admin-managed registration for students, pagination metadata (total counts), and an audit log. The demo password and seed script are for development only.

## Engineering decisions

- **Separate profile tables** keep credentials apart from academic data and make object-level checks simple.
- **Alembic from the start** instead of `create_all`, so schema changes are versioned and reviewable.
- **Tests run on PostgreSQL**, not SQLite, so behavior matches production.
- **403 for access to another user's record** (rather than 404) keeps the behavior explicit and easy to test.

## License

MIT. Add a `LICENSE` file to the repository to make this official.