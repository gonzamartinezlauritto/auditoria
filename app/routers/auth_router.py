from fastapi import APIRouter

from app.schemas.auth_schema import LoginRequest
from app.services.auth_service import login


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login")
def login_usuario(
    data: LoginRequest,
):
    return login(
        usuario=data.usuario,
        password=data.password,
    )