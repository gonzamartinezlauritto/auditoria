
from app.database import get_connection
from app.repositories.cupones_repository import obtener_cupones


def listar_cupones(
    fecha_desde: int,
    fecha_hasta: int,
    turno: str | None = None,
    pagina: int = 1,
    limite: int = 20,
    agencia: int | None = None,
    subagencia: int | None = None,
    maquina: int | None = None,
    numero_cupon: int | None = None,
    codigo_extracto: int | None = None,
    solo_ganadores: bool = False,
    anulados: bool = False,
) -> dict:

    conn = get_connection()

    try:
        return obtener_cupones(
            conn=conn,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
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

    finally:
        conn.close()
