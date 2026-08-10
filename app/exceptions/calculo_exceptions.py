from app.exceptions.base import AppException


class PrecondicionesCalculoError(AppException):
    status_code = 422
    code = "calculation_preconditions_not_met"
    message = "No se cumplen las precondiciones para ejecutar el cálculo"


class ExtractoNoEncontradoError(AppException):
    status_code = 404
    code = "extract_not_found"
    message = "No se encontró el extracto solicitado"


class ResultadosNoEncontradosError(AppException):
    status_code = 422
    code = "results_not_found"
    message = "No hay resultados cargados para el extracto solicitado"


class SinExtractosParaCalcularError(AppException):
    status_code = 422
    code = "no_extracts_to_calculate"
    message = "No hay extractos disponibles para calcular"


class ErrorProcesamientoCalculo(AppException):
    status_code = 500
    code = "calculation_processing_error"
    message = "Ocurrió un error al ejecutar el cálculo"

