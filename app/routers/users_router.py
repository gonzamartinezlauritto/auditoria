from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from app.constants.roles import ADMIN

from app.schemas.user_schema import (
    ActualizarUsuarioRequest,
    CambiarEstadoRequest,
    CambiarPasswordRequest,
    CrearUsuarioRequest,
    CurrentUser
)
from app.security.dependencies import (
    get_current_user,
    require_role,
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


@router.get("/me")
def obtener_perfil(
    usuario_actual: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
):
    return {
        "id": usuario_actual.id,
        "username": usuario_actual.username,
        "nombre": usuario_actual.nombre,
        "email": usuario_actual.email,
        "rol": usuario_actual.rol,
        "activo": usuario_actual.activo,
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def crear(
    data: CrearUsuarioRequest,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return crear_usuario(
        username=data.username,
        nombre=data.nombre,
        email=data.email,
        password=data.password,
        rol=data.rol,
    )


@router.get("")
def listar(
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return listar_usuarios()


@router.get("/{usuario_id}")
def obtener(
    usuario_id: int,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return obtener_usuario_por_id(usuario_id)


@router.put("/{usuario_id}")
def actualizar(
    usuario_id: int,
    data: ActualizarUsuarioRequest,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
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
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return cambiar_password(
        usuario_id=usuario_id,
        nueva_password=data.nueva_password,
    )


@router.patch("/{usuario_id}/estado")
def actualizar_estado(
    usuario_id: int,
    data: CambiarEstadoRequest,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return cambiar_estado_usuario(
        usuario_id=usuario_id,
        activo=data.activo,
    )


@router.delete("/{usuario_id}")
def eliminar(
    usuario_id: int,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return eliminar_usuario(usuario_id)