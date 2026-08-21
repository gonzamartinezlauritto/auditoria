from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    status,
)

from app.constants.roles import ADMIN

from app.docs.users_docs import (
    ACTUALIZAR_USUARIO_DOCS,
    CAMBIAR_ESTADO_DOCS,
    CAMBIAR_PASSWORD_DOCS,
    CREAR_USUARIO_DOCS,
    EDITAR_USUARIO_PARCIAL_DOCS,
    ELIMINAR_USUARIO_DOCS,
    LISTAR_USUARIOS_DOCS,
    ME_DOCS,
    OBTENER_USUARIO_DOCS,
)

from app.schemas.user_schema import (
    ActualizarUsuarioRequest,
    CambiarEstadoRequest,
    CambiarPasswordRequest,
    CrearUsuarioRequest,
    CurrentUser,
    EditarUsuarioRequest,
    MensajeResponse,
    UsuarioResponse,
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
    editar_usuario_parcial,
    eliminar_usuario,
    listar_usuarios,
    obtener_usuario_por_id,
)


router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
)


# =========================================================
# PERFIL
# =========================================================

@router.get(
    "/me",
    response_model=UsuarioResponse,
    **ME_DOCS,
)
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


# =========================================================
# CREAR
# =========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UsuarioResponse,
    **CREAR_USUARIO_DOCS,
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


# =========================================================
# LISTAR
# =========================================================

@router.get(
    "",
    response_model=list[UsuarioResponse],
    **LISTAR_USUARIOS_DOCS,
)
def listar(
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return listar_usuarios()


# =========================================================
# OBTENER POR ID
# =========================================================

@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    **OBTENER_USUARIO_DOCS,
)
def obtener(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID del usuario.",
            examples=[2],
        ),
    ],
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return obtener_usuario_por_id(
        usuario_id,
    )


# =========================================================
# ACTUALIZACIÓN COMPLETA
# =========================================================

@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    **ACTUALIZAR_USUARIO_DOCS,
)
def actualizar(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID del usuario a actualizar.",
            examples=[2],
        ),
    ],
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


# =========================================================
# ACTUALIZACIÓN PARCIAL
# =========================================================

@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    **EDITAR_USUARIO_PARCIAL_DOCS,
)
def editar_parcial(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description=(
                "ID del usuario que se desea modificar."
            ),
            examples=[5],
        ),
    ],
    data: EditarUsuarioRequest,
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return editar_usuario_parcial(
        usuario_id=usuario_id,
        username=data.username,
        nombre=data.nombre,
        email=data.email,
        rol=data.rol,
    )


# =========================================================
# CAMBIAR PASSWORD
# =========================================================

@router.patch(
    "/{usuario_id}/password",
    response_model=MensajeResponse,
    **CAMBIAR_PASSWORD_DOCS,
)
def actualizar_password(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID del usuario.",
            examples=[2],
        ),
    ],
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


# =========================================================
# CAMBIAR ESTADO
# =========================================================

@router.patch(
    "/{usuario_id}/estado",
    response_model=UsuarioResponse,
    **CAMBIAR_ESTADO_DOCS,
)
def actualizar_estado(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID del usuario.",
            examples=[2],
        ),
    ],
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


# =========================================================
# ELIMINAR
# =========================================================

@router.delete(
    "/{usuario_id}",
    response_model=MensajeResponse,
    **ELIMINAR_USUARIO_DOCS,
)
def eliminar(
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID del usuario a eliminar.",
            examples=[2],
        ),
    ],
    _usuario_actual: Annotated[
        CurrentUser,
        Depends(require_role(ADMIN)),
    ],
):
    return eliminar_usuario(
        usuario_id,
    )