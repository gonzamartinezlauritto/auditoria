CONTROL_ACIERTOS_DOCS = {
    "summary": "Consultar control de aciertos",
    "description": (
        "Obtiene los datos consolidados necesarios para construir "
        "el reporte de Control de Aciertos para una fecha y turno.\n\n"
        "La respuesta incluye:\n"
        "- Datos por extracto.\n"
        "- Recaudación.\n"
        "- Importe de aciertos.\n"
        "- Comisión.\n"
        "- Utilidad.\n"
        "- Porcentaje de utilidad.\n"
        "- Cantidad de aciertos informados por el DBF.\n"
        "- Cantidad de aciertos generados por la auditoría.\n"
        "- Totales generales.\n"
        "- Cupones ganadores únicos del DBF y de la auditoría.\n\n"
        "**Interpretación de campos:**\n"
        "- `archivo_frontend`: cantidad de aciertos informados por el DBF.\n"
        "- `generados_auditoria`: cantidad de aciertos calculados por el sistema.\n"
        "- `cupones_ganadores_unicos.frontend`: cupones ganadores únicos del DBF.\n"
        "- `cupones_ganadores_unicos.auditoria`: cupones ganadores únicos calculados por el sistema.\n\n"
        "Este endpoint entrega los datos; la presentación y generación "
        "del PDF queda a cargo del frontend.\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": "✅ Reporte obtenido correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "turno": "PV",
                        "reportes": [
                            {
                                "codigo_extracto": 52,
                                "sorteo": "La Previa Bs.As.",
                                "cupones_jugados": 12700,
                                "recaudacion": 10016158.0,
                                "importe_aciertos": 3620421.0,
                                "comision": 2003231.6,
                                "utilidad": 4392505.4,
                                "porcentaje_utilidad": 43.85,
                                "archivo_frontend": 319,
                                "generados_auditoria": 319,
                            },
                            {
                                "codigo_extracto": 51,
                                "sorteo": "La Previa Ciudad B.A.",
                                "cupones_jugados": 13867,
                                "recaudacion": 12980210.0,
                                "importe_aciertos": 3975455.0,
                                "comision": 2596042.0,
                                "utilidad": 6408713.0,
                                "porcentaje_utilidad": 49.37,
                                "archivo_frontend": 309,
                                "generados_auditoria": 309,
                            },
                        ],
                        "totales": {
                            "recaudacion": 61695820.0,
                            "importe_aciertos": 22282700.8,
                            "comision": 12339164.0,
                            "utilidad": 27073955.2,
                            "archivo_frontend": 2819,
                            "generados_auditoria": 2819,
                        },
                        "cupones_ganadores_unicos": {
                            "frontend": 2435,
                            "auditoria": 2435,
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
            "description": (
                "❌ Parámetros inválidos. "
                "Verifique fecha y turno."
            ),
        },
        500: {
            "description": (
                "❌ Error interno al obtener el control de aciertos."
            ),
        },
    },
}