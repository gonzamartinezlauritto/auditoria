from app.exceptions.base import AppException


class DbfNoCargadoError(AppException):
    status_code = 422
    code = "dbf_not_loaded"
    message = "Debe cargar el DBF antes de realizar la comparación"


class CalculoNoEjecutadoError(AppException):
    status_code = 422
    code = "calculation_not_executed"
    message = "Debe ejecutar el cálculo antes de realizar la comparación"


class ErrorComparacionError(AppException):
    status_code = 500
    code = "comparison_error"
    message = "Ocurrió un error al comparar los resultados"