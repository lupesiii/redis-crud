from typing import Any
from lib.connection import dbRedis, dbMongo
from pydantic import ValidationError

from models.Vendedor import Vendedor
from models.ErroException import ErroException


def validarVendedor(dados):
    try:
        return Vendedor.model_validate(dados)
    except ValidationError as e:
        raise ErroException(f"Dados do produto inválidos: {e}")


def mapearVendedor(vendedor: Vendedor) -> Any:
    return {
        "nome_loja": vendedor.nomeLoja,
        "usuario_id": vendedor.usuarioId,
    }


def cadastrarVendedor():
    try:
        vendedores = list(dbMongo.vendedores.find().sort("_id"))
        vendedores = [validarVendedor(vendedor) for vendedor in vendedores]

        for vendedor in vendedores:
            dbRedis.hset(f"vendedor_id:{vendedor.id}", mapping=mapearVendedor(vendedor))
        return vendedores

    except ErroException:
        raise
    except Exception:
        raise ErroException("Erro ao copiar produtos para o Redis")


def buscarVendedor(vendedorId: str):
    try:
        dados = dbRedis.hgetall(f"vendedor_id:{vendedorId}")
        if not dados:
            raise ErroException("Produto não encontrado no Redis")

        return validarVendedor(
            {
                "_id": vendedorId,
                "nome_loja": dados["nome_loja"],
                "usuario_id": dados["usuario_id"],
                "produtos_cadastrados": [],
                "vendas": [],
            }
        )

    except ErroException:
        raise
    except Exception:
        raise ErroException("Erro ao consultar produto no Redis")


def listarVendedoresRedis():
    try:
        ids = {
            chave.removeprefix("vendedor_id:")
            for chave in dbRedis.scan_iter(match="vendedor_id:*")
        }
        return [buscarVendedor(id) for id in sorted(ids)]
    except ErroException:
        raise
    except Exception:
        raise ErroException("Erro ao listar produtos no Redis")


def atualizarVendedorRedis(vendedorId: str, dados):
    try:
        alteracoes = dict(dados)

        if not alteracoes or any(valor is None for valor in alteracoes.values()):
            raise ErroException("Informe campos de atualização com valores não nulos")

        vendedorAtual = buscarVendedor(vendedorId)
        vendedor = validarVendedor({**vendedorAtual.model_dump(), **alteracoes})
        dbRedis.hset(f"vendedor_id:{vendedorId}", mapping=mapearVendedor(vendedor))

        return vendedor
    except ValidationError as erro:
        raise ErroException(f"Atualização inválida: {erro}")
    except ErroException:
        raise
    except Exception as erro:
        raise ErroException("Erro ao atualizar produto no Redis; tente novamente")


def excluirVendedorRedis(vendedorId: str):
    try:
        if not dbRedis.delete(f"vendedor_id:{vendedorId}"):
            raise ErroException("Vendedor não encontrado")
    except ErroException:
        raise
    except Exception:
        raise ErroException("Erro ao excluir produto do Redis")
