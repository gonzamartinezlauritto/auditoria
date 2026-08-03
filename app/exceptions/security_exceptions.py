from app.exceptions.base import AppException


class TokenRequeridoError(AppException):
    status_code = 401
    code = "authentication_required"
    message = "Se requiere un token de autenticación válido"


class TokenInvalidoError(AppException):
    status_code = 401
    code = "invalid_token"
    message = "Token inválido o expirado"


class PermisoDenegadoError(AppException):
    status_code = 403
    code = "permission_denied"
    message = "No posee permisos para realizar esta operación"