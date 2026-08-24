from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
)
from app.exceptions.security_exceptions import (
    TokenInvalidoError,
)


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "Falta configurar JWT_SECRET_KEY en el archivo .env"
    )


def create_access_token(
    data: dict[str, Any],
) -> str:
    payload = data.copy()

    expiration = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=JWT_EXPIRE_MINUTES,
    )

    payload.update({
        "exp": expiration,
    })

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

    except JWTError as error:
        raise TokenInvalidoError() from error