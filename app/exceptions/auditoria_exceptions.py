from app.exceptions.base import AppException


class EventoNoEncontradoError(AppException):
    status_code = 404
    code = "evento_no_encontrado"
    message = "No existe el evento de auditoría solicitado"


class EventoCerradoError(AppException):
    status_code = 409
    code = "evento_cerrado"
    message = (
        "El evento de auditoría se encuentra cerrado "
        "y no puede ser modificado"
    )


class EventoYaCerradoError(AppException):
    status_code = 409
    code = "evento_ya_cerrado"
    message = "El evento de auditoría ya se encuentra cerrado"


class EventoYaAbiertoError(AppException):
    status_code = 409
    code = "evento_ya_abierto"
    message = "El evento de auditoría ya se encuentra abierto"


class EventoIncompletoError(AppException):
    status_code = 409
    code = "evento_incompleto"
    message = (
        "El evento no puede cerrarse porque existen "
        "etapas pendientes"
    )


class MotivoReaperturaRequeridoError(AppException):
    status_code = 400
    code = "motivo_reapertura_requerido"
    message = "El motivo de reapertura es obligatorio"