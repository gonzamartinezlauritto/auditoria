from typing import Annotated

from pydantic import (
    BaseModel,
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
    usuario: UsuarioLogin
    password: str = Field(
        min_length=8,
        max_length=128,
    )