import bcrypt

def hash_password(password: str) -> str:
    """
    Toma una contraseña en texto plano, genera un salt moderno
    y devuelve la contraseña encriptada como un string listo para la BD.
    """
    # Convertimos el texto plano a bytes
    pwd_bytes = password.encode('utf-8')
    # Generamos el salt y encriptamos
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # Devolvemos el resultado como string para guardarlo en la base de datos
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con el hash guardado en la BD.
    Devuelve True si coinciden, False si no.
    """
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # Bcrypt se encarga de verificar de forma segura contra ataques de temporización
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)