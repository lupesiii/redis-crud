import uuid
from lib.connection import dbMongo, dbRedis
from models.ErroException import ErroException


def loginUsuario(email: str, senha: str):
    email = email.strip()
    senha = senha.strip()

    if not email or not senha:
        raise ErroException("Valores nulos não são permitidos")

    try:
        usuario = dbMongo.usuarios.find_one({"email": email, "senha": senha})
    except Exception:
        raise ErroException("Usuário não encontrado usuário")

    if not usuario:
        raise ErroException("Email ou senha inválido")

    token = str(uuid.uuid4())

    try:
        dbRedis.set(f"sessao:{token}", str(usuario["_id"]))
        dbRedis.expire(f"sessao:{token}", 60)
    except Exception:
        raise ErroException("Erro ao salvar token")

    return token


def verificarSessao(token: str):
    sessao = dbRedis.get(f"sessao:{token}")

    if sessao is None:
        raise Exception("Sessão expirada")

    return True
