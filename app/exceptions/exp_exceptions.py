from app.exceptions.base import AppException


class NombreArchivoInvalidoError(AppException):
    status_code = 400
    code = "invalid_file_name"
    message = "El archivo no posee un nombre válido"


class ExtensionExpInvalidaError(AppException):
    status_code = 400
    code = "invalid_exp_extension"
    message = "El archivo debe tener extensión .exp"


class ExtensionZipInvalidaError(AppException):
    status_code = 400
    code = "invalid_zip_extension"
    message = "El archivo debe tener extensión .zip"


class ArchivoExpNoEncontradoError(AppException):
    status_code = 404
    code = "exp_file_not_found"
    message = "No se encontró el archivo quiniela.exp dentro del ZIP"


class ArchivoZipInvalidoError(AppException):
    status_code = 400
    code = "invalid_zip_file"
    message = "El archivo ZIP es inválido o está dañado"


class ErrorProcesamientoExp(AppException):
    status_code = 500
    code = "exp_processing_error"
    message = "Ocurrió un error al procesar el archivo EXP"


class SinApuestasParaTurnoError(AppException):
    status_code = 422
    code = "no_bets_for_requested_draw"
    message = (
        "El archivo procesado no contiene apuestas "
        "para la fecha y turno solicitados"
    )