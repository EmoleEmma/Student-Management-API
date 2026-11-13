from fastapi import FastAPI

from app.core.errors import register_error_handlers
from app.routers import auth, courses, lecturers, students, users

app = FastAPI(title="Student Management API", version="0.2.0")
register_error_handlers(app)

for module in (auth, users, students, lecturers, courses):
    app.include_router(module.router)