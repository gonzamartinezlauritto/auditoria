LOGIN_DOCS = {
    "summary": "Iniciar sesión",
    "description": (
        "Autentica un usuario mediante nombre de usuario o email "
        "y devuelve un token JWT para consumir los endpoints "
        "protegidos de la API.\n\n"
        "El frontend debe enviar posteriormente el token en el header:\n\n"
        "`Authorization: Bearer <token>`\n\n"
        "El token incluye información del usuario y su rol."
    ),
    "responses": {
        200: {
            "description": "✅ Inicio de sesión correcto.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        ),
                        "token_type": "bearer",
                        "usuario": {
                            "id": 1,
                            "username": "operador1",
                            "nombre": "Operador Prueba",
                            "email": "operador@ejemplo.com",
                            "rol": "OPERADOR",
                        },
                    }
                }
            },
        },
        401: {
            "description": (
                "❌ Credenciales inválidas. "
                "El usuario/email o la contraseña no son correctos."
            ),
        },
        403: {
            "description": (
                "❌ Usuario inactivo. "
                "El usuario existe pero no tiene acceso habilitado."
            ),
        },
        422: {
            "description": "❌ Datos de login inválidos.",
            "content": {
                "application/json": {
                    "examples": {
                        "usuario_invalido": {
                            "summary": "Usuario inválido",
                            "value": {
                                "detail": [
                                    {
                                        "loc": [
                                            "body",
                                            "usuario",
                                        ],
                                        "msg": (
                                            "String should have at least "
                                            "3 characters"
                                        ),
                                        "type": (
                                            "string_too_short"
                                        ),
                                    }
                                ]
                            },
                        },
                        "password_invalido": {
                            "summary": "Contraseña inválida",
                            "value": {
                                "detail": [
                                    {
                                        "loc": [
                                            "body",
                                            "password",
                                        ],
                                        "msg": (
                                            "String should have at least "
                                            "8 characters"
                                        ),
                                        "type": (
                                            "string_too_short"
                                        ),
                                    }
                                ]
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": (
                "❌ Error interno durante la autenticación."
            ),
        },
    },
}