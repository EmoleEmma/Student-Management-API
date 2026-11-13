# Database schema

```mermaid
erDiagram
    USERS ||--o| STUDENTS : "has profile"
    USERS ||--o| LECTURERS : "has profile"
    LECTURERS |o--o{ COURSES : teaches
    STUDENTS ||--o{ ENROLLMENTS : registers
    COURSES ||--o{ ENROLLMENTS : has
    ENROLLMENTS ||--o| GRADES : receives

    USERS {
        int id PK
        string email UK
        string hashed_password
        enum role "ADMIN, LECTURER, STUDENT"
        boolean is_active
        datetime created_at
    }
    STUDENTS {
        int id PK
        int user_id FK, UK
        string matric_number UK
        string first_name
        string last_name
        string department
    }
    LECTURERS {
        int id PK
        int user_id FK, UK
        string staff_id UK
        string first_name
        string last_name
    }
    COURSES {
        int id PK
        string code UK
        string title
        int credit_units
        int lecturer_id FK "nullable"
    }
    ENROLLMENTS {
        int id PK
        int student_id FK
        int course_id FK
    }
    GRADES {
        int id PK
        int enrollment_id FK, UK
        decimal score "0 to 100"
    }
```

Key constraints: a student can register for a course only once (`UNIQUE(student_id, course_id)`), an enrollment has at most one grade, and scores are limited to 0-100 by a database check constraint.