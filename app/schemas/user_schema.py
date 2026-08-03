from pydantic import BaseModel, EmailStr, Field


class CrearUsuarioRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    nombre: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: str = "operador"


class ActualizarUsuarioRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    nombre: str = Field(min_length=2, max_length=150)
    email: EmailStr
    rol: str


class CambiarPasswordRequest(BaseModel):
    nueva_password: str = Field(min_length=8, max_length=128)


class CambiarEstadoRequest(BaseModel):
    activo: bool

class CurrentUser(BaseModel):
    id: int
    username: str
    nombre: str
    email: str
    rol: str
    activo: bool