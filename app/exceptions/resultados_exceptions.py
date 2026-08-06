from app.exceptions.base import AppException


class CantidadResultadosInvalidaError(AppException):
    status_code = 422
    code = "invalid_results_count"
    message = "Cada extracto debe contener exactamente 20 resultados"


class NumeroResultadoInvalidoError(AppException):
    status_code = 422
    code = "invalid_result_number"
    message = "Los resultados deben contener solamente números"


class ResultadosVaciosError(AppException):
    status_code = 422
    code = "empty_results"
    message = "Debe informar al menos un extracto con resultados"


class ErrorProcesamientoResultados(AppException):
    status_code = 500
    code = "results_processing_error"
    message = "Ocurrió un error al procesar los resultados"