ESTADO_AUDITORIA_DOCS = {
    "summary": "Consultar estado de auditoría",
    "description": (
        "Obtiene el estado de carga, procesamiento y cierre "
        "de cada turno para una fecha determinada.\n\n"
        "Permite conocer las etapas completadas:\n"
        "- EXP cargado.\n"
        "- Extractos/resultados cargados.\n"
        "- Cálculo ejecutado.\n"
        "- DBF cargado.\n"
        "- Comparación ejecutada.\n"
        "- Evento cerrado o abierto.\n\n"
        "También informa las fechas de las operaciones y los "
        "usuarios asociados al cierre o reapertura.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": (
                "Estado de auditoría obtenido correctamente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260910,
                        "turnos": [
                            {
                                "turno": "PV",
                                "exp_cargado": True,
                                "resultados_cargados": True,
                                "dbf_cargado": True,
                                "calculo_ejecutado": True,
                                "comparacion_ejecutada": True,
                                "evento_cerrado": True,
                                "archivo_exp": "quiniela.exp",
                                "archivo_dbf": (
                                    "Aciertos260910PV.dbf"
                                ),
                                "fecha_exp": (
                                    "2026-09-10 14:10:15"
                                ),
                                "fecha_dbf": (
                                    "2026-09-10 14:20:31"
                                ),
                                "fecha_calculo": (
                                    "2026-09-10 14:18:42"
                                ),
                                "fecha_comparacion": (
                                    "2026-09-10 14:25:00"
                                ),
                                "fecha_cierre": (
                                    "2026-09-10 14:30:00"
                                ),
                                "cerrado_por": "admin01",
                                "fecha_reapertura": None,
                                "reabierto_por": None,
                                "motivo_reapertura": None,
                                "updated_at": (
                                    "2026-09-10 14:30:00"
                                ),
                            }
                        ],
                    }
                }
            },
        },
        401: {
            "description": "No autenticado.",
        },
        403: {
            "description": "Acceso denegado.",
        },
        422: {
            "description": "Parámetros inválidos.",
        },
        500: {
            "description": (
                "Error interno al consultar "
                "el estado de auditoría."
            ),
        },
    },
}


CERRAR_EVENTO_DOCS = {
    "summary": "Cerrar evento de auditoría",
    "description": (
        "Cierra definitivamente el evento correspondiente "
        "a una fecha y turno.\n\n"
        "Para poder cerrar el evento deben haberse completado "
        "todas las etapas obligatorias:\n"
        "- EXP cargado.\n"
        "- Resultados cargados.\n"
        "- Cálculo ejecutado.\n"
        "- DBF cargado.\n"
        "- Comparación ejecutada.\n\n"
        "El cierre no exige que la comparación tenga cero "
        "diferencias. Las diferencias pueden formar parte del "
        "resultado de la auditoría.\n\n"
        "Una vez cerrado, el evento no podrá ser modificado "
        "hasta que un administrador realice una reapertura.\n\n"
        "El usuario que realiza el cierre se obtiene "
        "automáticamente de la sesión autenticada.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": (
                "Evento cerrado correctamente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260910,
                        "turno": "PV",
                        "evento_cerrado": True,
                        "cerrado_por": "admin01",
                        "message": (
                            "Evento de auditoría "
                            "cerrado correctamente."
                        ),
                    }
                }
            },
        },
        404: {
            "description": (
                "No existe el evento de auditoría."
            ),
        },
        409: {
            "description": (
                "El evento ya está cerrado o existen "
                "etapas pendientes."
            ),
        },
        401: {
            "description": "No autenticado.",
        },
        403: {
            "description": "Acceso denegado.",
        },
        422: {
            "description": "Parámetros inválidos.",
        },
        500: {
            "description": (
                "Error interno al cerrar el evento."
            ),
        },
    },
}


REABRIR_EVENTO_DOCS = {
    "summary": "Reabrir evento de auditoría",
    "description": (
        "Reabre un evento previamente cerrado para permitir "
        "correcciones o reprocesamientos.\n\n"
        "La reapertura requiere obligatoriamente indicar "
        "un motivo.\n\n"
        "Al reabrir el evento:\n"
        "- Se habilitan nuevamente las operaciones de escritura.\n"
        "- Se registra el usuario que realizó la reapertura.\n"
        "- Se registra el motivo.\n"
        "- Se conserva el cierre anterior para trazabilidad.\n"
        "- Se invalida la comparación anterior.\n"
        "- Será obligatorio volver a ejecutar la comparación "
        "antes de realizar un nuevo cierre.\n\n"
        "La reapertura también queda registrada en el historial "
        "del evento.\n\n"
        "**Rol permitido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": (
                "Evento reabierto correctamente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260910,
                        "turno": "PV",
                        "evento_cerrado": False,
                        "reabierto_por": "admin01",
                        "motivo_reapertura": (
                            "Corrección de resultados "
                            "del extracto 52"
                        ),
                        "message": (
                            "Evento de auditoría reabierto "
                            "correctamente. La comparación "
                            "anterior fue invalidada y deberá "
                            "ejecutarse nuevamente antes de "
                            "cerrar el evento."
                        ),
                    }
                }
            },
        },
        400: {
            "description": (
                "El motivo de reapertura es obligatorio."
            ),
        },
        404: {
            "description": (
                "No existe el evento de auditoría."
            ),
        },
        409: {
            "description": (
                "El evento ya se encuentra abierto."
            ),
        },
        401: {
            "description": "No autenticado.",
        },
        403: {
            "description": (
                "Acceso denegado. La reapertura "
                "requiere rol ADMIN."
            ),
        },
        422: {
            "description": "Datos inválidos.",
        },
        500: {
            "description": (
                "Error interno al reabrir el evento."
            ),
        },
    },
}


HISTORIAL_EVENTO_DOCS = {
    "summary": "Consultar historial de un evento",
    "description": (
        "Obtiene el historial de cierres y reaperturas "
        "correspondiente a una fecha y turno.\n\n"
        "Cada registro informa:\n"
        "- Acción realizada.\n"
        "- Usuario responsable.\n"
        "- Motivo, cuando corresponda.\n"
        "- Fecha y hora de la operación.\n\n"
        "El historial permite conservar la trazabilidad "
        "de los eventos de auditoría.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": (
                "Historial obtenido correctamente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260910,
                        "turno": "PV",
                        "historial": [
                            {
                                "id": 3,
                                "fecha": 20260910,
                                "turno": "PV",
                                "accion": "CIERRE",
                                "usuario": "admin01",
                                "motivo": None,
                                "fecha_operacion": (
                                    "2026-09-10 15:15:00"
                                ),
                            },
                            {
                                "id": 2,
                                "fecha": 20260910,
                                "turno": "PV",
                                "accion": "REAPERTURA",
                                "usuario": "admin01",
                                "motivo": (
                                    "Corrección de resultados "
                                    "del extracto 52"
                                ),
                                "fecha_operacion": (
                                    "2026-09-10 15:00:00"
                                ),
                            },
                            {
                                "id": 1,
                                "fecha": 20260910,
                                "turno": "PV",
                                "accion": "CIERRE",
                                "usuario": "operador1",
                                "motivo": None,
                                "fecha_operacion": (
                                    "2026-09-10 14:30:00"
                                ),
                            },
                        ],
                    }
                }
            },
        },
        401: {
            "description": "No autenticado.",
        },
        403: {
            "description": "Acceso denegado.",
        },
        422: {
            "description": "Parámetros inválidos.",
        },
        500: {
            "description": (
                "Error interno al consultar "
                "el historial."
            ),
        },
    },
}