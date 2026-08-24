RUN_COMPARACION_DOCS = {
    "summary": "Comparar cálculo del sistema contra DBF",
    "description": (
        "Compara los aciertos calculados por el sistema "
        "contra los aciertos oficiales cargados desde el DBF.\n\n"
        "**Precondiciones:**\n"
        "- El cálculo debe haber sido ejecutado.\n"
        "- El DBF debe estar cargado.\n\n"
        "La comparación se realiza en distintos niveles:\n"
        "- Total de aciertos.\n"
        "- Cupones ganadores únicos.\n"
        "- Cantidad de aciertos por extracto.\n"
        "- Coincidencias y diferencias entre sistema y DBF.\n\n"
        "**Interpretación de métricas:**\n"
        "- `aciertos.sistema`: aciertos generados por la auditoría.\n"
        "- `aciertos.dbf`: aciertos informados por el DBF.\n"
        "- `cupones_ganadores_unicos`: cupones ganadores sin duplicar.\n"
        "- `solo_sistema`: registros encontrados por la auditoría "
        "que no aparecen en el DBF.\n"
        "- `solo_dbf`: registros presentes en el DBF "
        "que no fueron encontrados por la auditoría.\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Comparación ejecutada correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "turno": "PV",
                        "aciertos": {
                            "sistema": 2819,
                            "dbf": 2819,
                            "diferencia": 0,
                        },
                        "cupones_ganadores_unicos": {
                            "sistema": 2435,
                            "dbf": 2435,
                            "diferencia": 0,
                        },
                        "por_extracto": [
                            {
                                "codigo_extracto": 50,
                                "sistema": 355,
                                "dbf": 355,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 51,
                                "sistema": 309,
                                "dbf": 309,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 52,
                                "sistema": 319,
                                "dbf": 319,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 53,
                                "sistema": 1108,
                                "dbf": 1108,
                                "diferencia": 0,
                            },
                            {
                                "codigo_extracto": 54,
                                "sistema": 214,
                                "dbf": 214,
                                "diferencia": 0,
                            },
                        ],
                        "detalle": {
                            "coincidentes": 2819,
                            "solo_sistema": 0,
                            "solo_dbf": 0,
                        },
                        "diferencias": {
                            "solo_sistema": [],
                            "solo_dbf": [],
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
            "description": "❌ Error interno al realizar la comparación.",
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