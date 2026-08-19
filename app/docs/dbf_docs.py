PROCESS_DBF_DOCS = {
    "summary": "Procesar archivo DBF de aciertos",
    "description": (
        "Sube y procesa un archivo `.dbf` de aciertos oficiales "
        "para una fecha y turno determinados.\n\n"
        "Los registros del DBF se almacenan para posteriormente "
        "compararlos con los aciertos calculados por el sistema.\n\n"
        "**Flujo recomendado:**\n"
        "1. Cargar el EXP.\n"
        "2. Cargar los extractos.\n"
        "3. Ejecutar el cálculo del sistema.\n"
        "4. Cargar y procesar el DBF.\n"
        "5. Ejecutar la comparación.\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Archivo DBF procesado correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "archivo_origen": "Aciertos260810PV.dbf",
                        "fecha": 20260810,
                        "turno": "PV",
                        "filas_insertadas": 2819,
                        "extractos": [
                            {
                                "codigo_extracto": 50,
                                "cantidad": 355,
                            },
                            {
                                "codigo_extracto": 51,
                                "cantidad": 309,
                            },
                            {
                                "codigo_extracto": 52,
                                "cantidad": 319,
                            },
                            {
                                "codigo_extracto": 53,
                                "cantidad": 1108,
                            },
                            {
                                "codigo_extracto": 54,
                                "cantidad": 214,
                            },
                        ],
                        "cupones_ganadores_unicos": 2435,
                        "tiempos_service": {
                            "total_segundos": 1.39,
                        },
                    }
                }
            },
        },
        400: {
            "description": "❌ Archivo DBF inválido.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "invalid_dbf_extension",
                        "message": (
                            "El archivo debe tener extensión .dbf"
                        ),
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
                "❌ Parámetros de entrada inválidos "
                "o archivo requerido no enviado."
            ),
        },
        500: {
            "description": "❌ Error interno al procesar el DBF.",
        },
    },
}


PROCESS_DBF_ZIP_DOCS = {
    "summary": "Procesar ZIP con archivo DBF de aciertos",
    "description": (
        "Sube un archivo `.zip`, extrae el archivo `.dbf` "
        "contenido en él y procesa los aciertos oficiales "
        "para la fecha y turno indicados.\n\n"
        "El resultado permite conocer la cantidad de aciertos "
        "informados por el DBF para cada extracto y la cantidad "
        "de cupones ganadores únicos.\n\n"
        "**Flujo recomendado:**\n"
        "1. Cargar el EXP.\n"
        "2. Cargar los extractos.\n"
        "3. Ejecutar el cálculo del sistema.\n"
        "4. Cargar y procesar el ZIP del DBF.\n"
        "5. Ejecutar la comparación.\n\n"
        "**Archivo permitido:** `.zip`\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ ZIP con DBF procesado correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "archivo_origen": "Aciertos260810PV.dbf",
                        "fecha": 20260810,
                        "turno": "PV",
                        "filas_insertadas": 2819,
                        "extractos": [
                            {
                                "codigo_extracto": 50,
                                "cantidad": 355,
                            },
                            {
                                "codigo_extracto": 51,
                                "cantidad": 309,
                            },
                            {
                                "codigo_extracto": 52,
                                "cantidad": 319,
                            },
                            {
                                "codigo_extracto": 53,
                                "cantidad": 1108,
                            },
                            {
                                "codigo_extracto": 54,
                                "cantidad": 214,
                            },
                        ],
                        "cupones_ganadores_unicos": 2435,
                        "tiempos_service": {
                            "total_segundos": 1.39,
                        },
                        "zip": {
                            "archivo_zip": "Aciertos260810PV_TS.zip",
                            "archivo_dbf": "Aciertos260810PV.dbf",
                            "carpeta": (
                                "uploads/20260810/PV/dbf"
                            ),
                        },
                        "tiempo_total_zip": 1.41,
                    }
                }
            },
        },
        400: {
            "description": "❌ Archivo ZIP inválido.",
            "content": {
                "application/json": {
                    "examples": {
                        "extension_invalida": {
                            "summary": "Extensión incorrecta",
                            "value": {
                                "ok": False,
                                "code": "invalid_zip_extension",
                                "message": (
                                    "El archivo debe tener extensión .zip"
                                ),
                            },
                        },
                        "zip_invalido": {
                            "summary": "ZIP inválido o dañado",
                            "value": {
                                "ok": False,
                                "code": "invalid_zip_file",
                                "message": (
                                    "El archivo ZIP es inválido "
                                    "o está dañado"
                                ),
                            },
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
        404: {
            "description": (
                "❌ No se encontró un archivo DBF dentro del ZIP."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "dbf_file_not_found",
                        "message": (
                            "No se encontró archivo .dbf "
                            "dentro del ZIP"
                        ),
                    }
                }
            },
        },
        422: {
            "description": (
                "❌ Parámetros de entrada inválidos "
                "o archivo requerido no enviado."
            ),
        },
        500: {
            "description": (
                "❌ Error interno al procesar el archivo DBF."
            ),
        },
    },
}