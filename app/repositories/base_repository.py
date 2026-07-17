from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def get_dict_cursor(conn: connection):
    """
    Devuelve un cursor que transforma cada fila en un diccionario.

    Ejemplo:
        {
            "id": 1,
            "username": "gonzalo"
        }
    """
    return conn.cursor(cursor_factory=RealDictCursor)