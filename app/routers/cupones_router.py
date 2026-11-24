
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.constants.roles import ADMIN, OPERADOR, CONSULTA
from app.security.dependencies import require_role
from app.services.cupones_service import listar_cupones


router = APIRouter(
    prefix="/cupones",
    tags=["Consulta de Cupones"],
    dependencies=[
        Depends(require_role(ADMIN, OPERADOR, CONSULTA))
    ],
)


def convertir_fecha(valor: int, campo: str):
    """
    Convierte una fecha AAAAMMDD a date.
    Devuelve HTTP 422 si el formato o la fecha no son válidos.
    """
    try:
        fecha = datetime.strptime(str(valor), "%Y%m%d").date()

        if fecha.strftime("%Y%m%d") != str(valor):
            raise ValueError()

        return fecha

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{campo} debe tener formato AAAAMMDD "
                "y ser una fecha valida"
            ),
        )


@router.get("")
def consultar_cupones(
    fecha_desde: int | None = Query(
        None,
        description="Fecha inicial en formato AAAAMMDD",
    ),
    fecha_hasta: int | None = Query(
        None,
        description="Fecha final opcional en formato AAAAMMDD",
    ),
    fecha: int | None = Query(
        None,
        description="Parametro anterior de fecha (compatibilidad)",
        deprecated=True,
    ),
    turno: Literal["PV", "PR", "M", "V", "N"] | None = Query(
        None,
        description="Turno del sorteo",
    ),
    pagina: int = Query(
        1,
        ge=1,
        description="Numero de pagina",
    ),
    limite: int = Query(
        20,
        ge=1,
        le=100,
        description="Cantidad de cupones por pagina",
    ),
    agencia: int | None = Query(
        None,
        ge=0,
        description="Filtrar por agencia",
    ),
    subagencia: int | None = Query(
        None,
        ge=0,
        description="Filtrar por subagencia",
    ),
    maquina: int | None = Query(
        None,
        ge=0,
        description="Filtrar por maquina",
    ),
    numero_cupon: int | None = Query(
        None,
        ge=0,
        description="Filtrar por numero de cupon",
    ),
    codigo_extracto: int | None = Query(
        None,
        ge=0,
        description="Filtrar por codigo de extracto",
    ),
    solo_ganadores: bool = Query(
        False,
        description="Mostrar solamente cupones premiados",
    ),
    anulados: bool = Query(
        False,
        description="Mostrar cupones anulados",
    ),
):
    # --------------------------------------------------
    # 1. VALIDAR FECHA OBLIGATORIA
    # --------------------------------------------------

    # Compatibilidad con consultas anteriores.
    if fecha_desde is None and fecha is None:
        raise HTTPException(
            status_code=422,
            detail="Debe informar fecha_desde",
        )

    # Si se informan ambos parámetros,
    # deben tener el mismo valor.
    if fecha_desde is not None and fecha is not None:
        if fecha_desde != fecha:
            raise HTTPException(
                status_code=422,
                detail=(
                    "fecha y fecha_desde "
                    "no pueden ser diferentes"
                ),
            )

    fecha_inicio = (
        fecha_desde
        if fecha_desde is not None
        else fecha
    )

    # --------------------------------------------------
    # 2. CONVERTIR Y VALIDAR FECHAS
    # --------------------------------------------------

    desde = convertir_fecha(
        fecha_inicio,
        "fecha_desde",
    )

    hasta = (
        convertir_fecha(
            fecha_hasta,
            "fecha_hasta",
        )
        if fecha_hasta is not None
        else desde
    )

    # La fecha final no puede ser anterior a la inicial.
    if hasta < desde:
        raise HTTPException(
            status_code=422,
            detail=(
                "fecha_hasta no puede ser "
                "anterior a fecha_desde"
            ),
        )

    # Máximo de 7 días calendario inclusive.
    if hasta - desde > timedelta(days=6):
        raise HTTPException(
            status_code=422,
            detail=(
                "El rango maximo permitido "
                "es de 7 dias calendario"
            ),
        )

    # --------------------------------------------------
    # 3. VALIDAR FILTRO DE ANULADOS
    # --------------------------------------------------

    # Todavía no se confirmó cómo identificar
    # los cupones anulados en la base de datos.
    # Evitamos devolver un error 500.
    if anulados:
        raise HTTPException(
            status_code=422,
            detail=(
                "El filtro de cupones anulados "
                "todavía no está disponible"
            ),
        )

    # --------------------------------------------------
    # 4. CONSULTAR CUPONES
    # --------------------------------------------------

    return listar_cupones(
        fecha_desde=int(desde.strftime("%Y%m%d")),
        fecha_hasta=int(hasta.strftime("%Y%m%d")),
        turno=turno,
        pagina=pagina,
        limite=limite,
        agencia=agencia,
        subagencia=subagencia,
        maquina=maquina,
        numero_cupon=numero_cupon,
        codigo_extracto=codigo_extracto,
        solo_ganadores=solo_ganadores,
        anulados=anulados,
    )
