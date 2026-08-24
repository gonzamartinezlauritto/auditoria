from app.exceptions.base import AppException


class ExtensionDbfInvalidaError(AppException):
    status_code = 400
    code = "invalid_dbf_extension"
    message = "El archivo debe tener extensión .dbf"


class ArchivoDbfNoEncontradoError(AppException):
    status_code = 400
    code = "dbf_file_not_found"
    message = "No se encontró ningún archivo .dbf dentro del ZIP"


class ArchivoDbfInvalidoError(AppException):
    status_code = 400
    code = "invalid_dbf_file"
    message = "El archivo DBF es inválido o está dañado"


class ErrorProcesamientoDbf(AppException):
    status_code = 500
    code = "dbf_processing_error"
    message = "Ocurrió un error al procesar el archivo DBF"