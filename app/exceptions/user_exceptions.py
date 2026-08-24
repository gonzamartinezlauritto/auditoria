from app.exceptions.base import AppException


class UsuarioNoEncontradoError(AppException):
    status_code = 404
    code = "user_not_found"
    message = "Usuario no encontrado"


class UsernameDuplicadoError(AppException):
    status_code = 409
    code = "username_already_exists"
    message = "El username ya se encuentra registrado"


class EmailDuplicadoError(AppException):
    status_code = 409
    code = "email_already_exists"
    message = "El email ya se encuentra registrado"


class UsuarioDuplicadoError(AppException):
    status_code = 409
    code = "user_already_exists"
    message = "El username o email ya se encuentra registrado"


class RolInvalidoError(AppException):
    status_code = 400
    code = "invalid_role"
    message = "Rol inválido"


class UsuarioInactivoError(AppException):
    status_code = 403
    code = "user_inactive"
    message = "Usuario inactivo"


class CredencialesInvalidasError(AppException):
    status_code = 401
    code = "invalid_credentials"
    message = "Usuario o contraseña incorrectos"