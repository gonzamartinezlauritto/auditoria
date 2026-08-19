from fastapi import APIRouter

from app.docs.auth_docs import LOGIN_DOCS
from app.schemas.auth_schema import LoginRequest
from app.services.auth_service import login


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    **LOGIN_DOCS,
)
def login_usuario(
    data: LoginRequest,
):
    return login(
        usuario=data.usuario,
        password=data.password,
    )