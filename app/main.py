from fastapi import FastAPI

from app.routers import auth, users

app = FastAPI(title="Student Management API", version="0.1.0")
app.include_router(auth.router)
app.include_router(users.router)