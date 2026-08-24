RUN_CALCULO_DOCS = {
    "summary": "Ejecutar cálculo de premios",
    "description": (
        "Ejecuta el cálculo propio de premios para una fecha y turno.\n\n"
        "**Precondiciones:**\n"
        "- El archivo EXP debe estar cargado.\n"
        "- Los extractos correspondientes deben estar cargados.\n"
        "- El DBF no es necesario para ejecutar el cálculo.\n\n"
        "El resultado generado por el sistema se utiliza posteriormente "
        "para compararlo contra el DBF oficial.\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Cálculo ejecutado correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "turno": "PV",
                        "reportes": [
                            {
                                "codigo_extracto": 50,
                                "sorteo": "La Previa Ctes.",
                                "cupones_jugados": 14750,
                                "recaudacion": 14258278,
                                "importe_premiados": 3735313.5,
                                "apuestas_premiadas": 355,
                            },
                            {
                                "codigo_extracto": 51,
                                "sorteo": "La Previa Ciudad B.A.",
                                "cupones_jugados": 13867,
                                "recaudacion": 12980210,
                                "importe_premiados": 3975455,
                                "apuestas_premiadas": 309,
                            },
                            {
                                "codigo_extracto": 52,
                                "sorteo": "La Previa Bs.As.",
                                "cupones_jugados": 12700,
                                "recaudacion": 10016158,
                                "importe_premiados": 3620421,
                                "apuestas_premiadas": 319,
                            },
                            {
                                "codigo_extracto": 53,
                                "sorteo": "La Previa Sta.Fe",
                                "cupones_jugados": 10291,
                                "recaudacion": 6686065,
                                "importe_premiados": 6849476.8,
                                "apuestas_premiadas": 1108,
                            },
                            {
                                "codigo_extracto": 54,
                                "sorteo": "La Previa Cordoba",
                                "cupones_jugados": 9696,
                                "recaudacion": 6257301,
                                "importe_premiados": 1053455.5,
                                "apuestas_premiadas": 214,
                            },
                        ],
                        "cupones_ganadores_unicos": 2435,
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
        422: {
            "description": (
                "❌ No se cumplen las precondiciones para ejecutar "
                "el cálculo."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "exp_no_cargado": {
                            "summary": "EXP no cargado",
                            "value": {
                                "ok": False,
                                "code": (
                                    "calculation_preconditions_not_met"
                                ),
                                "message": (
                                    "No se puede calcular: falta cargar "
                                    "el EXP para fecha=20260810, turno=PV"
                                ),
                            },
                        },
                        "extractos_no_cargados": {
                            "summary": "Extractos no cargados",
                            "value": {
                                "ok": False,
                                "code": (
                                    "calculation_preconditions_not_met"
                                ),
                                "message": (
                                    "No se puede calcular: faltan cargar "
                                    "los resultados para fecha=20260810, "
                                    "turno=PV"
                                ),
                            },
                        },
                        "sin_extractos": {
                            "summary": "Sin extractos para calcular",
                            "value": {
                                "ok": False,
                                "code": "no_extracts_to_calculate",
                                "message": (
                                    "No hay extractos disponibles "
                                    "para calcular"
                                ),
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "❌ Error interno al ejecutar el cálculo.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "calculation_processing_error",
                        "message": (
                            "Ocurrió un error al ejecutar el cálculo"
                        ),
                    }
                }
            },
        },
    },
}


RESUMEN_CALCULO_DOCS = {
    "summary": "Consultar resumen de cálculo",
    "description": (
        "Obtiene el resumen de auditoría generado por los cálculos "
        "realizados para una fecha determinada.\n\n"
        "El resumen contiene información de recaudación, premios, "
        "comisión, utilidad y cantidades calculadas por extracto.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": "✅ Resumen obtenido correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "origen": "resumen_auditoria",
                        "turnos": {
                            "PV": [
                                {
                                    "codigo_extracto": 50,
                                    "sorteo": "La Previa Ctes.",
                                    "cupones_jugados": 14750,
                                    "recaudacion": 14258278,
                                    "importe_premiados": 3735313.5,
                                    "comision": 2851655.6,
                                    "utilidad": 7671308.9,
                                    "porcentaje_utilidad": 53.8,
                                    "apuestas_premiadas": 355,
                                }
                            ]
                        },
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
        422: {
            "description": "❌ Formato de fecha inválido.",
        },
        500: {
            "description": (
                "❌ Error interno al obtener el resumen de cálculo."
            ),
        },
    },
}