from pydantic import BaseModel, Field


# ============================================================
# ITEM DE RESULTADOS DE UN EXTRACTO
# ============================================================

class ResultadoExtractoItem(BaseModel):
    codigo_extracto: int = Field(
        ...,
        gt=0,
        description="Código del extracto.",
        examples=[50],
    )

    numeros: list[str] = Field(
        ...,
        min_length=20,
        max_length=20,
        description=(
            "Lista completa de los 20 resultados "
            "del extracto, ordenados del puesto 1 al 20."
        ),
        examples=[
            [
                "4162",
                "6470",
                "6973",
                "8417",
                "0166",
                "4840",
                "3857",
                "3866",
                "7330",
                "6115",
                "5125",
                "5013",
                "0088",
                "1603",
                "0627",
                "7347",
                "6596",
                "0772",
                "9723",
                "3320",
            ]
        ],
    )


# ============================================================
# REQUEST - CARGAR RESULTADOS
# ============================================================

class CargarResultadosRequest(BaseModel):
    fecha: int = Field(
        ...,
        gt=0,
        description=(
            "Fecha del sorteo en formato AAAAMMDD."
        ),
        examples=[20260810],
    )

    turno: str = Field(
        ...,
        min_length=1,
        description=(
            "Código del turno del sorteo."
        ),
        examples=["PV"],
    )

    resultados: list[ResultadoExtractoItem] = Field(
        ...,
        min_length=1,
        description=(
            "Listado de extractos con sus "
            "20 resultados."
        ),
    )


# ============================================================
# REQUEST - MODIFICAR RESULTADOS
# ============================================================

class ModificarResultadosRequest(
    CargarResultadosRequest
):
    """
    Request para modificar uno o varios
    extractos previamente cargados.

    Se utiliza la misma estructura que para la carga:
    fecha, turno y uno o varios extractos con
    sus 20 resultados completos.
    """

    pass


# ============================================================
# REPORTE DE CÁLCULO POR EXTRACTO
# ============================================================

class ReporteCalculoItem(BaseModel):
    codigo_extracto: int = Field(
        ...,
        description="Código del extracto.",
        examples=[50],
    )

    sorteo: str = Field(
        ...,
        description="Nombre del sorteo.",
        examples=["La Previa Ctes."],
    )

    cupones_jugados: int = Field(
        ...,
        description=(
            "Cantidad de cupones jugados "
            "para el extracto."
        ),
        examples=[14750],
    )

    recaudacion: float = Field(
        ...,
        description=(
            "Importe total recaudado "
            "para el extracto."
        ),
        examples=[14258278.0],
    )

    importe_premiados: float = Field(
        ...,
        description=(
            "Importe total de premios "
            "calculados para el extracto."
        ),
        examples=[3735313.5],
    )

    apuestas_premiadas: int = Field(
        ...,
        description=(
            "Cantidad de apuestas/cupones "
            "premiados del extracto."
        ),
        examples=[355],
    )


# ============================================================
# RESPONSE - MODIFICAR RESULTADOS
# ============================================================

class ModificarResultadosResponse(BaseModel):
    ok: bool = Field(
        ...,
        description=(
            "Indica si la modificación "
            "y el recálculo finalizaron correctamente."
        ),
        examples=[True],
    )

    fecha: int = Field(
        ...,
        description=(
            "Fecha del sorteo en formato AAAAMMDD."
        ),
        examples=[20260810],
    )

    turno: str = Field(
        ...,
        description="Código del turno.",
        examples=["PV"],
    )

    reportes: list[ReporteCalculoItem] = Field(
        ...,
        description=(
            "Reporte completo actualizado de todos "
            "los extractos correspondientes al turno."
        ),
    )

    cupones_ganadores_unicos: int = Field(
        ...,
        description=(
            "Cantidad global de cupones ganadores "
            "únicos para la fecha y turno."
        ),
        examples=[2435],
    )