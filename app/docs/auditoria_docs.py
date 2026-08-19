ESTADO_AUDITORIA_DOCS = {
    "summary": "Consultar estado de auditoría",
    "description": (
        "Obtiene el estado de carga y procesamiento de cada turno "
        "para una fecha determinada.\n\n"
        "La respuesta permite conocer si ya se completaron las "
        "distintas etapas del flujo de auditoría:\n"
        "- EXP cargado.\n"
        "- Extractos cargados.\n"
        "- DBF cargado.\n"
        "- Cálculo ejecutado.\n\n"
        "También informa los nombres de los archivos asociados y "
        "las fechas en las que se realizaron las operaciones.\n\n"
        "**Interpretación de estados:**\n"
        "- `exp_cargado`: indica si el archivo EXP fue procesado.\n"
        "- `resultados_cargados`: indica si los extractos fueron cargados.\n"
        "- `dbf_cargado`: indica si el archivo DBF fue procesado.\n"
        "- `calculo_ejecutado`: indica si ya se ejecutó el cálculo propio.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": "✅ Estado de auditoría obtenido correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "turnos": [
                            {
                                "turno": "PV",
                                "exp_cargado": True,
                                "resultados_cargados": True,
                                "dbf_cargado": True,
                                "calculo_ejecutado": True,
                                "archivo_exp": "quiniela.exp",
                                "archivo_dbf": "Aciertos260810PV.dbf",
                                "fecha_exp": "2026-08-10 14:10:15.123456",
                                "fecha_dbf": "2026-08-10 14:20:31.654321",
                                "fecha_calculo": "2026-08-10 14:18:42.987654",
                                "updated_at": "2026-08-10 14:20:31.654321",
                            },
                            {
                                "turno": "PR",
                                "exp_cargado": True,
                                "resultados_cargados": False,
                                "dbf_cargado": False,
                                "calculo_ejecutado": False,
                                "archivo_exp": "quiniela.exp",
                                "archivo_dbf": None,
                                "fecha_exp": "2026-08-10 12:05:10.123456",
                                "fecha_dbf": None,
                                "fecha_calculo": None,
                                "updated_at": "2026-08-10 12:05:10.123456",
                            },
                        ],
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
                "❌ Error interno al consultar el estado de auditoría."
            ),
        },
    },
}