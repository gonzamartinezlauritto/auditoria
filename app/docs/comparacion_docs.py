RUN_COMPARACION_DOCS = {
    "summary": "Comparar cálculo del sistema contra DBF",
    "description": (
        "Compara los aciertos calculados por el sistema "
        "contra los aciertos oficiales cargados desde el DBF.\n\n"

        "**Precondiciones:**\n"
        "- El cálculo debe haber sido ejecutado.\n"
        "- El DBF debe estar cargado.\n\n"

        "**Protección del evento:**\n"
        "Si el evento correspondiente a la fecha y turno se encuentra "
        "cerrado, no se permite ejecutar nuevamente la comparación. "
        "El evento debe ser reabierto previamente por un usuario ADMIN.\n\n"

        "La comparación se realiza en distintos niveles:\n"
        "- Total de aciertos.\n"
        "- Cupones ganadores únicos.\n"
        "- Cantidad de aciertos por extracto.\n"
        "- Coincidencias y diferencias entre sistema y DBF.\n"
        "- Comparación monetaria global por cupón.\n\n"

        "**Comparación monetaria:**\n"
        "- Los importes se comparan a nivel de cupón global.\n"
        "- La clave del cupón está formada por agencia, "
        "subagencia, máquina y número de cupón.\n"
        "- Una diferencia absoluta de hasta $100 inclusive "
        "se considera tolerada.\n"
        "- Las diferencias superiores a $100 se informan en "
        "`diferencias_montos`.\n\n"

        "**Interpretación de métricas:**\n"
        "- `aciertos.sistema`: aciertos generados por la auditoría.\n"
        "- `aciertos.dbf`: aciertos informados por el DBF.\n"
        "- `aciertos.diferencia`: diferencia entre ambos.\n"
        "- `montos.sistema`: importe total calculado por la auditoría.\n"
        "- `montos.dbf`: importe total informado por el DBF.\n"
        "- `montos.diferencia`: diferencia monetaria total real.\n"
        "- `montos.tolerancia`: tolerancia aplicada a la comparación "
        "individual de cada cupón.\n"
        "- `cupones_ganadores_unicos`: cupones ganadores sin duplicar.\n"
        "- `solo_sistema`: registros encontrados por la auditoría "
        "que no aparecen en el DBF.\n"
        "- `solo_dbf`: registros presentes en el DBF "
        "que no fueron encontrados por la auditoría.\n"
        "- `coincidentes_exactos`: cupones cuyo importe coincide "
        "exactamente.\n"
        "- `diferencias_toleradas`: cupones cuya diferencia es "
        "mayor a $0 pero menor o igual a $100.\n"
        "- `cupones_con_diferencia`: cupones cuya diferencia "
        "supera la tolerancia de $100.\n\n"

        "**Estado de auditoría:**\n"
        "Si la comparación finaliza correctamente, el sistema registra "
        "automáticamente la comparación como ejecutada para esa fecha "
        "y turno (`comparacion_ejecutada = true`) y registra la fecha "
        "de ejecución (`fecha_comparacion`).\n\n"

        "Esta etapa es obligatoria para poder realizar posteriormente "
        "el cierre del evento de auditoría.\n\n"

        "**Validez de la comparación:**\n"
        "La comparación representa el estado del cálculo y del DBF en el "
        "momento en que fue ejecutada. Si posteriormente se modifica "
        "información que interviene en la auditoría, la comparación deja "
        "de ser válida y debe ejecutarse nuevamente.\n\n"

        "La comparación se invalida cuando:\n"
        "- Se procesa o reprocesa el EXP.\n"
        "- Se cargan nuevamente los extractos.\n"
        "- Se modifica al menos un extracto y se recalculan sus premios.\n"
        "- Se ejecuta nuevamente el cálculo de premios.\n"
        "- Se carga o reemplaza el DBF.\n"
        "- Se reabre un evento previamente cerrado.\n\n"

        "Cuando esto ocurre, el sistema establece "
        "`comparacion_ejecutada = false` y `fecha_comparacion = null`. "
        "Por lo tanto, será obligatorio ejecutar nuevamente esta operación "
        "antes de cerrar el evento.\n\n"

        "Una comparación puede considerarse ejecutada aunque existan "
        "diferencias entre el sistema y el DBF. El cierre del evento "
        "requiere que la comparación haya sido realizada, pero no exige "
        "que las diferencias sean cero.\n\n"

        "Una vez cerrado el evento, la comparación queda protegida "
        "junto con el resto de la auditoría y no puede volver a "
        "ejecutarse hasta que un ADMIN reabra el evento.\n\n"

        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": (
                "✅ Comparación ejecutada correctamente. "
                "La etapa de comparación queda registrada "
                "como completada para la fecha y turno."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260910,
                        "turno": "PV",

                        "aciertos": {
                            "sistema": 2677,
                            "dbf": 2677,
                            "diferencia": 0,
                        },

                        "montos": {
                            "sistema": 12543000.00,
                            "dbf": 12543000.00,
                            "diferencia": 0.00,
                            "tolerancia": 100.00,
                        },

                        "cupones_ganadores_unicos": {
                            "sistema": 2300,
                            "dbf": 2300,
                            "diferencia": 0,
                        },

                        "por_extracto": [
                            {
                                "codigo_extracto": 50,
                                "sistema": 168,
                                "dbf": 168,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 51,
                                "sistema": 300,
                                "dbf": 300,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 52,
                                "sistema": 575,
                                "dbf": 575,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 53,
                                "sistema": 609,
                                "dbf": 609,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 54,
                                "sistema": 265,
                                "dbf": 265,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 55,
                                "sistema": 281,
                                "dbf": 281,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 56,
                                "sistema": 479,
                                "dbf": 479,
                                "diferencia": 0,
                            },
                        ],

                        "detalle": {
                            "coincidentes": 2677,
                            "solo_sistema": 0,
                            "solo_dbf": 0,
                        },

                        "detalle_montos": {
                            "cupones_comparados": 2300,
                            "coincidentes_exactos": 2298,
                            "diferencias_toleradas": 2,
                            "cupones_con_diferencia": 0,
                        },

                        "diferencias": {
                            "solo_sistema": [],
                            "solo_dbf": [],
                        },

                        "diferencias_montos": [],
                    }
                }
            },
        },

        401: {
            "description": "❌ No autenticado.",
        },

        403: {
            "description": "❌ Acceso denegado.",
        },

        409: {
            "description": (
                "❌ El evento de auditoría se encuentra cerrado "
                "y no se puede ejecutar nuevamente la comparación."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "evento_cerrado",
                        "message": (
                            "El evento de auditoría se encuentra "
                            "cerrado y no puede ser modificado"
                        ),
                    }
                }
            },
        },

        422: {
            "description": "❌ No se cumplen las precondiciones.",
            "content": {
                "application/json": {
                    "examples": {
                        "calculo_no_ejecutado": {
                            "summary": "Cálculo no ejecutado",
                            "value": {
                                "ok": False,
                                "code": "calculation_not_executed",
                                "message": (
                                    "Debe ejecutar el cálculo antes "
                                    "de realizar la comparación"
                                ),
                            },
                        },

                        "dbf_no_cargado": {
                            "summary": "DBF no cargado",
                            "value": {
                                "ok": False,
                                "code": "dbf_not_loaded",
                                "message": (
                                    "Debe cargar el DBF antes "
                                    "de realizar la comparación"
                                ),
                            },
                        },
                    }
                }
            },
        },

        500: {
            "description": (
                "❌ Error interno al realizar la comparación. "
                "Si la operación falla, la comparación no queda "
                "marcada como ejecutada."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "comparison_error",
                        "message": (
                            "Ocurrió un error al comparar "
                            "los resultados"
                        ),
                    }
                }
            },
        },
    },
}