GET_ESTADO_PROCESO_DOCS = {
    "summary": "Consultar proceso completo de Quiniela",
    "description": (
        "Obtiene el estado completo del proceso de Quiniela "
        "para una fecha determinada. "
        "Devuelve todos los turnos y extractos disponibles "
        "en la jornada, junto con los estados de procesamiento, "
        "recaudación, cupones jugados, importes de aciertos, "
        "cupones premiados por Auditoría y cupones premiados "
        "informados por el sistema."
    ),
    "responses": {
        200: {
            "description": (
                "Estado completo de la jornada obtenido correctamente."
            ),
        },
        401: {
            "description": "Usuario no autenticado.",
        },
        403: {
            "description": "Usuario sin permisos.",
        },
    },
}