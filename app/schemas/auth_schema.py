from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)