from typing import Any
from psycopg2.extensions import connection
from psycopg2 import IntegrityError

from app.constants.roles import OPERADOR, ROLES_VALIDOS
from app.core.logger import logger
from app.core.transaction import transaction
from app.exceptions.base import AppException, InternalServerError
from app.exceptions.user_exceptions import (
    EmailDuplicadoError,
    RolInvalidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
    UsernameDuplicadoError,
)
from app.repositories import user_repository
from app.security.password import hash_password


def _obtener_usuario_o_error(
    conn: connection,
    usuario_id: int,
) -> dict[str, Any]:
    usuario = user_repository.find_by_id(
        conn,
        usuario_id,
    )

    if not usuario:
        raise UsuarioNoEncontradoError()

    return usuario

def _normalizar_datos_usuario(
    username: str,
    nombre: str,
    email: str,
) -> tuple[str, str, str]:
    return (
        username.strip(),
        nombre.strip(),
        email.lower().strip(),
    )

def _validar_usuario_duplicado(
    conn: connection,
    username: str,
    email: str,
    usuario_id: int | None = None,
) -> None:
    usuario_username = user_repository.find_by_username(
        conn,
        username,
    )

    if (
        usuario_username
        and usuario_username["id"] != usuario_id
    ):
        raise UsernameDuplicadoError()

    usuario_email = user_repository.find_by_email(
        conn,
        email,
    )

    if (
        usuario_email
        and usuario_email["id"] != usuario_id
    ):
        raise EmailDuplicadoError()

def _validar_rol(rol: str) -> str:
    rol_normalizado = rol.lower().strip()

    if rol_normalizado not in ROLES_VALIDOS:
        raise RolInvalidoError(
            "Rol inválido. Valores permitidos: "
            f"{', '.join(sorted(ROLES_VALIDOS))}"
        )

    return rol_normalizado


def crear_usuario(
    username: str,
    nombre: str,
    email: str,
    password: str,
    rol: str = OPERADOR,
) -> dict[str, Any]:
    username, nombre, email = _normalizar_datos_usuario(username, nombre, email)
    rol = _validar_rol(rol)

    try:
        with transaction() as conn:
            _validar_usuario_duplicado(conn=conn,username=username,email=email)

            usuario = user_repository.insert_usuario(
                conn=conn,
                username=username,
                nombre=nombre,
                email=email,
                password_hash=hash_password(password),
                rol=rol,
            )

        logger.info(
            "Usuario creado correctamente: id=%s username=%s",
            usuario["id"],
            usuario["username"],
        )

        return usuario

    except AppException:
        raise

    except IntegrityError:
        logger.warning(
            "Conflicto de integridad al crear usuario: "
            "username=%s email=%s",
            username,
            email,
        )
        raise UsuarioDuplicadoError()

    except Exception as error:
        logger.exception(
            "Error inesperado al crear usuario: username=%s",
            username,
        )
        raise InternalServerError(
            "Error interno al crear el usuario"
        ) from error


def listar_usuarios() -> list[dict[str, Any]]:
    try:
        with transaction() as conn:
            return user_repository.find_all(conn)

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error inesperado al listar usuarios"
        )
        raise InternalServerError(
            "Error interno al listar los usuarios"
        ) from error


def obtener_usuario_por_id(usuario_id: int) -> dict[str, Any]:
    try:
        with transaction() as conn:
            return _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error inesperado al obtener usuario: id=%s",
            usuario_id,
        )
        raise InternalServerError(
            "Error interno al obtener el usuario"
        ) from error


def actualizar_usuario(
    usuario_id: int,
    username: str,
    nombre: str,
    email: str,
    rol: str,
) -> dict[str, Any]:
    username, nombre, email = _normalizar_datos_usuario(
        username,
        nombre,
        email,
    )

    rol = _validar_rol(rol)

    try:
        with transaction() as conn:
            _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

            _validar_usuario_duplicado(
                conn=conn,
                username=username,
                email=email,
                usuario_id=usuario_id,
            )

            usuario = user_repository.update_usuario(
                conn=conn,
                usuario_id=usuario_id,
                username=username,
                nombre=nombre,
                email=email,
                rol=rol,
            )

            if not usuario:
                raise UsuarioNoEncontradoError()

        logger.info(
            "Usuario actualizado correctamente: id=%s",
            usuario_id,
        )

        return usuario

    except AppException:
        raise

    except IntegrityError:
        logger.warning(
            "Conflicto de integridad al actualizar usuario: "
            "id=%s username=%s email=%s",
            usuario_id,
            username,
            email,
        )

        raise UsuarioDuplicadoError()

    except Exception as error:
        logger.exception(
            "Error inesperado al actualizar usuario: id=%s",
            usuario_id,
        )

        raise InternalServerError(
            "Error interno al actualizar el usuario"
        ) from error

def editar_usuario_parcial(
    usuario_id: int,
    username: str | None = None,
    nombre: str | None = None,
    email: str | None = None,
    rol: str | None = None,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            usuario_actual = _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

            nuevo_username = (
                username.strip()
                if username is not None
                else usuario_actual["username"]
            )

            nuevo_nombre = (
                nombre.strip()
                if nombre is not None
                else usuario_actual["nombre"]
            )

            nuevo_email = (
                email.strip().lower()
                if email is not None
                else usuario_actual["email"]
            )

            nuevo_rol = (
                _validar_rol(rol)
                if rol is not None
                else usuario_actual["rol"]
            )

            _validar_usuario_duplicado(
                conn=conn,
                username=nuevo_username,
                email=nuevo_email,
                usuario_id=usuario_id,
            )

            usuario = user_repository.update_usuario(
                conn=conn,
                usuario_id=usuario_id,
                username=nuevo_username,
                nombre=nuevo_nombre,
                email=nuevo_email,
                rol=nuevo_rol,
            )

            if not usuario:
                raise UsuarioNoEncontradoError()

        logger.info(
            "Usuario editado parcialmente: id=%s",
            usuario_id,
        )

        return usuario

    except AppException:
        raise

    except IntegrityError:
        logger.warning(
            "Conflicto de integridad al editar usuario: id=%s",
            usuario_id,
        )
        raise UsuarioDuplicadoError()

    except Exception as error:
        logger.exception(
            "Error inesperado al editar usuario: id=%s",
            usuario_id,
        )

        raise InternalServerError(
            "Error interno al editar el usuario"
        ) from error

def cambiar_password(
    usuario_id: int,
    nueva_password: str,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

            user_repository.update_password(
                conn=conn,
                usuario_id=usuario_id,
                password_hash=hash_password(nueva_password),
            )

        logger.info(
            "Contraseña actualizada correctamente: usuario_id=%s",
            usuario_id,
        )

        return {
            "message": "Contraseña actualizada correctamente",
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error inesperado al cambiar contraseña: usuario_id=%s",
            usuario_id,
        )
        raise InternalServerError(
            "Error interno al cambiar la contraseña"
        ) from error


def cambiar_estado_usuario(
    usuario_id: int,
    activo: bool,
) -> dict[str, Any]:
    try:
        with transaction() as conn:
            _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

            usuario = user_repository.update_estado(
                conn=conn,
                usuario_id=usuario_id,
                activo=activo,
            )

        logger.info(
            "Estado de usuario actualizado: "
            "usuario_id=%s activo=%s",
            usuario_id,
            activo,
        )

        return usuario

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error inesperado al modificar estado: usuario_id=%s",
            usuario_id,
        )
        raise InternalServerError(
            "Error interno al modificar el estado del usuario"
        ) from error


def eliminar_usuario(usuario_id: int) -> dict[str, Any]:
    try:
        with transaction() as conn:
            _obtener_usuario_o_error(
                conn,
                usuario_id,
            )

            user_repository.delete_usuario(
                conn,
                usuario_id,
            )

        logger.info(
            "Usuario eliminado correctamente: id=%s",
            usuario_id,
        )

        return {
            "message": "Usuario eliminado correctamente",
        }

    except AppException:
        raise

    except Exception as error:
        logger.exception(
            "Error inesperado al eliminar usuario: id=%s",
            usuario_id,
        )
        raise InternalServerError(
            "Error interno al eliminar el usuario"
        ) from error