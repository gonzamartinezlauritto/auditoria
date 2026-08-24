from contextlib import contextmanager
from typing import Generator

from psycopg2.extensions import connection

from app.database import get_connection


@contextmanager
def transaction() -> Generator[connection, None, None]:
    """
    Administra una transacción de base de datos.

    - Abre una conexión.
    - Hace commit si la operación termina correctamente.
    - Hace rollback si ocurre una excepción.
    - Cierra siempre la conexión.
    """
    conn = get_connection()

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()