from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)


UsuarioLogin = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=150,
    ),
]


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario": "operador1",
                "password": "Password123",
            }
        }
    )

    usuario: UsuarioLogin = Field(
        description=(
            "Nombre de usuario o email registrado "
            "en el sistema."
        ),
        examples=["operador1"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        description="Contraseña del usuario.",
        examples=["Password123"],
    )