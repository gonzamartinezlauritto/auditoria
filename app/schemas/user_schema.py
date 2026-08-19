from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class CrearUsuarioRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "operador1",
                "nombre": "Operador Prueba",
                "email": "operador1@ejemplo.com",
                "password": "Password123",
                "rol": "operador",
            }
        }
    )

    username: str = Field(
        min_length=3,
        max_length=100,
        description="Nombre de usuario único.",
        examples=["operador1"],
    )

    nombre: str = Field(
        min_length=2,
        max_length=150,
        description="Nombre completo del usuario.",
        examples=["Operador Prueba"],
    )

    email: EmailStr = Field(
        description="Correo electrónico del usuario.",
        examples=["operador1@ejemplo.com"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        description="Contraseña inicial del usuario.",
        examples=["Password123"],
    )

    rol: str = Field(
        default="operador",
        description=(
            "Rol asignado al usuario. "
            "Ejemplos: admin, operador o consulta."
        ),
        examples=["operador"],
    )


class ActualizarUsuarioRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
        description="Nombre de usuario.",
        examples=["operador1"],
    )

    nombre: str = Field(
        min_length=2,
        max_length=150,
        description="Nombre completo.",
        examples=["Operador Actualizado"],
    )

    email: EmailStr = Field(
        description="Correo electrónico.",
        examples=["operador1@ejemplo.com"],
    )

    rol: str = Field(
        description="Rol asignado.",
        examples=["operador"],
    )


class CambiarPasswordRequest(BaseModel):
    nueva_password: str = Field(
        min_length=8,
        max_length=128,
        description="Nueva contraseña del usuario.",
        examples=["NuevaPassword123"],
    )


class CambiarEstadoRequest(BaseModel):
    activo: bool = Field(
        description=(
            "Estado del usuario. "
            "true = activo, false = inactivo."
        ),
        examples=[True],
    )


class CurrentUser(BaseModel):
    id: int
    username: str
    nombre: str
    email: str
    rol: str
    activo: bool