from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Genera un hash seguro de la contraseña utilizando
    el algoritmo recomendado por pwdlib, actualmente Argon2.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verifica una contraseña en texto plano contra
    el hash almacenado en la base de datos.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )