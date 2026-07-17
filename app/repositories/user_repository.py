from psycopg2.extensions import connection

from app.repositories.base_repository import get_dict_cursor


USER_PUBLIC_COLUMNS = """
    id,
    username,
    nombre,
    email,
    rol,
    activo,
    created_at,
    updated_at
"""


INSERT_USUARIO_SQL = f"""
    INSERT INTO usuarios (
        username,
        nombre,
        email,
        password_hash,
        rol,
        activo
    )
    VALUES (%s, %s, %s, %s, %s, TRUE)
    RETURNING {USER_PUBLIC_COLUMNS}
"""


FIND_BY_ID_SQL = f"""
    SELECT {USER_PUBLIC_COLUMNS}
    FROM usuarios
    WHERE id = %s
"""


FIND_BY_USERNAME_SQL = """
    SELECT
        id,
        username,
        nombre,
        email,
        password_hash,
        rol,
        activo,
        created_at,
        updated_at
    FROM usuarios
    WHERE username = %s
"""


FIND_BY_EMAIL_SQL = """
    SELECT
        id,
        username,
        nombre,
        email,
        password_hash,
        rol,
        activo,
        created_at,
        updated_at
    FROM usuarios
    WHERE email = %s
"""


FIND_BY_USERNAME_OR_EMAIL_SQL = """
    SELECT
        id,
        username,
        nombre,
        email,
        password_hash,
        rol,
        activo,
        created_at,
        updated_at
    FROM usuarios
    WHERE username = %s
       OR email = %s
"""


FIND_ALL_SQL = f"""
    SELECT {USER_PUBLIC_COLUMNS}
    FROM usuarios
    ORDER BY id
"""


UPDATE_USUARIO_SQL = f"""
    UPDATE usuarios
    SET
        username = %s,
        nombre = %s,
        email = %s,
        rol = %s,
        updated_at = NOW()
    WHERE id = %s
    RETURNING {USER_PUBLIC_COLUMNS}
"""


UPDATE_PASSWORD_SQL = """
    UPDATE usuarios
    SET
        password_hash = %s,
        updated_at = NOW()
    WHERE id = %s
    RETURNING id
"""


UPDATE_ESTADO_SQL = f"""
    UPDATE usuarios
    SET
        activo = %s,
        updated_at = NOW()
    WHERE id = %s
    RETURNING {USER_PUBLIC_COLUMNS}
"""


DELETE_USUARIO_SQL = """
    DELETE FROM usuarios
    WHERE id = %s
    RETURNING id
"""


def insert_usuario(
    conn: connection,
    username: str,
    nombre: str,
    email: str,
    password_hash: str,
    rol: str,
):
    with get_dict_cursor(conn) as cur:
        cur.execute(
            INSERT_USUARIO_SQL,
            (
                username,
                nombre,
                email,
                password_hash,
                rol,
            ),
        )
        return cur.fetchone()


def find_by_id(conn: connection, usuario_id: int):
    with get_dict_cursor(conn) as cur:
        cur.execute(FIND_BY_ID_SQL, (usuario_id,))
        return cur.fetchone()


def find_by_username(conn: connection, username: str):
    with get_dict_cursor(conn) as cur:
        cur.execute(FIND_BY_USERNAME_SQL, (username,))
        return cur.fetchone()


def find_by_email(conn: connection, email: str):
    with get_dict_cursor(conn) as cur:
        cur.execute(FIND_BY_EMAIL_SQL, (email,))
        return cur.fetchone()


def find_by_username_or_email(conn: connection, usuario: str):
    with get_dict_cursor(conn) as cur:
        cur.execute(
            FIND_BY_USERNAME_OR_EMAIL_SQL,
            (
                usuario,
                usuario,
            ),
        )
        return cur.fetchone()


def find_all(conn: connection):
    with get_dict_cursor(conn) as cur:
        cur.execute(FIND_ALL_SQL)
        return cur.fetchall()


def update_usuario(
    conn: connection,
    usuario_id: int,
    username: str,
    nombre: str,
    email: str,
    rol: str,
):
    with get_dict_cursor(conn) as cur:
        cur.execute(
            UPDATE_USUARIO_SQL,
            (
                username,
                nombre,
                email,
                rol,
                usuario_id,
            ),
        )
        return cur.fetchone()


def update_password(
    conn: connection,
    usuario_id: int,
    password_hash: str,
):
    with get_dict_cursor(conn) as cur:
        cur.execute(
            UPDATE_PASSWORD_SQL,
            (
                password_hash,
                usuario_id,
            ),
        )
        return cur.fetchone()


def update_estado(
    conn: connection,
    usuario_id: int,
    activo: bool,
):
    with get_dict_cursor(conn) as cur:
        cur.execute(
            UPDATE_ESTADO_SQL,
            (
                activo,
                usuario_id,
            ),
        )
        return cur.fetchone()


def delete_usuario(conn: connection, usuario_id: int):
    with get_dict_cursor(conn) as cur:
        cur.execute(DELETE_USUARIO_SQL, (usuario_id,))
        return cur.fetchone()
