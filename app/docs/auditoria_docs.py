ESTADO_AUDITORIA_DOCS = {
    "summary": "Consultar estado de auditoría",
    "description": (
        "Obtiene el estado de carga, procesamiento y cierre "
        "de cada turno para una fecha determinada.\n\n"
        "Cada evento de auditoría se identifica mediante la combinación "
        "de `fecha_sorteo` y `turno`.\n\n"
        "Permite conocer las etapas completadas:\n"
        "- EXP cargado.\n"
        "- Extractos/resultados cargados.\n"
        "- Cálculo ejecutado.\n"
        "- DBF cargado.\n"
        "- Comparación ejecutada.\n"
        "- Evento cerrado o abierto.\n\n"
        "También informa las fechas de las operaciones y los "
        "usuarios asociados al cierre o reapertura.\n\n"
        "**Interpretación de estados:**\n"
        "- `exp_cargado`: existe un EXP procesado para el evento.\n"
        "- `resultados_cargados`: existen resultados oficiales cargados.\n"
        "- `calculo_ejecutado`: el cálculo actual se encuentra ejecutado.\n"
        "- `dbf_cargado`: existe un DBF procesado para el evento.\n"
        "- `comparacion_ejecutada`: existe una comparación válida entre "
        "el cálculo actual y el DBF actual.\n"
        "- `evento_cerrado`: indica si el evento se encuentra protegido "
        "contra modificaciones.\n\n"
        "Los estados de cálculo y comparación pueden volver a `false` "
        "cuando se reprocesa información que invalida resultados "
        "anteriores.\n\n"
        "Este endpoint es únicamente de consulta y permanece disponible "
        "aunque el evento se encuentre cerrado.\n\n"
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
        "Cierra el evento correspondiente a una fecha y turno "
        "y protege la auditoría contra nuevas modificaciones.\n\n"
        "Para poder cerrar el evento deben haberse completado "
        "todas las etapas obligatorias:\n"
        "- EXP cargado.\n"
        "- Resultados cargados.\n"
        "- Cálculo ejecutado.\n"
        "- DBF cargado.\n"
        "- Comparación ejecutada.\n\n"
        "**Validación de vigencia:**\n"
        "La comparación debe continuar siendo válida al momento del cierre. "
        "Si después de comparar se reprocesa el EXP, se cargan o modifican "
        "extractos, se ejecuta nuevamente el cálculo o se reemplaza el DBF, "
        "la comparación queda invalidada y deberá ejecutarse nuevamente "
        "antes de cerrar.\n\n"
        "**Diferencias de auditoría:**\n"
        "El cierre no exige que la comparación tenga cero diferencias. "
        "Las diferencias detectadas entre el sistema y el DBF pueden formar "
        "parte legítima del resultado de la auditoría.\n\n"
        "**Protección posterior al cierre:**\n"
        "Una vez cerrado, no podrán ejecutarse operaciones que modifiquen "
        "los datos del evento, incluyendo reprocesamiento de EXP, carga o "
        "modificación de extractos, nuevo cálculo, carga o reemplazo del DBF "
        "y nueva comparación.\n\n"
        "Las operaciones de consulta y reportes permanecen disponibles.\n\n"
        "Para volver a modificar el evento será necesaria una reapertura "
        "realizada por un usuario ADMIN, indicando obligatoriamente "
        "el motivo.\n\n"
        "El usuario que realiza el cierre se obtiene automáticamente "
        "de la sesión autenticada y el cierre queda registrado en "
        "el historial del evento.\n\n"
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
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "error": {
                            "code": "evento_no_encontrado",
                            "message": (
                                "No existe el evento de auditoría solicitado"
                            ),
                        },
                    }
                }
            },
        },
        409: {
            "description": (
                "El evento ya está cerrado o existen "
                "etapas pendientes."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "evento_ya_cerrado": {
                            "summary": "Evento ya cerrado",
                            "value": {
                                "ok": False,
                                "error": {
                                    "code": "evento_ya_cerrado",
                                    "message": (
                                        "El evento de auditoría ya "
                                        "se encuentra cerrado"
                                    ),
                                },
                            },
                        },
                        "evento_incompleto": {
                            "summary": "Etapas pendientes",
                            "value": {
                                "ok": False,
                                "error": {
                                    "code": "evento_incompleto",
                                    "message": (
                                        "No se puede cerrar el evento. "
                                        "Faltan completar las siguientes "
                                        "etapas: comparación."
                                    ),
                                },
                            },
                        },
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
        "El usuario que realiza la reapertura se obtiene "
        "automáticamente de la sesión autenticada.\n\n"
        "**Efectos de la reapertura:**\n"
        "- `evento_cerrado = false`.\n"
        "- Se habilitan nuevamente las operaciones de escritura.\n"
        "- Se registra la fecha de reapertura.\n"
        "- Se registra el usuario que realizó la reapertura.\n"
        "- Se registra el motivo de la reapertura.\n"
        "- Se conserva la información del cierre anterior.\n"
        "- `comparacion_ejecutada = false`.\n"
        "- `fecha_comparacion = null`.\n\n"
        "La reapertura no invalida automáticamente el cálculo existente. "
        "El cálculo conservará su estado mientras no se modifique información "
        "que obligue a recalcularlo.\n\n"
        "Después de la reapertura será obligatorio ejecutar nuevamente "
        "la comparación antes de realizar un nuevo cierre.\n\n"
        "Si durante la corrección se reprocesa el EXP o se cargan nuevamente "
        "los extractos, también se invalidará el cálculo y deberá ejecutarse "
        "nuevamente antes de comparar.\n\n"
        "La reapertura queda registrada en el historial del evento "
        "junto con el usuario, el motivo y la fecha de la operación.\n\n"
        "**Rol permitido:** ADMIN."
    ),
    "responses": {
        200: {
            "description": (
                "Evento reabierto correctamente. "
                "La comparación anterior queda invalidada."
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
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "error": {
                            "code": "motivo_reapertura_requerido",
                            "message": (
                                "El motivo de reapertura es obligatorio"
                            ),
                        },
                    }
                }
            },
        },
        404: {
            "description": (
                "No existe el evento de auditoría."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "error": {
                            "code": "evento_no_encontrado",
                            "message": (
                                "No existe el evento de auditoría solicitado"
                            ),
                        },
                    }
                }
            },
        },
        409: {
            "description": (
                "El evento ya se encuentra abierto."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "error": {
                            "code": "evento_ya_abierto",
                            "message": (
                                "El evento de auditoría ya "
                                "se encuentra abierto"
                            ),
                        },
                    }
                }
            },
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
        "- Acción realizada (`CIERRE` o `REAPERTURA`).\n"
        "- Usuario responsable.\n"
        "- Motivo, cuando corresponda.\n"
        "- Fecha y hora de la operación.\n\n"
        "Cada nuevo cierre o reapertura genera un registro independiente, "
        "por lo que es posible reconstruir los distintos ciclos del evento.\n\n"
        "El historial es únicamente de consulta y permanece disponible "
        "aunque el evento se encuentre cerrado.\n\n"
        "Los registros se presentan desde la operación más reciente "
        "hasta la más antigua.\n\n"
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