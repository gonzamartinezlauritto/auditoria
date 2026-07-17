from fastapi import APIRouter, status

from app.schemas.user_schema import (
    ActualizarUsuarioRequest,
    CambiarEstadoRequest,
    CambiarPasswordRequest,
    CrearUsuarioRequest,
)
from app.services.user_service import (
    actualizar_usuario,
    cambiar_estado_usuario,
    cambiar_password,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    obtener_usuario_por_id,
)


router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def crear(data: CrearUsuarioRequest):
    return crear_usuario(
        username=data.username,
        nombre=data.nombre,
        email=data.email,
        password=data.password,
        rol=data.rol,
    )


@router.get("")
def listar():
    return listar_usuarios()


@router.get("/{usuario_id}")
def obtener(usuario_id: int):
    return obtener_usuario_por_id(usuario_id)


@router.put("/{usuario_id}")
def actualizar(
    usuario_id: int,
    data: ActualizarUsuarioRequest,
):
    return actualizar_usuario(
        usuario_id=usuario_id,
        username=data.username,
        nombre=data.nombre,
        email=data.email,
        rol=data.rol,
    )


@router.patch("/{usuario_id}/password")
def actualizar_password(
    usuario_id: int,
    data: CambiarPasswordRequest,
):
    return cambiar_password(
        usuario_id=usuario_id,
        nueva_password=data.nueva_password,
    )


@router.patch("/{usuario_id}/estado")
def actualizar_estado(
    usuario_id: int,
    data: CambiarEstadoRequest,
):
    return cambiar_estado_usuario(
        usuario_id=usuario_id,
        activo=data.activo,
    )


@router.delete("/{usuario_id}")
def eliminar(usuario_id: int):
    return eliminar_usuario(usuario_id)