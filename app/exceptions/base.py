class AppException(Exception):
    status_code = 500
    code = "internal_error"
    message = "Error interno del sistema"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
    ):
        self.message = message or self.message
        self.code = code or self.code
        super().__init__(self.message)


class InternalServerError(AppException):
    status_code = 500
    code = "internal_server_error"
    message = "Error interno del sistema"