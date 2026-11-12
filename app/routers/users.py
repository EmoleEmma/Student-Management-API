from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, require_roles
from app.models.user import Role, User
from app.schemas.auth import UserRead

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserRead)
def read_me(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.get("/admin/ping")
def admin_ping(user: Annotated[User, Depends(require_roles(Role.ADMIN))]):
    return {"message": f"Hello admin {user.email}"}