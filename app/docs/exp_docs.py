TEST_EXP_DOCS = {
    "summary": "Verificar módulo EXP",
    "description": (
        "Comprueba que el módulo de procesamiento EXP "
        "se encuentra disponible.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Módulo EXP disponible.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Router EXP funcionando",
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
    },
}


UPLOAD_EXP_DOCS = {
    "summary": "Subir archivo EXP",
    "description": (
        "Sube un archivo con extensión `.exp` al servidor "
        "sin ejecutar el procesamiento de apuestas.\n\n"
        "**Archivo permitido:** `.exp`\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Archivo EXP subido correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Archivo EXP subido correctamente",
                        "filename": "quiniela.exp",
                        "path": "uploads/quiniela.exp",
                        "size_bytes": 15482736,
                    }
                }
            },
        },
        400: {
            "description": "❌ Archivo inválido.",
            "content": {
                "application/json": {
                    "examples": {
                        "extension_invalida": {
                            "summary": "Extensión incorrecta",
                            "value": {
                                "ok": False,
                                "code": "invalid_exp_extension",
                                "message": (
                                    "El archivo debe tener extensión .exp"
                                ),
                            },
                        },
                        "nombre_invalido": {
                            "summary": "Nombre de archivo inválido",
                            "value": {
                                "ok": False,
                                "code": "invalid_file_name",
                                "message": (
                                    "El archivo no posee un nombre válido"
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
        422: {
            "description": "❌ No se envió el archivo requerido.",
        },
    },
}


PROCESS_EXP_DOCS = {
    "summary": "Procesar archivo EXP",
    "description": (
        "Sube y procesa un archivo `.exp` para una fecha "
        "y turno determinados.\n\n"
        "Durante el procesamiento se cargan las apuestas "
        "válidas del archivo en la base de datos.\n\n"
        "Los registros cuyo turno no pertenezca a los turnos "
        "permitidos son ignorados sin interrumpir la carga.\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Archivo EXP procesado correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "archivo_origen": "quiniela.exp",
                        "fecha": 20260810,
                        "turno": "PV",
                        "total_archivo": 125000,
                        "insertados": 124800,
                        "ignorados_por_duplicado": 200,
                        "cargados_turno": 30125,
                        "modo": (
                            "copy_tmp_insert_on_conflict_do_nothing"
                        ),
                    }
                }
            },
        },
        400: {
            "description": "❌ Archivo EXP inválido.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "invalid_exp_extension",
                        "message": (
                            "El archivo debe tener extensión .exp"
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
                "❌ El archivo no contiene apuestas "
                "para la fecha o turno solicitado."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "no_bets_for_requested_draw",
                        "message": (
                            "El archivo procesado no contiene apuestas "
                            "para la fecha y turno solicitados"
                        ),
                    }
                }
            },
        },
        500: {
            "description": "❌ Error interno al procesar el EXP.",
        },
    },
}


PROCESS_EXP_ZIP_DOCS = {
    "summary": "Procesar ZIP con archivo EXP",
    "description": (
        "Sube un archivo ZIP, localiza el archivo `.exp` "
        "contenido dentro del ZIP y ejecuta su procesamiento.\n\n"
        "Si el ZIP contiene `quiniela.exp`, ese archivo tiene prioridad. "
        "Si no, se utiliza el primer archivo con extensión `.exp` encontrado.\n\n"
        "**Archivo permitido:** `.zip`\n\n"
        "**Turnos válidos:** PV, PR, M, V y N.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ ZIP procesado correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "archivo_origen": "quiniela.exp",
                        "fecha": 20260810,
                        "turno": "PV",
                        "total_archivo": 125000,
                        "insertados": 124800,
                        "ignorados_por_duplicado": 200,
                        "cargados_turno": 30125,
                        "zip": {
                            "archivo_zip": "quiniela.zip",
                            "archivo_exp": "quiniela.exp",
                            "carpeta": "uploads/20260810/PV/exp",
                        },
                    }
                }
            },
        },
        400: {
            "description": "❌ ZIP inválido.",
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
                        "zip_danado": {
                            "summary": "ZIP inválido o dañado",
                            "value": {
                                "ok": False,
                                "code": "invalid_zip_file",
                                "message": (
                                    "El archivo ZIP es inválido o está dañado"
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
            "description": "❌ No se encontró un archivo EXP dentro del ZIP.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "exp_file_not_found",
                        "message": (
                            "No se encontró el archivo quiniela.exp "
                            "dentro del ZIP"
                        ),
                    }
                }
            },
        },
        422: {
            "description": (
                "❌ El EXP extraído no contiene apuestas "
                "para la fecha o turno solicitado."
            ),
        },
        500: {
            "description": "❌ Error interno al procesar el archivo.",
        },
    },
}