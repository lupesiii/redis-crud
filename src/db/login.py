import uuid

from InquirerPy import inquirer
from lib.connection import dbMongo, dbRedis
from lib.inquirrerPy import verificarEmail, verificarVazio
from models.ErroException import ErroException


def login():
    email = (
        inquirer.text(message="Digite seu email: ", validate=verificarEmail)
        .execute()
        .strip()
    )
    senha = (
        inquirer.secret(message="Digite sua senha: ", validate=verificarVazio)
        .execute()
        .strip()
    )

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
        dbRedis.expire(f"sessao:{token}", 10)
    except Exception:
        raise ErroException("Erro ao salvar token")

    return token


def loginUsuario():
    token = None
    while token is None:
        try:
            token = login()
        except ErroException as e:
            print(e)
    return token


def verificarSessao(token: str):
    sessao = dbRedis.get(f"sessao:{token}")

    if sessao is None:
        return False

    return True
