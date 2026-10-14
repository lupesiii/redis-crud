from typing import Any

from bson import ObjectId
from pydantic import ValidationError

from lib.connection import dbMongo, dbRedis
from models.ErroException import ErroException
from models.Produto import Produto, ProdutoUpdate


def validarProduto(dados):
    try:
        return Produto.model_validate(dados)
    except ValidationError as erro:
        raise ErroException(f"Dados do produto inválidos: {erro}")


def mapearProduto(produto: Produto) -> Any:
    return {
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco_em_centavos": produto.precoEmCentavos,
        "estoque": produto.estoque,
        "imagem": produto.imagem,
        "vendedor_id": produto.vendedor.vendedor_id,
        "nome_loja": produto.vendedor.nome_loja,
    }


def cadastrarProduto(nomeLoja: str):
    try:
        produtos = list(
            dbMongo.produtos.find({"vendedor.nome_loja": nomeLoja}).sort("_id", 1)
        )
        produtos = [validarProduto(produto) for produto in produtos]

        for produto in produtos:
            dbRedis.hset(f"produto_id:{produto.id}", mapping=mapearProduto(produto))

        return produtos

    except ErroException:
        raise
    except Exception as erro:
        raise ErroException("Erro ao copiar produtos para o Redis")


def buscarProdutos(produtoId: str):
    try:
        dados = dbRedis.hgetall(f"produto_id:{produtoId}")
        if not dados:
            raise ErroException("Produto não encontrado no Redis")
        return validarProduto(
            {
                "_id": produtoId,
                "nome": dados["nome"],
                "descricao": dados["descricao"],
                "precoEmCentavos": dados["preco_em_centavos"],
                "estoque": dados["estoque"],
                "imagem": dados["imagem"],
                "vendedor": {
                    "vendedor_id": dados["vendedor_id"],
                    "nome_loja": dados["nome_loja"],
                },
            }
        )
    except ErroException:
        raise
    except Exception:
        raise ErroException("Erro ao consultar produto no Redis")


def listarProdutosRedis():
    try:
        ids = {
            chave.removeprefix("produto_id:")
            for chave in dbRedis.scan_iter(match="produto_id:*")
        }
        return [buscarProdutos(produtoId) for produtoId in sorted(ids)]
    except ErroException:
        raise
    except Exception as erro:
        raise ErroException("Erro ao listar produtos no Redis")


def atualizarProdutoRedis(produtoId: str, dados):
    try:

        alteracoes = ProdutoUpdate.model_validate(dados).model_dump(exclude_unset=True)

        if not alteracoes or any(valor is None for valor in alteracoes.values()):
            raise ErroException("Informe campos de atualização com valores não nulos")

        atual = buscarProdutos(produtoId)
        produto = validarProduto({**atual.model_dump(), **alteracoes})
        dbRedis.hset(f"produto_id:{produtoId}", mapping=mapearProduto(produto))

        return produto
    except ValidationError as erro:
        raise ErroException(f"Atualização inválida: {erro}")
    except ErroException:
        raise
    except Exception as erro:
        raise ErroException("Erro ao atualizar produto no Redis; tente novamente")


def excluirProdutoRedis(produtoId: str):
    try:
        if not dbRedis.delete(f"produto_id:{produtoId}"):
            raise ErroException("Produto não encontrado no Redis")
        return True
    except ErroException:
        raise
    except Exception as erro:
        raise ErroException("Erro ao excluir produto do Redis")
