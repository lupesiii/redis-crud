from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field, ConfigDict


class ProdutosCadastrados(BaseModel):
    produtoId: str = Field(alias="id_produto")
    nome: str
    precoEmCentavos: int


class Vendedor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Annotated[str, BeforeValidator(str)] | None = Field(default=None, alias="_id")
    nomeLoja: str = Field(alias="nome_loja")
    usuarioId: str = Field(alias="usuario_id")
    produtosCadastrados: list[ProdutosCadastrados] = Field(alias="produtos_cadastrados")
    vendas: list


class VendedorProduto(BaseModel):
    vendedor_id: str
    nome_loja: str
