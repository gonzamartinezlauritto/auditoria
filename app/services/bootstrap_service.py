import os

from app.constants.roles import ADMIN
from app.core.logger import logger
from app.core.transaction import transaction
from app.repositories import user_repository
from app.services.user_service import crear_usuario


def crear_admin_inicial() -> None:
    username = os.getenv(
        "INITIAL_ADMIN_USERNAME"
    )

    nombre = os.getenv(
        "INITIAL_ADMIN_NAME"
    )

    email = os.getenv(
        "INITIAL_ADMIN_EMAIL"
    )

    password = os.getenv(
        "INITIAL_ADMIN_PASSWORD"
    )

    if not all(
        [
            username,
            nombre,
            email,
            password,
        ]
    ):
        logger.info(
            "Bootstrap de administrador omitido: "
            "faltan variables INITIAL_ADMIN_*"
        )
        return

    with transaction() as conn:
        usuario_existente = (
            user_repository.find_by_username_or_email(
                conn=conn,
                usuario=username,
            )
        )

        if not usuario_existente:
            usuario_existente = (
                user_repository.find_by_username_or_email(
                    conn=conn,
                    usuario=email,
                )
            )

    if usuario_existente:
        logger.info(
            "Administrador inicial ya existe: username=%s",
            username,
        )
        return

    usuario = crear_usuario(
        username=username,
        nombre=nombre,
        email=email,
        password=password,
        rol=ADMIN,
    )

    logger.info(
        "Administrador inicial creado: id=%s username=%s",
        usuario["id"],
        usuario["username"],
    )