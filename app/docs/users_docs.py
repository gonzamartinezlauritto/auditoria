ME_DOCS = {
    "summary": "Consultar perfil autenticado",
    "description": (
        "Devuelve la información del usuario asociado "
        "al token JWT enviado en la solicitud."
    ),
    "responses": {
        200: {
            "description": "✅ Perfil obtenido correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "operador1",
                        "nombre": "Operador Prueba",
                        "email": "operador1@ejemplo.com",
                        "rol": "OPERADOR",
                        "activo": True,
                    }
                }
            },
        },
        401: {
            "description": "❌ Token ausente o inválido.",
        },
        403: {
            "description": "❌ Usuario inactivo.",
        },
    },
}


CREAR_USUARIO_DOCS = {
    "summary": "Crear usuario",
    "description": (
        "Crea un nuevo usuario en el sistema.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        201: {
            "description": "✅ Usuario creado correctamente.",
        },
        400: {
            "description": "❌ Datos de usuario inválidos.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Solo un ADMIN puede crear usuarios.",
        },
        409: {
            "description": (
                "❌ Ya existe un usuario con el username "
                "o email indicado."
            ),
        },
        422: {
            "description": "❌ Error de validación de datos.",
        },
    },
}


LISTAR_USUARIOS_DOCS = {
    "summary": "Listar usuarios",
    "description": (
        "Obtiene el listado de usuarios registrados.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Usuarios obtenidos correctamente.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "username": "admin",
                            "nombre": "Administrador",
                            "email": "admin@ejemplo.com",
                            "rol": "ADMIN",
                            "activo": True,
                        },
                        {
                            "id": 2,
                            "username": "operador1",
                            "nombre": "Operador Prueba",
                            "email": "operador1@ejemplo.com",
                            "rol": "OPERADOR",
                            "activo": True,
                        },
                    ]
                }
            },
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Solo un ADMIN puede listar usuarios.",
        },
    },
}


OBTENER_USUARIO_DOCS = {
    "summary": "Consultar usuario por ID",
    "description": (
        "Obtiene un usuario específico mediante su ID.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Usuario encontrado.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Acceso denegado.",
        },
        404: {
            "description": "❌ Usuario no encontrado.",
        },
        422: {
            "description": "❌ ID de usuario inválido.",
        },
    },
}


ACTUALIZAR_USUARIO_DOCS = {
    "summary": "Actualizar usuario",
    "description": (
        "Actualiza username, nombre, email y rol "
        "de un usuario existente.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Usuario actualizado correctamente.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Acceso denegado.",
        },
        404: {
            "description": "❌ Usuario no encontrado.",
        },
        409: {
            "description": (
                "❌ Username o email ya utilizado por otro usuario."
            ),
        },
        422: {
            "description": "❌ Datos de usuario inválidos.",
        },
    },
}


CAMBIAR_PASSWORD_DOCS = {
    "summary": "Cambiar contraseña de usuario",
    "description": (
        "Establece una nueva contraseña para el usuario indicado.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Contraseña actualizada correctamente.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Acceso denegado.",
        },
        404: {
            "description": "❌ Usuario no encontrado.",
        },
        422: {
            "description": "❌ Contraseña inválida.",
        },
    },
}


CAMBIAR_ESTADO_DOCS = {
    "summary": "Cambiar estado de usuario",
    "description": (
        "Activa o desactiva un usuario del sistema.\n\n"
        "`true` = usuario activo.\n\n"
        "`false` = usuario inactivo.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Estado actualizado correctamente.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Acceso denegado.",
        },
        404: {
            "description": "❌ Usuario no encontrado.",
        },
        422: {
            "description": "❌ Estado inválido.",
        },
    },
}


ELIMINAR_USUARIO_DOCS = {
    "summary": "Eliminar usuario",
    "description": (
        "Elimina el usuario indicado del sistema.\n\n"
        "**Rol requerido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": "✅ Usuario eliminado correctamente.",
        },
        401: {
            "description": "❌ No autenticado.",
        },
        403: {
            "description": "❌ Acceso denegado.",
        },
        404: {
            "description": "❌ Usuario no encontrado.",
        },
        422: {
            "description": "❌ ID de usuario inválido.",
        },
    },
}