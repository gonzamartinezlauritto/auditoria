from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.exceptions.security_exceptions import (
    PermisoDenegadoError,
    TokenInvalidoError,
    TokenRequeridoError,
)
from app.security.jwt import decode_access_token
from app.services.auth_service import obtener_usuario_autenticado
from app.schemas.user_schema import CurrentUser


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> CurrentUser:
    if credentials is None:
        raise TokenRequeridoError()

    if credentials.scheme.lower() != "bearer":
        raise TokenInvalidoError(
            "El esquema de autenticación debe ser Bearer"
        )

    payload = decode_access_token(
        credentials.credentials,
    )

    usuario_id = payload.get("user_id")

    if (
        not isinstance(usuario_id, int)
        or isinstance(usuario_id, bool)
    ):
        raise TokenInvalidoError(
            "El token no contiene un usuario válido"
        )

    usuario = obtener_usuario_autenticado(
        usuario_id=usuario_id,
    )

    return CurrentUser(**usuario)


def require_role(
    *roles: str,
) -> Callable[..., CurrentUser]:
    def dependency(
        usuario_actual: Annotated[
            CurrentUser,
            Depends(get_current_user),
        ],
    ) -> CurrentUser:
        if usuario_actual.rol not in roles:
            raise PermisoDenegadoError()

        return usuario_actual

    return dependency