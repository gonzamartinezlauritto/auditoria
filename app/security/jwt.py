from datetime import datetime, timedelta, timezone
import os
from typing import Any

from jose import JWTError, jwt

from app.exceptions.security_exceptions import TokenInvalidoError


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "480")
)


if not SECRET_KEY:
    raise RuntimeError(
        "Falta configurar JWT_SECRET_KEY en el archivo .env"
    )


def create_access_token(
    data: dict[str, Any],
) -> str:
    payload = data.copy()

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=EXPIRE_MINUTES,
    )

    payload.update({
        "exp": expiration,
    })

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except JWTError as error:
        raise TokenInvalidoError() from error