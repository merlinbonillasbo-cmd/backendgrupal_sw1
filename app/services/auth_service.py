import bcrypt


def hash_password(password: str) -> str:
    """
    Recibe una contraseña en texto plano, genera un hash con bcrypt
    y devuelve el resultado como string para guardarlo en la base de datos.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)

    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con el hash guardado.
    Devuelve True si coinciden, False si no.
    """
    pwd_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(pwd_bytes, hashed_bytes)