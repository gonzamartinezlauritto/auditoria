CARGAR_EXTRACTOS_DOCS = {
    "summary": "Cargar resultados de los 7 extractos",
    "description": (
        "Carga los resultados oficiales de los 7 extractos "
        "correspondientes a una fecha y turno.\n\n"
        "**Reglas:**\n"
        "- Deben enviarse exactamente 7 extractos.\n"
        "- Cada extracto debe contener exactamente 20 números.\n"
        "- Los números deben respetar el orden de salida del 1 al 20.\n"
        "- Los números deben enviarse como texto para conservar ceros iniciales.\n\n"
        "**Roles permitidos:** ADMIN y OPERADOR."
    ),
    "responses": {
        200: {
            "description": "✅ Extractos cargados correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "turno": "PV",
                        "extractos_cargados": 5,
                        "resultados_insertados": 100,
                    }
                }
            },
        },
        401: {
            "description": "❌ No autenticado.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "invalid_token",
                        "message": (
                            "Token de acceso ausente o inválido"
                        ),
                    }
                }
            },
        },
        403: {
            "description": "❌ Acceso denegado.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": "forbidden",
                        "message": (
                            "El usuario no posee permisos "
                            "para realizar esta operación"
                        ),
                    }
                }
            },
        },
        422: {
            "description": (
                "❌ Datos inválidos. Deben enviarse exactamente "
                "7 extractos y cada uno debe contener 20 números."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "cantidad_extractos": {
                            "summary": (
                                "Cantidad incorrecta de extractos"
                            ),
                            "value": {
                                "detail": [
                                    {
                                        "type": "too_short",
                                        "loc": [
                                            "body",
                                            "resultados",
                                        ],
                                        "msg": (
                                            "List should have at least "
                                            "7 items after validation"
                                        ),
                                    }
                                ]
                            },
                        },
                        "cantidad_numeros": {
                            "summary": (
                                "Cantidad incorrecta de números"
                            ),
                            "value": {
                                "detail": [
                                    {
                                        "type": "too_short",
                                        "loc": [
                                            "body",
                                            "resultados",
                                            0,
                                            "numeros",
                                        ],
                                        "msg": (
                                            "List should have at least "
                                            "20 items after validation"
                                        ),
                                    }
                                ]
                            },
                        },
                    }
                }
            },
        },
    },
}


CARGAR_EXTRACTOS_EXAMPLES = {
    "carga_completa": {
        "summary": "Carga completa de 7 extractos",
        "description": (
            "Los 7 extractos deben enviarse juntos "
            "en una única solicitud."
        ),
        "value": {
            "fecha": 20260810,
            "turno": "PV",
            "resultados": [
                {
                    "codigo_extracto": 50,
                    "numeros": [
                        "3359", "4249", "6765", "2210",
                        "5357", "4051", "6479", "5895",
                        "9818", "7106", "8184", "0922",
                        "3165", "1275", "2968", "7639",
                        "0682", "6683", "9474", "2243",
                    ],
                },
                {
                    "codigo_extracto": 51,
                    "numeros": [
                        "5603", "1545", "6242", "7770",
                        "0864", "3515", "8708", "4234",
                        "4161", "6774", "0453", "4564",
                        "8771", "1483", "6517", "7932",
                        "3418", "9920", "0969", "2054",
                    ],
                },
                {
                    "codigo_extracto": 52,
                    "numeros": [
                        "1741", "6331", "0931", "5727",
                        "0972", "8682", "2189", "8937",
                        "8887", "5818", "2303", "2124",
                        "0719", "3091", "1312", "4863",
                        "8789", "2778", "2645", "9750",
                    ],
                },
                {
                    "codigo_extracto": 53,
                    "numeros": [
                        "4233", "8215", "2918", "5443",
                        "0390", "8269", "0779", "3774",
                        "2177", "9787", "3455", "5307",
                        "0281", "4966", "3352", "1011",
                        "6753", "2421", "5090", "2442",
                    ],
                },
                {
                    "codigo_extracto": 54,
                    "numeros": [
                        "6778", "7082", "8416", "5737",
                        "9291", "8666", "2457", "7486",
                        "7231", "5318", "8352", "6886",
                        "3460", "7666", "8883", "7246",
                        "7577", "4966", "7103", "2758",
                    ],
                },
            ],
        },
    },
}


CONSULTAR_EXTRACTOS_DOCS = {
    "summary": "Consultar extractos cargados",
    "description": (
        "Obtiene los resultados de los extractos cargados "
        "para una fecha determinada.\n\n"
        "**Roles permitidos:** ADMIN, OPERADOR y CONSULTA."
    ),
    "responses": {
        200: {
            "description": "✅ Consulta realizada correctamente.",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "fecha": 20260810,
                        "resultados": {
                            "PV": {
                                "50": {
                                    "codigo_extracto": 50,
                                    "nombre_extracto": (
                                        "La Previa Ctes."
                                    ),
                                    "numeros": [
                                        {
                                            "orden": 1,
                                            "numero": "3359",
                                        },
                                        {
                                            "orden": 2,
                                            "numero": "4249",
                                        },
                                    ],
                                }
                            }
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
    },
}