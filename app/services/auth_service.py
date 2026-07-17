from app.core.transaction import transaction
from app.exceptions.user_exceptions import (
    CredencialesInvalidasError,
    UsuarioInactivoError,
)
from app.repositories import user_repository
from app.security.jwt import create_access_token
from app.security.password import verify_password


def login(usuario: str, password: str):
    usuario_normalizado = usuario.strip()

    with transaction() as conn:
        user = user_repository.find_by_username_or_email(
            conn=conn,
            usuario=usuario_normalizado,
        )

        if not user:
            raise CredencialesInvalidasError()

        if not user["activo"]:
            raise UsuarioInactivoError()

        if not verify_password(
            plain_password=password,
            hashed_password=user["password_hash"],
        ):
            raise CredencialesInvalidasError()

        token = create_access_token({
            "sub": user["username"],
            "user_id": user["id"],
            "rol": user["rol"],
        })

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": user["id"],
            "username": user["username"],
            "nombre": user["nombre"],
            "email": user["email"],
            "rol": user["rol"],
        },
    }